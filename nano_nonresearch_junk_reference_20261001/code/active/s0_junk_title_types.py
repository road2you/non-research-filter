"""s0_junk_title_types — 정크 제목 유형 분포의 재생성기(구판 생산 코드 부재 해소).

junk_title_type_dist.parquet 은 정크 후보 nano 의 팩 H 에 실리는 유형 분포(§5 가군:
순수 잡물 뭉치의 라벨 재료)인데, 구판(08-26)은 #79 정규식 정합 이전 플래그로 만들어졌고
생산 코드도 저장소에 없었다. 이 스크립트는 현행 junk_doc_flags(#79 정합판 101,462편)의
제목을 s0_lib.JUNK 의 분기 구조를 그대로 옮긴 유형 규칙으로 분류해 같은 경로에 다시 쓴다.

사용: .venv/bin/python pipeline/scripts/s0_junk_title_types.py
출력: pipeline/out/junk_title_type_dist.parquet (nano_id, junk_type, docs)
"""
import os
import re
import sys

import duckdb
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s0_lib as L  # noqa: E402

OUT = f'{L.PIPE}/out/junk_title_type_dist.parquet'

# 유형 규칙: s0_lib.JUNK 의 분기를 유형별로 나눈 것(첫 일치 우선, 결정적).
TYPES = [
    ('correction', re.compile(
        r'(?i)^\s*((corrections?|corrigend[a-z]*|errat[a-z]*)(\s+(to|of|for|in))?\s*[:"“‘«\']'
        r'|corrections?$|erratum$|errata$|corrigendum$|corrigenda$)')),
    ('reply', re.compile(
        r'(?i)^\s*(response to (the )?(comments?|letters?|editor|referees?|reviewers?|reply|critique|discussion)'
        r'|response to\s*[:"“‘«]|responses?$|comments?$|reply$|authors.{0,2}\s*reply$'
        r'|letter to the editor)')),
    ('editorial', re.compile(
        r'(?i)^\s*(editorial|preface|foreword|publisher.s note|in this issue)')),
    ('book_review', re.compile(r'(?i)^\s*book review')),
    ('index_toc', re.compile(
        r'(?i)^\s*(author index|subject index|front matter|back matter|table of contents'
        r'|issue information|list of contents|contents of volume|masthead)')),
    ('announcement', re.compile(
        r'(?i)^\s*(announcement|obituar|reviewer acknowledg|acknowledgement to referee'
        r'|call for papers)')),
    ('untitled', re.compile(r'(?i)^\s*untitled')),
]


def junk_type(title):
    t = str(title or '')
    for name, pat in TYPES:
        if pat.search(t):
            return name
    return 'other'


c = duckdb.connect()
c.execute("SET threads=16")
# 09-09 밤 팩 반영 재빌드(#131): 원천을 junk_doc_flags_v3(v2 + v3.2 통합)로 바꾼다. v3 유형이 있는 문헌은 그 유형(들)로,
# v2 만 잡은 문헌(junk_types 비어 있음)은 종전 v2 유형 규칙으로 분류한다. 2차 판정으로 강등된 표시(flag_only)는 뺀다.
rows = c.execute(f"""
  select j.nano_id, coalesce(v.title_display, j.title_head, '') title, j.junk_types
  from '{L.JUNK_DOC_FLAGS_V3}' j
  left join '{L.BIB_STORE}' v using(work_id)
  where not j.flag_only""").fetchall()
n_v3 = sum(1 for _, _, ty in rows if ty is not None and len(ty) > 0)
print(f'정크 플래그 {len(rows):,}편 로드 (v3 유형 보유 {n_v3:,}편 · v2 규칙 분류 {len(rows)-n_v3:,}편)')
agg = {}
for nid, t, ty in rows:
    types = list(ty) if (ty is not None and len(ty) > 0) else [junk_type(t)]
    for y in types:
        k = (int(nid), y)
        agg[k] = agg.get(k, 0) + 1
df = pd.DataFrame([(n, ty, d) for (n, ty), d in sorted(agg.items())],
                  columns=['nano_id', 'junk_type', 'docs'])
df.to_parquet(OUT, index=False)
print(f'저장 {OUT}: {len(df):,}행 · nano {df.nano_id.nunique():,}개 · 합계 {df.docs.sum():,}편')
print(df.groupby('junk_type').docs.sum().sort_values(ascending=False).to_string())
