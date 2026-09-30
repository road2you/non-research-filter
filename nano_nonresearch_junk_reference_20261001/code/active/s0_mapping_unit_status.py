"""s0_mapping_unit_status — 나노별 매핑 단위 상태(#118, 09-07 사용자 확정 정책의 코드 판정 함수).

정책 원문(#118): 나노는 매핑 단위다. 혼합 확정이거나 정크 우세이면 단위로 쓰지 않는다. 그런 나노에
코어(먼 갈래 제외 잔류 몫 ≥30%이고 재판정이 single)가 있으면 코어만 나노로 매핑한다. 코어 밖 문헌과
코어 없는 나노의 문헌은 v1 에서 매핑 보류로 공개한다.

판정 재료
  · 정크 비율: 정본 = a5_dist.pct_mem_jd(09-09 팩 반영 재빌드 #131 부터 정본 배제 표 exclusion_flags 의 정크 사유 v2 + v3.2 기준; 전 멤버 분모 #90).
    열 이름 junk_ratio_v3_preview 는 그대로 두되 값은 정본이다(구 a5_dist_v3 미리보기와 같은 정의; 철회∩정크 문헌은 철회 사유가 앞서 정크에서 빠진다).
  · 혼합 확정: mixed_confirmed_v3.parquet(Sol, 2,471개)를 읽고 Astra 재판정(q_results_mixed_astra.jsonl, #121)으로
    single 판정된 1,780개를 mixed_cleared 로 표기해 제외 → 남는 691개 = 정본 v4(mixed_confirmed_v4.parquet)와 동일.
  · 먼 갈래: 나노 안 ETO 갈래의 근접도 prox(비층화 z; 나머지 기준 갈래와의 편수 가중평균 유사도라 클수록 가깝다. 구 이름
    '고립도 iso' 는 뜻과 반대라 09-08 밤 사용자 지시로 개칭, 계산 불변) < TAU_Z(2.0). #125(09-08): 근접도의 기준 집합은 3편 이상 갈래이고
    갈래 수 상한은 없다(조각 갈래는 그 기준에 대해 평가만 받는다; s0_eto_coherence 의 상한 400·기준 전부 정의와 다르다, A.75).
    잔류 몫 core_share = 1 − 먼 갈래 문헌 ÷ 유효 멤버(size) — 미부착 문헌은 잔류에 포함(#118).
  · 코어 재판정: q_results_core.jsonl(item_id 'DC_<nano>', verdict single/mixed) — 있으면 반영.
  · 코어 갈래 0 규칙(#123, 09-07 사용자 확정): 혼합 확정 나노에 CORE_STRAND_MIN_DOCS(3)편 이상인 코어 갈래가
    하나도 없으면 잔류 몫·재판정과 무관하게 mixed_no_core.

상태(우선순위 순, #127): 정크 나노(v3 비율 ≥30%) → junk_core / junk_core_review / junk_core_pending / junk_no_core(잔여 코어 절차)
  > 혼합 나노 → mixed_core / mixed_core_review / mixed_core_pending / mixed_no_core > normal
출력: pipeline/out/mapping_unit_status.parquet · mapping_unit_strands.parquet(혼합·정크 나노의 갈래별 prox·far)
사용: .venv/bin/python pipeline/scripts/s0_mapping_unit_status.py [--junk-source v2|v3]
"""
import argparse
import json
import os
import sys
import time

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s0_lib as L  # noqa: E402
import s0_core_ladder as LAD  # noqa: E402  (#128 코어 단계별 임계값 규칙)

SNAP = '/data3/openalex-csv(20260625)/postprocess'
OUT = f'{L.PIPE}/out'
TAU_Z = 2.0            # 먼 갈래 경계(#118: 비층화 z, 순도 우선)
JUNK_DOMINATED = 50.0  # #118
JUNK_REVIEW = 30.0     # #118
CORE_SHARE_MIN = 0.30  # #118
CORE_STRAND_MIN_DOCS = 3   # 코어 갈래 최소 편수(#123: 3편 이상 코어 갈래가 하나도 없으면 잔류 몫·재판정과 무관하게 코어 없음)
STRAND_CAP = 0             # #125: 갈래 평가 상한 없음(구 400 은 s0_eto_coherence 의 비용 상한을 물려받은 구현 세부, A.75)
STRAND_REF_MIN_DOCS = 3    # #125: 고립도 기준 집합 = 3편 이상 갈래(조각 갈래는 평가만 받는다)
V3_PREVIEW = f'{OUT}/_junk_v3/junk_ratio_v3.parquet'   # 09-07 후보 미리보기(정본 편입 전)
A5_V3 = L.A5_DIST                                        # 09-09 팩 반영 재빌드(#131): 정크 비율 정본 = a5_dist(정본 배제 표 기준). 구 a5_dist_v3 는 비교용으로만 남는다
CORE_RESULTS = f'{OUT}/q_results_core.jsonl'            # Sol(v1) — 보존·병기
CORE_RESULTS_ASTRA = f'{OUT}/q_results_core_astra.jsonl' # Astra(v1.1, #121) — 있으면 우선
CORE_RESULTS_ASTRA_C = f'{OUT}/q_results_core_astra_c.jsonl' # #125 정의 C 로 코어가 바뀐 나노의 Astra 재판정(같은 나노는 이 결과가 앞선다)
CORE_RESULTS_ASTRA_J = f'{OUT}/q_results_core_astra_j.jsonl' # #127 정크 나노 잔여 코어의 Astra 재판정(정크 나노에서는 이 결과만 쓴다)
EXCLUSION_V3 = L.EXCLUSION_FLAGS                          # 09-09 재빌드(#131): 정본 배제 표 하나(v2 + v3.2 + 철회). 구 exclusion_flags_v3 와 내용이 같음을 s0_exclusion_flags 가 단언한다
CORE_RESULTS_ASTRA_V3 = f'{OUT}/q_results_core_astra_v3.jsonl'   # 09-09 재빌드: 코어 집합 키로 식별하는 근접도 코어 재판정(DC_<nano>_<key>)
CORE_KEY_SNAPSHOT = f'{OUT}/core_key_pre_v3.parquet'      # 재빌드 직전 근접도 코어 키(나노별) — 옛 DC_<nano> 판정은 키가 그대로일 때만 재사용
NOINFO_FLAGS = f'{OUT}/noinfo_flags.parquet'               # C-F1 정보 없음(m42 09-08 정정판)
JUNK_STATUSES = ('junk_core', 'junk_core_review', 'junk_core_pending', 'junk_no_core')   # #127
LADDER_TAUS = LAD.LADDER_TAUS       # #128: 문헌 가중 평균 연결 단계별 임계값 규칙 1.5 → 1.75 → 2.0(넓은 것부터)
LADDER_KEEP_VALIDATED = True        # #128 이행 규칙: 현행 규칙으로 Astra 가 single 확정한 코어는 다시 열지 않는다
MIXED_RESULTS_ASTRA = f'{OUT}/q_results_mixed_astra.jsonl' # 혼합 확정 2,471 의 Astra 재판정: single 이면 normal 복귀
OVERRIDES = f'{OUT}/mapping_unit_overrides.json'         # 사람 확정(검토 대기 처분): {nano_id: {status, reason, date, by}}


def strand_prox(con, cap=STRAND_CAP, ref_min_docs=STRAND_REF_MIN_DOCS, basis='mixed_v2'):
    """갈래별 근접도(구 '고립도 iso'; 09-08 개칭, 계산 불변) — m52 정의에 기준 집합 조건을 더한 것. 값이 클수록 나머지 갈래와 가깝다.
    basis='mixed_v2': 혼합 확정 나노(mixed_confirmed_v3), 유효 문헌 = 멤버 − 정본 배제 표(exclusion_flags; 09-09 재빌드부터 v2 + v3.2)(상태표 n_valid 와 같은 기준). 이름의 'v2'는 이력상 표기다.
    basis='junk_v3'(#127): 정크 나노(junk_targets 테이블), 잔여 문헌 = 멤버 − C-F1 v3(비연구 v3.1·철회) − 정보 없음.
    정본(#125, 정의 C) = cap 0(상한 없음) · ref_min_docs 3: ETO 임베딩이 있는 3편 이상 갈래만 서로의 기준이 되고, 조각 갈래
    (1~2편)는 그 기준에 대해 평가만 받는다(prox_i = Σ_{j∈기준, j≠i} share_j z_ij / Σ_{j∈기준, j≠i} share_j; 기준이 자기뿐이면
    prox=+inf 로 코어; 기준 집합이 비면 조각 갈래는 평가 불능 = prox 결측). 임베딩 있는 갈래가 둘 미만인 나노는 평가하지 않는다.
    cap 400 · ref 0 은 구 정의 A(s0_eto_coherence 의 pair 비용 상한을 물려받은 구현 세부; A.75 비교용, --out-suffix _capA)."""
    z = np.load(f'{OUT}/eto_cluster_emb_tsk.npz')
    cids, V = z['cids'], z['V'].astype(np.float32)
    V /= np.linalg.norm(V, axis=1, keepdims=True) + 1e-9
    cidx = {int(c): i for i, c in enumerate(cids)}
    rng = np.random.default_rng(7)
    ra, rb = rng.integers(0, len(V), 400_000), rng.integers(0, len(V), 400_000)
    nc = (V[ra] * V[rb]).sum(1)
    mu, sd = float(nc.mean()), float(nc.std())
    if basis == 'mixed_v2':
        target = f"'{OUT}/mixed_confirmed_v3.parquet'"
        excl = f"anti join '{L.EXCLUSION_FLAGS}' e using (work_id)"
    else:
        target = 'junk_targets'
        excl = (f"anti join '{EXCLUSION_V3}' e using (work_id) "
                f"anti join (select work_id from '{NOINFO_FLAGS}' where ut and not has_abs and not jd) ni using (work_id)")
    rows = con.execute(f"""
      with mem as (select m.effective_nano_id nano_id, m.work_id
        from '{L.YJK}/work/atlas_work_membership.parquet' m
        join {target} x on x.nano_id = m.effective_nano_id
        {excl})
      select m.nano_id, cast(w.cluster_id as bigint) cid, count(*) n
      from read_csv('{SNAP}/works_cset_mapofscience.csv', header=true, quote='"',
                    ignore_errors=true, all_varchar=true) w
      join mem m on m.work_id = w.oaid_w group by 1, 2 order by 1, 2""").fetchall()
    out = []
    i = 0
    while i < len(rows):
        nid = rows[i][0]; j = i
        while j < len(rows) and rows[j][0] == nid:
            j += 1
        grp = rows[i:j]; i = j
        idx = [cidx.get(int(c)) for _, c, _ in grp]
        keep = [k for k, x in enumerate(idx) if x is not None]
        if len(keep) < 2:
            continue
        ns = np.array([grp[k][2] for k in keep], dtype=np.float64)
        if cap and len(ns) > cap:
            top = np.argsort(-ns)[:cap]; ns = ns[top]; keep = [keep[k] for k in top]
        M = V[[idx[k] for k in keep]]
        sh = ns / ns.sum()
        Sg = (M @ M.T - mu) / sd
        ref = (ns >= ref_min_docs) if ref_min_docs else np.ones(len(ns), dtype=bool)
        W = sh[None, :] * ref[None, :]
        num = (Sg * W).sum(1) - np.diag(Sg) * sh * ref
        den = W.sum(1) - sh * ref
        # 분모 0: 기준 갈래 자신이면(다른 기준이 없음) 코어(+inf), 조각 갈래이면 평가 불능(NaN; far 는 False 로 남지만 뜻 없음)
        prox = np.where(den > 1e-9, num / np.maximum(den, 1e-9), np.where(ref, np.inf, np.nan))
        for k, s, n, z_ in zip(keep, sh, ns, prox):
            out.append((int(nid), int(grp[k][1]), int(n), float(s), float(z_), bool(z_ < TAU_Z), basis))
    return pd.DataFrame(out, columns=['nano_id', 'cid', 'n', 'share', 'prox', 'far', 'basis'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--junk-source', default='v3', choices=['v2', 'v3'])
    # #125(09-08 사용자 확정 "C안을 수용합니다"): 정본 정의 = 상한 없음 · 기준 집합 = 3편 이상 갈래. 구 정의 A(상한 400·기준 전부)는
    # --strand-cap 400 --ref-min-docs 0 --out-suffix _capA 로 재현한다(A.75 비교).
    ap.add_argument('--strand-cap', type=int, default=STRAND_CAP, help='나노당 평가 갈래 수 상한(0 = 전부; 정본 0)')
    ap.add_argument('--out-suffix', default='', help="산출 파일 접미(예: '_capA' → 정본을 덮지 않는 비교 실행)")
    ap.add_argument('--ref-min-docs', type=int, default=STRAND_REF_MIN_DOCS, help='고립도 기준 집합 최소 편수(정본 3 = 실질 갈래만 기준)')
    a = ap.parse_args()
    t0 = time.time()
    con = duckdb.connect(); con.execute("SET threads TO 32; SET memory_limit='96GB'")
    base = con.execute(f"""
      select p.nano_id, p.size n_valid, a.pct_mem_jd junk_ratio_v2, p.junk_candidate,
             x.nano_id is not null in_mixed, x."group" mixed_group, x.confidence mixed_confidence
      from '{L.PIPE}/out/packs_v2.parquet' p
      left join '{L.A5_DIST}' a using (nano_id)
      left join '{OUT}/mixed_confirmed_v3.parquet' x using (nano_id)""").fetchdf()
    # 09-09 재빌드(#131) 정합 단언: 상태표 n_valid(packs_v2.size)는 정본 배제 표와 같은 판이어야 한다(다른 판의 팩으로 돌리면 즉시 멈춘다)
    _mem_n = con.execute(f"select count(*) from '{L.YJK}/work/atlas_work_membership.parquet'").fetchone()[0]
    _ex_n = con.execute(f"select count(distinct work_id) from '{L.EXCLUSION_FLAGS}'").fetchone()[0]
    if int(base.n_valid.sum()) != _mem_n - _ex_n:
        raise SystemExit(f'packs_v2 size 합 {int(base.n_valid.sum()):,} ≠ 멤버십 {_mem_n:,} − 정본 배제 {_ex_n:,} = {_mem_n-_ex_n:,}: 팩과 배제 표의 판이 다르다 — 재빌드 순서(배제 표 → 팩 → 상태표)를 확인하라')
    if os.path.exists(A5_V3):
        v3 = pd.read_parquet(A5_V3)[['nano_id', 'pct_mem_jd']].rename(columns={'pct_mem_jd': 'junk_ratio_v3_preview'})
        base = base.merge(v3, on='nano_id', how='left')
        print('정크 비율 원천 = a5_dist(정본 배제 표 기준 v2 + v3.2; 09-09 재빌드 #131)')
    elif os.path.exists(V3_PREVIEW):
        v3 = pd.read_parquet(V3_PREVIEW)[['nano_id', 'pct_v3']].rename(columns={'pct_v3': 'junk_ratio_v3_preview'})
        base = base.merge(v3, on='nano_id', how='left')
    else:
        base['junk_ratio_v3_preview'] = np.nan
    jr = base['junk_ratio_v2'] if a.junk_source == 'v2' else base['junk_ratio_v3_preview']
    base['junk_source'] = a.junk_source
    base['junk_flag'] = np.where(jr >= JUNK_DOMINATED, 'dominated', np.where(jr >= JUNK_REVIEW, 'review', 'none'))

    # #127: 정크 나노(v3 비율 ≥30%)는 잔여(− C-F1 v3 − 정보 없음) 기준의 갈래표를 따로 만들어 그것만 쓴다(혼합·정크 겹침 46개 포함).
    # 혼합·정크 겹침 나노의 갈래표는 정크 기준 한 벌만 저장해 (nano_id, cid) 유일성을 지킨다.
    is_junk = base.junk_flag.isin(['dominated', 'review'])
    con.register('junk_targets', base.loc[is_junk, ['nano_id']])
    n_res = con.execute(f"""select m.effective_nano_id nano_id, count(*) n
        from '{L.YJK}/work/atlas_work_membership.parquet' m join junk_targets x on x.nano_id = m.effective_nano_id
        anti join '{EXCLUSION_V3}' e using (work_id)
        anti join (select work_id from '{NOINFO_FLAGS}' where ut and not has_abs and not jd) ni using (work_id)
        group by 1""").df().set_index('nano_id').n
    base['n_residue_v3'] = base.nano_id.map(n_res).where(is_junk)
    st_m = strand_prox(con, a.strand_cap, a.ref_min_docs, 'mixed_v2')
    st_j = strand_prox(con, a.strand_cap, a.ref_min_docs, 'junk_v3')
    junk_ids = set(base.loc[is_junk, 'nano_id'])
    st = pd.concat([st_m[~st_m.nano_id.isin(junk_ids)], st_j], ignore_index=True)
    st.to_parquet(f'{OUT}/mapping_unit_strands{a.out_suffix}.parquet', index=False)
    far = st[st.far].groupby('nano_id').n.sum().rename('far_docs')
    att = st.groupby('nano_id').n.sum().rename('attached_docs')
    ncore3 = st[(~st.far) & (st.n >= CORE_STRAND_MIN_DOCS)].groupby('nano_id').size().rename('n_core_strands_ge3')
    base = base.merge(far, on='nano_id', how='left').merge(att, on='nano_id', how='left').merge(ncore3, on='nano_id', how='left')
    base['n_core_strands_ge3'] = base.n_core_strands_ge3.fillna(0).astype(int)
    base['far_docs'] = base.far_docs.fillna(0).astype(int)
    denom = np.where(is_junk, base.n_residue_v3.fillna(0), base.n_valid)
    # #129(09-09 사용자 확정; A.85) R1: 부착률(부착 ÷ 분모)이 ATTACH_FRAC_MIN 미만이면 갈래 기반 코어 판정을 하지 않는다(코어 없음·보류)
    base['attach_frac'] = np.where(base.attached_docs.notna(), base.attached_docs.fillna(0) / np.maximum(1, denom), np.nan)
    base['attach_frac_low'] = base.attach_frac.notna() & (base.attach_frac < LAD.ATTACH_FRAC_MIN)
    # #129 R2: 미부착 문헌 가운데 임베딩 최근접 갈래가 여유폭 이상으로 '평가된 먼 갈래'이면 먼 갈래로 본다(코어 몫·처분 모두).
    # 근접도 코어(status_v1 사슬)에 대해 먼저 적용하고, 단계별 임계값 규칙의 코어에는 수준별로 다시 센다(run_ladder 안).
    cand_nanos = set(base.loc[base.in_mixed | is_junk, 'nano_id'])
    un_by_nano = LAD.load_unattached(cand_nanos, residue_nanos=set(base.loc[is_junk, 'nano_id']))   # 09-09: 유효성은 정본 플래그로 재적용(정크 = 잔여, 혼합 = v2)
    base['n_unattached_margin'] = base.nano_id.map(lambda n: len(un_by_nano.get(int(n), {}))).astype(int)
    _core_v1 = {int(n): set(int(c) for c in g[~g.far].cid) for n, g in st.groupby('nano_id')}
    _eval = {int(n): set(int(c) for c in g.cid) for n, g in st.groupby('nano_id')}
    base['un_far_docs'] = [LAD.unattached_far(un_by_nano.get(int(n), {}), _core_v1.get(int(n), set()), _eval.get(int(n), set())) if int(n) in _core_v1 else 0 for n in base.nano_id]
    base['far_docs'] = base.far_docs + base.un_far_docs          # 먼 갈래 문헌 = 먼 갈래 부착 + 먼 갈래로 귀속된 미부착(보류 목록의 far_strand + far_unattached)
    base['core_share'] = np.where((base.in_mixed | is_junk) & base.attached_docs.notna(),
                                  1.0 - base.far_docs / np.maximum(1, denom), np.nan)
    base.loc[base.attach_frac_low, 'core_share'] = 0.0             # R1: 코어 판정 불가 → 코어 없음
    print(f'정크 나노 {int(is_junk.sum())}개: 잔여 문헌 합 {int(base.n_residue_v3.sum()):,} · 갈래표 {len(st_j):,}행(mixed 기준 {len(st_m):,}행 중 정크 겹침 제외)', flush=True)

    # 09-09 재빌드(#131) 계획 검토 적발: 옛 DC_<nano> 판정은 나노 id 로만 재사용되어 갈래 판이 바뀌면 낡은 판정이 조용히 남는다.
    # → 현재 근접도 코어 키(prox_key)를 먼저 계산하고, 옛 판정은 재빌드 직전 스냅샷 키와 현재 키가 같을 때만, 새 판정(DC_<nano>_<key>)은 키가 같을 때만 쓴다.
    prox_key = {int(n): LAD.core_key(g[~g.far].cid) for n, g in st.groupby('nano_id')}
    snap_key = dict(zip(*(lambda d: (d.nano_id.astype(int), d.core_key))(pd.read_parquet(CORE_KEY_SNAPSHOT)))) if os.path.exists(CORE_KEY_SNAPSHOT) else {}

    def _load(path, prefix):
        """prefix 'DC_' 결과를 나노별로 해소한다: item_id 'DC_<nano>' (옛 형식) 은 snap_key == prox_key 인 나노에만, 'DC_<nano>_<key>' 는 key == prox_key 일 때만 유효.
        'D_'(혼합 판정) 등 다른 접두는 종전대로 나노 id 만 쓴다."""
        out = {}
        if os.path.exists(path):
            for line in open(path):
                j = json.loads(line)
                iid = j.get('item_id', '')
                if not (iid.startswith(prefix) and 'format_error' not in j):
                    continue
                parts = iid[len(prefix):].split('_')
                nid = int(parts[0])
                if prefix == 'DC_':
                    key = parts[1] if len(parts) > 1 else None
                    cur = prox_key.get(nid)
                    if key is None and not (cur is not None and snap_key.get(nid) == cur):
                        continue          # 옛 판정: 코어 키가 스냅샷과 다르면 버린다(재판정 대상)
                    if key is not None and key != cur:
                        continue          # 다른 코어 집합에 대한 판정
                out[nid] = j.get('verdict')
        return out
    rej_sol = _load(CORE_RESULTS, 'DC_'); rej_astra = _load(CORE_RESULTS_ASTRA, 'DC_')
    # #125: 정의 C 코어에 대한 재판정은 정본 정의로 산출할 때만 구 판정을 덮는다 — 정의 A 재현(--strand-cap 400 --ref-min-docs 0)에는
    # 정의 A 코어에 대한 구 판정만 써야 A.73 이 재현된다(09-08 재검증 지적)
    canonical = (a.strand_cap == STRAND_CAP and a.ref_min_docs == STRAND_REF_MIN_DOCS)
    rej_astra_c = _load(CORE_RESULTS_ASTRA_C, 'DC_') if canonical else {}
    rej_astra_j = _load(CORE_RESULTS_ASTRA_J, 'DC_') if canonical else {}   # #127: 정크 잔여 코어 재판정
    rej_astra_v3 = _load(CORE_RESULTS_ASTRA_V3, 'DC_') if canonical else {}  # 09-09 재빌드: 키 식별 재판정(혼합·정크 공용; 키가 맞는 것만 남는다)
    rej_astra_all = dict(rej_astra); rej_astra_all.update(rej_astra_c); rej_astra_all.update(rej_astra_v3)
    rej_astra_j = dict(rej_astra_j); rej_astra_j.update(rej_astra_v3)
    # 정크 나노는 잔여 코어(정크·정보 없음 제거)에 대한 재판정만 유효하다 — 혼합 기준 재판정은 쓰지 않는다
    base['core_rejudge_sol'] = [None if j else rej_sol.get(n) for n, j in zip(base.nano_id, is_junk)]
    base['core_rejudge_astra'] = [rej_astra_j.get(n) if j else rej_astra_all.get(n) for n, j in zip(base.nano_id, is_junk)]
    base['core_rejudge'] = base.core_rejudge_astra.where(base.core_rejudge_astra.notna(), base.core_rejudge_sol)
    base['core_rejudge_source'] = np.where(base.nano_id.isin(rej_astra_v3.keys()), 'astra_v1.1_v3(#131)',
                                  np.where(base.nano_id.isin(rej_astra_j.keys()) & is_junk, 'astra_v1.1_j(#127)',
                                  np.where(base.nano_id.isin(rej_astra_c.keys()) & ~is_junk, 'astra_v1.1_c(#125)',
                                  np.where(base.core_rejudge_astra.notna(), 'astra_v1.1', np.where(base.core_rejudge_sol.notna(), 'sol_v1', None)))))
    # #121: 혼합 확정(Sol v1) 나노를 Astra(v1.1)가 single 로 판정하면 매핑 단위로 복귀(mixed_cleared)
    mix_astra = _load(MIXED_RESULTS_ASTRA, 'D_')
    base['mixed_astra_verdict'] = base.nano_id.map(mix_astra)
    # 09-08(사용자 지적 "확신도 medium 도 좀 있네요"): Astra 확신도를 공개 산출물에 싣는다 — medium ∧ mixed_no_core 는 v2 재검토 1순위(A.79 보론)
    mix_conf = {}
    if os.path.exists(MIXED_RESULTS_ASTRA):
        for line in open(MIXED_RESULTS_ASTRA):
            j = json.loads(line)
            if j.get('item_id', '').startswith('D_') and 'format_error' not in j:
                mix_conf[int(j['item_id'][2:])] = j.get('confidence')
    base['mixed_astra_confidence'] = base.nano_id.map(mix_conf)
    base['in_mixed_sol'] = base.in_mixed
    base['mixed_cleared'] = base.in_mixed & (base.mixed_astra_verdict == 'single')
    base['in_mixed'] = base.in_mixed & ~base.mixed_cleared

    def status(r):
        if r.attach_frac_low:                      # #129 R1: 부착률 미달 → 갈래 기반 코어 판정 불가(보류)
            return 'junk_no_core' if r.junk_flag in ('dominated', 'review') else ('mixed_no_core' if r.in_mixed else 'normal')
        if r.junk_flag in ('dominated', 'review'):
            # #127(09-08 사용자 확정): 정크 나노도 비연구·정보 없음을 뺀 잔여로 코어 절차를 밟는다(#118 문언대로). 코어 갈래 0 이면
            # #123 대로 코어 없음. 구 junk_dominated(전부 보류)·junk_review(사람 대기열)는 폐지.
            if r.n_core_strands_ge3 == 0:
                return 'junk_no_core'
            if r.core_share == r.core_share and r.core_share >= CORE_SHARE_MIN:
                if r.core_rejudge == 'single':
                    return 'junk_core'
                if r.core_rejudge == 'mixed':
                    return 'junk_no_core'
                if r.core_rejudge == 'uncertain':
                    return 'junk_core_review'
                return 'junk_core_pending'
            return 'junk_no_core'
        if r.in_mixed:
            # #123(09-07 사용자 확정): 코어 갈래(3편 이상)가 하나도 없으면 잔류 몫이 크거나 재판정이 single 이어도 코어 없음 — 잔류가
            # 잔가지·미부착뿐이라 재판정 입력이 비어 판정이 성립하지 않는다(78891 사례)
            if r.n_core_strands_ge3 == 0:
                return 'mixed_no_core'
            if r.core_share == r.core_share and r.core_share >= CORE_SHARE_MIN:
                if r.core_rejudge == 'single':
                    return 'mixed_core'
                if r.core_rejudge == 'mixed':
                    return 'mixed_no_core'
                if r.core_rejudge == 'uncertain':
                    return 'mixed_core_review'      # 재판정 보류(low) → 사람 확정(D15 indeterminate)
                return 'mixed_core_pending'
            return 'mixed_no_core'
        return 'normal'
    base['status_v1'] = base.apply(status, axis=1)      # #118·#125 근접도 규칙의 판정(기록·이행 규칙용)
    # #128(09-09 사용자 확정): 현행 규칙으로 확정된 코어(single)는 유지하고, 그 밖의 혼합·정크 나노는 문헌 가중 평균 연결 단계별 임계값 규칙을 거친다.
    # 이행 규칙(LADDER_KEEP_VALIDATED): 근접도 규칙으로 Astra 가 single 확정한 코어와 사람 확정 대기(uncertain) 코어는 다시 열지 않는다
    kept = ['mixed_core', 'junk_core', 'mixed_core_review', 'junk_core_review'] if LADDER_KEEP_VALIDATED else []
    # 사람 지시 'rederive_ladder'(overrides.json): 이행 규칙의 예외로 그 나노는 확정 코어가 있어도 단계별 임계값 규칙을 다시 탄다(09-09 71933)
    _ov0 = json.load(open(OVERRIDES)) if os.path.exists(OVERRIDES) else {}
    rederive = {int(k) for k, o in _ov0.items() if not str(k).startswith('_') and o.get('rederive_ladder')}
    base['core_rule'] = np.where(base.status_v1.isin(kept) & ~base.nano_id.isin(rederive), 'prox_v1', None)
    base['core_tau'] = np.nan; base['core_key'] = None; base['core_cids'] = None; base['ladder'] = None
    if canonical:
        elig = base[(base.in_mixed | is_junk) & (~base.status_v1.isin(kept) | base.nano_id.isin(rederive)) & ~base.attach_frac_low].nano_id   # R1 나노는 단계별 임계값 규칙도 타지 않는다
        cur_key = {}; cur_v = {}
        for nid, g in st[st.nano_id.isin(elig)].groupby('nano_id'):
            cur_key[int(nid)] = LAD.core_key(g[~g.far].cid); cur_v[int(nid)] = base.loc[base.nano_id == nid, 'core_rejudge'].iloc[0]
        denom_map = {int(n): float(d) for n, d in zip(base.nano_id, denom)}
        lad = LAD.run_ladder(st, set(elig), denom_map, cur_key, cur_v, CORE_SHARE_MIN, CORE_STRAND_MIN_DOCS, LADDER_TAUS, un_by_nano).set_index('nano_id')
        adopted = lad[lad.core_rule.notna()]
        # 갈래표: 채택된 묶음 밖은 먼 갈래(조각 포함), 안은 코어
        st['core_rule'] = np.where(st.nano_id.isin(base.loc[base.core_rule == 'prox_v1', 'nano_id']), 'prox_v1', None)   # 코어 없음 나노의 far 는 근접도 기준(표시용)이나 core_rule 은 비운다
        st['core_tau'] = np.nan
        for nid, r in adopted.iterrows():
            core = set(json.loads(r.core_cids)); m = st.nano_id == nid
            st.loc[m, 'far'] = ~st.loc[m, 'cid'].isin(core); st.loc[m, 'core_rule'] = 'ladder_w'; st.loc[m, 'core_tau'] = r.core_tau
        far2 = st[st.far].groupby('nano_id').n.sum(); ncore2 = st[(~st.far) & (st.n >= CORE_STRAND_MIN_DOCS)].groupby('nano_id').size()
        for nid, r in adopted.iterrows():
            m = base.nano_id == nid
            base.loc[m, 'un_far_docs'] = int(r.un_far)                       # R2: 채택 묶음 기준으로 다시 센 미부착 먼 갈래
            base.loc[m, 'far_docs'] = int(far2.get(nid, 0)) + int(r.un_far); base.loc[m, 'n_core_strands_ge3'] = int(ncore2.get(nid, 0))
            base.loc[m, 'core_share'] = float(r.core_share); base.loc[m, 'core_rejudge'] = r.verdict
            base.loc[m, 'core_rejudge_astra'] = r.verdict; base.loc[m, 'core_rejudge_source'] = 'astra_v1.1_w(#128)' if r.verdict else None
            base.loc[m, 'core_rule'] = 'ladder_w'; base.loc[m, 'core_tau'] = r.core_tau; base.loc[m, 'core_key'] = r.core_key; base.loc[m, 'core_cids'] = r.core_cids
        base['ladder'] = base.nano_id.map(lad.ladder)
        st.to_parquet(f'{OUT}/mapping_unit_strands{a.out_suffix}.parquet', index=False)   # 단계별 임계값 규칙 반영판으로 다시 저장
        print(f'#128 단계별 임계값 규칙: 대상 {len(elig)} · 채택 {int((adopted.verdict == "single").sum())} · 사람 확정(uncertain) {int((adopted.verdict == "uncertain").sum())} · 판정 없음 {int(adopted.verdict.isna().sum())}', flush=True)
    base['status'] = base.apply(status, axis=1)
    base['status_auto'] = base.status
    base['override_reason'] = None
    if os.path.exists(OVERRIDES):
        ov = json.load(open(OVERRIDES))
        for nid, o in ov.items():
            if str(nid).startswith('_') or not o.get('status'):   # 이력 키·지시 전용 항목(rederive_ladder)은 status 를 덮지 않는다
                continue
            m = base.nano_id == int(nid)
            base.loc[m, 'status'] = o['status']; base.loc[m, 'override_reason'] = f"{o.get('date')} {o.get('by')}: {o.get('reason')}"
        print(f'사람 확정 반영 {sum(1 for k, o in ov.items() if not str(k).startswith("_") and o.get("status"))}건 · 재도출 지시 {len(rederive)}건 · 이력 {len(ov.get("_retired", {}))}건')
    base['tau_z'] = TAU_Z; base['policy'] = ('#118·#121·#123·#125·#127·#128·#129' if canonical else '#118·#121·#123 (비정본 재현)'); base['strand_cap'] = a.strand_cap; base['ref_min_docs'] = a.ref_min_docs
    base = base.sort_values('nano_id')
    base.to_parquet(f'{OUT}/mapping_unit_status{a.out_suffix}.parquet', index=False)
    print(f'저장 {OUT}/mapping_unit_status.parquet ({len(base):,}행, 정크 원천 {a.junk_source}, {time.time()-t0:.0f}s)')
    print('상태 분포:', base.status.value_counts().to_dict())
    print('코어 재판정 원천:', base.core_rejudge_source.value_counts(dropna=False).to_dict(), '| 혼합 해제(mixed_cleared):', int(base.mixed_cleared.sum()))
    print(f'정크 플래그(판정 원천 {a.junk_source}):', base.junk_flag.value_counts().to_dict())
    if base.junk_ratio_v3_preview.notna().any():
        v3f = np.where(base.junk_ratio_v3_preview >= JUNK_DOMINATED, 'dominated',
                       np.where(base.junk_ratio_v3_preview >= JUNK_REVIEW, 'review', 'none'))
        print('정크 플래그(v3 미리보기):', pd.Series(v3f).value_counts().to_dict())
    m = base[base.in_mixed]
    print(f'혼합 {len(m):,}: 잔류 몫 ≥{CORE_SHARE_MIN:.0%} {int((m.core_share >= CORE_SHARE_MIN).sum()):,} · '
          f'미만 {int((m.core_share < CORE_SHARE_MIN).sum()):,} · 측정불능 {int(m.core_share.isna().sum())}')


if __name__ == '__main__':
    main()
