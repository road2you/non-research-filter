"""m70 — 정규식 v3.2 후보 유형(하위 형태 포함)의 전수 적중·표본·블라인드 감사 키(R7-e 09-09; 62793·61858·31986 확정에서 적발).
정본(s0_lib.JUNK_V3)은 건드리지 않는다. 산출(_junk_v3/): m70_v32_counts.parquet · m70_v32_hits.parquet(신규 적중 전건) · m70_v32_audit_key.parquet(표본 정답표: work_id,type,subform)
· m70_v32_audit_blind.jsonl(판독자용: work_id·제목·초록 머리·연도만, 유형 없음, 무작위 순서)."""
import json, os, re, sys, time
import duckdb, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s0_lib as L  # noqa: E402
OUT = f'{L.PIPE}/out'; EXP = f'{OUT}/_junk_v3'
MON = r'(?:january|february|march|april|may|june|july|august|september|october|november|december)'
# (유형, 하위 형태 이름, 정규식) — 앞 고정(^), 대소문자 무시. 조건부 유형은 conditional=True
SUBFORMS = [
 ('issue_note', 'spotlight_dated', rf'^\s*spotlight on the {MON} \d{{1,2}},? (issue|\d{{4}})', False),
 ('issue_note', 'in_this_issue_bare', r'^\s*(in|about) this (issue|number)\s*(\.{3}|…)?\s*$', False),
 ('issue_note', 'in_this_number_colon', r'^\s*in this number\s*:', False),
 ('issue_note', 'about_this_issue_colon', r'^\s*about this issue\s*(:|/|and acknowledg)', False),
 ('issue_note', 'perspectives_on_issue', r'^\s*(perspectives?|reflections?|comments?) on this (issue|month.?s)', False),
 ('issue_note', 'highlights_of_edition', r'^\s*highlights? of (the|this) (edition|issue|number)\b', False),
 ('issue_note', 'this_weeks_no1', r"^\s*this week.?s no\.? ?1\s*$", False),
 ('reviewer_ack', 'ack_of_reviewers', r'^\s*(a |an )?(acknowledg(e)?ments?|thanks|thank you|appreciation|gratitude|tribute|recognition)\s+(of|to|for)\s+(our |the |all |\d{4} |ad hoc |manuscript |peer |guest |external |journal |volunteer |outstanding )*(reviewers|referees|peer reviewers|editorial board|editorial board members|editors and reviewers|reviewers and editors)\b', False),
 ('reviewer_ack', 'reviewers_thank_you', r'^\s*(?:[a-z&.\'’ ]{2,40} )?(reviewers?|referees?|reviewer and editorial board|reviewers and editors)\s+(thank you|thanks|acknowledg(e)?ments?|appreciation)\b', False),
 ('reviewer_ack', 'reviewers_list_year', r'^\s*(list of |our |journal |manuscript |peer |ad hoc |guest )?(reviewers|referees)\s+(for|of|in)\s+(\d{4}|volume|the year|this year|the journal|the past year)\b', False),
 ('reviewer_ack', 'reviewer_of_year', r'^\s*(\d{4} )?(?:[a-z&.\'’ ]{2,40} )?(reviewers?|referees?)\s+of the year\b', False),
 ('reviewer_ack', 'prefixed_ack', r'^\s*(?:[a-z0-9&.\'’:()-]+\s+){0,5}(?:\d{4}\s+)?(?:acknowledg(?:e)?ments?\s+(?:of|to)\s+(?:the |our |all |\d{4} |peer |manuscript |ad hoc |guest |external )*(?:reviewers|referees|editorial board)|(?:peer )?reviewers?(?:\s+and editorial board(?: members)?)?\s+thank you|reviewer of the year|thank you to (?:our |the |all )?(?:\d{4} )?(?:peer )?(?:reviewers|referees)|(?:peer )?reviewer acknowledg(?:e)?ments?|reviewers? for \d{4}|our \d{4} (?:peer )?reviewers)\b', False),
 ('reviewer_ack', 'journal_reviewers_year', r'^\s*[a-z&.\'’ ]{2,40}\s+(reviewers|referees)\s+(\d{4}|for \d{4})\s*$', False),
 ('editors_picks', 'editors_picks', r'^\s*editors?[\'’]?\s*picks?\b', False),
 ('editors_picks', 'editors_choice_bare', r'^\s*editor[\'’]?s?\s*choice\s*(\.|:|$|\s*[–—-]\s*(most|top|selected|highlights?|the best|\d|' + MON + r'))', False),
 ('editors_picks', 'editors_spotlight', r'^\s*editor[\'’]?s?\s*(spotlight|highlights?|selection|summary|summaries)\s*(\.|:|/|$|\s*[–—-])', False),
 ('teaching_case', 'lesson_of_week', r'^\s*lessons? of the (week|month)\b', True),
 ('teaching_case', 'strip_of_month', r'^\s*strip of the month\b', True),
 ('teaching_case', 'image_case_of_month', r'^\s*(image|images|case|cases|picture|photo|quiz|puzzle|problem|question|ecg|echo|radiograph|film) of the (month|week|quarter)\b', True),
]
def main():
    t0 = time.time(); con = duckdb.connect(); con.execute("SET threads TO 32; SET memory_limit='120GB'")
    con.execute(f"create view mem as select m.work_id, m.effective_nano_id nano_id from '{L.YJK}/work/atlas_work_membership.parquet' m")
    con.execute(f"create view bib as select work_id, title_display, substr(coalesce(abstract_display,''),1,300) abs_head, publication_year, type_openalex from '{L.BIB_STORE}'")
    con.execute(f"create view v3 as select distinct work_id from '{OUT}/exclusion_flags_v3.parquet'")
    rows, hits = [], []
    for typ, sub, rx, cond in SUBFORMS:
        rx_sql = ('(?i)' + rx).replace("'", "''")
        df = con.execute(f"""select b.work_id, m.nano_id, b.publication_year, b.title_display, b.abs_head, b.type_openalex, (v3.work_id is not null) in_v3
            from bib b join mem m using (work_id) left join v3 using (work_id) where regexp_matches(b.title_display, '{rx_sql}')""").fetchdf()
        df['type'] = typ; df['subform'] = sub; df['conditional'] = cond
        rows.append(dict(type=typ, subform=sub, conditional=cond, n=len(df), in_v3=int(df.in_v3.sum()), new=int((~df.in_v3).sum()), nanos=int(df.nano_id.nunique())))
        hits.append(df)
        print(f'{typ:14s} {sub:24s} 적중 {len(df):>6,} · 신규 {int((~df.in_v3).sum()):>6,} · 나노 {df.nano_id.nunique():>5,} ({time.time()-t0:.0f}s)', flush=True)
    counts = pd.DataFrame(rows); counts.to_parquet(f'{EXP}/m70_v32_counts.parquet', index=False)
    H = pd.concat(hits).drop_duplicates('work_id'); H.to_parquet(f'{EXP}/m70_v32_hits.parquet', index=False)
    # 감사 표본: 유형당 45 이상(하위 형태 비례, 최소 6), 신규 적중에서, 새 seed
    rng = np.random.default_rng(20260909); key = []
    for typ, g in H[~H.in_v3].groupby('type'):
        per = max(45, 0); parts = []
        for sub, gg in g.groupby('subform'):
            k = max(6, int(round(per * len(gg) / len(g))))
            parts.append(gg.sample(min(k, len(gg)), random_state=int(rng.integers(1e9))))
        key.append(pd.concat(parts))
    K = pd.concat(key).drop_duplicates('work_id'); K['batch'] = rng.integers(0, 6, len(K))
    K[['work_id', 'type', 'subform', 'batch']].to_parquet(f'{EXP}/m70_v32_audit_key.parquet', index=False)
    blind = K.sample(frac=1, random_state=11)[['work_id', 'title_display', 'abs_head', 'publication_year', 'type_openalex', 'batch']]
    with open(f'{EXP}/m70_v32_audit_blind.jsonl', 'w') as f:
        for r in blind.itertuples():
            f.write(json.dumps(dict(work_id=r.work_id, title=r.title_display, abstract_head=r.abs_head, year=int(r.publication_year) if r.publication_year == r.publication_year else None, type_openalex=r.type_openalex, batch=int(r.batch)), ensure_ascii=False) + '\n')
    print('\n감사 표본', len(K), K.groupby('type').size().to_dict(), '| 묶음', K.batch.value_counts().sort_index().to_dict())
if __name__ == '__main__':
    main()
