"""정크 문서 전수 플래그 테이블 생성 (결정원장 #26, 2026-08-23 사용자 확정).

전 멤버십(78,049 nano, 58,748,955편)의 제목에 s0_lib.JUNK(정규식 v2)를 적용해서
`design_v1/precomputed/junk_doc_flags.parquet`를 만든다. 목적은 팩 입력 정제만이
아니라 이후 활용 전반(시험 문제 선정, 정크 nano 판정, 문헌 집합 출고)이다.

결정원장 #25에 따라 초단문·내용어 부족 제목은 여기 포함하지 않는다(정크가 아님).
소비처 연결(E2 표본·E3 통계·시험 30편·L0 전 멤버 정크율·출고)은 v2 배치에서 한다.

사용: .venv/bin/python pipeline/scripts/s0_junk_flags.py
"""
import duckdb
import s0_lib as L

OUT = f'{L.BASE}/design_v1/precomputed/junk_doc_flags.parquet'
REASON = 'regex_v2'


def main():
    c = duckdb.connect()
    c.execute('SET threads=32')
    mem = f'{L.YJK}/work/atlas_work_membership.parquet'
    md = L.BIB_STORE   # #55·#79: 제목은 정제 정본에서
    pat = L.JUNK.pattern.replace("'", "''")
    c.execute(f"""
      copy (
        select m.work_id, m.effective_nano_id nano_id,
               substr(coalesce(t.title_display,''), 1, 120) title_head,
               '{REASON}' reason
        from '{mem}' m join '{md}' t using(work_id)
        where regexp_matches(coalesce(t.title_display,''), '{pat}')
        order by m.work_id
      ) to '{OUT}' (format parquet)
    """)
    n, nd, nn = c.execute(
        f"select count(*), count(distinct work_id), count(distinct nano_id) from '{OUT}'"
    ).fetchone()
    print(f'junk_doc_flags.parquet: {n:,}행 (고유 work {nd:,}, 관련 nano {nn:,})')


if __name__ == '__main__':
    main()
