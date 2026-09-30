"""s0_exclusion_flags — 문서 배제 통합 테이블 생성(#89 D6).

exclusion_flags.parquet = 정크 정규식 배제(junk_doc_flags, #26 v2·#79 정합판)
                        ∪ 장르 정크 v3.2 배제(junk_doc_flags_v3 의 v3 신규분, #122·#131; 09-09 밤 팩 반영 재빌드에서 정본 편입)
                        ∪ 철회 배제(work_meta_v2.is_retracted, #87 6월판 단일 원천).
우선순위 = 철회 > junk_regex_v2 > junk_regex_v3(한 문헌 한 행). 2차 판정으로 강등된 v3 표시(flag_only)는 배제하지 않는다.
reason 을 1급 열로 둔다. 두 사유가 겹치는 문헌(실측 1편)은 철회를 앞세운다 —
철회는 제목 규칙과 무관한 외부 사실이므로 규칙 판정에 가려지면 안 된다(#89).

주의: 판정 원천은 work_meta_v2 하나뿐이다. 김영진 판 atlas_work_metadata 의
is_retracted 는 58,748,955행 전건 거짓이라 그것을 쓰면 배제가 조용히 0건으로 꺼진다.

사용: .venv/bin/python pipeline/scripts/s0_exclusion_flags.py
출력: pipeline/out/exclusion_flags.parquet (work_id, nano_id, reason, title_head, snapshot)
검증: 행수 = 정크 101,462 + 철회 2,326 − 교집합 1 = 103,787
"""
import os
import sys

import duckdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s0_lib as L  # noqa: E402

c = duckdb.connect()
c.execute("SET threads=16; SET memory_limit='48GB'")

c.execute(f"""
copy (
  with retr as (
    select w.work_id, m.effective_nano_id nano_id,
           substr(coalesce(b.title_display, ''), 1, 80) title_head
    from '{L.WORK_META}' w
    join '{L.YJK}/work/atlas_work_membership.parquet' m using (work_id)
    left join '{L.BIB_STORE}' b using (work_id)
    where w.is_retracted
  ),
  junk as (
    select work_id, nano_id, title_head
    from 'design_v1/precomputed/junk_doc_flags.parquet'
  )
  select work_id, nano_id, 'retracted' as reason, title_head,
         '20260625' as snapshot
  from retr
  union all
  select j.work_id, j.nano_id, 'junk_regex_v2' as reason, j.title_head,
         'junk_flags_v2(#79)' as snapshot
  from junk j
  anti join retr r on r.work_id = j.work_id      -- 교집합은 철회가 앞선다(#89)
  union all
  select v.work_id, v.nano_id, 'junk_regex_v3' as reason, v.title_head,
         'junk_flags_v3.2(#131)' as snapshot
  from '{L.JUNK_DOC_FLAGS_V3}' v
  anti join retr r on r.work_id = v.work_id
  anti join junk j on j.work_id = v.work_id      -- v2 가 이미 잡은 문헌은 v2 사유를 유지한다
  where v.flag_source = 'v3' and not v.flag_only
  order by work_id
) to '{L.EXCLUSION_FLAGS}' (format parquet)""")

r = c.execute(f"""select count(*), count(distinct work_id),
    count(*) filter (reason = 'retracted'),
    count(*) filter (reason = 'junk_regex_v2'),
    count(*) filter (reason = 'junk_regex_v3') from '{L.EXCLUSION_FLAGS}'""").fetchone()
print(f'저장 {L.EXCLUSION_FLAGS}')
print(f'  행 {r[0]:,} (고유 {r[1]:,}) | retracted {r[2]:,} | junk_regex_v2 {r[3]:,} | junk_regex_v3 {r[4]:,}')
assert r[0] == r[1], '한 문헌에 두 행이 있으면 안 된다'
# 검증: 같은 우선순위로 지은 s0_junk_flags_v3 의 exclusion_flags_v3 와 문헌 집합·사유가 같아야 한다
v3 = f'{L.PIPE}/out/exclusion_flags_v3.parquet'
if os.path.exists(v3):
    d = c.execute(f"""select count(*) from (select work_id, reason from '{L.EXCLUSION_FLAGS}'
        except select work_id, reason from '{v3}') union all
        select count(*) from (select work_id, reason from '{v3}' except select work_id, reason from '{L.EXCLUSION_FLAGS}')""").fetchall()
    print(f'  exclusion_flags_v3 대조: 차집합 {d[0][0]:,} / {d[1][0]:,} → {"일치" if d[0][0] == 0 and d[1][0] == 0 else "불일치!"}')
    assert d[0][0] == 0 and d[1][0] == 0, 'exclusion_flags_v3 와 어긋난다'
exp = 101462 + 2326 - 1
print(f'  v2 기준 기대 행수 {exp:,}(참고; v3 편입 뒤에는 v3 대조가 정본 검증)')
for reason in sorted(set(c.execute(
        f"select distinct reason from '{L.EXCLUSION_FLAGS}'").fetchdf()['reason'])):
    assert reason in L.EXCLUSION_REASONS, f'미등재 사유 {reason}'
print('  사유 열거형 = s0_lib.EXCLUSION_REASONS 정합 확인')
