"""S0 공용 규칙 모듈 (설계서 v1.5 §4·§8 준거).

정본: design_v1/나노클러스터_텍스트표상_정밀화_작업설계서_v1.md (v1.5-RC; 결정 정본은 결정원장)
- 정크 제목 정규식: §4 정리 규칙 2(excluded_junk). thk 감사 패턴 확장판(프로토타입 계승).
- 초록 유효성: §4 (#85 25자 미만·"No abstract"류·LaTeX 잔재 과다 → 무효).
- 절단: #91(2026-09-02)로 팩 경로 폐기(전문 수록). trunc()는 V 슬림 팩 전용으로 존속.
- 기능·응용 문장 패턴(E5): §4 E5. v1.3 보강 패턴('applications like/such as', 'is used in') 포함.
- 결정성: 모든 무작위는 md5 해시 순서(seed 고정)로 대체한다(§4 공통: seed 고정, pack_hash 재현).
"""
import hashlib
import re

BASE = '/home/snoopy/Positron/nano-cluster-massage'
YJK = (f'{BASE}/resource/yjk_ver/science_atlas_explorer_paris_datapack_domain8_macro32_'
       'meso425_micro5299_k32_twostep_labels_nano78049_domain_macro_reviewed_meso_v3_'
       'terrain_rollup_sync20260610')
THK = f'{BASE}/resource/thk_ver'
PRE = f'{BASE}/design_v1/precomputed'
PIPE = f'{BASE}/pipeline'

RULES_VERSION = 'v1.5'          # 팩 규격 판(설계서 v1.5 frozen §4; #55 부착·E2 정크 필터)
# 근거팩 정본 경로(A.40): 경로 상수를 각 스크립트에 흩어 두었더니 #79의 경로 교체를
# 다섯 소비처가 채택하지 못하고 구판 out/packs를 계속 읽었다. 여기 한 곳에서만 정한다.
PACKS_DIR = f'{PIPE}/out/packs_v2'
PACKS_PARQUET = f'{PIPE}/out/packs_v2.parquet'
PACKS_DIR_LEGACY = f'{PIPE}/out/packs'      # 2026-08-22 파일럿 v1 팩. 읽지 말 것.

# ── 배제·부착 자원의 정본 경로(#87·#89·#90·#86·#88). 경로와 사유 상수는 여기 한 곳에서만
# 정의한다. #89: 별도 파일로 흩으면 경로 산재 사고가, 기존 파일에 합치면 '정크'의 의미가
# 코드 변경 없이 바뀌는 사고(junk_pct 사고)가 재발한다. ──
WORK_META = f'{PIPE}/out/work_meta_v2.parquet'            # #87 분류·출처 메타(6월판 전면 교체)
EXCLUSION_FLAGS = f'{PIPE}/out/exclusion_flags.parquet'   # #89 문서 배제 통합(reason 1급 열)
EXCLUSION_REASONS = {                                     # reason 값 → 팩 status 키의 정합
    'junk_regex_v2': 'excluded_junk',                     # 정크 정규식(#26 v2, #79 정합판)
    'retracted': 'excluded_retracted',                    # 철회(#89; work_meta_v2 단일 원천)
    'junk_regex_v3': 'excluded_junk',                     # 장르 정크 v3.2(#122·#131; 09-09 팩 반영 재빌드부터 정본 exclusion_flags 에 편입)
}
BIB_STORE = f'{PIPE}/out/bib_store_full_v116.parquet'   # 09-06 판 스위치(#112; 구판 = v115)  # 서지 정본(제목·초록 display). 판 전환은
                                # **이 상수 한 곳**에서만 한다(A.40 재발 방지 — 09-05 감사에서
                                # 30개 스크립트 하드코딩 적발·생산 체인 소비처 일괄 전환).
                                # v116(원천 교체) 재빌드 때 v116 으로 올린다.
ABSTRACT_FLAGS = f'{PIPE}/out/abstract_flags.parquet'     # 정형문 차단 178,980편(#99 소급+D-14 잔재 456; 초록만 무효)
ABSTRACT_RECOVERED = f'{PIPE}/out/abstract_recovered_union.parquet'  # 회수 보강층 3,359편(가드 후)
LANG_STATUS_TABLE = f'{PIPE}/out/lang_status_v1.parquet'  # #86 5R 실측 정본(코어 7.2M)
LANG_STATUS_FULL = f'{PIPE}/out/lang_status_full.parquet'  # #97 전 멤버 확장(37.4M; source=m5|lib)
LANG_INVALID = ('non_english_script', 'non_english_latin', 'mojibake')  # 5R 무효 3종
A5_DIST = f'{PIPE}/out/a5_dist.parquet'                   # #90 A5 전 멤버 분포(s0_a5_dist.py)
NANO_TOPIC_DIST = f'{PIPE}/out/nano_topic_dist_v2.parquet'  # #88 유효 멤버 기준 단일본
CSET_REF = f'{PIPE}/out/cset_ref_v2.parquet'              # #35 top1~3 점유율(유효 멤버 기준)
MAPPING_UNIT_STATUS = f'{PIPE}/out/mapping_unit_status.parquet'  # #118 매핑 단위 상태(s0_mapping_unit_status.py)
MAPPING_UNIT_DOCS = f'{PIPE}/out/mapping_unit_docs.parquet'      # #118 ⑤ 문헌별 매핑 단위(s0_mapping_hold_list.py; far_strand 등)
JUNK_DOC_FLAGS_V3 = f'{PIPE}/out/junk_doc_flags_v3.parquet'      # #122 장르 정크 v3.1 문헌 플래그(junk_types[], flag_only)
PACKS_DIR_MU = f'{PIPE}/out/packs_v26'                           # #124 v2.6 'mu' 변형 팩(코드 판정 헤더·mixed_core 코어만) — 정본 packs_v2 불변
PACKS_PARQUET_MU = f'{PIPE}/out/packs_v26.parquet'
# #136(09-12) member-fill 선별 신호의 정본 경로. 내부 인용도 = 같은 나노 멤버들로부터 받은 인용 수(s0_citation_rank.py; 시험 30편 #17 과
# 같은 표), CSET 배정 = ETO v5.17.0 클러스터 배정(A.60 판 검증; cid 없음 = 미배정, 2024+ 등). 소비처 = s0_pack_builder.load_member_fill·
# s0_exposure_ledger.fill_candidates_bulk·s0_pack_bulk_v2(청크 조인)·s0_pack_regen_mu(부분집합 키).
INTERNAL_CITATION_RANK = f'{PIPE}/out/internal_citation_rank.parquet'   # (nano_id, work_id, internal_cites) 33.8M 행
CSET_ASSIGN = f'{PIPE}/out/cset_v517_assign.parquet'                    # (work_id, cid) 140.8M 행

BUILDER_VERSION = 's0_pack_builder/3.1'   # 3.1: 09-09 팩 반영 재빌드(#131) — 코어·멤버 정크 판정 = 정본 배제 표(v2 + 장르 정크 v3.2); 3.0: #86~#90 배제·언어·A5·메타 v2(2026-09-02 이행)
JUNK_TITLE_TYPE_DIST = f'{PIPE}/out/junk_title_type_dist.parquet'   # 정크 제목 유형 분포(s0_junk_title_types.py; 09-09 재빌드부터 junk_doc_flags_v3 기준)
# 09-09 팩 반영 재빌드(#131): 정본 배제 표의 확정 규모. s0_exclusion_flags 가 만들고 s0_pack_bulk_v2.preflight 와 s0_contract_check 가 대조한다.
EXCL_EXPECTED = {'rows': 283292, 'retracted': 2326, 'junk_regex_v2': 101461, 'junk_regex_v3': 179505}
SEED = 7                        # v1.2 프로토타입과 동일한 고정 seed
EXTREME_SIZE = 2964             # extreme nano 기준(≥2,964편; 진단·층화용)
# extreme 초록 상한 200은 2026-08-22 사용자 결정으로 제거됨(전수 입력; 코어셋 상한으로 유계)
import datetime as _dt
RECENT_FROM = _dt.date.today().year - 5   # C몫 '실행 시점 기준 최근 5년'(§4 L146·#36-A1;
                                          # 규격대조 N: 2021 고정은 2027년부터 규격 이탈)
MEMBER_FILL_MIN = 30            # core_ok·초록 유효 <30 → 멤버 보충(§4 규칙 4)
MEMBER_FILL_MAX = 20
# #136(2026-09-12 사용자 승인; 실측 A.96 = m81_member_fill_rules_probe_20260912): member-fill 후보의 선별 순서. 종전 det_key('fill') 해시 순
# (사실상 무작위)을 두 층으로 바꾼다 — 1층 = 코어 CSET 클러스터 일치 ∪ CSET 미배정(cid 없음; 미확인은 불일치가 아니므로 일치와 같은 층),
# 2층 = CSET 불일치. 각 층 안은 내부 인용도(INTERNAL_CITATION_RANK.internal_cites; 없으면 0) 내림차순, 동률은 det_key('fill', work_id).
# 코어 CSET 집합 = 팩 코어 문헌(E1a 코어 행 ∪ E1b = 배제 4종 status 를 뺀 코어)의 cid 분포에서 누적 점유가 MEMBER_FILL_CSET_CORE_COVER 를
# 처음 넘기는 상위 집합(상한 MEMBER_FILL_CSET_CORE_MAX, 동률 cid 오름차순). 정크 후보 나노의 멤버 탐침 10편(junk-probe)은 탐침 목적상
# 종전 해시 순을 유지한다(JUNK_PROBE_ORDER). 상한 20편(MEMBER_FILL_MAX)은 그대로다(상향은 별도 결정). 값은 contract_v1.json pack 절과
# s0_contract_check 가 대조한다. 구현 = s0_pack_builder.cset_core_set/fill_sort_key/load_member_fill(order='tiered').
MEMBER_FILL_ORDER = 'cset_match_or_unknown, internal_cites desc, det_key'
MEMBER_FILL_CSET_CORE_COVER = 0.5
MEMBER_FILL_CSET_CORE_MAX = 3
JUNK_PROBE_ORDER = 'det_key'
# 구분표 A2(09-11): K1 키워드 근거에서 초록 본문을 빼는 E1a 행의 표지(제목은 근거로 유지).
# #140 뒤 제외 대상은 s0_pack_builder curate 의 'abstract_mismatch?' 플래그뿐이다. 유효 member-fill 은 포함한다.
# 팩 빌더는 바꾸지 않는다(팩 해시 불변); 게이트(g_gate.Gate.k1_evidence_lines)가 읽을 때 걷어 낸다.
# 그 초록에만 근거한 term(전 행 기준 strong·recombined 인데 제외본에서 없음)의 처분은 '표시만' 이다: 게이트가 minor
# K1_MISMATCH_ONLY_NOTE 를 붙이고 행은 지우지 않는다(#101 ② 유지; 생성 프레임 확정안 v1.1 D1, 09-11). g_repair 의 행 삭제 스위치는
# K1_MISMATCH_ONLY_DISPOSITION 이 'drop_row' 일 때만 켜지며, 그 값은 원장에 #101 ② 예외 결정이 오르기 전에는 쓰지 않는다.
# 계약 등재 예정(확정안 D14; 등재 전이라 코드가 정본): hard_gates.k1_evidence_excluded_rows = K1_EXCLUDED_ROW_MARKERS ·
# k1_excluded_rows_keep_title = True · k1_mismatch_only_grade = 'minor' · k1_mismatch_only_disposition = 'mark_only'.
K1_EXCLUDED_ROW_MARKERS = ('abstract_mismatch?',)  # #140: 유효 member-fill 초록은 K1 근거에 포함

# #140(09-13): 상태별 키워드 수량의 단일 상수. 의미·역할별 최소 수는 두지 않는다.
KEYWORDS_MIN = 1
MIXED_NO_CORE_KEYWORDS_MIN = 2
KEYWORDS_MAX = 25
CORE_OBJECT_MIN = 0


def keyword_count_bounds(status=None, *, mixed_nc=False, junk=False):
    """G/V 공용 수량 범위. 코드 상태가 있으면 우선하고, 구 호출의 bool 인수도 받는다."""
    if status:
        mixed_nc, junk = status == 'mixed_no_core', status == 'junk_no_core'
    return (0 if junk else MIXED_NO_CORE_KEYWORDS_MIN if mixed_nc else KEYWORDS_MIN), KEYWORDS_MAX


def keyword_row_identity(row):
    """#140 완전 동일 반복 행 키. 누락·추가 필드나 잘못된 형식은 병합하지 않는다."""
    if (not isinstance(row, dict) or set(row) != {'term', 'role', 'variants'}
            or not isinstance(row['term'], str) or not row['term'].strip()
            or row['role'] not in ('core_object', 'method', 'component_material', 'capability_metric', 'application')
            or not isinstance(row['variants'], list)
            or not all(isinstance(v, str) for v in row['variants'])):
        return None
    return row['term'], row['role'], tuple(row['variants'])


K1_EXCLUDED_ROWS_KEEP_TITLE = True
K1_MISMATCH_ONLY_GRADE = 'minor'                 # 게이트 등급(g_gate K1 mismatch-only 표시의 sev)
K1_MISMATCH_ONLY_DISPOSITION = 'mark_only'       # 'mark_only' | 'drop_row' — g_repair.K1_MISMATCH_ONLY_DROP 이 이 값에서 파생된다
K1_MISMATCH_ONLY_NOTE = 'not grounded (excluded abstract rows only; verify)'   # 표시 문구(게이트가 쓰고 수리기·셀프테스트가 식별)
# 구분표 A3(09-11): CODE VERDICT mixed_no_core 라벨의 갈래 이름에 걸리는 장르어·잡동사니어(형식 표시 MXG; #130 "코드는 형식, 판정은 의미").
# 등급은 minor 표시만이다(확정안 v1.1 D2: 'other eponymous disorders' 같은 오탐이 있어 수리·재생성 대상이 아니다; 갈래 실재는 V 몫).
# 대조 위치는 갈래 문자열 안 임의 위치의 단어 경계이다(머리 명사 한정 아님). 앞뒤 하이픈 결합형('review-based'·'peer-review bias')은 제외.
# v_issue_corpus_stats.GENRE(M4 측정)와 같은 정규식이어야 한다(정규식 복제 금지 — 그쪽이 이것을 참조).
# 계약 등재 예정(확정안 D14): hard_gates.impl_mixed_strand_genre_regex = 이 상수 경로 · mixed_strand_genre_grade = 'minor' ·
# mixed_strand_genre_scope = 'any_word_boundary'.
MIXED_STRAND_GENRE_GRADE = 'minor'
MIXED_STRAND_GENRE_SCOPE = 'any_word_boundary'
MIXED_STRAND_GENRE_RE = re.compile(
    r'(?<!-)\b(case reports?|editorials?|letters?|notes?|essays?|commentar(?:y|ies)|reviews?|miscellaneous|unrelated|other)\b(?!-)', re.I)
ABSTRACT_MIN_CHARS = 25         # 초록 유효성 길이 하한(#85, 구 200)
LANG_RES_MIN_CHARS = 200        # 비영어 판정의 잔여 문자열 하한(#86). ABSTRACT_MIN_CHARS 와
                                # 하는 일이 다르다: 이쪽은 '영어 판정을 신뢰할 만큼 라틴 문자가
                                # 남았는가'를 본다. 25 로 낮추면 hard 중앙 0.899 인 비영어 88편이
                                # 유입되고 영어는 한 편도 살아나지 않는다(실측).
JUNK_NOTE_PCT = 10.0            # H에 정크 통계·예시 기재 임계(§4)
JUNK_CAND_PCT = 30.0            # 정크 nano 후보 확정 임계(§4 규칙 5)
JUNK_AUX_LATEX_PCT = 30.0       # A5 보조 신호: 코어 제목 LaTeX 잔재 비율(§4 규칙 5·#90)
JUNK_AUX_VALID_ABS_LT = 10      # A5 보조 신호: 유효 초록 절대 수 하한(#90 — 비율로는
                                # 잡히지 않는 근거 빈약을 절대 수로 잡는다)

# 정크 제목 정규식 v2 (2026-08-23 사용자 확정, 결정원장 #26).
# v1 대비: 정정(correction·corrigendum·erratum)·회신(response to)은 '고지 형태'만 잡는다.
# 고지 형태 = 콜론·인용부호 직결형("Correction to: X", 'Correction to "X"') 또는 단독형.
# 'Correction of Depth Bias ...'(측정 보정 연구), 'Response to fever ...'(생리 반응 연구)
# 같은 학술 용법 오탐(꼬리 감사 실측 약 10%)을 막기 위한 것이다. 이름만 딸린 회신
# ("Response to Wang and Guo")은 기계 구분이 불가능해서 놓치며, 과소 방향으로 설계했다.
JUNK = re.compile(
    r'(?i)^\s*('
    r'(corrections?|corrigend[a-z]*|errat[a-z]*)(\s+(to|of|for|in))?\s*[:"“‘«\']'
    r'|corrections?$|erratum$|errata$|corrigendum$|corrigenda$'
    r'|response to (the )?(comments?|letters?|editor|referees?|reviewers?|reply|critique|discussion)'
    r'|response to\s*[:"“‘«]'
    r'|responses?$|comments?$'
    r'|editorial|preface|foreword'
    r'|book review|reply$|authors.{0,2}\s*reply$|letter to the editor'
    r'|author index|subject index|untitled'
    r'|front matter|back matter|table of contents|issue information'
    r'|announcement|obituar|reviewer acknowledg|acknowledgement to referee|call for papers'
    r'|list of contents|contents of volume|masthead|publisher.s note|in this issue)')

# 정규식 v3.1 — 장르 정크 15종(#117·#122, 2026-09-07; 산출·검증 = m54_junk_genre_v31.py·m55_junk_genre_v31_verify.py,
# 블라인드 감사 600건 오탐 1.67%, 유형 최대 7.5%). 09-09 팩 반영 재빌드(#131)부터 v3 는 s0_junk_flags_v3.py → s0_exclusion_flags.py 를 거쳐
# 정본 배제 표(exclusion_flags.parquet, reason junk_regex_v3)에 들어가고, 팩·상태표·C-F1 이 모두 그 표 하나를 읽는다(JUNK v2 정규식은 v2 사유의 원천으로만 남는다).
JUNK_V3 = {   # 값은 (?i) 접두를 포함한 완성 정규식(파이썬 re·DuckDB RE2 공통) — m54 는 실행 때 붙였으므로 여기서 미리 붙여 둔다
    'commentary': '(?i)^\\s*(?:a |an |some |brief |further |additional |editorial |invited |guest |clinical |clinicians?[’\\\']?s? |authors?[’\\\']?s? |expert |critical |short )?(?-i:(?:commentary|Commentary|COMMENTARY|commentaries|Commentaries|COMMENTARIES|comment|Comment|COMMENT|comments|Comments|COMMENTS))\\s*(?:(?:$|\\s*[:.•;(\\[]|\\s+[-–]|\\s+\\d)|(?:one|two|three|four|five|six|seven|eight|nine|ten|i|ii|iii|iv)\\b|(?:on|to|regarding|concerning)\\s*(?:[:"“‘«\\\']|the (?:article|paper|report|letter|manuscript|note|study|editorial|review|comments?|response|reply|proposal|discussion|papers|articles|contribution|target article|commentary|book|preceding|foregoing|above|accompanying)\\b))|^\\s*(?:comments?|commentary),\\s*(?:with (?:the )?(?:authors?[’\\\']? )?repl(?:y|ies)|with response|and repl(?:y|ies)|and responses?|response|reply)\\b|^\\s*(?:a |general |panel |open |floor |invited |formal |further |the )?(?-i:(?:discussion|Discussion|DISCUSSION|discussions|Discussions|DISCUSSIONS))\\s*(?:$|\\s*[:.•;(\\[]|\\s+[-–]|(?:of|on)\\s*(?:[:"“‘«\\\']|the (?:article|paper|report|letter|manuscript|note|study|editorial|review|comments?|response|reply|proposal|discussion|papers|articles|contribution|target article|commentary|book|preceding|foregoing|above|accompanying)\\b)|by\\b)',
    'reply': '(?i)^\\s*(?:a |an |the |our |brief |short |further )?(?:authors?[’\\\']?s? |editors?[’\\\']?s? )?(?-i:(?:reply|Reply|REPLY|rejoinder|Rejoinder|REJOINDER|replies|Replies|REPLIES|rejoinders|Rejoinders|REJOINDERS))\\s*(?:(?:$|\\s*[:.•;(\\[]|\\s+[-–]|\\s+\\d)|(?:to|by|from)\\b)|^\\s*in (?:reply|rejoinder)\\s*(?:$|\\s*[:.]|\\s+[-–]|to\\b)|^\\s*in response\\s*(?:$|\\s*[:.]|\\s+[-–]|to (?:the |a |an |our |my )?(?:comments?|letters?|critics?|critique|editors?|drs?\\.?|prof\\.?|professor|article|paper|review|reply|commentary|commentaries|discussion|editorial|correspondence|[:"“‘«\\\']))|^\\s*(?:a |an |the |our |brief |short |further )?(?:authors?[’\\\']?s? )?(?-i:(?:response|Response|RESPONSE|responses|Responses|RESPONSES))\\s*(?:$|\\s*[:.]|\\s+[-–]|to (?:the |our |my )?(?:critics?|comments?|commentar|discussants?|discussion|reviewers?|referees?|editors?|letters?|reply|replies|rejoinder|critique|responses?|commentaries|correspondence|readers?)\\b|to\\s*[:"“‘«\\\'])',
    'letter': "(?i)^\\s*(?:clinical |readers?[’\\']?s? |selected |brief |short )?(?-i:(?:letter|Letter|LETTER|letters|Letters|LETTERS|correspondence|Correspondence|CORRESPONDENCE))\\s*(?:$|\\s*[:.(]|\\s+[-–]|to the (?:editors?|case|journal)\\b|and (?:comments?|replies|reply|responses?|corrections?|notes)\\b|from (?:the )?(?:editors?|readers?)\\b)|^\\s*dear (?:editors?|readers?|colleagues?|members?|sir|sirs|madam)\\b",
    'editor_note': '(?i)^\\s*(?:the |a |an )?(?:guest |managing |associate |new |outgoing |incoming |section |senior |executive |consulting )?(?:editors?[’\\\']?s?|editor.in.chief[’\\\']?s?|editorial board[’\\\']?s?)\\s+(?:notes?|comments?|corner|page|forum|foreword|message|column|desk|picks?|top picks|preface|welcome|remarks|reflections?|word|farewell|greeting|mailbag|mailbox|postbag|notebook|diary|soapbox|musings|pen|prerogative|chair|roundtable|recommends)\\b|^\\s*(?:the |a |an )?(?:guest |managing |associate |section |senior |executive )?(?:editors?[’\\\']?s?|editor.in.chief[’\\\']?s?)\\s+(?:introduction|perspective|report|annual report|letter|view|viewpoint|summary|selections?|commentary|preview|overview|prologue|epilogue|statement|announcement|reply|response|update|address|thoughts|voice|review|challenge)\\s*(?:$|\\s*[:.(]|\\s+\\d|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b|\\s+to\\b|\\s+for\\b|\\s+on\\b)|^\\s*(?:the )?(?:guest )?(?:editors?[’\\\']?s?|editor.in.chief[’\\\']?s?)\\s+(?:choices?|highlights?|picks?)\\s*(?:$|\\s+\\d|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b|\\s+for\\b|\\s+from\\b)|^\\s*(?:a |the )?(?:notes?|messages?|words?|letters?|greetings?|reports?|welcome|thoughts|comments?|remarks|column|reflections?|statement|updates?)\\s+from\\s+(?:the |our |your )?(?:editors?|editor.in.chief|guest editors?|presidents?|chair|chairman|chairwoman|chairperson|publishers?|editorial (?:board|office|desk|team)|desk|board|executive director|director|dean|secretary|secretariat|program (?:chair|director)|committee|society|association|council|officers?)\\b|^\\s*from the (?:editors?|editor.in.chief|guest editors?|desk|presidents?|chair|chairman|publishers?|editorial (?:board|office|desk)|secretary|director|dean)\\b|^\\s*(?:invited|guest) editorials?\\b|^\\s*ask the (?:editors?|experts?|expert panel|doctor|professor|authors?|specialist)\\b|^\\s*(?:special issue|special section|guest|theme|themed|symposium|section|supplement) editorials?\\b|^\\s*(?:a |the )?forewords?\\s+by\\b|^\\s*(?:guest |special issue |symposium |section )?(?:introduction|preface|foreword|prologue)s?\\s+(?:to|of|for)\\s+(?:the |this |a )?(?:special (?:issue|section|series|feature|edition|topic)|symposium|themed?|thematic|focus|forum|festschrift|colloquium|supplement|virtual (?:issue|special))\\b|^\\s*(?:guest )?(?:introduction|preface|foreword|prologue)s?\\s+(?:to|of|for)\\s+(?:the|this) (?:issue|section|volume|series|proceedings)\\s*(?:$|\\s*[:.(–—]|\\s+-|\\s+on\\b|\\s+of\\b|\\s*[:"“‘«\\\'])|^\\s*state of the (?:journal|society|association|college|academy|division|section|institute|federation)\\b',
    'books_received': '(?i)^\\s*(?:books?|publications?|monographs|new books|recent books|new publications|recent publications|literature|periodicals|journals|reports|pamphlets|reprints|materials?|documents?)\\s+(?:received|noted|noticed|available|reviewed|for review|in brief|in review|recently received|and (?:monographs|films|other|literature|media|journals|reports|pamphlets|reviews|periodicals|articles|publications|documents|software|videos|the media|materials|booklets|book reviews|bulletins|proceedings|papers|serials))\\b|^\\s*(?:new |recent |current )?(?-i:(?:books|Books|BOOKS|publications|Publications|PUBLICATIONS))\\s*(?:$|\\s*[:.(/]|\\s+[-–]|list\\b|for (?:review|the)\\b|of (?:the (?:month|year|week|quarter)|interest|note)\\b|in (?:brief|review|print|the news)\\b)|^\\s*(?:recent|new|current) [a-z]+ (?:and [a-z]+ )?(?:books|publications)\\s*(?:$|\\s*[:.(–—]|\\s+-|received\\b|of\\b|in\\b)|^\\s*books? lists?\\b|^\\s*books reviews?\\b|^\\s*review articles\\s*$|^\\s*reports (?:&|and) (?:other )?(?:publications|documents)\\b|^\\s*doctoral dissertations (?:in|on|completed|accepted|received|abstracts)\\b|^\\s*reviews? of (?:periodical|recent|current) (?:literature|publications)\\b|^\\s*current literature (?:reviewed|review|abstracts|abstracted)\\b|^\\s*literature reviews? and comment\\b|^\\s*\\[?(?:book|books)\\s*(?:&|and|/)\\s*(?:resource|film|media|journal|software|video|other|other media|electronic|multimedia|web)s?\\s+(?:reviews?|notes?|notices?)\\b|^\\s*book (?:notes?|notices?|briefs?|section|corner|forum|column|watch|essays?|of the (?:month|week|year|quarter)|reviews? (?:section|essay|column|symposium|supplement|editor))\\b|^\\s*(?:extended|commissioned|brief|special|critical|featured|essay|double|joint|comparative|long|short|mini|classic|graphic|new|recent|invited) (?:book|film|media|software) reviews?\\b|^\\s*\\[(?:book|film|media)s? reviews?\\]|^\\s*title \\((?:book|film) reviews?\\)|^\\s*review (?:essays?|symposi(?:um|a)|section|forum|column|feature|notes?|notices?|of books|of recent books|of new books)\\s*(?:$|\\s*[:.(–—]|\\s+-)|^\\s*reviews\\s*[—–-]\\s*(?:besprechungen|comptes rendus|book reviews|buchbesprechungen)\\b|^\\s*(?-i:(?:reviews|Reviews|REVIEWS))\\s*(?:$|\\s*[:.(]|\\s+[-–]|of (?:books|recent|new|current|periodical)\\b|and (?:notices|notes|comments|short notices|announcements|book notes|abstracts|reports)\\b)|^\\s*(?:research|book|literature|brief|short|media|film|software|web ?site|resource|product|video|recent|critical|journal|periodical|new book|new books|journal article|article|shorter|short notices and|briefer) reviews\\s*(?:$|\\s*[:.(–—]|\\s+-|and\\b|of (?:recent|new|current|the)\\b)|^\\s*(?:buch)?besprechung(?:en)?\\b|^\\s*rezension(?:en)?\\b|^\\s*comptes?[- ]rendus?\\b|^\\s*recensioni\\b|^\\s*recensions?\\b|^\\s*rese[ñn]as?\\b|^\\s*livres re[çc]us\\b|^\\s*boekbespreking(?:en)?\\b|^\\s*bücherschau\\b|^\\s*neue bücher\\b|^\\s*literaturbericht\\b|^\\s*notes de lecture\\b|^\\s*libros recibidos\\b|^\\s*list of (?:publications|books|new books|recent publications|papers|articles|references|contributors|participants|members|fellows|officers|delegates|reviewers|referees|abbreviations|figures|tables|symbols|plates|illustrations|maps|authors|exhibitors|sponsors|speakers|attendees|registrants|advertisers|donors|awards)\\b|^\\s*(?:recent|current|new) (?:publications|literature|books|articles|references|titles|releases)\\s*(?:$|\\s*[:.,(–—]|\\s+-|in\\b|on\\b|of\\b|received\\b|from\\b|relating\\b|relevant\\b)',
    'bibliography': "(?i)^\\s*(?:a |an )?(?:select(?:ed)? |annotated |current |recent |cumulative |classified |brief |short |partial |running |annual |supplementary |critical |comprehensive )?(?-i:(?:bibliography|Bibliography|BIBLIOGRAPHY|bibliographies|Bibliographies|BIBLIOGRAPHIES))\\s*(?:$|\\s*[:.(]|\\s+[-–]|of\\b|on\\b|for\\b|\\s*[—–-]\\s*editors[’\\']? selection\\b)",
    'news': "(?i)^\\s*(?-i:(?:news|News|NEWS))\\s*(?:$|\\s*[:&;.(]|\\s+[-–]|\\s+\\d|\\s+(?:and|&)\\s+(?:views?|notes?|notices?|comments?|announcements?|events?|reviews?|reports?|information|updates?|features?|letters?|highlights?|briefs?|analysis|opinion|people|appointments|diary|calendar|the (?:profession|society|association))\\b|\\s+in brief\\b|\\s+briefs?\\b|\\s+from\\b|\\s+for\\b|\\s+of the\\b|\\s+round-?ups?\\b|\\s+updates?\\b|\\s+items?\\b|\\s+notes?\\b|\\s+digest\\b|\\s+flash\\b|\\s+releases?\\b|\\s+views\\b|\\s+section\\b|\\s+column\\b|\\s+page\\b|\\s+desk\\b|\\s+feature\\b|\\s+report\\b|\\s+review\\b|\\s+watch\\b|\\s+headlines?\\b|\\s+highlights?\\b|\\s+corner\\b|\\s+bulletin\\b|\\s+summary\\b|\\s+letter\\b|\\s+brief\\b)|^\\s*[a-z&’\\']+ news\\s*$|^\\s*(?:association|society|institute|industry|member(?:ship)?|members[’\\']?|chapter|section|division|faculty|department|college|academy|foundation|federation|council|committee|company|corporate|campus|staff|alumni|conference|meeting|journal|research|science|policy|legislative|regulatory|government|international|national|regional|world|european|global|clinical|medical|nursing|hospital|health|technical|technology|business|trade|patent|book|publishing|education|product|people|personnel|professional|branch|state|local|federal|university|school|library|market|other|general|late|latest|breaking|current|recent|brief|short|miscellaneous|sundry|home|foreign|overseas)\\s+news\\s*(?:$|\\s*[:.,;(&–—]|\\s+-|\\s+\\d|\\s+(?:and|&)\\s+(?:views?|notes?|notices?|comments?|announcements?|events?|information|updates?)\\b|\\s+from\\b|\\s+in brief\\b|\\s+briefs?\\b|\\s+for\\b|\\s+of\\b|\\s+updates?\\b|\\s+items\\b|\\s+notes\\b|\\s+section\\b|\\s+column\\b)|^\\s*(?:research|news|literature|journal|clinical|science|policy|legislative|regulatory|technology|industry|evidence|practice|drug|product|conference|meeting|congress|abstract|paper|article|media|web|website|internet|patent|book|software|market|clinical trials?|publication|publications) (?:round-?ups?|watch|scan|scans|briefing|alerts?|monitor|corner|snippets)\\s*(?:$|\\s*[:.;(–—]|\\s+-|\\s+\\d|\\s+monthly\\b|\\s+weekly\\b|\\s+quarterly\\b|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*(?:research|news|literature|journal|clinical|science|policy|legislative|regulatory|technology|industry|evidence|practice|drug|product|conference|meeting|congress|abstract|paper|article|media|web|website|internet|patent|book|software|market|clinical trials?|publication|publications) (?:updates?|digest|briefs?|highlights|selections?|summaries|abstracts|abstracted)\\s*(?:(?:$|\\s+\\d|\\s*[(]\\s*(?:\\d|(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|\\s+monthly\\b|\\s+weekly\\b|\\s+quarterly\\b|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|\\s*[:;–—]\\s*(?:the )?(?:latest|recent|monthly|weekly|quarterly|top \\d|top ten|top five|highlights from|highlights of|this (?:month|issue|week)|news|\\d|(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)\\b)|^\\s*policy briefs?\\s*(?:$|\\s*[:.;(–—]|\\s+-|\\s+\\d|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*highlights (?:from|of) the (?:[a-z]+ ){0,3}(?:literature|latest (?:articles|literature|papers|research))\\s*(?:$|\\s*[:.;(]|\\s+\\d)|^\\s*(?:the )?(?:(?-i:[A-Z])[a-z&.’\\']*\\s+){0,3}(?-i:[A-Z])(?-i:(?:igest|IGEST|ewsletter|EWSLETTER|oticeboard|OTICEBOARD|otice board|OTICE BOARD))\\s*(?:$|\\s*[:.;(]|\\s+[-–]|\\s+\\d|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*bulletin board\\s*(?:$|\\s*[:.;(]|\\s+[-–]|\\s+\\d|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*digest of (?:articles|recent|current|the literature|literature|papers)\\b|^\\s*latest (?:clinical |medical |scientific )?(?:research|literature|evidence|publications|papers|articles)\\s*(?:$|\\s*[:.;(]|\\s+[-–]|\\s+\\d|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*(?:clinical|current|topical|professional|practice|policy|regulatory|legal|ethical|legislative) issues\\s*(?:$|\\s*[:;]|\\s+[-–]|\\s*[–—]\\s*(?:\\d|(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|\\s+\\d|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*(?:articles|papers|publications|books|items|literature) of interest\\s*(?:$|\\s*[:.;(]|\\s+[-–]|\\s+\\d|\\s+to\\b|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*in the literature\\s*(?:$|\\s*[:.;(]|\\s+[-–]|\\s+\\d|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*what[’\\']?s new\\s*(?:$|\\?\\s*$|\\s*[:.;]|\\s+[-–]|\\s+\\d|\\s+in this issue\\b|\\s*\\(\\s*(?:\\d|(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*(?:new year|birthday|queen[’\\']?s birthday|king[’\\']?s birthday|merit) (?:honou?rs|awards)\\b|^\\s*(?:awards?|honou?rs|prizes?|awards and honou?rs|honou?rs and awards|prizes and awards|awards and prizes)\\s*(?:$|\\s+\\d{4}|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*(?:upcoming|forthcoming|future|coming) (?:events|meetings|conferences|articles|papers|issues|symposia|courses|congresses|workshops|dates|seminars|publications|activities|special issues|titles)\\b|^\\s*(?:calendar|diary|diary dates|dates for your diary|events|meetings|conferences|courses|congresses|symposia|workshops|seminars|exhibitions|meetings? calendar|conference calendar|events calendar|calendar of (?:events|meetings|conferences|courses)|meetings? and (?:conferences|courses|events|symposia|congresses)|courses and (?:conferences|meetings|events)|conferences and (?:meetings|courses|events|symposia)|conferences, congresses,? and symposia|meetings? (?:announcements?|notices?|of interest|ahead|diary)|conference (?:announcements?|notices?|diary)|congress (?:calendar|diary)|society (?:notices?|announcements?|business|affairs|matters|news and notes)|association (?:business|affairs|matters|notices?|announcements?))\\s*(?:$|\\s*[:.;(]|\\s+[-–]|\\s+\\d|\\s+(?:for|of)\\s+(?:the )?(?:month|week|year|\\d|interest|societies|society|events|meetings|forthcoming|coming|upcoming|note|(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)\\b|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*calls? for (?:papers|abstracts|nominations|applications|proposals|manuscripts|submissions|contributions|participation|entries|posters|presentations|reviewers|volunteers|articles|chapters|comments|awards?|fellowships?|editors?|book|books|expressions)\\b|^\\s*(?-i:(?:notice|Notice|NOTICE|notices|Notices|NOTICES))\\s*(?:$|\\s*[:.]|\\s+[-–]|of (?:meetings?|the annual|annual|change|withdrawal|redundant|duplicate|books|forthcoming|elections?|awards?)\\b|to (?:authors|contributors|members|readers|subscribers|advertisers|our readers)\\b)|^\\s*(?:miscellany|miscellanea)\\s*(?:$|\\s+\\d|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*(?:personalia|personal and miscellaneous|people and places|appointments and awards|awards and (?:honou?rs|prizes|appointments)|honou?rs and awards|prizes and awards|new members|new fellows|members[’\\']? news|member news|notes and (?:news|comments|queries|notices|announcements)|odds and ends|in brief|briefly|short items|items of interest|in the news|in the journals|in other journals|elsewhere in the literature|from the literature|from the journals|from other journals|around the (?:world|journals|societies|regions|profession)|abstracts from around the world|highlights (?:of|from|in) this issue|in the next issue|coming in the next issue|next issue|inside this issue|about this issue|this month[’\\']?s (?:issue|special|highlights|cover|articles|selections))\\s*(?:$|\\s*[:.;(]|\\s+[-–]|\\s+\\d|\\s+from\\b|\\s+for\\b|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)",
    'index_toc': "(?i)^\\s*(?:cumulative |annual |volume |combined |five.year |ten.year |keyword |key ?word |name |species |taxonomic |title |citation |chemical |topical |topic |general |analytic(?:al)? |systematic |consolidated |complete |alphabetical |classified |contributors[’\\']? |reviewers[’\\']? )?(?:(?:author|subject|keyword|key ?word|volume|cumulative|annual|contributor|reviewer|advertiser|abbreviation|acronym|title|contents)s?[’\\']?s?(?: (?:and|&|/) (?:subject|author|title|keyword|name|species|volume|contents|contributor|advertiser|topic|topical|formula|key.?word)s?)?|(?:name|names|species|taxonomic|citation|chemical|topical|topic|general|combined|analytical|formula|compound|organism|genus|proper name) (?:and|&|/) (?:subject|author|title|keyword|name|species|volume|contents|contributor|advertiser|topic|topical|formula|key.?word)s?) index(?:es|ices)?\\s*(?:$|\\s*[:.,;(–—]|\\s+-|\\s+\\d|\\s+to\\b|\\s+for\\b|\\s+of (?:vol|volume|authors|subjects|the)\\b|\\s+vol\\b|\\s+volume\\b)|^\\s*(?:name|names|species|taxonomic|citation|chemical|topical|topic|general|combined|analytical|formula|compound|organism|genus|proper name) index(?:es|ices)?\\s*(?:$|\\s*[,:;(–—]?\\s*(?:to |for |of )?(?:the )?(?:vol|volume|\\d)|\\s+(?:to|for|of)\\s+(?:the )?[^,:;]{0,40}?\\b(?:vol|volume)\\b)|^\\s*index (?:of|to|by|for) (?:authors?|subjects?|volumes?|vol\\.?|contributors|keywords?|titles?|advertisers|papers|articles|abstracts|reviewers|referees|book reviews|books reviewed|contents|this (?:issue|volume)|the (?:volume|issue|year)|\\d|(?:names?|species|genera|taxa)\\s*(?:$|[,:;(]|\\s+(?:in|to|for|of)\\s+(?:vol|volume|this|the)\\b))|^\\s*(?-i:(?:index|Index|INDEX))\\s*(?:$|\\s*[:.;(]|\\s+[-–]|\\s*[,–—]\\s*(?:vol|volume|\\d)|\\s*,\\s*[^,:;]{0,60},\\s*(?:vol|volume)\\b|\\s+to vol|\\s+vol\\b|\\s+\\d|\\s+for (?:volume|vol)\\b|\\s+of (?:volume|vol|authors|subjects|names|papers)\\b)|^\\s*(?:cumulative|annual|volume|decennial|five.year|ten.year|master|general|comprehensive|combined|consolidated|complete|keyword|key ?word|alphabetical|classified) (?:index|indexes|indices|contents|table of contents)\\s*(?:$|\\s*[:.,;(–—]|\\s+-|\\s+\\d|\\s+to (?:vol|volume)|\\s+for (?:vol|volume)|\\s+of (?:vol|volume|authors|subjects))|^\\s*(?-i:(?:contents|Contents|CONTENTS))\\s*(?:$|\\s*[:;/]|\\s+[-–]\\s|\\s*[,.–—]\\s*(?:vol|volume|\\d|no\\.?\\s*\\d|issue|index|abstracts|masthead|table of contents)|\\s+list\\b|\\s+of (?:vol|volume|this|the (?:volume|issue|journal|present))\\b|\\s+vol\\b|\\s+volume\\b|\\s+pages?\\b|\\s+for\\b|\\s+\\d|\\s+and (?:index|author index|abstracts|masthead|editorial board)\\b|\\s+continued\\b|\\s+cont\\b|\\s+in this issue\\b|\\s+this issue\\b)|^\\s*(?:volume|issue|journal|annual|cumulative) (?:contents|table of contents|index|information|masthead)\\s*(?:$|\\s*[:.,;(–—]|\\s+-|\\s+\\d|\\s+to (?:vol|volume)|\\s+for (?:vol|volume)|\\s+of (?:vol|volume|authors|subjects))|^\\s*(?:front|back|end|prelim(?:inary)?)\\s?(?:matter|pages?)\\b|^\\s*(?:front|back|inside|outside|inside front|inside back|outside front|outside back) covers?\\b|^\\s*(?-i:(?:cover|Cover|COVER|covers|Covers|COVERS))\\s*(?:$|\\s*[:.;(]|\\s+[-–]|\\s+images?\\b|\\s+pictures?\\b|\\s+photos?\\b|\\s+photographs?\\b|\\s+illustrations?\\b|\\s+captions?\\b|\\s+story\\b|\\s+legends?\\b|\\s+art\\b|\\s+artwork\\b|\\s+\\d|\\s+and (?:contents|table of contents|masthead|front matter)\\b)|^\\s*(?:about|on) the covers?\\b|^\\s*(?:instructions?|information|guidelines?|guide|guidance|notes?|advice|notice|directions?|requirements?|checklist|suggestions?|rules|policy|policies) (?:to|for) (?:the )?(?:authors?|contributors?|prospective authors|reviewers?|referees?|advertisers?|subscribers?|readers?|manuscript (?:preparation|submission)|submission of (?:manuscripts|papers|articles)|preparation of (?:manuscripts|papers))\\b|^\\s*(?:full|entire|complete|whole|this) issue\\s*(?:$|\\s*[:.,;(–—]|\\s+-|\\s+pdf\\b|\\s+in pdf\\b|\\s+as pdf\\b|\\s+\\d)|^\\s*issue (?:information|contents|highlights|cover|masthead|table of contents|index|editorial board|front matter)\\b|^\\s*(?:editorial board|editorial (?:staff|committee|advisory board|advisers|advisors|office)|board of (?:editors|associate editors|reviewers|referees)|advisory board|associate editors|reviewing editors|consulting editors|editorial and advisory board|international advisory board|scientific advisory board|scientific committee|organizing committee|organising committee|programme committee|program committee|committee members?|officers and committees?|officers and council|society officers|membership list|list of members|roll of members|directory of members|members? directory|copyright page|copyright notice|copyright information|publication information|subscription information|subscription page|advertisers[’\\']? index|advertiser index|index to advertisers|classified advertisements?|reprint information|title page|half.title|list of abbreviations|cumulative contents|contents of volume|volume index|blank page|end page|inside pages|annual subscriptions?|subscription (?:rates|form|order form|prices)|advertisers? in this (?:issue|number))\\s*(?:$|\\s*[:.,;(–—]|\\s+-|\\s+\\d)|^\\s*(?:advertisements?)\\s*(?:$|\\s+\\d|\\s*[,:;(–—]\\s*(?:vol\\b|volume\\b|\\d))|^\\s*(?:classifieds|permissions|subscriptions|impressum|colophon|masthead)\\s*(?:$|\\s*[:;(]|\\s+[-–]|\\s+\\d)",
    'abstracts_meeting': '(?i)^\\s*(?:selected |poster |oral |speaker |free paper |scientific |meeting |conference |congress |session |symposium |invited |accepted |plenary |paper |presentation |society |research |trainee |resident |student |fellow |young investigator |late.breaking |encore |podium |platform |workshop |seminar |annual meeting |supplement |published |additional |further |other |misc(?:ellaneous)? |general |clinical |basic science |case report |video |e.?poster |mini.?oral |moderated poster |rapid fire |top |best |award |prize )abstracts\\s*(?:$|\\s*[:.,;(–—]|\\s+-|\\s+\\d|\\s+of\\b|\\s+from\\b|\\s+presented\\b|\\s+accepted\\b|\\s+for\\b|\\s+submitted\\b|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*abstracts\\s+(?:of (?:the |papers|posters|presentations|communications|invited|selected|scientific|free|oral|poster|current|recent|accepted|contributed|\\d)|from (?:the |\\d|papers|around|invited|selected|speakers)|presented (?:at|to|during)\\b|accepted for\\b|for (?:the |\\d|presentation|poster|oral)|submitted to\\b|(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*(?:proceedings|transactions|minutes|programme|program|reports?|summary|summaries|highlights|papers|communications|presentations|posters|lectures|sessions|agenda|records?|report and proceedings|proceedings and abstracts|scientific proceedings|selected proceedings|abstracts and proceedings|abstracts and programme) (?:of|from|for|at) (?:the )?(?:\\d+(?:st|nd|rd|th) |first |second |third |fourth |fifth |sixth |seventh |eighth |ninth |tenth |eleventh |twelfth |\\d{4} |annual |biennial |international |national |joint |spring |fall |autumn |winter |summer |regional |european |asian |american |british |world |inaugural |combined |scientific |general |business |plenary |mid.?year |midwinter |midsummer |[a-z]+ annual )*(?:meeting|conference|congress|symposium|symposia|session|sessions|colloquium|convention|assembly|scientific meeting|annual meeting|general meeting|business meeting|joint meeting)s?(?:\\s+(?:on|of|in|at|held|for)\\b|\\s*[,;(]|\\s*$|\\s+\\d|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*(?:meeting|meetings|conference|congress|symposium|session|plenary|annual meeting|society meeting|poster sessions?|oral sessions?|scientific sessions?|plenary sessions?|keynote session|business meeting|general meeting|council meeting|board meeting) (?:highlights?|summaries|summary|reports?|digest|round-?ups?|proceedings|minutes|programme|program|abstracts|papers|agenda|announcements?|notices?|in brief|at a glance|calendar|diary|news|notes|presentations?|posters?|lectures?|records?|schedule|timetable|itinerary|information|details|registration|invitation)s?\\s*(?:$|\\s*[:.,;(–—]|\\s+-|\\s+\\d|\\s+of\\b|\\s+from\\b|\\s+on\\b|\\s+at\\b|\\s+for\\b|\\s+in\\b|\\s+and\\b|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*(?:meeting|conference|congress|symposium|session) overview\\s*$|^\\s*(?-i:(?:highlights|Highlights|HIGHLIGHTS))\\s*(?:$|\\s*[:.;(]|\\s+[-–]|\\s+\\d|\\s+in this\\b|\\s+this\\b|\\s+(?:of|from|in)\\s+(?:the |this |our )?[^:;]{0,100}?\\b(?:(?:meeting|conference|symposium|congress|proceedings|abstracts|session|workshop|summit|assembly|convention|seminar)s?|issue|volume)\\b)|^\\s*(?:the )?(?:\\d+(?:st|nd|rd|th) |first |second |third |fourth |fifth |sixth |seventh |eighth |ninth |tenth |\\d{4} |annual |biennial |international |national |joint |spring |fall |autumn |winter |summer |regional |european |asian |american |british |world |inaugural |combined |scientific |general |business |plenary |mid.?year )*(?:annual|scientific|general|business|plenary|joint|spring|fall|autumn|winter|summer|international|national|regional|biennial|inaugural|combined|mid.?year)\\s+(?:meeting|conference|congress|symposium|assembly|convention|session)s?\\s*(?:$|\\s*[:.,;(–—]|\\s+-|\\s+\\d|\\s+of the\\b|\\s+of\\b|\\s+in\\b|\\s+at\\b|\\s+programme\\b|\\s+program\\b|\\s+abstracts\\b|\\s+report\\b|\\s+highlights\\b|\\s+proceedings\\b|\\s+announcement\\b|\\s+notice\\b|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*(?:scientific |final |preliminary |conference |meeting |congress |symposium |workshop |seminar |course |annual meeting |technical |educational |social |advance |detailed |full |complete |daily |printed )?programme?\\s*(?:$|\\s*[:.,;(–—]|\\s+-|\\s+\\d|\\s+(?:of|for)\\s+(?:the )?(?:\\d|(?:[a-z]+ ){0,3}(?:meeting|conference|congress|symposium|session|workshop|course|seminar|colloquium)s?\\b)|\\s+and abstracts\\b|\\s+at a glance\\b|\\s+overview\\b|\\s+schedule\\b|\\s+committee\\b|\\s+book\\b)',
    'case_record': "(?i)^\\s*case \\d{1,3}[-–— ]\\d{4}\\s*(?:$|\\s*[:.,;(–—]|\\s+-)|^\\s*(?:the )?(?:quiz |photo |picture |image |imaging |radiology |radiological |pathology |dermatology |ecg |ekg |x.?ray |clinical |interesting |teaching |mystery |puzzling |unusual |challenging |pediatric |paediatric |surgical |neurology |neurological |cardiology |ophthalmic |ophthalmology |dental |oral |veterinary |forensic )?(?:case|cases|picture|pictures|image|images|photo|photos|photograph|photographs|figure|film|radiograph|radiographs|ecg|ekg|slide|specimen|puzzle|puzzler|problem|question|quiz|diagnosis|patient|x.?ray|scan|cartoon|challenge|dilemma|pearl|conundrum|mystery|riddle|teaser|vignette|snapshot|record|records|presentation|conference|corner)s? of the (?:month|week|year|quarter|issue|day)\\b|^\\s*(?:clinical |christmas |snapshot |photo |picture |image |imaging |radiology |radiological |pathology |histopathology |cytology |dermatology |dermatologic |ecg |ekg |electrocardiographic |x.?ray |diagnostic |self.?assessment |self.?test |board.?style |board review |mcq |multiple.choice |pediatric |paediatric |surgical |neurology |neurological |neuro |cardiology |cardiac |ophthalmic |ophthalmology |ocular |dental |oral |veterinary |forensic |anatomy |anatomical |histology |microbiology |haematology |hematology |endocrine |renal |pulmonary |chest |gastrointestinal |gi |musculoskeletal |orthopaedic |orthopedic |spine |abdominal |pelvic |head and neck |ent |ultrasound |sonographic |ct |mri |nuclear medicine |emergency |trauma |toxicology |pharmacology |nursing |medical |monthly |weekly |quarterly |annual |new year |summer |winter |holiday |easter |anniversary |interactive |educational |teaching |resident[’\\']?s? |trainee[’\\']?s? |student[’\\']?s? |reader[’\\']?s? |photographic |pictorial |visual |video )?(?:quiz|quizzes|quiz case|quiz cases|brain.?teasers?|self.?assessment (?:quiz|questions?|test)|test yourself|spot diagnosis|spot the diagnosis|what[’\\']s your diagnosis|what is your diagnosis|whats your diagnosis|guess the diagnosis|can you diagnose|diagnose this|diagnosis please|image challenge|photo quiz|picture quiz|image quiz|mystery case|mystery diagnosis|unknown case|clinical problem.solving|problem solving case)s?\\s*(?:$|\\s*[:.,;(?!–—]|\\s+-|\\s+\\d|\\s+of the\\b|\\s+for\\b|\\s+no\\.?\\s*\\d|\\s+number\\b|\\s+answers?\\b|\\s+solutions?\\b|\\s+questions?\\b|\\s+case\\b|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*(?:clinical|diagnostic|image|imaging|photo|picture|radiology|radiological|radiologic|pathology|ecg|ekg|dermatology|christmas|snapshot|neuroimaging|neuroradiology|ultrasound|echo|endoscopy|endoscopic|ophthalmic|ophthalmology|dental|oral|veterinary) challenges?\\s*(?:$|\\s*[:.,;(?!–—]|\\s+-|\\s+\\d|\\s+of the\\b|\\s+no\\.?\\s*\\d|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*(?:answers?|solutions?|key|discussion|explanations?|the answers?|answer key) (?:to|for|of) (?:the |this |last |previous |the previous |the last |our |this month[’\\']?s |last month[’\\']?s |this issue[’\\']?s |last issue[’\\']?s )?(?:clinical |photo |picture |image |imaging |radiology |radiological |pathology |dermatology |ecg |ekg |x.?ray |diagnostic |self.?assessment |board.?style |christmas |snapshot |monthly |weekly |month[’\\']?s |issue[’\\']?s |case |photographic |pictorial )?(?:quiz|quizzes|challenge|challenges|puzzle|puzzles|puzzler|puzzlers|conundrum|brain.?teaser|brainteaser|teaser|riddle|self.?assessment|test yourself|spot diagnosis|case of the (?:month|week|year|quarter|issue)|picture of the (?:month|week|year|quarter|issue)|image of the (?:month|week|year|quarter|issue)|photo of the (?:month|week|year|quarter|issue)|mystery case|unknown case|clinical problem|problem case|diagnostic dilemma|mcqs?|multiple.choice questions?|cme questions?|cpd questions?|self.?test)s?\\b|^\\s*clinico-?patholog(?:ic|ical) (?:conference|conferences|exercise|exercises|session|sessions|seminar|seminars|rounds?|quiz|quizzes|puzzle|puzzles)s?\\s*(?:$|\\s*[:.,;(–—]|\\s+-|\\s+\\d|\\s+of the\\b|\\s+of\\b|\\s+from\\b|\\s+at\\b|\\s+on\\b|\\s+in\\b|\\s+no\\.?\\s*\\d|\\s+number\\b|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*(?:grand rounds?|clinical grand rounds?|clinicopathologic(?:al)? (?:conference|rounds?)|clinical conference|clinical case conference|clinical therapeutic conference|clinicotherapeutic conference|case conference|weekly clinicopathological exercises?|weekly clinicopathologic exercises?|mortality conference|morbidity and mortality conference|morbidity and mortality rounds?|tumou?r board|tumou?r conference|(?:radiology|pathology|teaching|surgical|medical|medicine|neurology|cardiology|dermatology|pediatric|paediatric|ethics|nursing|pharmacy|emergency|icu|residents?[’\\']?|chief[’\\']?s|professor[’\\']?s|attending|morning|noon) rounds)\\s*(?:$|\\s*[:.,;(–—]|\\s+-|\\s+\\d|\\s+of the\\b|\\s+from the\\b|\\s+at the\\b|\\s+no\\.?\\s*\\d|\\s+number\\b|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*(?:cen|cme|cpd|ce|mcq|self.?assessment|board review|review|test) questions\\s*(?:$|\\s*[:.,;(–—]|\\s+-|\\s+for\\b|\\s+\\d|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*case records? of the (?:massachusetts general hospital|mgh|beth israel|children[’\\']?s hospital|johns hopkins hospital|mayo clinic|royal (?:infirmary|hospital)|[a-z]+ (?:general |university |memorial |royal |children[’\\']?s |county |city |state |regional |district |teaching |medical )?(?:hospital|infirmary|clinic|medical cent(?:er|re)|institute|university|school|college|department|service|unit|society|association))\\b",
    'tribute_address': "(?i)^\\s*(?:a |the |an )?(?-i:(?:tribute|Tribute|TRIBUTE|tributes|Tributes|TRIBUTES))\\s*(?:$|\\s*[:.;(]|\\s+[-–]|\\s+to\\b|\\s+for\\b|\\s+in memory\\b|\\s+in honou?r\\b)|^\\s*in memoriam\\b|^\\s*in memory of\\b|^\\s*in remembrance\\b|^\\s*in honou?r of\\b|^\\s*(?:a |the )?notes? of (?:thanks|appreciation|gratitude|welcome|farewell|apology)\\b|^\\s*(?:an |a )?(?-i:(?:appreciation|Appreciation|APPRECIATION|appreciations|Appreciations|APPRECIATIONS))\\s*(?:$|\\s*[:;(]|\\s+[-–]|\\s+to\\b|\\s+of (?:dr\\.?|prof\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|the late|his|her)\\b)|^\\s*(?:a |an )?eulog(?:y|ies)\\s*(?:$|\\s*[:;(]|\\s+[-–]|\\s+to\\b|\\s+of\\b)|^\\s*(?:a |the )?(?:remembrances?|memorial (?:tribute|note|notice|minute)s?|necrolog(?:y|ies)|death notices?|valedictions?|homages?|salutes?|laudatio|laudations?|encomi(?:um|a)|panegyrics?|festschrift(?:en)?|gedenkschrift)\\s*(?:$|\\s*[:.;(]|\\s+[-–]|\\s+to\\b|\\s+for\\b|\\s+of\\b|\\s+on\\b|\\s+in\\b|\\s+from\\b|\\s+by\\b|\\s+\\d|\\s+dr\\b|\\s+prof|\\s+mr\\b|\\s+mrs\\b|\\s+ms\\b|\\s+sir\\b|\\s+professor\\b|\\s+the\\b|\\s+our\\b|\\s+a\\b|\\s+an\\b)|^\\s*(?:a |the )?farewells?\\s*(?:$|\\s*[:;(]|\\s+[-–]|\\s+from\\b|\\s+to (?:the editors?|our readers|readers|dr\\.?|prof\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|a friend|an? (?:colleague|friend|mentor|editor))\\b|\\s+address\\b|\\s+message\\b|\\s+remarks\\b)|^\\s*(?:thank you|thanks)\\s*(?:$|\\s*[:;(]|\\s+[-–]|\\s+to\\s+(?:[\\w’\\'&.-]+\\s+){0,4}(?:reviewers|referees|peer reviewers|editors|contributors|authors|sponsors|donors|readers|members|volunteers|colleagues|supporters|editorial board|board|guest editors|associate editors|panel|committee)\\b|\\s+reviewers\\b|\\s+referees\\b)|^\\s*(?:a |the |an )?(?-i:(?:acknowledgment|Acknowledgment|ACKNOWLEDGMENT|acknowledgments|Acknowledgments|ACKNOWLEDGMENTS|acknowledgement|Acknowledgement|ACKNOWLEDGEMENT|acknowledgements|Acknowledgements|ACKNOWLEDGEMENTS))\\s*(?:$|\\s*[;(]|\\s+[-–]|\\s+to\\b|\\s+for\\s+(?:volume|vol|\\d|the year|reviewers|referees|support|funding|assistance|help)\\b|\\s+of\\s+(?:priority|prior work|related prior work)\\b|\\s+of\\s+(?:our |the |all |principal |ad hoc |manuscript |guest |external |peer |and |\\d{4} |volume \\d+ )*(?:reviewers|referees|support|funding|sponsors|donors|contributors|assistance|help|editors|editorial board|guest editors|financial support|grants?|sources)\\b|\\s+from\\b|\\s+\\d|\\s+dr\\b|\\s+prof|\\s+mr\\b|\\s+mrs\\b|\\s+ms\\b|\\s+sir\\b|\\s+professor\\b)|^\\s*(?:congratulations|felicitations|birthday (?:greetings|tributes?)|anniversary tributes?)\\s*(?:$|\\s*[:.;(]|\\s+[-–]|\\s+to\\b|\\s+for\\b|\\s+on\\b|\\s+from\\b|\\s+\\d|\\s+dr\\b|\\s+prof|\\s+mr\\b|\\s+mrs\\b|\\s+ms\\b|\\s+sir\\b|\\s+professor\\b)|^\\s*(?:a |the )?(?:presidential|president[’\\']?s|presidents[’\\']?|chairman[’\\']?s|chair[’\\']?s|chairperson[’\\']?s|chairwoman[’\\']?s|inaugural|opening|closing|valedictory|welcome|welcoming|acceptance|banquet|commencement|retiring|retirement|introductory|after.dinner|luncheon|dinner|convocation|graduation|installation|induction|founders?[’\\']?|centennial|centenary|jubilee|dean[’\\']?s|director[’\\']?s|principal[’\\']?s|rector[’\\']?s|provost[’\\']?s|chancellor[’\\']?s|governor[’\\']?s|mayor[’\\']?s|minister[’\\']?s|secretary[’\\']?s|treasurer[’\\']?s|master[’\\']?s|warden[’\\']?s|orator[’\\']?s|lord mayor[’\\']?s|recipient[’\\']?s|awardee[’\\']?s|laureate[’\\']?s|honoree[’\\']?s|outgoing president[’\\']?s|incoming president[’\\']?s|past president[’\\']?s|new president[’\\']?s|retiring president[’\\']?s) (?:address|addresses|remarks|speech|speeches|message|messages|oration|orations|welcome|welcomes|greetings?|letters?|column|report|page|corner|forum|statement|reflections?|farewells?|valedictions?|acceptance (?:speech|remarks|address))\\s*(?:$|\\s*[:.,;(–—]|\\s+-|\\s+\\d|\\s+to\\b|\\s+of\\b|\\s+at\\b|\\s+for\\b|\\s+on\\b|\\s+by\\b|\\s+from\\b|\\s+and\\b|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*(?:list of |our |journal |the |this year[’\\']?s |\\d{4} |volume \\d+ |vol\\.? \\d+ )?(?:reviewers|referees|peer reviewers|manuscript reviewers|guest reviewers|external reviewers|ad hoc reviewers|reviewer panel|reviewer board|review panel)\\s*(?:$|\\s*[:.,;(–—]|\\s+-|\\s+\\d|\\s+for\\b|\\s+of (?:the year|volume|vol|\\d|manuscripts|papers|articles|this)\\b|\\s+volume\\b|\\s+vol\\b|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)|^\\s*(?:our |journal |the |this year[’\\']?s |\\d{4} )?(?:reviewer acknowledge?ments?|referee acknowledge?ments?|acknowledge?ments? (?:of|to) (?:our )?(?:reviewers|referees)|thanks to (?:our )?(?:reviewers|referees)|thank you(?:,)? (?:to )?(?:our )?(?:reviewers|referees)|with thanks to (?:our )?(?:reviewers|referees)|in appreciation of (?:our )?(?:reviewers|referees)|appreciation to (?:our )?(?:reviewers|referees)|reviewer (?:appreciation|thanks|recognition|list|index)|referee (?:appreciation|thanks|recognition|list|index)|recognition of (?:our )?(?:reviewers|referees)|list of (?:reviewers|referees)|index of (?:reviewers|referees)|(?:reviewers?|referees?) of the year|top (?:reviewers|referees)|outstanding (?:reviewers|referees))\\s*(?:$|\\s*[:.,;(–—]|\\s+-|\\s+\\d|\\s+for\\b|\\s+of\\b|\\s+in\\b|\\s+to\\b|\\s+and\\b|\\s+volume\\b|\\s+vol\\b|\\s+the\\b|\\s+this\\b|\\s+(?:january|february|march|april|may|june|july|august|september|october|november|december|spring|summer|autumn|fall|winter)\\b)",
    'interview': '(?i)^\\s*(?:a |an |the )?(?:conversation|interview|q ?& ?a|q and a|five questions|ten questions|twenty questions) with\\b|^\\s*in conversation\\s*(?:$|\\s*[:.,;(–—]|\\s+-|\\s+with\\b)|^\\s*(?:an |the )?interview\\s*(?:$|\\s*[:;(–—]|\\s+-|\\s+by\\b)|^\\s*interviews\\s*$',
    'retraction_notice': '(?i)^\\s*\\[?(?:(?:retraction|retracted|withdrawn)\\s*(?:$|\\s*[:.;(\\]]|\\s+[-–])|(?:retracted article|withdrawn article|expression of concern|editorial expression of concern|notice of (?:retraction|withdrawal|duplicate publication|redundant publication|concern|correction|erratum|corrigendum)|statement of retraction|retraction notice|retraction note|retraction statement|notice of concern|temporary removal|temporarily removed|removal notice|article withdrawn|paper withdrawn|manuscript withdrawn|duplicate publication|redundant publication|retraction and republication|partial retraction|editor[’\\\']?s note of concern|editorial note of concern)\\s*(?:$|\\s*[:.,;(\\]–—]|\\s+-)|(?:retraction|retracted|retracted article|withdrawn|withdrawn article|expression of concern|notice of (?:retraction|withdrawal|concern)|retraction notice|temporary removal|removal notice|partial retraction)\\s+(?:notice\\b|to\\b|for\\b|note\\b|statement\\b|article\\b|paper\\b|manuscript\\b|of\\s*(?::|[:"“‘«\\\']|the (?:article|articles|paper|papers|publication|manuscript|report|letter|study|abstract|review|editorial|case report|following|above|preceding)\\b|\\d|(?:volume|vol)\\b|[^:;]{0,150}(?:,\\s*(?:vol|volume)\\b|\\bvol\\.?\\s*\\d|\\bpp\\.\\s*\\d|\\bcytologia\\b))))|^\\s*withdrawal\\s*(?:$|\\s*[:]|\\s+[-–]|\\s+notice\\b|\\s+of (?:the )?(?:article|paper|manuscript|publication|abstract)\\b)|^\\s*(?:publisher|author|authors|editorial|editor[’\\\']?s|editors[’\\\']?|journal|publisher[’\\\']?s|editorial office|production|typesetting|printing)\\s*(?:corrections?|erratum|errata|corrigendum|corrigenda|apolog(?:y|ies)|clarifications?|amendments?)\\s*(?:$|\\s*[:"“‘«\\\'(–—]|\\s+-|\\s+to\\b|\\s+for\\b|\\s+of\\b|\\s+on\\b|\\s+regarding\\b|\\s+concerning\\b)|^\\s*(?:corrections?|erratum|errata|corrigendum|corrigenda|clarifications?|amendments?|addend(?:um|a))\\s+(?:to|for|in|of|on|regarding|concerning|re)\\s+(?:the )?(?:article|articles|paper|papers|report|reports|letter|letters|abstract|abstracts|title|titles|author|authors|authorship|affiliation|affiliations|reference|references|citation|citations|acknowledg[a-z]*|funding|supplement|supplementary|appendix|legend|legends|caption|captions)\\b|^\\s*(?:corrections?|erratum|errata|corrigendum|corrigenda|clarifications?|amendments?|addend(?:um|a))\\s+(?:to|for|in|of|on|regarding|concerning|re)\\s+(?:the )?(?:(?:figure|figures|fig|table|tables|equation|equations|eq|page|pages|volume|vol|issue|number|no)\\.?\\s*\\(?\\s*(?:\\d|[ivxl]+\\b)|(?:figure|figures|fig|table|tables|equation|equations|eq)s?\\s*[:.])|^\\s*(?:corrections?|erratum|errata|corrigendum|corrigenda|clarifications?|amendments?|addend(?:um|a))\\s+(?:to|for|in|of|on|regarding|concerning|re)\\s+(?:the )?(?:(?:lancet|bmj|jama|nejm|plos|journal|proceedings|proc|annals|archives)\\b|j\\.|(?:nature|science|cell|ann|arch|am|br|eur|int|clin)\\b\\s*(?:\\d|[(:,;.]|(?-i:[A-Z])))|^\\s*(?:corrections?|erratum|errata|corrigendum|corrigenda|clarifications?|amendments?|addend(?:um|a))\\s+(?:to|for|in|of|on|regarding|concerning|re)\\s+(?:\\d|"|“|‘|«|\\\')|^\\s*(?:corrections?|erratum|errata|corrigendum|corrigenda)\\s+(?:published|appearing|printed|issued|(?:for|to|in) (?:volume|vol\\.?)\\s*(?:\\d|[ivxl]+\\b)|volume\\s*\\d|vol\\.?\\s*\\d|\\d)',
    'book_review_of': '(?i)^\\s*(?:a |an )?(?:book |brief |critical |extended |short )?review of\\s*:\\s*\\S|^\\s*(?:a |an )?(?:book |brief |critical |extended |short )?review of\\s*(?:["“](?-i:[A-Z])[^"“”]{3,200}["”]|[‘\\\'](?-i:[A-Z])[^‘’\\\']{3,200}[’\\\']|«(?-i:[A-Z])[^«»]{3,200}»)\\s*(?:$|[,.;(]|\\s+(?:by|edited|eds?|and|\\d{4})\\b)|^\\s*(?:a |an )?(?:book |brief |critical |extended |short )?review of\\s+(?-i:[A-Z])[^"“”]{0,200}?(?:[^\\s"“”]*[^d\\s"“”]|[^\\s"“”]*[^e\\s"“”]d|edited|translated|compiled|introduced|selected|revised|collected|annotated|illustrated|abridged|authored|co-authored|ed\\.|eds\\.|\\(eds?\\.?\\)|,|\\))\\s+by\\s+(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|rev\\.?)\\s+)?(?-i:(?:[A-Z][a-z’\'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O\'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+(?:[A-Z]\\.?|[A-Z][a-z’\'\\-]+|de|van|von|der|den|la|le|du|da|di|del|della|bin|ibn|y|e|Jr\\.?|Sr\\.?)){1,2})\\s*(?:$|[,.;]|\\s+(?:and|&|with)\\s+(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|rev\\.?)\\s+)?(?-i:(?:[A-Z][a-z’\'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O\'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+(?:[A-Z]\\.?|[A-Z][a-z’\'\\-]+|de|van|von|der|den|la|le|du|da|di|del|della|bin|ibn|y|e|Jr\\.?|Sr\\.?)){0,2})\\s*(?:$|[,.;(]|\\s+\\d{4}\\b|\\s+(?:and|&|with)\\b)|\\s*\\(\\s*(?:\\d{4}|eds?)|\\s+\\d{4}\\b|\\s+\\(?eds?\\b|\\s+(?:london|new york|oxford|cambridge|chicago|berlin|paris|boston|philadelphia|amsterdam|dordrecht|heidelberg|routledge|springer|wiley|elsevier|palgrave|macmillan|blackwell|sage|penguin|mit press|the mit press)\\b|\\s+(?-i:[A-Z][a-z]+ (?:University )?Press)\\b)|^\\s*(?:book )?reviews?\\s*:.{0,250}(?:\\bisbn\\b|\\bpp\\.|\\b\\d+\\s?pp\\b|£\\s?\\d|\\$\\s?\\d|€\\s?\\d|university press|routledge|springer|wiley|elsevier|palgrave|macmillan|blackwell|\\bsage\\b|penguin|oxford:|london:|new york:|cambridge:|chicago:|berlin:|paris:|boston:|philadelphia:|amsterdam:|hardcover|paperback|hardback|\\bhbk\\b|\\bpbk\\b|\\(eds?\\.?\\)|\\beds?\\.\\s|edited by|translated by|reviewed by)|^\\s*(?:a |an )?(?:book )?review of\\s.{0,250}(?:\\bisbn\\b|\\bpp\\.|\\b\\d+\\s?pp\\b|£\\s?\\d|\\$\\s?\\d|€\\s?\\d|university press|routledge|springer|wiley|elsevier|palgrave|macmillan|blackwell|\\bsage\\b|penguin|oxford:|london:|new york:|cambridge:|chicago:|berlin:|paris:|boston:|philadelphia:|amsterdam:|hardcover|paperback|hardback|\\bhbk\\b|\\bpbk\\b|\\(eds?\\.?\\)|\\beds?\\.\\s|edited by|translated by|reviewed by)|^\\s*reviews?\\s*:\\s*(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|rev\\.?)\\s+)?(?-i:(?:(?:[A-Z]\\.\\s*)+(?:[A-Z][a-z’\'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O\'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)|(?:[A-Z][a-z’\'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O\'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+[A-Z]\\.)+\\s+(?:[A-Z][a-z’\'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O\'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)))\\s*,\\s*(?-i:[A-Z])',
    'named_reply': "(?i)^\\s*(?:a |an |brief |short |further |invited )?(?:commentary|commentaries|comments?|responses?|repl(?:y|ies)|rejoinders?|critiques?)\\s+by\\s+(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|rev\\.?)\\s+)?(?-i:(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+(?:[A-Z]\\.?|[A-Z][a-z’'\\-]+|de|van|von|der|den|la|le|du|da|di|del|della|bin|ibn|y|e|Jr\\.?|Sr\\.?)){0,5})(?:\\s*$|\\s*[,.:;/(]|\\s+(?:and|&|et\\s+al|to|on|regarding|re)\\b|[’\\']s\\b)|^\\s*(?:a |an |the |brief |short |further |our |authors?[’\\']?s? )?(?:responses?|repl(?:y|ies)|comments?|commentary|rejoinders?)\\s+(?:to|on)\\s+(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|rev\\.?)\\s+)?(?-i:(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+(?:[A-Z]\\.?|[A-Z][a-z’'\\-]+|de|van|von|der|den|la|le|du|da|di|del|della|bin|ibn|y|e|Jr\\.?|Sr\\.?)){0,3})(?:\\s+et\\s+al\\b|\\s*\\(\\d{4}|\\s+\\d{4}\\b)|^\\s*(?:a |an |the |brief |short |further |our |authors?[’\\']?s? )?(?:responses?|repl(?:y|ies)|comments?|commentary|rejoinders?)\\s+(?:to|on)\\s+(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|rev\\.?)\\s+)?(?-i:(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)|(?:(?:[A-Z]\\.\\s*)+(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)|(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+[A-Z]\\.)+\\s+(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)))\\s*,|^\\s*(?:a |an |the |brief |short |further |our |authors?[’\\']?s? )?(?:responses?|repl(?:y|ies)|comments?|commentary|rejoinders?)\\s+(?:to|on)\\s+(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|rev\\.?)\\s+)?(?-i:(?:(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)|(?:(?:[A-Z]\\.\\s*)+(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)|(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+[A-Z]\\.)+\\s+(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+))))(?:\\s*,\\s*(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|rev\\.?)\\s+)?(?-i:(?:(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)|(?:(?:[A-Z]\\.\\s*)+(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)|(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+[A-Z]\\.)+\\s+(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)))))*,?\\s+(?:and|&)\\s+(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|rev\\.?)\\s+)?(?-i:(?:(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)|(?:(?:[A-Z]\\.\\s*)+(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)|(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+[A-Z]\\.)+\\s+(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+))))(?:\\s*$|\\s*[,:;(’\\']|\\s+et\\s+al\\b|\\s+\\d{4}\\b)|^\\s*(?:a |an |the |brief |short |further |our |authors?[’\\']?s? )?(?:responses?|repl(?:y|ies)|comments?|commentary|rejoinders?)\\s+(?:to|on)\\s+(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|rev\\.?)\\s+)?(?-i:(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+(?:[A-Z]\\.?|[A-Z][a-z’'\\-]+|de|van|von|der|den|la|le|du|da|di|del|della|bin|ibn|y|e|Jr\\.?|Sr\\.?)){0,3})[’\\']s?(?:\\s*\\(\\d{4}\\))?\\s+(?:comments?|commentary|critique|letter|reply|response|rejoinder|review|paper|article|remarks?|notes?|discussion|critical|analysis|proposal|argument|essay|objections?|claims?|reading|interpretation|viewpoint|editorial|critics|readers|reviewers|discussants)\\b|^\\s*(?:a |an |brief |short |further |our |authors?[’\\']?s? )?(?:repl(?:y|ies)|rejoinders?)\\s+to\\s+(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|rev\\.?)\\s+)?(?-i:(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+(?:[A-Z]\\.?|[A-Z][a-z’'\\-]+|de|van|von|der|den|la|le|du|da|di|del|della|bin|ibn|y|e|Jr\\.?|Sr\\.?)){0,3})\\s*$|^\\s*(?:a |an |brief |short |further |our |authors?[’\\']?s? )?responses?\\s+to\\s+(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|rev\\.?)\\s+)?(?-i:(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+))\\s*$|^\\s*(?:a |an |brief |short |further |our |authors?[’\\']?s? )?responses?\\s+to\\s+(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame)\\s+(?-i:(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+(?:[A-Z]\\.?|[A-Z][a-z’'\\-]+|de|van|von|der|den|la|le|du|da|di|del|della|bin|ibn|y|e|Jr\\.?|Sr\\.?)){0,3})|(?-i:(?:(?:[A-Z]\\.\\s*)+(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)|(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+[A-Z]\\.)+\\s+(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+))))\\s*$|^\\s*(?:a |an |brief |short |further |our |authors?[’\\']?s? )?responses?\\s+to\\s+(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|rev\\.?)\\s+)?(?-i:(?:[A-Z][a-z’'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+(?:[A-Z]\\.?|[A-Z][a-z’'\\-]+|de|van|von|der|den|la|le|du|da|di|del|della|bin|ibn|y|e|Jr\\.?|Sr\\.?)){0,2})\\s+(?:review|letter|paper|commentary|critique|comments?|rejoinder|article|essay)\\s*$",
    # ── v3.2(2026-09-09, R7-e 09-09 추가; 산출 m70_junk_v32_patterns.py, 블라인드 감사 193건 m70_v32_audit_result.parquet):
    #    issue_note(호별 안내 7 하위 형태, 오탐 0/54)·reviewer_ack(심사자 사사 6 하위 형태, 0/49)·strip_of_month(교육용 기록 띠, 0/13) 편입.
    #    불편입 = editors_picks('Editor's Choice/Highlight: <제목>' 연구 23/45)·lesson_of_week(연구 0/32 이나 경계 29/32 = 임상 소견을 보고하는 증례 형식).
    'issue_note': '(?i)^\\s*spotlight on the (?:january|february|march|april|may|june|july|august|september|october|november|december) \\d{1,2},? (issue|\\d{4})|^\\s*(in|about) this (issue|number)\\s*(\\.{3}|…)?\\s*$|^\\s*in this number\\s*:|^\\s*about this issue\\s*(:|/|and acknowledg)|^\\s*(perspectives?|reflections?|comments?) on this (issue|month.?s)|^\\s*highlights? of (the|this) (edition|issue|number)\\b|^\\s*this week.?s no\\.? ?1\\s*$',
    'reviewer_ack': "(?i)^\\s*(a |an )?(acknowledg(e)?ments?|thanks|thank you|appreciation|gratitude|tribute|recognition)\\s+(of|to|for)\\s+(our |the |all |\\d{4} |ad hoc |manuscript |peer |guest |external |journal |volunteer |outstanding )*(reviewers|referees|peer reviewers|editorial board|editorial board members|editors and reviewers|reviewers and editors)\\b|^\\s*(?:[a-z&.\\'’ ]{2,40} )?(reviewers?|referees?|reviewer and editorial board|reviewers and editors)\\s+(thank you|thanks|acknowledg(e)?ments?|appreciation)\\b|^\\s*(list of |our |journal |manuscript |peer |ad hoc |guest )?(reviewers|referees)\\s+(for|of|in)\\s+(\\d{4}|volume|the year|this year|the journal|the past year)\\b|^\\s*(\\d{4} )?(?:[a-z&.\\'’ ]{2,40} )?(reviewers?|referees?)\\s+of the year\\b|^\\s*(?:[a-z0-9&.\\'’:()-]+\\s+){0,5}(?:\\d{4}\\s+)?(?:acknowledg(?:e)?ments?\\s+(?:of|to)\\s+(?:the |our |all |\\d{4} |peer |manuscript |ad hoc |guest |external )*(?:reviewers|referees|editorial board)|(?:peer )?reviewers?(?:\\s+and editorial board(?: members)?)?\\s+thank you|reviewer of the year|thank you to (?:our |the |all )?(?:\\d{4} )?(?:peer )?(?:reviewers|referees)|(?:peer )?reviewer acknowledg(?:e)?ments?|reviewers? for \\d{4}|our \\d{4} (?:peer )?reviewers)\\b|^\\s*[a-z&.\\'’ ]{2,40}\\s+(reviewers|referees)\\s+(\\d{4}|for \\d{4})\\s*$",
    'strip_of_month': '(?i)^\\s*strip of the month\\b',
    #    v3.2 추가(09-09 밤, 31986 코어에서 적발): 학술지 이름이 앞에 붙은 "<Journal> Editors' Picks"(맨 앞형은 editor_note 가 잡음) — 전수 98편(31986 에 95), 블라인드 감사 48건 오탐 0.
    'editors_picks': "(?i)^\\s*(?:[a-z&.'’:()\\-]+\\s+){1,7}editors?['’]?\\s*picks?\\s*(?:$|[:.,;(–—\\-]|\\s+(?:most|top|from|for|in|of|and|the)\\b|\\s+\\d)",
    # ── v3.2 2차(09-09 밤 후속 조사, 사용자 질문 "후속 후보도 조사 중이신거죠?"; m72 접두형 694건·m73 종결형 1,013건·m74 서평 접두형 45건 블라인드 감사, A.88):
    #    종결형(제목이 장르 구절로 끝남: 뒤에 콜론·연도·권호만 허용)과 학술지 이름 접두형 가운데 오탐률 10% 이하만 편입. 정규식은 감사한 산출 코드(m73 PHRASES·TAIL, m72 prefixed)의 것을 그대로 옮겼다.
    #    불편입 = index·cover·corrections·correspondence 접두형(연구 제목 안의 일반 명사), news·highlights·calendar·announcements·letters·reviewers(심판)·proceedings 접두형, in memoriam 접두형(비유적 obituary 20%), 기타 A.88 표.
    'abstracts_terminal': '(?i)^\\s*(?:(?:meeting |conference |congress |annual meeting |scientific |poster |selected )?abstracts)\\s*(?:$|[:.,;(–—\\-]\\s*(?:$|\\d|vol|volume|no\\.?|issue|part|[a-z]{0,40}$)|\\s+(?:\\d{4}|\\d{1,3}|vol\\.?|volume|no\\.?|issue|part|for|to volume|to vol\\.?)\\b)|^\\s*(?:proceedings)\\s*(?:$|[:.,;(–—\\-]\\s*(?:$|\\d|vol|volume|no\\.?|issue|part|[a-z]{0,40}$)|\\s+(?:\\d{4}|\\d{1,3}|vol\\.?|volume|no\\.?|issue|part|for|to volume|to vol\\.?)\\b)',
    'front_matter': "(?i)^\\s*(?:(?:international |the )?editorial (?:board|advisory board|committee))\\s*(?:$|[:.,;(–—\\-]\\s*(?:$|\\d|vol|volume|no\\.?|issue|part|[a-z]{0,40}$)|\\s+(?:\\d{4}|\\d{1,3}|vol\\.?|volume|no\\.?|issue|part|for|to volume|to vol\\.?)\\b)|^\\s*(?-i:[A-Z])[a-z&.'’:()\\-]*(?:\\s+[a-z&.'’:()\\-]+){0,6}\\s+(?:(?:international |the )?editorial (?:board|advisory board|committee))\\s*(?:$|[:.,;(–—\\-]\\s*(?:$|\\d|vol|volume|no\\.?|issue|part|[a-z]{0,40}$)|\\s+(?:\\d{4}|\\d{1,3}|vol\\.?|volume|no\\.?|issue|part|for|to volume|to vol\\.?)\\b)|^\\s*(?-i:[A-Z])[a-z&.'’:()\\-]*(?:\\s+[a-z&.'’:()\\-]+){0,6}\\s+(?:masthead)\\s*(?:$|[:.,;(–—\\-]\\s*(?:$|\\d|vol|volume|no\\.?|issue|part|[a-z]{0,40}$)|\\s+(?:\\d{4}|\\d{1,3}|vol\\.?|volume|no\\.?|issue|part|for|to volume|to vol\\.?)\\b)|^\\s*(?:forthcoming(?: papers| articles| events| meetings)?)\\s*(?:$|[:.,;(–—\\-]\\s*(?:$|\\d|vol|volume|no\\.?|issue|part|[a-z]{0,40}$)|\\s+(?:\\d{4}|\\d{1,3}|vol\\.?|volume|no\\.?|issue|part|for|to volume|to vol\\.?)\\b)|^\\s*(?-i:[A-Z])[a-z&.'’:()\\-]*(?:\\s+[a-z&.'’:()\\-]+){0,6}\\s+(?:call for papers)\\s*(?:$|[:.,;(–—\\-]\\s*(?:$|\\d|vol|volume|no\\.?|issue|part|[a-z]{0,40}$)|\\s+(?:\\d{4}|\\d{1,3}|vol\\.?|volume|no\\.?|issue|part|for|to volume|to vol\\.?)\\b)|^\\s*(?-i:[A-Z])[a-z&.'’:()\\-]*(?:\\s+[a-z&.'’:()\\-]+){0,6}\\s+(?:(?:information|instructions|guidelines?|notes?) (?:for|to) (?:authors|contributors)|author guidelines)\\s*(?:$|[:.,;(–—\\-]\\s*(?:$|\\d|vol|volume|no\\.?|issue|part|[a-z]{0,40}$)|\\s+(?:\\d{4}|\\d{1,3}|vol\\.?|volume|no\\.?|issue|part|for|to volume|to vol\\.?)\\b)",
    'contents_terminal': '(?i)^\\s*(?:(?:table of )?contents)\\s*(?:$|[:.,;(–—\\-]\\s*(?:$|\\d|vol|volume|no\\.?|issue|part|[a-z]{0,40}$)|\\s+(?:\\d{4}|\\d{1,3}|vol\\.?|volume|no\\.?|issue|part|for|to volume|to vol\\.?)\\b)',
    'books_received_prefixed': "(?i)^\\s*(?-i:[A-Z])[a-z&.'’:()\\-]*(?:\\s+[a-z&.'’:()\\-]+){0,6}\\s+(?:(?:books|publications|new books) received)\\s*(?:$|[:.,;(–—\\-]\\s*(?:$|\\d|vol|volume|no\\.?|issue|part|[a-z]{0,40}$)|\\s+(?:\\d{4}|\\d{1,3}|vol\\.?|volume|no\\.?|issue|part|for|to volume|to vol\\.?)\\b)",
    'correspondence_terminal': '(?i)^\\s*(?:correspondence)\\s*(?:$|[:.,;(–—\\-]\\s*(?:$|\\d|vol|volume|no\\.?|issue|part|[a-z]{0,40}$)|\\s+(?:\\d{4}|\\d{1,3}|vol\\.?|volume|no\\.?|issue|part|for|to volume|to vol\\.?)\\b)',
    'editorial_terminal': "(?i)^\\s*(?-i:[A-Z])[a-z&.'’:()\\-]*(?:\\s+[a-z&.'’:()\\-]+){0,6}\\s+(?:in this issue|editorial(?: comment)?|editor[’']?s? (?:note|page|corner|column)|from the editors?|editors?[’']? (?:choice|picks?|highlights?|spotlight))\\s*(?:$|[:.,;(–—\\-]\\s*(?:$|\\d|vol|volume|no\\.?|issue|part|[a-z]{0,40}$)|\\s+(?:\\d{4}|\\d{1,3}|vol\\.?|volume|no\\.?|issue|part|for|to volume|to vol\\.?)\\b)",
    'book_review_prefixed': '(?i)^\\s*(?-i:[A-Z])[a-z&.\'’:()\\-]*(?:\\s+[a-z&.\'’:()\\-]+){0,6}\\s+(?:a |an )?(?:book |brief |critical |extended |short )?review of\\s*:\\s*\\S|^\\s*(?-i:[A-Z])[a-z&.\'’:()\\-]*(?:\\s+[a-z&.\'’:()\\-]+){0,6}\\s+(?:a |an )?(?:book |brief |critical |extended |short )?review of\\s*(?:["“](?-i:[A-Z])[^"“”]{3,200}["”]|[‘\\\'](?-i:[A-Z])[^‘’\\\']{3,200}[’\\\']|«(?-i:[A-Z])[^«»]{3,200}»)\\s*(?:$|[,.;(]|\\s+(?:by|edited|eds?|and|\\d{4})\\b)|^\\s*(?-i:[A-Z])[a-z&.\'’:()\\-]*(?:\\s+[a-z&.\'’:()\\-]+){0,6}\\s+(?:a |an )?(?:book |brief |critical |extended |short )?review of\\s+(?-i:[A-Z])[^"“”]{0,200}?(?:[^\\s"“”]*[^d\\s"“”]|[^\\s"“”]*[^e\\s"“”]d|edited|translated|compiled|introduced|selected|revised|collected|annotated|illustrated|abridged|authored|co-authored|ed\\.|eds\\.|\\(eds?\\.?\\)|,|\\))\\s+by\\s+(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|rev\\.?)\\s+)?(?-i:(?:[A-Z][a-z’\'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O\'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+(?:[A-Z]\\.?|[A-Z][a-z’\'\\-]+|de|van|von|der|den|la|le|du|da|di|del|della|bin|ibn|y|e|Jr\\.?|Sr\\.?)){1,2})\\s*(?:$|[,.;]|\\s+(?:and|&|with)\\s+(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|rev\\.?)\\s+)?(?-i:(?:[A-Z][a-z’\'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O\'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+(?:[A-Z]\\.?|[A-Z][a-z’\'\\-]+|de|van|von|der|den|la|le|du|da|di|del|della|bin|ibn|y|e|Jr\\.?|Sr\\.?)){0,2})\\s*(?:$|[,.;(]|\\s+\\d{4}\\b|\\s+(?:and|&|with)\\b)|\\s*\\(\\s*(?:\\d{4}|eds?)|\\s+\\d{4}\\b|\\s+\\(?eds?\\b|\\s+(?:london|new york|oxford|cambridge|chicago|berlin|paris|boston|philadelphia|amsterdam|dordrecht|heidelberg|routledge|springer|wiley|elsevier|palgrave|macmillan|blackwell|sage|penguin|mit press|the mit press)\\b|\\s+(?-i:[A-Z][a-z]+ (?:University )?Press)\\b)|^\\s*(?-i:[A-Z])[a-z&.\'’:()\\-]*(?:\\s+[a-z&.\'’:()\\-]+){0,6}\\s+(?:book )?reviews?\\s*:.{0,250}(?:\\bisbn\\b|\\bpp\\.|\\b\\d+\\s?pp\\b|£\\s?\\d|\\$\\s?\\d|€\\s?\\d|university press|routledge|springer|wiley|elsevier|palgrave|macmillan|blackwell|\\bsage\\b|penguin|oxford:|london:|new york:|cambridge:|chicago:|berlin:|paris:|boston:|philadelphia:|amsterdam:|hardcover|paperback|hardback|\\bhbk\\b|\\bpbk\\b|\\(eds?\\.?\\)|\\beds?\\.\\s|edited by|translated by|reviewed by)|^\\s*(?-i:[A-Z])[a-z&.\'’:()\\-]*(?:\\s+[a-z&.\'’:()\\-]+){0,6}\\s+(?:a |an )?(?:book )?review of\\s.{0,250}(?:\\bisbn\\b|\\bpp\\.|\\b\\d+\\s?pp\\b|£\\s?\\d|\\$\\s?\\d|€\\s?\\d|university press|routledge|springer|wiley|elsevier|palgrave|macmillan|blackwell|\\bsage\\b|penguin|oxford:|london:|new york:|cambridge:|chicago:|berlin:|paris:|boston:|philadelphia:|amsterdam:|hardcover|paperback|hardback|\\bhbk\\b|\\bpbk\\b|\\(eds?\\.?\\)|\\beds?\\.\\s|edited by|translated by|reviewed by)|^\\s*(?-i:[A-Z])[a-z&.\'’:()\\-]*(?:\\s+[a-z&.\'’:()\\-]+){0,6}\\s+reviews?\\s*:\\s*(?:(?:drs?\\.?|profs?\\.?|professor|mr\\.?|mrs\\.?|ms\\.?|sir|dame|rev\\.?)\\s+)?(?-i:(?:(?:[A-Z]\\.\\s*)+(?:[A-Z][a-z’\'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O\'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)|(?:[A-Z][a-z’\'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O\'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)(?:\\s+[A-Z]\\.)+\\s+(?:[A-Z][a-z’\'\\-]+|[A-Z]\\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O\'[A-Z][a-z]+|D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)))\\s*,\\s*(?-i:[A-Z])',
    'reviewer_ack_prefixed': "(?i)^\\s*(?-i:[A-Z])[a-z&.'’:()\\-]*(?:\\s+[a-z&.'’:()\\-]+){0,6}\\s+(a |an )?(acknowledg(e)?ments?|thanks|thank you|appreciation|gratitude|tribute|recognition)\\s+(of|to|for)\\s+(our |the |all |\\d{4} |ad hoc |manuscript |peer |guest |external |journal |volunteer |outstanding )*(reviewers|referees|peer reviewers|editorial board|editorial board members|editors and reviewers|reviewers and editors)\\b|^\\s*(?-i:[A-Z])[a-z&.'’:()\\-]*(?:\\s+[a-z&.'’:()\\-]+){0,6}\\s+(?:[a-z&.\\'’ ]{2,40} )?(reviewers?|referees?|reviewer and editorial board|reviewers and editors)\\s+(thank you|thanks|acknowledg(e)?ments?|appreciation)\\b|^\\s*(?-i:[A-Z])[a-z&.'’:()\\-]*(?:\\s+[a-z&.'’:()\\-]+){0,6}\\s+(list of |our |journal |manuscript |peer |ad hoc |guest )?(reviewers|referees)\\s+(for|of|in)\\s+(\\d{4}|volume|the year|this year|the journal|the past year)\\b|^\\s*(?-i:[A-Z])[a-z&.'’:()\\-]*(?:\\s+[a-z&.'’:()\\-]+){0,6}\\s+(\\d{4} )?(?:[a-z&.\\'’ ]{2,40} )?(reviewers?|referees?)\\s+of the year\\b|^\\s*(?-i:[A-Z])[a-z&.'’:()\\-]*(?:\\s+[a-z&.'’:()\\-]+){0,6}\\s+(?:[a-z0-9&.\\'’:()-]+\\s+){0,5}(?:\\d{4}\\s+)?(?:acknowledg(?:e)?ments?\\s+(?:of|to)\\s+(?:the |our |all |\\d{4} |peer |manuscript |ad hoc |guest |external )*(?:reviewers|referees|editorial board)|(?:peer )?reviewers?(?:\\s+and editorial board(?: members)?)?\\s+thank you|reviewer of the year|thank you to (?:our |the |all )?(?:\\d{4} )?(?:peer )?(?:reviewers|referees)|(?:peer )?reviewer acknowledg(?:e)?ments?|reviewers? for \\d{4}|our \\d{4} (?:peer )?reviewers)\\b|^\\s*(?-i:[A-Z])[a-z&.'’:()\\-]*(?:\\s+[a-z&.'’:()\\-]+){0,6}\\s+[a-z&.\\'’ ]{2,40}\\s+(reviewers|referees)\\s+(\\d{4}|for \\d{4})\\s*$",   # v3.2 2차: reviewer_ack 의 학술지 이름 접두형(전수 29편 전건 감사: 연구 1·경계 1)
}
# v3.1 적중 뒤 제외할 하위 형태(검증 m55: 'In Brief: <주제>' ≈80%·'News & Notes: <제목>' 36~43% 가 연구 논문). RE2 에 전방탐색이 없어 별도 제외식으로 둔다.
JUNK_V3_EXCLUDE = {
    'news': r'(?i)^\s*(?:in brief|news\s*(?:&|and)\s*notes)\s*:',
    'book_review_prefixed': r'(?i)^\s*(?:a|an|the)\s',   # v3.2 2차: 관사 한 단어 접두('A Brief Review of <주제>')는 연구 논문(m72 감사 오탐 전부) → 제외
}

# 정크 유형 표준 명칭 v3(#78 의 8종 + 장르 정크 확장, #122). 정크 라벨은 이 명칭 어휘만으로 짓는다(J1 게이트).
# 팩 헤더 "junk record TYPES" 줄과 g_gate.TYPE_VOCAB 이 이 표에서 파생된다(재빌드 때 s0_junk_title_types v3 와 함께 발효).
JUNK_TYPE_NAMES_V3 = {
    'correction': 'correction notices', 'reply': 'replies and comments', 'editorial': 'editorial material',
    'book_review': 'book reviews', 'index_toc': 'index and table of contents pages', 'announcement': 'announcements',
    'untitled': 'untitled records', 'other': 'other non-research records',
    'commentary': 'commentaries and discussions', 'letter': 'letters and correspondence', 'editor_note': "editor's notes",
    'books_received': 'books received lists', 'bibliography': 'bibliographies', 'news': 'news and notices',
    'abstracts_meeting': 'meeting abstracts and reports', 'case_record': 'teaching case records',
    'tribute_address': 'tributes and addresses', 'interview': 'interviews and conversations',
    'retraction_notice': 'retraction and correction notices', 'book_review_of': 'book reviews', 'named_reply': 'replies and comments',    'issue_note': 'issue announcements', 'reviewer_ack': 'reviewer acknowledgments', 'strip_of_month': 'teaching case records',
    'editors_picks': "editors' picks notices",  # v3.2
    'abstracts_terminal': 'meeting abstracts and reports',
    'front_matter': 'journal front matter',
    'contents_terminal': 'index and table of contents pages',
    'books_received_prefixed': 'books received lists',
    'correspondence_terminal': 'letters and correspondence',
    'editorial_terminal': 'editorial material',
    'book_review_prefixed': 'book reviews', 'reviewer_ack_prefixed': 'reviewer acknowledgments',
}

BRIDGE = {'sibling_external_in_bridge', 'far_external_in_impact', 'topic_bridge_sentinel'}
# yjk 초록 몫 우선 버킷(§4 A몫: term_evidence·internal·lifecycle·review 우선, coverage_fill 후순위)
BUCKET_PRIORITY = {
    'term_evidence': 0, 'internal_in_foundation': 0, 'internal_out_integrator': 0,
    'lifecycle_milestone': 0, 'review_synthesis': 0, 'recent_frontier': 1,
    'coverage_fill': 2,
}

FUNC = re.compile(
    r'(?i)\b(used (for|in|to)|is used in|applied to|applications? (in|of|for|like|such as)'
    r'|enables?|enabling|for the (design|development|treatment|production|detection|removal'
    r'|monitoring|management)|industrial|commercial|clinical(ly)? (use|practice|application)'
    r'|device|therapy|therapeutic|diagnos|manufactur|deployment|practical (use|application)'
    r'|promising (for|candidate)|potential (application|use))\b')

STOP = set(('a an the of in on for and or to with by from at as into via under over between '
            'among during after before through vs versus is are be its their using based study '
            'studies research analysis approach approaches method methods application '
            'applications effect effects role new novel toward towards').split())


def norm(s):
    """소문자화·구두점 제거(하이픈 유지)·공백 정규화 (§8 정규화)."""
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9 \-]+', ' ', str(s or '').lower())).strip()


IRREGULAR_PLURAL = {
    'vortices': 'vortex', 'matrices': 'matrix', 'indices': 'index', 'analyses': 'analysis',
    'hypotheses': 'hypothesis', 'syntheses': 'synthesis', 'criteria': 'criterion',
    'phenomena': 'phenomenon', 'bacteria': 'bacterium', 'algae': 'alga', 'fungi': 'fungus',
    'nuclei': 'nucleus', 'spectra': 'spectrum', 'media': 'medium', 'radii': 'radius',
    'foci': 'focus', 'larvae': 'larva', 'genera': 'genus', 'stimuli': 'stimulus',
}


def singular(w):
    """복수 통합용 소박한 단수화(§8: 복수 통합). 화학식·숫자 토큰은 건드리지 않고,
    과학 용어의 흔한 불규칙 복수는 사전으로 처리한다('단순 굴절형 허용'의 구현)."""
    if w in IRREGULAR_PLURAL:
        return IRREGULAR_PLURAL[w]
    if any(c.isdigit() for c in w):
        return w
    # -ies → -y (commentaries→commentary, studies→study; 2026-08-29 파일럿 실측 결함 수정:
    # 종전 -s 절단이 'commentarie'·'studie' 같은 비어를 만들어 팩 대조를 실패시켰다)
    if len(w) > 4 and w.endswith('ies'):
        return w[:-3] + 'y'
    # -sses/-shes/-ches/-xes/-zes → -es 절단(classes→class, batches→batch)
    if len(w) > 4 and w.endswith('es') and w[:-2].endswith(('ss', 'sh', 'ch', 'x', 'z')):
        return w[:-2]
    if len(w) > 3 and w.endswith('s') and not w.endswith('ss'):
        return w[:-1]
    return w


def term_key(term):
    return ' '.join(singular(w) for w in term.split())


def det_key(*parts):
    """결정적 정렬 키: md5(seed:parts). 모든 '무작위' 표본은 이 키 순서로 뽑는다."""
    return hashlib.md5((f'{SEED}:' + ':'.join(str(p) for p in parts)).encode()).hexdigest()


def junk_doc(title):
    """정크 문서 판정(결정원장 #25): 열거형 정규식만 쓴다. 정정·서평·목차·판권지류는
    초록이 있어도 출판 잡물이므로 초록 유무와 무관하게 정크로 본다."""
    return bool(JUNK.search(str(title or '')))


def uninformative_title(title):
    """제목 단독 입력의 무가치 판정(정크 아님). LaTeX 제거 후 8자 미만이거나 내용어가
    3개 미만인 제목이 대상이다. 결정원장 #25: 유효 초록이 있는 문서는 이 판정으로
    제외하지 않으며, 초록 없는 문서를 제목 목록(E1b)에서 건너뛸 때만 쓴다.
    ('Lithium'·'Asthma' 같은 한 단어 제목의 정식 리뷰 논문을 정크로 오판하지 않기 위한
    분리다. 2026-08-23 전수 실측에서 오판 사례가 확인되어 사용자 결정으로 강등됨.)"""
    t = str(title or '')
    if len(re.sub(r'\\[a-zA-Z]+', '', t)) < 8:          # LaTeX 조각·초단문
        return True
    content = [w for w in norm(t).split() if w not in STOP]
    return len(content) < 3                              # 내용어 <3개


def abstract_ok(a):
    """초록 채택 여부(설계서 §4). 길이 하한은 #85 로 200 → 25 로 개정되었다.
    200 은 정상 초록 116,241편을 버리면서 정형문의 59.3%(200자 이상)를 통과시켜
    방향이 반대인 규칙이었다. 25 는 5자 단위 실측의 무릎이며, 이 하한이 맡는 역할은
    '문장이라 부를 수 없는 조각의 배제' 하나뿐이다. 잡물 차단은 정형문 차단 목록이 맡는다."""
    a = str(a or '')
    if len(a) < ABSTRACT_MIN_CHARS:
        return False
    if re.match(r'(?i)\s*(no abstract|abstract not available)', a):
        return False
    # #110(09-05): LaTeX 잔재 규칙(백슬래시 5+ → 무효) 폐지. 원천 교체판 감사에서
    # 해당 초록 100편 전부가 정상 수식 문헌으로 확인 — 훼손판에서는 잡물 표지였으나
    # 복원판에서는 수식 표지다. 잔물 방어는 정제의 formula-only 분류·길이 하한·정형문
    # 차단이 맡는다. 이 자리에 백슬래시 규칙을 되살리지 말 것.
    return True


def clean_abstract(a):
    a = str(a or '').replace('\u2028', ' ')   # R3: 교체판의 문단 표시(U+2028) — 행 불변식 보호
    a = re.sub(r'<[^>]+>', ' ', a)
    # D-14(#106): 출판사 웹 UI 평문 잔재 제거. 태그 세척과 전문 일치 차단 사이의
    # 사각(아티팩트+실문 16,636편 실측)을 메운다. 실문이 뒤에 있으므로 차단이 아니라
    # 제거가 맞다. 반영은 차기 재빌드(팩 내용이 바뀐다).
    a = re.sub(r'(?i)click to (increase|decrease) image size', ' ', a)
    a = re.sub(r'(?i)^\s*abstract[:.\s]+', '', a)
    return re.sub(r'\s+', ' ', a).strip()


# ── 근접 동일 초록 판정 C3R(#96; §4 "근접 동일 초록은 제거(1편만)"의 연산 정의) ────────
# 정규화는 NFKC·소문자화·유니코드 비단어 공백 치환이다. L.norm 을 쓰면 안 된다 —
# 비ASCII 를 지워 한자·가나 초록이 전부 같은 빈 문자열로 붕괴한다(규칙설계 §2.3 실측).
C3R_THETA = 0.85          # 낱말 5-shingle 자카드 임계
C3R_SHINGLE_K = 5
C3R_MIN_WORDS = 9         # 이 미만이면 문자 8-gram 으로 판정
C3R_CHAR_NGRAM = 8
C3R_MIN_CHARS = 12        # 공백 제거 후 이 미만이면 판정 대상에서 제외(잔류)
C3R_CONTENT_MIN_LEN = 3   # 가드용 내용어 최소 길이


def c3r_norm(s):
    """C3R 정규화: NFKC → 소문자 → 유니코드 비단어(밑줄 포함) 공백 치환 → 공백 축약."""
    import unicodedata
    t = unicodedata.normalize('NFKC', str(s or '')).lower()
    return re.sub(r'\s+', ' ', re.sub(r'[\W_]+', ' ', t)).strip()


def c3r_shingles(nrm):
    """정규화 문자열의 판정용 shingle 집합. 낱말 5-shingle 이 기본이고, 낱말이 9개
    미만이면 공백 제거 문자열의 문자 8-gram, 12자 미만이면 None(판정 제외)."""
    ws = nrm.split()
    if len(ws) >= C3R_MIN_WORDS:
        k = C3R_SHINGLE_K
        return frozenset(' '.join(ws[i:i + k]) for i in range(len(ws) - k + 1))
    flat = nrm.replace(' ', '')
    if len(flat) < C3R_MIN_CHARS:
        return None
    n = C3R_CHAR_NGRAM
    if len(flat) < n:
        return frozenset((flat,))
    return frozenset(flat[i:i + n] for i in range(len(flat) - n + 1))


def c3r_content_words(nrm):
    """가드용 내용어: 정규화 후 3자 이상이면서 STOP 에 없는 낱말(#96 ④)."""
    return {w for w in nrm.split() if len(w) >= C3R_CONTENT_MIN_LEN and w not in STOP}


def c3r_jaccard(sh_a, sh_b):
    a, b = len(sh_a), len(sh_b)
    if min(a, b) < C3R_THETA * max(a, b):     # 크기 비만으로 임계 미달이 확정되는 쌍
        return 0.0
    inter = len(sh_a & sh_b)
    return inter / (a + b - inter)


# ── 비영어 판정 5R(#86, 결정 2-A·2-B; contract_v1.json 'language' 절과 짝) ──────────────
# 판정 대상은 초록 전문이다(절단으로 언어가 바뀌지 않으므로; 규칙설계_결정2_3 §1.3).
# 코어 문헌의 판정 정본은 LANG_STATUS_TABLE(실측 M5, 무효 11,552편 재현)이고, 이 함수들은
# 그 표에 없는 텍스트(멤버 보충·회수 초록)에 같은 규칙을 적용하기 위한 것이다.
# 기능어 54어는 실측표 win_max 재현 1,500/1,500(50낱말 창·10 이동·[A-Za-z]+ 토큰)으로,
# 비영어 불용어 102어는 실측표 역산(홀드아웃 80,000행 중 99.10% 일치, [A-Za-z0-9]+ 토큰의
# 순알파벳만)으로 확정했다. 원 산출 코드가 저장소에 남지 않아 역산으로 복원한 것이며,
# 상태 단위 일치는 층화 표본 17,254행에서 98.79%였다(무효 3종을 가르는 불일치는 0.2%).
LANG_RES_MIN = LANG_RES_MIN_CHARS       # english_usable 의 잔여 문자열 하한(200)
LANG_WIN, LANG_STEP = 50, 10            # 기능어 밀도 창(낱말 50, 이동 10)
LANG_WIN_MAX_TH = 0.15                  # english_usable 의 창 최대 밀도 하한
LANG_HARD_TH, LANG_HARD_LOW, LANG_HARD_LOW_WM = 0.35, 0.20, 0.05
LANG_NE_D_TH, LANG_NE_HITS_MIN, LANG_L1_TH = 0.10, 6, 0.30
LANG_INVALID = ('non_english_script', 'non_english_latin', 'mojibake')
LANG_FW = frozenset((
    'after also an and are as at based be been before between both but by can during for found '
    'from has have however in is it its not of on or our results show shown study such than that '
    'the their therefore these this thus to used using was we were when which with').split())
LANG_NE = frozenset((
    'ainsi al alla anche au auch aux avec bei bij ces cette che com come como con dal dans das '
    'degli dei del delle dem den der des desarrollo desde die dieser dont door dos durch ein eine '
    'einer el elle entre est esta este foi fue gli han het il ist kann las le les leur lo los '
    'mais met mit nach nel nella nicht niet nos nous objetivo onder ont par para pela plus por '
    'pour que questo se ser sich sind sobre son sono sont sulla sur sus tambi uma una und une '
    'van von werden wie wird zur').split())


def _char_class(ch):
    """문자 분류: l=라틴, g=그리스, o=그 밖의 문자 체계(경성), x=비문자.
    hard 분자 = o (그리스 제외; #86 — 화학·수식 영어 초록 379편 오판 방지)."""
    if not ch.isalpha():
        return 'x'
    if ch in 'ªº':                      # Latin-1 서수 표지는 Unicode Script가 Latin이다
        return 'l'
    import unicodedata
    try:
        nm = unicodedata.name(ch)
    except ValueError:
        return 'o'
    if nm.startswith('LATIN'):
        return 'l'
    if nm.startswith('GREEK'):
        return 'g'
    return 'o'


_CHAR_CLASS_CACHE = {}


def lang_features(a):
    """5R 특징량(#86): hard·res_len·res_words·win_max·ne_hits·ne_d·l1_ratio."""
    s = str(a or '')
    letters = oth = l1 = 0
    res_chars = []
    for ch in s:
        o = ord(ch)
        if 0xA0 <= o <= 0xFF:
            l1 += 1
        c = _CHAR_CLASS_CACHE.get(ch)
        if c is None:
            c = _CHAR_CLASS_CACHE[ch] = _char_class(ch)
        if c != 'x':
            letters += 1
            if c == 'o':
                oth += 1
        res_chars.append(' ' if c == 'o' else ch)
    res = re.sub(r'\s+', ' ', ''.join(res_chars)).strip()
    words = re.findall(r'[A-Za-z]+', res.lower())
    hits = [1 if w in LANG_FW else 0 for w in words]
    if not words:
        win_max = 0.0
    elif len(words) <= LANG_WIN:
        win_max = sum(hits) / len(words)
    else:
        win_max = max(sum(hits[i:i + LANG_WIN]) / float(LANG_WIN)
                      for i in range(0, len(words) - LANG_WIN + 1, LANG_STEP))
    ne_hits = sum(1 for t in re.findall(r'[A-Za-z0-9]+', res.lower())
                  if t.isalpha() and t in LANG_NE)
    return {'hard': oth / letters if letters else 0.0, 'res_len': len(res),
            'res_words': len(words), 'win_max': round(win_max, 2), 'ne_hits': ne_hits,
            'ne_d': ne_hits / len(words) if words else 0.0,
            'l1_ratio': l1 / len(s) if s else 0.0}


def lang_status(a):
    """evidence_language_status 8종 판정(#86 표). 빈 초록은 not_applicable."""
    s = str(a or '')
    if not s.strip():
        return 'not_applicable'
    f = lang_features(s)
    usable = f['res_len'] >= LANG_RES_MIN and f['win_max'] >= LANG_WIN_MAX_TH
    if not usable:
        if f['hard'] >= LANG_HARD_TH or (f['hard'] >= LANG_HARD_LOW
                                         and f['win_max'] < LANG_HARD_LOW_WM):
            return 'non_english_script'
        if f['hard'] < 0.05 and f['ne_d'] >= LANG_NE_D_TH and f['ne_hits'] >= LANG_NE_HITS_MIN:
            return 'non_english_latin'
        if f['hard'] < 0.05 and f['l1_ratio'] >= LANG_L1_TH:
            return 'mojibake'
        return 'low_english_undetermined'
    if f['hard'] >= 0.05:
        return 'english_bilingual_script'
    if f['ne_d'] >= LANG_NE_D_TH:
        return 'english_bilingual_latin'
    return 'english'


def trunc(a):
    """#91(2026-09-02): 근거팩(E1a·fill) 경로에서는 절단이 폐기되었다 — 초록은
    clean_abstract 전문을 싣는다. 이 함수는 자체 분량 예산을 가진 V 슬림 팩
    (v_pack_builder, 슬림 ≈16k 토큰 규격)에서만 쓴다. 팩 빌더에서 다시 쓰지 말 것."""
    a = clean_abstract(a)
    return a if len(a) <= 1200 else a[:800] + ' … ' + a[-400:]


def script_profile(s):
    """문자 스크립트 구성비(제목-초록 언어 불일치 검사용): (라틴, 한중일, 기타) 비율."""
    s = str(s or '')
    letters = [c for c in s if c.isalpha()]
    if not letters:
        return (0.0, 0.0, 0.0)
    lat = sum(1 for c in letters if c.isascii())
    cjk = sum(1 for c in letters if '一' <= c <= '鿿' or '가' <= c <= '힯'
              or '぀' <= c <= 'ヿ')
    n = len(letters)
    return (lat / n, cjk / n, (n - lat - cjk) / n)


def tokens_est(text):
    """토큰 추정 = chars/4 (설계서 §4 '토큰은 chars/4 평균')."""
    return int(len(text) / 4)


def load_env():
    """프로젝트 .env의 API 키를 환경에 싣는다(이미 설정된 변수는 존중). 값은 출력 금지."""
    import os
    path = f'{BASE}/.env'
    loaded = []
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and v and k not in os.environ:
                os.environ[k] = v
                loaded.append(k)
    return loaded


def parts_sig_guard(parts_dir, files):
    """parts 재개 가드(A.40·A.49 계열, 2026-09-03 적대 검수 A-4 이행): 청크 parts 는
    '있으면 건너뜀'이라, 코드·자원을 고친 뒤 일부만 비우면 구판 청크가 신판과 섞인다.
    parts 를 처음 만들 때 코드 서명을 남기고, 서명이 다르면 재개를 거부한다."""
    import os
    h = hashlib.sha256()
    for p in files:
        with open(p, 'rb') as f:
            h.update(f.read())
    cur = h.hexdigest()[:16]
    sp = os.path.join(parts_dir, '_CODE_SIG')
    old = open(sp).read().strip() if os.path.exists(sp) else None
    if old is not None and old != cur:
        raise SystemExit(
            f'중단: {parts_dir} 의 기존 parts 는 다른 코드 서명({old})으로 만든 것입니다'
            f'(현재 {cur}). 일부 재개는 세대 혼합을 만드므로 parts 를 비우고 다시 실행하십시오.')
    os.makedirs(parts_dir, exist_ok=True)
    with open(sp, 'w') as f:
        f.write(cur + '\n')
