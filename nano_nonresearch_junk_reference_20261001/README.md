# 나노 클러스터의 비연구 문헌 판별과 제외 기준

김영진 박사의 나노 클러스터 결과에서 OpenAlex가 Article로 분류한 문헌 중 비연구성 자료가 섞이는 문제를 다루면서 사용한 제목 정규식, 문헌별 제외표, 나노 단위 junk 판정 기준을 정리한 자료입니다. 2026년 10월 1일에 확인한 코드와 기존 산출물의 사본을 함께 보관했습니다.

핵심 판별식은 `s0_lib.py`의 `JUNK`와 `JUNK_V3`입니다. 제목에서 정정 고지, 편집글, 서평, 목차, 심사자 감사문 등의 형태를 감지하고, 판정 예외와 철회 우선순위를 반영해 `exclusion_flags.parquet`를 만듭니다. 후속 작업은 이 제외표를 기준으로 문헌을 걸러냅니다. 원래 멤버십 자료를 삭제하거나 소속을 변경하는 방식은 아닙니다.

이 자료를 만들면서 원본 코드와 산출물을 변경하지 않았고, 판별 파이프라인이나 외부 API를 실행하지 않았습니다. 아래 건수는 이 폴더에 복사한 기존 Parquet 파일을 SELECT로 조회한 결과입니다.

## 먼저 볼 파일

| 확인할 내용 | 이 폴더의 파일 | 주요 위치와 역할 |
|---|---|---|
| 판별 정규식 | [s0_lib.py](code/active/s0_lib.py) | 144–206행에 v2 규칙, 확장 규칙 27개, 오탐 방지용 제외식이 있습니다. |
| 정규식만 따로 확인 | [regex_patterns.json](reference/regex_patterns.json) | 원본 코드를 실행하지 않고 AST로 추출한 전체 규칙과 원본 행 번호입니다. |
| v2 문헌 플래그 생성 | [s0_junk_flags.py](code/active/s0_junk_flags.py) | 19–33행에서 전체 멤버십의 정제된 제목에 v2 규칙을 적용합니다. |
| 확장 규칙과 판정 예외 반영 | [s0_junk_flags_v3.py](code/active/s0_junk_flags_v3.py) | 43–80행에서 확장 규칙, 제외식, 2차 판정, v2 우선 처리를 통합합니다. |
| 최종 문헌 제외표 생성 | [s0_exclusion_flags.py](code/active/s0_exclusion_flags.py) | 28–58행에서 철회와 비연구 사유를 통합합니다. |
| 나노별 비연구 비율 계산 | [s0_a5_dist.py](code/active/s0_a5_dist.py) | 27–55행과 86–90행에서 분자와 분모를 확인할 수 있습니다. |
| 나노의 junk 상태 결정 | [s0_mapping_unit_status.py](code/active/s0_mapping_unit_status.py) | 156–167행에서 대상 나노를 고르고, 257행 이후에서 잔여 코어와 최종 상태를 처리합니다. |
| 비연구 제목 유형 집계 | [s0_junk_title_types.py](code/active/s0_junk_title_types.py) | 플래그의 유형을 나노별로 집계합니다. |
| 현재 정의와 활용 범위 | [정크와 혼합의 현행 정의](reference/정크와혼합_현행정의_2026-09-24.md) | junk 계열, 연구 코어, 매핑 참여 범위를 설명한 기존 문서의 사본입니다. |

원본 프로젝트 위치는 `/home/snoopy/Positron/nano-cluster-massage`입니다. 각 사본의 정확한 원본 경로와 SHA256은 [manifest.json](manifest.json)에 기록했습니다.

## 문헌 단위 판별 방식

판별 입력은 김영진 판 멤버십에 속한 문헌의 정제된 제목 `title_display`입니다. `s0_junk_flags.py`와 `s0_junk_flags_v3.py`의 해당 경로에는 `type = 'article'` 조건이 없습니다. 따라서 Article 오분류 문제를 해결하려는 작업 배경과 실제 검사 범위를 구분해야 합니다. 이 자료의 제외 건수를 곧바로 “Article 오분류가 확정된 건수”로 해석할 수는 없습니다. 또한 이 경로는 문헌 본문 전체를 읽어 연구성을 판정하는 절차가 아닙니다.

v2 규칙은 정정 고지, 회신, 편집글과 서문, 서평, 목차와 색인, 판권지, 공지 등을 감지합니다. 이후 확장한 `JUNK_V3`에는 심사자 감사문, 호별 안내, 편집자 추천 목록, 입수 도서 목록, 학술대회 초록·보고, 일부 교육용 증례 형식 등의 규칙이 추가됐습니다. 현재 딕셔너리에는 27개의 규칙 항목이 있습니다. 서로 겹칠 수 있는 항목이므로 27개가 상호 배타적인 문헌 유형을 뜻하지는 않습니다.

오탐을 줄이기 위한 보완도 포함되어 있습니다. v2는 `Correction to: …` 같은 정정 고지 형태를 잡으면서, `Correction of Depth Bias …` 같은 보정 연구나 `Response to fever …` 같은 생리 반응 연구까지 넓게 잡지 않도록 제한했습니다. 확장 규칙의 `JUNK_V3_EXCLUDE`에는 `In Brief: …`, `News & Notes: …`와 일부 서평 접두형에 대한 예외가 있습니다. 세부 정규식은 위 코드와 추출 JSON에 원문 그대로 보관했습니다.

제목이 짧거나 내용어가 부족한 경우는 `uninformative_title()`로 별도 표시합니다. 이것만으로 비연구 문헌이라고 확정하지 않습니다. `junk_doc()` 함수는 v2의 `JUNK`만 적용하므로, 이 함수 하나를 호출하는 것으로 현재의 전체 제외 판정을 재현할 수 없습니다.

확장 규칙에 적중한 문헌 중 2차 판정에서 `research`로 판단된 것은 `flag_only=True`로 남겨 실제 제외 대상에서 뺍니다. 다만 v2에도 적중한 문헌은 코드상 v2 판정이 우선합니다. 관련 기록은 [second_pass_results.jsonl](reference/second_pass_results.jsonl)에 있습니다.

## 실제 제외표와 현재 건수

실제 제외 여부의 기준 파일은 **[exclusion_flags.parquet](data/exclusion_flags.parquet)**입니다. `work_id`당 한 행을 남기며, 사유가 겹치면 `retracted` → `junk_regex_v2` → `junk_regex_v3` 순으로 우선합니다. 따라서 철회와 비연구 사유가 겹친 문헌은 철회 사유로 집계됩니다.

2026년 10월 1일에 복사본을 직접 조회한 결과는 다음과 같습니다.

| 제외 사유 | 문헌 수 |
|---|---:|
| `junk_regex_v2` | 101,461편 |
| `junk_regex_v3` | 179,505편 |
| 비연구 사유 합계 | **280,966편** |
| `retracted` | 2,326편 |
| 전체 제외표 | **283,292편** |

전체 제외표의 행수와 고유 `work_id` 수는 모두 283,292개로 일치합니다. 이는 규칙과 기존 판정에 따른 제외 결과이며, 모든 문헌의 연구성을 이번에 다시 심사했다는 뜻은 아닙니다.

함께 보관한 [junk_doc_flags_v3.parquet](data/junk_doc_flags_v3.parquet)는 판별 플래그 자료입니다. v2 출처 101,462편, v3 출처 중 제외용 표시 181,192편, 표시만 남긴 `flag_only=True` 462편이 있습니다. 이 파일에는 철회 사유로 우선 집계되는 문헌도 있으므로, 단순 행수 합계를 정본 비연구 제외 건수로 쓰면 안 됩니다.

초기 v2 플래그는 [junk_doc_flags.parquet](data/junk_doc_flags.parquet), 나노별 유형 집계는 [junk_title_type_dist.parquet](data/junk_title_type_dist.parquet)에 있습니다. 유형 집계에는 한 문헌이 여러 유형에 기여할 수 있으므로 유형별 편수를 더한 값과 고유 제외 문헌 수를 구분해야 합니다.

## 나노 클러스터의 junk 기준

분모는 **제외 전 해당 나노의 전체 멤버 문헌 수**이고, 분자는 **정본 제외표에서 `junk_regex_v2` 또는 `junk_regex_v3` 사유를 가진 문헌 수**입니다. 철회 사유는 비연구 분자에 넣지 않습니다.

```text
비연구 문헌 비율 pct_mem_jd
  = 100 × 정본 비연구 사유 문헌 수 ÷ 원래 나노 전체 멤버 수
```

현재는 이 비율이 **30% 이상**인 나노에 비연구 문헌 등을 제외한 잔여 코어 판정 절차를 적용합니다. 승인된 연구 코어가 남으면 `junk_core`, 승인된 코어가 없으면 `junk_no_core`로 구분합니다. 판정 과정에는 검토 대기와 미완료 상태도 있으며, 최종 상태는 단순히 비율 하나로 모두 결정되지 않습니다. 공개 개요서의 `is_junk=true`는 `junk_no_core`에 해당하고, `junk_core`는 승인된 코어를 활용합니다.

과거 결정 #118은 50% 이상을 정크 우세, 30% 이상 50% 미만을 검토 대상으로 나눴습니다. 이후 #127에서 30% 이상 전체에 잔여 코어 절차를 적용하도록 바뀌었습니다. 코드의 `JUNK_DOMINATED=50.0`과 `JUNK_REVIEW=30.0`은 남아 있지만, 예전의 `junk_dominated`와 `junk_review`를 현재 최종 상태로 해석하면 안 됩니다.

[a5_dist.parquet](data/a5_dist.parquet)와 [mapping_unit_status.parquet](data/mapping_unit_status.parquet)를 조회한 현재 결과는 다음과 같습니다.

| 집계 항목 | 확인값 |
|---|---:|
| 전체 나노 수 | 78,049개 |
| 비율 계산의 전체 멤버 수 합계 | 58,904,845편 |
| 비연구 비율 30% 이상 50% 미만 | 42개 나노 |
| 비연구 비율 50% 이상 | 50개 나노 |
| 비연구 비율 30% 이상 합계 | 92개 나노 |
| 최종 `junk_core` | 19개 나노 |
| 최종 `junk_no_core` | 73개 나노 |

이 수치는 현재 보관 중인 산출물의 집계입니다. 초기 김영진 자료의 당시 문헌 수나 과거 코드 주석의 건수와 동일하다고 가정하지 않습니다. `s0_exclusion_flags.py` 머리말의 103,787편도 v2 시기의 값이며, 현재 전체 제외 건수는 위의 283,292편입니다.

`pct_mem_jd`와 `pct_mem_comb`도 구분해야 합니다. 전자는 비연구 사유의 비율이고, 후자는 비연구 표시와 정보 부족 제목의 합집합 비율입니다. 예전 A5의 `junk_pct`라는 이름만 보고 모두 비연구 비율로 해석하면 혼동이 생깁니다. 현재 나노 상태 판정의 비연구 비율 원천은 `a5_dist.pct_mem_jd`입니다.

## 규칙이 개선된 과정의 근거

관련 결정 #25, #26, #29, #79, #89, #90, #118, #122, #127, #131, #132의 원문 행을 [결정원장 관련 항목](reference/결정원장_관련항목.md)에 발췌했습니다. 원본 행 번호와 원본 파일의 해시를 함께 기록했습니다.

| 이력 코드 | 용도 |
|---|---|
| [s9_junk.py](code/history/s9_junk.py) | thk 대표 코어 제목에서 정규식 적중 비율을 탐색하던 초기 코드입니다. 현재 전체 멤버 기준 판정과 분모가 다릅니다. |
| [m54_junk_genre_v31.py](code/history/m54_junk_genre_v31.py) | 장르별 규칙 v3.1을 조사하던 코드입니다. |
| [m55_junk_genre_v31_verify.py](code/history/m55_junk_genre_v31_verify.py) | 확장 규칙의 적중 사례와 오탐을 검토하기 위한 코드입니다. |
| [m70_junk_v32_patterns.py](code/history/m70_junk_v32_patterns.py) | v3.2 추가 제목 형태와 검토 표본을 조사하던 코드입니다. |

실제 현재 규칙은 이력 코드가 아니라 `code/active/s0_lib.py`와 정본 제외표를 기준으로 확인합니다. 과거 조사에서 사용한 모든 중간 파일을 이 폴더에 모은 것은 아닙니다.

## 보관 범위와 검증

이 폴더는 설명과 검토를 위한 사본 묶음입니다. 원본 스크립트의 절대경로를 보존했기 때문에 사본을 실행해도 원본 프로젝트의 산출물을 덮어쓸 수 있습니다. 일부 생성기는 모듈을 import하는 것만으로도 집계와 파일 쓰기를 시작합니다. 코드와 정규식 확인에는 텍스트 사본 또는 `reference/regex_patterns.json`을 사용해야 합니다.

독립적으로 전체 판별을 다시 실행하는 데 필요한 원본 전체 멤버십, 대규모 서지 정본, 철회 메타데이터, 코어 판정 의존 자료와 실행 환경은 포함하지 않았습니다. 이 묶음만으로 전체 파이프라인을 재실행할 수 있는 것은 아닙니다.

| 파일 | 기록 내용 |
|---|---|
| [manifest.json](manifest.json) | 사본별 원본 위치, 크기, 원본 수정 시각, SHA256과 추출 자료의 근거를 기록했습니다. |
| [queries.sql](verification/queries.sql) | 복사한 데이터의 건수를 확인한 SELECT 질의입니다. 이 README가 있는 폴더를 기준으로 상대경로를 사용합니다. |
| [snapshot_summary.json](verification/snapshot_summary.json) | 조회 시각과 실제 집계 결과를 기록했습니다. |
| [data_schemas.json](verification/data_schemas.json) | 포함된 Parquet 파일 6개의 열 이름과 자료형을 기록했습니다. |
| [package_validation.json](verification/package_validation.json) | 사본과 원본의 해시 일치, 정규식 추출 일치, 설명서 링크와 집계 대조 결과를 기록했습니다. |
| [SHA256SUMS](SHA256SUMS) | 검증 기록을 포함한 묶음 내 파일의 최종 SHA256 목록입니다. 목록 파일 자체는 제외합니다. |
