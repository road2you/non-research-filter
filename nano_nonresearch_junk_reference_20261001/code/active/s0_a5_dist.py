"""s0_a5_dist — A5 정크 후보 신호의 분포 실측(결정원장 #29가 명령한 미이행분).

#29: "thk 코어·정규식 v1 기준 junk_share를 전 멤버·정규식 v2 기준으로 재계산하고,
임계(10%/30%)의 유지 여부를 분포 실측으로 재확인." 재계산 산출물
junk_share_member.parquet 은 존재하나 소비처가 없고 임계 재확인도 수행되지 않았다.

설계서 139행의 A5 정의 = 결합 판정(정규식 정크 ∪ 무가치 제목) 비율.
이 스크립트는 같은 결합 판정을 세 모집단에서 계산해서 임계 이동을 잰다.
  (가) 코어 합집합  = 현행 구현(s0_pack_builder.junk_pct)의 분모
  (나) 전 멤버      = #29가 명령한 분모
정크 탐지 신호이므로 분모에서 정크를 빼지 않는다(유효 멤버 기준을 쓰지 않는 이유).

사용: .venv/bin/python pipeline/scripts/s0_a5_dist.py
출력: pipeline/out/a5_dist.parquet 과 콘솔 요약
"""
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import duckdb
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s0_lib as L  # noqa: E402

# 주의: member_titles_v3.parquet 를 쓰면 안 된다. 그 파일은 s0_e3_bulk_v3.py:26 이
# junk_doc_flags 를 anti join 해서 만든 '정크 제외' 제목표이므로(정크 잔존 0편 실측),
# 그것으로 재면 A5 의 분모가 재려는 대상을 이미 빼 버린 상태가 된다. A5 는 정크 탐지
# 신호이므로 분모는 정크를 포함한 전 멤버여야 한다. 그래서 멤버십과 서지 정본을 직접
# 조인해서 원 제목을 쓴다(정크 판정도 title_display 기준이므로 열을 맞춘다).
# 09-09 밤 팩 반영 재빌드(#131): 정규식 정크 판정(jd)은 제목 정규식 v2(L.junk_doc)가 아니라 정본 배제 표(exclusion_flags,
# reason junk_regex_v2·junk_regex_v3)에서 읽는다 — 판 스위치가 한 곳(s0_exclusion_flags)에서만 일어나게 한다. ut(무가치 제목)는 그대로.
MEMBER_SQL = """
  select m.effective_nano_id nano_id, coalesce(b.title_display,'') title,
         (x.work_id is not null) jd
  from '{yjk}/work/atlas_work_membership.parquet' m
  left join '{bib}' b using(work_id)
  left join (select work_id from '{excl}' where reason like 'junk_regex_%') x using(work_id)
  where m.effective_nano_id >= {lo} and m.effective_nano_id < {hi}"""
OUT = f'{L.PIPE}/out/a5_dist.parquet'
NPART = 16


def _judge(args):
    """한 조각의 제목들에 결합 판정을 적용해 nano별로 집계한다."""
    lo, hi = args
    con = duckdb.connect()
    df = con.execute(MEMBER_SQL.format(yjk=L.YJK, pipe=L.PIPE, lo=lo, hi=hi, bib=L.BIB_STORE, excl=L.EXCLUSION_FLAGS)).fetchdf()
    if df.empty:
        return pd.DataFrame(columns=['nano_id', 'members', 'jd', 'ut', 'comb'])
    t = df['title'].astype(str)
    df['jd'] = df['jd'].astype(bool)                          # 정규식 정크 = 정본 배제 표(v2 + v3.2)
    df['ut'] = [L.uninformative_title(x) for x in t]         # 무가치 제목(#25, 정크 아님)
    df['comb'] = df['jd'] | df['ut']                         # A5 결합 판정(§4 139행)
    g = df.groupby('nano_id').agg(members=('title', 'size'), jd=('jd', 'sum'),
                                  ut=('ut', 'sum'), comb=('comb', 'sum')).reset_index()
    return g


def main():
    t0 = time.time()
    con = duckdb.connect()
    con.execute('SET threads=16')
    mx = con.execute(f"select max(effective_nano_id)+1 from '{L.YJK}/work/atlas_work_membership.parquet'").fetchone()[0]
    step = -(-mx // NPART)
    bounds = [(i, min(i + step, mx)) for i in range(0, mx, step)]
    with ProcessPoolExecutor(NPART) as ex:
        parts = list(ex.map(_judge, bounds))
    mem = pd.concat(parts, ignore_index=True)
    print(f'전 멤버 집계 완료: nano {len(mem):,}개 · {time.time()-t0:.0f}s', flush=True)

    # 코어 합집합 기준 같은 판정
    core = con.execute(f"""
      select u.nano_id, coalesce(v.title_display,'') title, (x.work_id is not null) jd
      from 'design_v1/precomputed/ta_union_docs.parquet' u
      left join '{L.BIB_STORE}' v using(work_id)
      left join (select work_id from '{L.EXCLUSION_FLAGS}' where reason like 'junk_regex_%') x using(work_id)""").fetchdf()   # 09-09: 서지 정본 상수 경유(구 bib_store_v2 하드코딩 정정)
    tc = core['title'].astype(str)
    core['jd'] = core['jd'].astype(bool)
    core['comb'] = [bool(j) or L.uninformative_title(x) for j, x in zip(core['jd'], tc)]
    cg = core.groupby('nano_id').agg(core_n=('title', 'size'), core_comb=('comb', 'sum'),
                                     core_jd=('jd', 'sum')).reset_index()
    print(f'코어 집계 완료: nano {len(cg):,}개 · {time.time()-t0:.0f}s', flush=True)

    df = mem.merge(cg, on='nano_id', how='outer').fillna(0)
    df['pct_mem_comb'] = 100.0 * df.comb / df.members.clip(lower=1)
    df['pct_mem_jd'] = 100.0 * df.jd / df.members.clip(lower=1)
    df['pct_core_comb'] = 100.0 * df.core_comb / df.core_n.clip(lower=1)
    df['pct_core_jd'] = 100.0 * df.core_jd / df.core_n.clip(lower=1)
    df.to_parquet(OUT, index=False)
    print(f'\n저장 {OUT} ({len(df):,}행)\n', flush=True)

    def line(nm, s):
        return (f'{nm:<28} 중앙 {s.median():>6.2f}% · p90 {s.quantile(.9):>6.2f}% · '
                f'p99 {s.quantile(.99):>6.2f}% · 최대 {s.max():>6.2f}% | '
                f'≥10% {int((s >= 10).sum()):>6,} · ≥30% {int((s >= 30).sum()):>6,}')
    print(line('(가) 코어·결합 [현행]', df.pct_core_comb))
    print(line('(나) 전 멤버·결합 [#29]', df.pct_mem_comb))
    print(line('     코어·정규식만', df.pct_core_jd))
    print(line('     전 멤버·정규식만', df.pct_mem_jd))

    print('\n=== 임계 이동(현행 → #29 전환) ===')
    for th in (10, 30):
        a = df.pct_core_comb >= th
        b = df.pct_mem_comb >= th
        print(f'  {th}% 선: 현행 {int(a.sum()):,} → 전환 후 {int(b.sum()):,} '
              f'(신규 진입 {int((~a & b).sum()):,} · 이탈 {int((a & ~b).sum()):,})')
    print(f'\n총 {time.time()-t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
