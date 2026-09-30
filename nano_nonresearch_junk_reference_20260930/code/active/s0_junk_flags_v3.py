"""s0_junk_flags_v3 — 문헌 단위 정크 플래그 v3(장르 정크 편입; #117·#122, 2026-09-07).

정본 v2(design_v1/precomputed/junk_doc_flags.parquet, s0_lib.JUNK)는 차기 재빌드까지 불변이다(A.40 원칙:
판 전환은 s0_lib 상수 한 곳에서). 이 스크립트는 v3 를 **별도 파일**로 만들어 상태표(s0_mapping_unit_status
--junk-source v3)와 C-F1 출고 필터가 먼저 쓰게 한다.

v3 = v2 ∪ (s0_lib.JUNK_V3 유형별 정규식 v3.1 적중) − 2차 판정에서 research 로 판정된 문헌(표시로 강등,
flag_only=True; 제외 대상에서 뺀다). 철회(#89)는 별도 사유이므로 여기서 중복 기재하지 않는다.

출력
  pipeline/out/junk_doc_flags_v3.parquet   (work_id, nano_id, title_head, junk_types[], flag_source in {'v2','v3'}, flag_only)
  pipeline/out/exclusion_flags_v3.parquet  (work_id, nano_id, reason in {'retracted','junk_regex_v2','junk_regex_v3'}, title_head, snapshot)
  pipeline/out/a5_dist_v3.parquet          (nano_id, members, jd, pct_mem_jd) — v3 정크 비율(전 멤버 분모, #90)
사용: .venv/bin/python pipeline/scripts/s0_junk_flags_v3.py
"""
import json
import os
import sys
import time

import duckdb
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s0_lib as L  # noqa: E402

OUT = f'{L.PIPE}/out'
SECOND_PASS = f'{OUT}/_junk_v3/second_pass_results.jsonl'
t0 = time.time()

if not hasattr(L, 'JUNK_V3'):
    raise SystemExit('s0_lib.JUNK_V3 (유형 → 정규식 v3.1) 가 없습니다. 검증 완료 후 s0_lib 에 편입하세요.')

con = duckdb.connect()
con.execute("SET threads TO 32; SET memory_limit='96GB'")
con.execute(f"""create table mem as
  select m.work_id, m.effective_nano_id nano_id, coalesce(b.title_display, '') title
  from '{L.YJK}/work/atlas_work_membership.parquet' m
  left join '{L.BIB_STORE}' b using (work_id)""")
n_mem = con.execute("select count(*) from mem").fetchone()[0]
print(f'멤버십 {n_mem:,} ({time.time()-t0:.0f}s)', flush=True)

# 유형별 적중(v2 미적중 포함해 전부 세고, 뒤에서 v2 와 합친다)
hit_cols = []
for typ, pat in L.JUNK_V3.items():
    sql_pat = pat.pattern.replace("'", "''") if hasattr(pat, 'pattern') else str(pat).replace("'", "''")
    con.execute(f"alter table mem add column t_{typ} boolean")
    con.execute(f"update mem set t_{typ} = regexp_matches(title, '{sql_pat}')")
    if typ in getattr(L, 'JUNK_V3_EXCLUDE', {}):
        ex = L.JUNK_V3_EXCLUDE[typ].replace("'", "''")
        n_ex = con.execute(f"select count(*) from mem where t_{typ} and regexp_matches(title, '{ex}')").fetchone()[0]
        con.execute(f"update mem set t_{typ} = false where t_{typ} and regexp_matches(title, '{ex}')")
        print(f'    제외식 적용({typ}): {n_ex:,}건 해제', flush=True)
    hit_cols.append(f't_{typ}')
    print(f'  {typ}: {con.execute(f"select count(*) from mem where t_{typ}").fetchone()[0]:,}', flush=True)
any_v3 = ' or '.join(hit_cols)
types_expr = "list_filter([" + ", ".join(f"case when t_{t} then '{t}' end" for t in L.JUNK_V3) + "], x -> x is not null)"

# 2차 판정: research → 표시로 강등
down = set()
if os.path.exists(SECOND_PASS):
    for line in open(SECOND_PASS):
        j = json.loads(line)
        if j.get('verdict') == 'research':
            down.add(j['work_id'])
con.register('down', pd.DataFrame({'work_id': sorted(down)}))
print(f'2차 판정 research(표시 강등) {len(down):,}편', flush=True)

con.execute(f"""create table v3 as
  select m.work_id, m.nano_id, substr(m.title, 1, 120) title_head, {types_expr} junk_types,
         (d.work_id is not null) flag_only
  from mem m left join down d using (work_id) where {any_v3}""")
con.execute(f"""copy (
  select coalesce(v.work_id, j.work_id) work_id, coalesce(v.nano_id, j.nano_id) nano_id,
         coalesce(v.title_head, j.title_head) title_head,
         coalesce(v.junk_types, []) junk_types,
         case when j.work_id is not null then 'v2' else 'v3' end flag_source,
         coalesce(v.flag_only, false) and j.work_id is null flag_only
  from v3 v full outer join 'design_v1/precomputed/junk_doc_flags.parquet' j on j.work_id = v.work_id
) to '{OUT}/junk_doc_flags_v3.parquet' (format parquet)""")
r = con.execute(f"""select count(*), count(*) filter (flag_source='v2'), count(*) filter (flag_source='v3'),
  count(*) filter (flag_only) from '{OUT}/junk_doc_flags_v3.parquet'""").fetchone()
print(f'junk_doc_flags_v3: {r[0]:,} (v2 {r[1]:,} · v3 신규 {r[2]:,} · 표시만 {r[3]:,}) ({time.time()-t0:.0f}s)', flush=True)

# exclusion_flags_v3: 철회 우선, 그다음 v2, v3(표시만은 제외 아님)
con.execute(f"""copy (
  select work_id, nano_id, reason, title_head, snapshot from '{L.EXCLUSION_FLAGS}' where reason = 'retracted'
  union all
  select f.work_id, f.nano_id, 'junk_regex_v2' as reason, f.title_head, 'junk_flags_v3(#122)' as snapshot
  from '{OUT}/junk_doc_flags_v3.parquet' f
  anti join (select work_id from '{L.EXCLUSION_FLAGS}' where reason='retracted') x using (work_id)
  where f.flag_source = 'v2'
  union all
  select f.work_id, f.nano_id, 'junk_regex_v3' as reason, f.title_head, 'junk_flags_v3(#122)' as snapshot
  from '{OUT}/junk_doc_flags_v3.parquet' f
  anti join (select work_id from '{L.EXCLUSION_FLAGS}' where reason='retracted') x using (work_id)
  where f.flag_source = 'v3' and not f.flag_only
) to '{OUT}/exclusion_flags_v3.parquet' (format parquet)""")
r = con.execute(f"""select count(*), count(distinct work_id), count(*) filter (reason='retracted'),
  count(*) filter (reason='junk_regex_v2'), count(*) filter (reason='junk_regex_v3') from '{OUT}/exclusion_flags_v3.parquet'""").fetchone()
print(f'exclusion_flags_v3: {r[0]:,} (고유 {r[1]:,}) | retracted {r[2]:,} · v2 {r[3]:,} · v3 {r[4]:,}', flush=True)

# a5_dist_v3: 전 멤버 분모(#90) 정크 비율(제외 대상 정크만; 표시만은 분자에 넣지 않음)
con.execute(f"""copy (
  select m.nano_id, count(*) members,
         count(*) filter (f.work_id is not null and not coalesce(f.flag_only, false)) jd,
         100.0 * count(*) filter (f.work_id is not null and not coalesce(f.flag_only, false)) / count(*) pct_mem_jd
  from mem m left join '{OUT}/junk_doc_flags_v3.parquet' f using (work_id)
  group by 1 order by 1
) to '{OUT}/a5_dist_v3.parquet' (format parquet)""")
r = con.execute(f"""select count(*), count(*) filter (pct_mem_jd>=50), count(*) filter (pct_mem_jd>=30 and pct_mem_jd<50)
  from '{OUT}/a5_dist_v3.parquet'""").fetchone()
print(f'a5_dist_v3: {r[0]:,} nano | 정크 ≥50% {r[1]} · 30~50% {r[2]} ({time.time()-t0:.0f}s)')
