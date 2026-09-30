"""m55_junk_genre_v31_verify — v3.1 장르 정규식(m54) 결과의 적대 검증.

m54 의 산출(genre_hits_v31.parquet·genre_counts_v31.json)에 의존하지 않고, 정규식 파일
genre_patterns_v31.json·genre_patterns_v3.json 을 서지 정본(s0_lib.BIB_STORE)에 직접 적용해
유형별 전수 적중을 다시 센다. 그 밖에 (1) JSON 정규식과 m54 코드 PATTERNS 의 동일성,
(2) 지시된 하위 형태 제외가 실제로 적용됐는지 제목 프로브(파이썬 re · DuckDB RE2 양쪽),
(3) 블라인드 판독 결과 × 감사 정답표의 유형별 오탐률, (4) 2차 판정 대상의 포괄 여부를 계산한다.

산출(pipeline/out/_junk_v3/):
  m55_recount.json        유형별 독립 재계산 건수와 보고값 대조
  m55_probes.json         제목 프로브 결과(re·RE2 일치 여부 포함)
  m55_audit_fp.json       유형별·하위 형태별 오탐률(research ÷ n)·borderline 비율
  m55_audit_merged.parquet 판독 결과 + 정답표 + 제목(600행)

사용: .venv/bin/python pipeline/scripts/m55_junk_genre_v31_verify.py [recount|probe|audit|all]
"""
import json
import os
import re
import sys
import time

import duckdb
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s0_lib as L  # noqa: E402
import m54_junk_genre_v31 as M54  # noqa: E402

OUT_DIR = f'{L.PIPE}/out/_junk_v3'
P31_FILE = f'{OUT_DIR}/genre_patterns_v31.json'
P3_FILE = f'{OUT_DIR}/genre_patterns_v3.json'
SCRATCH = M54.SCRATCH
CALLS = f'{SCRATCH}/v31_blind_calls.txt'
KEY = f'{OUT_DIR}/v31_audit_key.parquet'
SECOND = f'{OUT_DIR}/second_pass_candidates.parquet'


def con():
    c = duckdb.connect()
    c.execute('SET threads=32')
    return c


def sql_pat(p):
    return ('(?i)' + p).replace("'", "''")


def load_patterns():
    p31 = json.load(open(P31_FILE))
    p3 = json.load(open(P3_FILE))
    return p3, p31


def recount():
    """정규식 파일을 BIB_STORE 전수에 직접 적용해 유형별 건수를 다시 센다(v2 미적중·철회 제외)."""
    p3, p31 = load_patterns()
    same = {k: (p31[k] == M54.PATTERNS.get(k)) for k in p31}
    c = con()
    v2 = sql_pat(L.JUNK.pattern[4:])
    cols3 = ',\n'.join(f"regexp_matches(t, '{sql_pat(p)}') as \"v3_{k}\"" for k, p in p3.items())
    cols31 = ',\n'.join(f"regexp_matches(t, '{sql_pat(p)}') as \"v31_{k}\"" for k, p in p31.items())
    any3 = ' or '.join(f'"v3_{k}"' for k in p3)
    any31 = ' or '.join(f'"v31_{k}"' for k in p31)
    t0 = time.time()
    c.execute(f"""
      create table f as
      with b as (select work_id, coalesce(title_display,'') t from '{L.BIB_STORE}'),
      f0 as (select work_id, t, regexp_matches(t, '{v2}') v2_hit, {cols3}, {cols31} from b),
      h as (select * from f0 where ({any3}) or ({any31}))
      select h.*, (r.work_id is not null) retracted
      from h left join (select work_id from '{L.EXCLUSION_FLAGS}' where reason='retracted') r using(work_id)
    """)
    elapsed = time.time() - t0
    rows = []
    for k in p31:
        has3 = f'"v3_{k}"' if k in p3 else 'false'
        r = c.execute(f"""
          select count(*) filter (where {has3}) v3_docs,
                 count(*) filter (where "v31_{k}") v31_docs,
                 count(*) filter (where {has3} and not "v31_{k}") removed_docs,
                 count(*) filter (where "v31_{k}" and not {has3}) added_docs
          from f where not v2_hit and not retracted""").df().iloc[0].to_dict()
        rows.append({'type': k, **{a: int(b) for a, b in r.items()}})
    cnt = pd.DataFrame(rows)
    tot = c.execute(f"""
      select count(*) filter (where {any3}) v3_union,
             count(*) filter (where {any31}) v31_union,
             count(*) filter (where ({any3}) and not ({any31})) v3_only,
             count(*) filter (where ({any31}) and not ({any3})) v31_only
      from f where not v2_hit and not retracted""").df().iloc[0].to_dict()
    tot = {a: int(b) for a, b in tot.items()}
    raw = c.execute(f"""
      select count(*) rows_total, count(*) filter (where v2_hit) v2_hit_rows,
             count(*) filter (where retracted and not v2_hit) retracted_not_v2
      from f""").df().iloc[0].to_dict()
    raw = {a: int(b) for a, b in raw.items()}
    rep = json.load(open(f'{OUT_DIR}/genre_counts_v31.json'))
    rep_map = {r['type']: r for r in rep['per_type']}
    diff = []
    for r in rows:
        rr = rep_map.get(r['type'], {})
        for f_ in ('v3_docs', 'v31_docs', 'removed_docs', 'added_docs'):
            if rr.get(f_) != r[f_]:
                diff.append({'type': r['type'], 'field': f_, 'reported': rr.get(f_), 'recount': r[f_]})
    for f_ in ('v3_union', 'v31_union', 'v3_only', 'v31_only'):
        if rep['union'].get(f_) != tot[f_]:
            diff.append({'type': 'UNION', 'field': f_, 'reported': rep['union'].get(f_), 'recount': tot[f_]})
    out = {'scan_seconds': round(elapsed, 1), 'json_equals_code_patterns': same,
           'per_type': rows, 'union': tot, 'raw': raw, 'diff_vs_reported': diff}
    json.dump(out, open(f'{OUT_DIR}/m55_recount.json', 'w'), ensure_ascii=False, indent=1)
    print(cnt.to_string())
    print(tot, raw)
    print('JSON==code:', all(same.values()), 'scan', f'{elapsed:.0f}s')
    print('DIFF vs reported:', diff if diff else 'NONE')


# 지시된 제외·유지 항목의 제목 프로브: (유형, 제목, 기대값)
PROBES = [
    ('commentary', 'Commentary—The future of nursing', False),
    ('commentary', 'Commentary, with reply', False),
    ('commentary', 'Comments, assertions and pragmas', False),
    ('commentary', 'Comments, Shares, or Likes: What Do People Do on Social Media?', False),
    ('commentary', 'Comments, with reply, on "Adaptive filters"', True),
    ('commentary', 'Comment on "Quantum criticality in heavy fermions"', True),
    ('commentary', 'Commentary', True),
    ('commentary', 'Commentary: The role of X', True),
    ('commentary', 'COMMENTARY - ethics', True),
    ('commentary', 'ComMENT on things', False),
    ('reply', 'RESPOnSE—A Framework for Responsive Systems', False),
    ('reply', 'Response–reinforcer contiguity in rats', False),
    ('reply', 'Response—reinforcer contiguity', False),
    ('reply', 'Author Response - Letter to the Editor Regarding X', True),
    ('reply', 'Reply to Wang and Guo', True),
    ('reply', 'Response to the comments by X', True),
    ('reply', 'Response to Intervention: A Guide', False),
    ('reply', 'Response: Re: Something', True),
    ('letter', 'Letter–sound complexity in reading', False),
    ('letter', 'Letter–speech sound integration', False),
    ('letter', 'Letter: Predictors of ST-segment resolution', True),
    ('letter', 'Letters to the editor', True),
    ('letter', 'Letter—a reply', False),
    ('books_received', 'Reviews — Besprechungen — Comptes rendus', True),
    ('books_received', 'Reviews, Books', False),
    ('books_received', 'Books', True),
    ('books_received', 'Review Essay: The New History', True),
    ('bibliography', 'Bibliography—Editors\' selection of current world literature', True),
    ('bibliography', 'Bibliography, sources and methods of X', False),
    ('bibliography', 'Bibliography of Sri Lanka', True),
    ('news', 'Research Update: Recent progress in perovskite solar cells', True),
    ('news', 'Research Update: Perovskite solar cells for tandem devices', False),
    ('news', 'Clinical Update: Management of sepsis', False),
    ('news', 'Research brief: A study of nurses', False),
    ('news', 'Technology selection—A framework', False),
    ('news', 'Miscellanea. A note on the Wishart distribution', False),
    ('news', 'Miscellanea', True),
    ('news', 'Current issues, trends and directions in nursing', False),
    ('news', 'Current issues (in the field)', False),
    ('news', 'Current Issues: Pediatric Pelvic Fractures', True),
    ('news', 'News, views and comments about nothing', False),
    ('news', 'Diary of a working boy', False),
    ('news', 'Courses of treatment for depression', False),
    ('news', 'Policy brief: Universal health coverage', True),
    ('news', 'Highlights from the Flow Chemistry Literature 2014', True),
    ('news', 'Highlights of the literature on X', False),
    ('news', 'Research Update: the latest findings', True),
    ('news', 'Research Update: March 2020', True),
    ('news', 'In Brief', True),
    ('news', 'In Brief: Cost-effectiveness analysis in health care', True),
    ('news', 'News & Notes', True),
    ('index_toc', 'Index, localization and stability of periodic orbits', False),
    ('index_toc', 'Contents, composition and structure of the soil', False),
    ('index_toc', 'Advertisements: The Role of Persuasion', False),
    ('index_toc', 'Advertisements', True),
    ('index_toc', 'Advertisements, Vol. 12', True),
    ('index_toc', 'Citation Indexes for Science', False),
    ('index_toc', 'Index, J. Differential Geometry, Volume 6', True),
    ('index_toc', 'General Index to taxon Volume 60', True),
    ('index_toc', 'Name index', True),
    ('index_toc', 'Name index of authors cited', False),
    ('index_toc', 'Contents', True),
    ('index_toc', 'Contents: A review of chemistry', True),
    ('index_toc', 'Contents of a nutrient in soil', False),
    ('abstracts_meeting', 'Highlights of the STAR experiment', False),
    ('abstracts_meeting', 'Highlights from LHCb', False),
    ('abstracts_meeting', 'Highlights from CMS at the LHC', False),
    ('abstracts_meeting', 'Highlights from AACR 2024 annual meeting', True),
    ('abstracts_meeting', 'Highlights of the 2019 ASCO Annual Meeting', True),
    ('abstracts_meeting', 'Highlights from the STAR experiment presented at the Quark Matter conference', True),
    ('abstracts_meeting', 'Poster Abstract: Deep learning for X', False),
    ('abstracts_meeting', 'Conference Abstract', False),
    ('abstracts_meeting', 'Poster abstracts', True),
    ('abstracts_meeting', 'Programme of the Galactic meridian', False),
    ('abstracts_meeting', 'Programme of the annual meeting', True),
    ('abstracts_meeting', 'Meeting report: 12th workshop on X', True),
    ('abstracts_meeting', 'General Meetings as a Corporate Governance Mechanism', False),
    ('abstracts_meeting', 'General meeting', True),
    ('tribute_address', 'Acknowledgment of Support: NSF grant', False),
    ('tribute_address', 'Acknowledgment of reviewers', True),
    ('tribute_address', 'Acknowledgment of priority', True),
    ('tribute_address', 'Acknowledgment of the role of X in Y', False),
    ('tribute_address', 'Thanks to JMPT peer reviewers', True),
    ('tribute_address', 'Thank You to JMPT Peer Reviewers', True),
    ('tribute_address', 'Thanks to the invisible hand of markets', False),
    ('tribute_address', 'Thank you, Sorry and Please in Cypriot Greek', False),
    ('tribute_address', 'Farewell, old friend: a field analysis of X', False),
    ('tribute_address', 'Reviewers in 2020', False),
    ('tribute_address', 'Reviewers and referees of manuscripts', False),
    ('tribute_address', 'Reviewers for volume 12', True),
    ('tribute_address', 'Reviewers', True),
    ('tribute_address', 'Presidential address: social structure', True),
    ('retraction_notice', 'Retraction of Soft Growing Robots for X', False),
    ('retraction_notice', 'Retraction of soft growing robots', False),
    ('retraction_notice', 'Retraction of: Soft Growing Robots', True),
    ('retraction_notice', 'Retraction of "Soft Growing Robots"', True),
    ('retraction_notice', 'Retraction of the article X', True),
    ('retraction_notice', 'Retraction of 2 papers', True),
    ('retraction_notice', 'Retraction: Soft Growing Robots', True),
    ('retraction_notice', 'RETRACTED: Soft Growing Robots', True),
    ('retraction_notice', 'RETRACTED–Lessons learned', False),
    ('retraction_notice', 'Retraction notice', True),
    ('retraction_notice', 'Expression of concern—X', True),
    ('retraction_notice', 'Correction for volume of precipitate', False),
    ('retraction_notice', 'Correction for Volume 7', True),
    ('retraction_notice', 'Correction to equation (3)', True),
    ('retraction_notice', 'Correction of cell number counts in tumours', False),
    ('retraction_notice', 'Addendum to "Gauge theories"', True),
    ('retraction_notice', 'Addendum to gauge theories', False),
    ('book_review_of', 'Review of Ground-Based Remote Sensing of Cloud Properties by Passive Microwave Radiometers', True),
    ('book_review_of', 'Review of Water Contamination Caused by Mining', False),
    ('book_review_of', 'Review of The Selfish Gene by Richard Dawkins', True),
    ('book_review_of', 'Review of: The Selfish Gene', True),
    ('book_review_of', 'Review of "The Selfish Gene"', True),
    ('book_review_of', 'Review of "The Selfish Gene" for biologists working in X', False),
    ('book_review_of', 'Review: J. R. Smith, The Selfish Gene', True),
    ('named_reply', 'Comment on Smith', False),
    ('named_reply', 'Comment on Smith et al.', True),
    ('named_reply', 'Response to Diversity', True),
    ('named_reply', 'Response to Questions', True),
    ('named_reply', 'Response to Air Pollution', False),
    ('named_reply', 'Response to Intervention: A Guide', False),
    ('named_reply', 'Response to Dr. Smith', True),
    ('named_reply', 'Response to Smith and Jones', True),
    ('named_reply', 'Commentary by the Editor', False),
    ('named_reply', 'Commentary by John Smith', True),
    ('named_reply', 'Reply to Wang and Guo', True),
    ('named_reply', "Response to Smith's commentary", True),
    ('interview', 'In Conversation with Teachers: Perceptions of Inclusive Education in Armenia', True),
    ('interview', 'A Conversation With ChatGPT on Alignment', True),
    ('interview', 'Interview with a vampire', True),
]


def probe():
    """지시된 제외·유지 항목이 실제로 적용됐는지 파이썬 re 와 DuckDB RE2 로 동시에 확인한다."""
    _, p31 = load_patterns()
    rx = {k: re.compile('(?i)' + v) for k, v in p31.items()}
    c = con()
    res = []
    bad = 0
    for typ, title, exp in PROBES:
        py = bool(rx[typ].search(title))
        duck = c.execute("select regexp_matches(?, ?)", [title, '(?i)' + p31[typ]]).fetchone()[0]
        all_types = [k for k, r in rx.items() if r.search(title)]
        ok = (py == exp) and (duck == exp)
        bad += (not ok)
        res.append({'type': typ, 'title': title, 'expected': exp, 're': py, 're2': bool(duck),
                    'ok': ok, 'all_types_hit': all_types})
        flag = '' if ok else '  <== MISMATCH'
        print(f'{typ:18s} exp={int(exp)} re={int(py)} re2={int(duck)} {title[:70]!r} {all_types}{flag}')
    json.dump({'n': len(res), 'mismatch': bad, 'probes': res},
              open(f'{OUT_DIR}/m55_probes.json', 'w'), ensure_ascii=False, indent=1)
    print('probes', len(res), 'mismatch', bad)


# 감사 표본 안에서 하위 형태별 오탐률을 보기 위한 보조 정규식(m54.SUBFORMS 에 없는 것)
EXTRA_SUBFORMS = [
    ('interview', 'conversation_with', r'^\s*(?:a |an |the |in )?conversations?\s+(?:with|between|on|about)\b'),
    ('interview', 'interview_head', r'^\s*(?:an |the |a )?interview'),
    ('tribute_address', 'presidential_address', r'^\s*(?:a |the )?(?:presidential|president[’\']?s)\s+address'),
    ('retraction_notice', 'addendum', r'^\s*addend'),
    ('retraction_notice', 'withdrawn_prefix', r'^\s*withdrawn'),
    ('news', 'in_brief', r'^\s*in brief'),
    ('news', 'news_and_notes', r'^\s*news\s*(?:&|and)'),
    ('index_toc', 'contents_head', r'^\s*contents'),
    ('abstracts_meeting', 'general_meeting', r'^\s*(?:the )?general meetings?'),
    ('abstracts_meeting', 'meeting_report', r'^\s*(?:meeting|conference|congress|symposium|session) (?:report|highlights|summary)'),
    ('books_received', 'book_lists', r'^\s*books? lists?'),
    ('books_received', 'review_essay', r'^\s*(?:review essays?|book review essay|essay review)'),
    ('case_record', 'cpc_record', r'^\s*case \d{1,3}[-–— ]\d{4}'),
    ('commentary', 'commentary_colon_topic', r'^\s*(?:a |an |invited |guest |editorial )?commentar(?:y|ies)\s*:\s*\S'),
    ('editor_note', 'intro_special_issue', r'^\s*(?:guest )?(?:introduction|preface|foreword)s?\s+(?:to|of|for)\s+'),
]


def audit():
    """블라인드 판독 결과 × 정답표 → 유형별 오탐률(research ÷ n)·borderline 비율, 하위 형태별 오탐률."""
    calls = []
    batch = None
    for line in open(CALLS):
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            batch = int(line.split()[-1])
            continue
        w, call = line.split()
        calls.append({'work_id': w, 'call': call, 'call_batch': batch})
    calls = pd.DataFrame(calls)
    assert calls.work_id.is_unique, calls[calls.work_id.duplicated()]
    c = con()
    key = c.execute(f"select * from '{KEY}'").df()
    m = key.merge(calls, on='work_id', how='outer', indicator=True)
    print('merge:', m._merge.value_counts().to_dict())
    assert (m._merge == 'both').all(), m[m._merge != 'both']
    assert (m.batch == m.call_batch).all()
    ids = ', '.join(repr(w) for w in m.work_id)
    bib = c.execute(f"""select work_id, coalesce(title_display,'') title,
                        substr(coalesce(abstract_display,''),1,300) abstract_head, publication_year, type_openalex
                        from '{L.BIB_STORE}' where work_id in ({ids})""").df()
    m = m.merge(bib, on='work_id', how='left')
    sec = c.execute(f"select distinct work_id, subform from '{SECOND}'").df()
    m = m.merge(sec.groupby('work_id').subform.agg(lambda s: ','.join(sorted(s))).rename('second_pass_subform'),
                on='work_id', how='left')
    m['second_pass'] = m.second_pass_subform.notna()
    # 하위 형태 표지
    subs = [(t, n, re.compile('(?i)' + rx)) for t, n, rx, _ in M54.SUBFORMS]
    subs += [(t, n, re.compile('(?i)' + rx)) for t, n, rx in EXTRA_SUBFORMS]
    def sub_of(row):
        return ','.join(n for t, n, r in subs if t == row['type'] and r.search(row['title'] or ''))
    m['subform'] = m.apply(sub_of, axis=1)
    m.drop(columns=['_merge']).to_parquet(f'{OUT_DIR}/m55_audit_merged.parquet', index=False)

    def rate(g):
        n = len(g)
        r = int((g.call == 'research').sum())
        b = int((g.call == 'borderline').sum())
        return {'n': n, 'research': r, 'borderline': b, 'fp_rate': round(r / n, 4) if n else None,
                'borderline_rate': round(b / n, 4) if n else None,
                'research_in_second_pass': int(((g.call == 'research') & g.second_pass).sum())}
    by_type = [{'type': t, **rate(g)} for t, g in m.groupby('type', sort=False)]
    overall = rate(m)
    by_sub = []
    for t, n, r in subs:
        g = m[(m.type == t) & m.subform.str.contains(n, regex=False)]
        if len(g):
            by_sub.append({'type': t, 'subform': n, **rate(g),
                           'in_second_pass': int(g.second_pass.sum()),
                           'research_ids': list(g.work_id[g.call == 'research'])})
    research = m[m.call == 'research'][['work_id', 'type', 'subform', 'second_pass', 'second_pass_subform',
                                        'title', 'publication_year', 'type_openalex']]
    border = m[m.call == 'borderline'][['work_id', 'type', 'subform', 'second_pass', 'title']]
    out = {'overall': overall, 'by_type': by_type, 'by_subform': by_sub,
           'research_calls': research.to_dict('records'),
           'borderline_calls': border.to_dict('records')}
    json.dump(out, open(f'{OUT_DIR}/m55_audit_fp.json', 'w'), ensure_ascii=False, indent=1, default=str)
    pd.set_option('display.width', 250)
    pd.set_option('display.max_colwidth', 120)
    print(pd.DataFrame(by_type).to_string())
    print('overall', overall)
    print(pd.DataFrame(by_sub).drop(columns=['research_ids']).to_string())
    print(research.to_string())
    print(border.to_string())


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else 'all'
    steps = {'recount': recount, 'probe': probe, 'audit': audit}
    if step == 'all':
        for s in ('recount', 'probe', 'audit'):
            steps[s]()
    else:
        steps[step]()


if __name__ == '__main__':
    main()
