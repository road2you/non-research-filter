"""m54_junk_genre_v31 — 장르 정크 정규식 v3 → v3.1 보수, 전수 재집계, 2차 판정 대상, 블라인드 감사 표본.

배경: 독립 감사(facts A.67, 미이행대장 R7-e, 결정 #122)가 정규식 v3 후보 13종에서 오탐 구조를 실측으로
적발했다. 이 스크립트는 그 보수 목록을 반영한 v3.1 정규식을 정의하고(정규식 정의·전수 스캔·집계·표본
추출을 한 파일에), v3(m47_junk_genre_scan.PATTERNS)와 같은 스캔에서 나란히 계산해 유형별 증감을 센다.
정본(s0_lib.JUNK, pipeline/out 의 v2 산출물)과 m47 은 수정하지 않는다.

보수 내용(R7-e ①~⑦, 이 파일 주석의 [A1]~[A5]·[B6]·[B7]·[C] 표지가 지시 항목과 대응한다):
  [A1] 일반 명사 단독형(news·index·response·retraction·acknowledgment·comment 등)의 종결 집합에서
       쉼표·엠대시를 제거(END1). 엔대시·하이픈은 앞에 공백이 있을 때만 구분자로 본다("Response–Response
       Binding"·"RETRACTED–Lessons" 같은 붙여 쓴 형태는 복합어로 취급). 표제어의 대소문자 형태는
       lower·Capitalized·UPPER 만 허용해 'RESPOnSE'·'InDEx'·'DigEST' 같은 대소문자 혼합 약어를 제외한다
       (cw 함수). 전대문자는 'RETRACTED:'·'CORRESPONDENCE:'·'RESPONSE: Re:' 같은 고지형이 1,636건이라
       유지한다(실측, 표본 30건 전건 고지).
  [A2] news: '<난 표제> update/highlights/brief/digest: <주제>' 콜론 직결형 제외. 다만 뒤가 '(the) latest/
       recent/monthly/top five/highlights from/<월>/<숫자>' 같은 난 표지일 때만 남긴다(2차 판정 대상 잔여).
       'Miscellanea.' 는 단독형만, '<형용사> issues' 는 쉼표·괄호 제외(콜론형은 남기고 2차 판정).
       'selection(s)/summaries/abstracts' 의 콜론 직결형도 제외(표본에서 연구 제목 5/40).
  [A3] abstracts_meeting: 'Highlights of/from the X' 는 100자 안에 학회·호 어휘(meeting·conference·
       symposium·congress·issue·volume·proceedings·abstracts·session·workshop·summit·assembly·
       convention·seminar)가 있을 때만. 단수 'abstract'(Poster Abstract: <제목>) 제외 — 복수형만.
       'Programme of/for the X' 는 학회 어휘 직결형만.
  [A4] retraction_notice: 'Retraction of <주제>' 는 인용부호·'the article' 류·숫자·권호 표기 직결형만
       (소문자 주제뿐 아니라 대문자 주제도 30건 중 22건이 물리·생리 연구라 함께 제외).
       'Correction for/of volume·cell·number·equation …' 은 숫자 직결(volume 7, equation (3))이나
       저널 약칭 뒤 숫자·대문자일 때만.
  [A5] tribute_address: 'Acknowledgment of <주제>' 는 reviewers/referees/support 류 직결형만, 콜론 직결형
       제거(6건 전부 연구), 'Thanks to <주제>' 는 역할 명사 직결형만, 'Reviewers/Referees in|and <주제>'
       제외. index_toc: 'Advertisements: <주제>' 제외(단독·권호형만), 'Name/Citation/Taxonomic … index'
       는 단독형과 'index of/to <권·숫자>' 형만.
  [B6] book_review_of(신설): 'Review of <책> by <이름>'(by 앞 낱말이 -ed 로 끝나면 제외; edited/translated
       등은 허용), 'Review of: X'·'Review of “X”'(닫는 인용부호 뒤 종결 필수), 'Review(s): … <출판 표지>'
       (ISBN·pp.·가격·출판사·도시:), 'Review: <이니셜 포함 저자>, <책>'.
  [B7] named_reply(신설): 'Commentary/Comment(s)/Response/Reply/Rejoinder by <대문자 이름>'(정관사 the 제외),
       'Response/Reply/Comment(s)/Commentary to|on <이름>' + 엄격한 종결(쉼표·and <이름>·et al·연도·
       's <comment 류>·이니셜/경칭·성 하나 뒤 $ 는 reply/rejoinder/response 만). 'Comment(s) on <한 낱말>$'
       은 30% 오탐이라 제외, 'Response to <두 낱말 이상>$' 은 12.5% 오탐이라 경칭·이니셜·꼬리 명사형만.
       신설 2종의 배타 신규분 표본 40건 자체 판정: book_review_of 0/40, named_reply 2~3/40(10% 이하).
  [C]  조건부 유형 처리(#122 기본안): case_record·bibliography 포함, 학회 보고·서평 에세이·정책 브리프 포함,
       'Introduction: <주제>' 미포함(보류).

산출(pipeline/out/_junk_v3/):
  genre_patterns_v31.json        v3.1 정규식(유형 → 정규식; 15종)
  genre_hits_v31.parquet         v3 ∪ v3.1 적중 문헌(work_id, nano_id, title_head, v2_hit, retracted,
                                 types_v3, types_v31)
  genre_counts_v31.parquet       유형별 v3·v3.1 건수(v2 미적중·#89 철회 제외), 제거·추가 건수
  genre_counts_v31.json          위 표 + 합집합 신규 정크 문헌 수
  second_pass_candidates.parquet 2차 판정 대상(work_id, nano_id, title, abstract_head, type, subform, why)
  second_pass_subforms.json      하위 형태별 건수·선정 이유
  v31_audit_key.parquet          블라인드 감사 표본 정답표(work_id → type, batch)
  <scratch>/v31_audit_batch{0,1,2}.jsonl  판독자용(work_id·제목·초록 300자만)

사용: .venv/bin/python pipeline/scripts/m54_junk_genre_v31.py [scan|count|second|audit|selftest|stats|all]
"""
import hashlib
import json
import os
import re
import sys
import time

import duckdb
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s0_lib as L  # noqa: E402
import m47_junk_genre_scan as M47  # noqa: E402

OUT_DIR = M47.OUT_DIR
MEM = M47.MEM
HITS = f'{OUT_DIR}/genre_hits_v31.parquet'
SCRATCH = ('/tmp/claude-1000/-home-snoopy-Positron-nano-cluster-massage/'
           '39c13675-cbd8-4013-a305-76255266ae39/scratchpad')
AUDIT_SEED = 'v31'
AUDIT_N = 40
ABS_HEAD_2ND = 600
ABS_HEAD_AUDIT = 300
V3 = M47.PATTERNS

# ── 공통 조각(v3 계승) ──────────────────────────────────────────────────────────────
Q = M47.Q
MON = M47.MON
ART = M47.ART
CAP = M47.CAP
END = M47.END                                     # v3 종결 집합(쉼표·엠대시 포함) — 다어절 표제에만
# [A1] 단일 일반명사 단독형의 종결 집합: 쉼표·엠대시 제거, 엔대시·하이픈은 앞 공백 필수
END1 = r'(?:$|\s*[:.•;(\[]|\s+[-–]|\s+\d)'
VENUE = (r'(?:(?:meeting|conference|symposium|congress|proceedings|abstracts|session|workshop|summit|'
         r'assembly|convention|seminar)s?|issue|volume)\b')   # 'issues in'(리뷰) 오탐 방지: issue 는 단수만


def cw(*words):
    """[A1] 단일 일반명사 표제어를 lower·Capitalized·UPPER 세 형태로만 허용(대소문자 혼합 약어 제외).
    (?i) 전역 모드 안에서 (?-i:) 로 대소문자를 강제한다(RE2·re 공통 문법)."""
    alts = []
    for w in words:
        alts += [w, w.capitalize(), w.upper()]
    return '(?-i:(?:' + '|'.join(alts) + '))'


# 이름 조각(대소문자 강제 블록 안에서 쓴다). 성 하나·이니셜·복합성.
NAME = (r"(?:[A-Z][a-z’'\-]+|[A-Z]\.|Mc[A-Z][a-z]+|Mac[A-Z][a-z]+|O’[A-Z][a-z]+|O'[A-Z][a-z]+|"
        r"D[ei][A-Z][a-z]+|La[A-Z][a-z]+|Van[A-Z][a-z]+|[A-Z][a-z]+-[A-Z][a-z]+)")
NAMEX = (r"(?:\s+(?:[A-Z]\.?|[A-Z][a-z’'\-]+|de|van|von|der|den|la|le|du|da|di|del|della|bin|ibn|"
         r"y|e|Jr\.?|Sr\.?))")   # 'Boris R Krasnov' 처럼 마침표 없는 중간 이니셜 허용
NAMEI = (r"(?:(?:[A-Z]\.\s*)+" + NAME + r"|" + NAME + r"(?:\s+[A-Z]\.)+\s+" + NAME + r")")  # 이니셜 포함
HON = r"(?:(?:drs?\.?|profs?\.?|professor|mr\.?|mrs\.?|ms\.?|sir|dame|rev\.?)\s+)?"  # 경칭(대소문자 무시)
PUB = (r'(?:\bisbn\b|\bpp\.|\b\d+\s?pp\b|£\s?\d|\$\s?\d|€\s?\d|university press|routledge|springer|'
       r'wiley|elsevier|palgrave|macmillan|blackwell|\bsage\b|penguin|oxford:|london:|new york:|'
       r'cambridge:|chicago:|berlin:|paris:|boston:|philadelphia:|amsterdam:|hardcover|paperback|'
       r'hardback|\bhbk\b|\bpbk\b|\(eds?\.?\)|\beds?\.\s|edited by|translated by|reviewed by)')
# 'by' 앞 낱말: -ed 로 끝나는 분사(Caused/Manufactured/Induced by <방법>)는 제외, 편집·번역 표지는 허용
PREV_OK = (r'(?:[^\s"“”]*[^d\s"“”]|[^\s"“”]*[^e\s"“”]d|edited|translated|compiled|introduced|'
           r'selected|revised|collected|annotated|illustrated|abridged|authored|co-authored|ed\.|'
           r'eds\.|\(eds?\.?\)|,|\))')
NAME_END = (r'\s*(?:$|[,.;]|\s+(?:and|&|with)\s+' + HON + r'(?-i:' + NAME + NAMEX + r'{0,2})\s*'
            r'(?:$|[,.;(]|\s+\d{4}\b|\s+(?:and|&|with)\b)|\s*\(\s*(?:\d{4}|eds?)|\s+\d{4}\b|'
            r'\s+\(?eds?\b|\s+(?:london|new york|oxford|cambridge|chicago|berlin|paris|boston|'
            r'philadelphia|amsterdam|dordrecht|heidelberg|routledge|springer|wiley|elsevier|palgrave|'
            r'macmillan|blackwell|sage|penguin|mit press|the mit press)\b|\s+(?-i:[A-Z][a-z]+ '
            r'(?:University )?Press)\b)')
RP_HEAD = (r'(?:a |an |the |brief |short |further |our |authors?[’\']?s? )?'
           r'(?:responses?|repl(?:y|ies)|comments?|commentary|rejoinders?)')
RP_TAIL_NOUN = (r'(?:comments?|commentary|critique|letter|reply|response|rejoinder|review|paper|'
                r'article|remarks?|notes?|discussion|critical|analysis|proposal|argument|essay|'
                r'objections?|claims?|reading|interpretation|viewpoint|editorial|critics|readers|'
                r'reviewers|discussants)')
IDX_LIST = (r'(?:subject|author|title|keyword|name|species|volume|contents|contributor|advertiser|'
            r'topic|topical|formula|key.?word)s?')
IDX_STRONG = (r'(?:author|subject|keyword|key ?word|volume|cumulative|annual|contributor|reviewer|'
              r'advertiser|abbreviation|acronym|title|contents)s?[’\']?s?')
IDX_WEAK = (r'(?:name|names|species|taxonomic|citation|chemical|topical|topic|general|combined|'
            r'analytical|formula|compound|organism|genus|proper name)')
NEWS_HEADS = (r'(?:research|news|literature|journal|clinical|science|policy|legislative|regulatory|'
              r'technology|industry|evidence|practice|drug|product|conference|meeting|congress|'
              r'abstract|paper|article|media|web|website|internet|patent|book|software|market|'
              r'clinical trials?|publication|publications)')
DATE_END = r'(?:$|\s+\d|\s*[(]\s*(?:\d|' + MON + r')|\s+monthly\b|\s+weekly\b|\s+quarterly\b|\s+' + MON + r')'
COL_MARK = (r'(?:the )?(?:latest|recent|monthly|weekly|quarterly|top \d|top ten|top five|highlights '
            r'from|highlights of|this (?:month|issue|week)|news|\d|' + MON + r')\b')

PATTERNS = {
    # 논평 [A1]
    'commentary': (
        r'^\s*(?:a |an |some |brief |further |additional |editorial |invited |guest |clinical |'
        r'clinicians?[’\']?s? |authors?[’\']?s? |expert |critical |short )?'
        + cw('commentary', 'commentaries', 'comment', 'comments') + r'\s*'
        r'(?:' + END1 + r'|(?:one|two|three|four|five|six|seven|eight|nine|ten|i|ii|iii|iv)\b'
        r'|(?:on|to|regarding|concerning)\s*(?:' + Q + r'|' + ART + r'))'
        # 쉼표 제거([A1])의 예외: 'Comments, with reply, on …'(IEEE 정형 표제)
        r'|^\s*(?:comments?|commentary),\s*(?:with (?:the )?(?:authors?[’\']? )?repl(?:y|ies)|with response|'
        r'and repl(?:y|ies)|and responses?|response|reply)\b'
        r'|^\s*(?:a |general |panel |open |floor |invited |formal |further |the )?'
        + cw('discussion', 'discussions') + r'\s*'
        r'(?:$|\s*[:.•;(\[]|\s+[-–]|(?:of|on)\s*(?:' + Q + r'|' + ART + r')|by\b)'),
    # 회신·재반론 [A1]
    'reply': (
        r'^\s*(?:a |an |the |our |brief |short |further )?(?:authors?[’\']?s? |editors?[’\']?s? )?'
        + cw('reply', 'rejoinder', 'replies', 'rejoinders') + r'\s*(?:' + END1 + r'|(?:to|by|from)\b)'
        r'|^\s*in (?:reply|rejoinder)\s*(?:$|\s*[:.]|\s+[-–]|to\b)'
        r'|^\s*in response\s*(?:$|\s*[:.]|\s+[-–]|to (?:the |a |an |our |my )?(?:comments?|letters?|'
        r'critics?|critique|editors?|drs?\.?|prof\.?|professor|article|paper|review|reply|'
        r'commentary|commentaries|discussion|editorial|correspondence|' + Q + r'))'
        r'|^\s*(?:a |an |the |our |brief |short |further )?(?:authors?[’\']?s? )?'
        + cw('response', 'responses') + r'\s*'
        r'(?:$|\s*[:.]|\s+[-–]|to (?:the |our |my )?(?:critics?|comments?|commentar|discussants?|'
        r'discussion|reviewers?|referees?|editors?|letters?|reply|replies|rejoinder|critique|'
        r'responses?|commentaries|correspondence|readers?)\b|to\s*' + Q + r')'),
    # 서신 [A1]
    'letter': (
        r'^\s*(?:clinical |readers?[’\']?s? |selected |brief |short )?'
        + cw('letter', 'letters', 'correspondence') + r'\s*(?:$|\s*[:.(]|\s+[-–]|to the (?:editors?|'
        r'case|journal)\b|and (?:comments?|replies|reply|responses?|corrections?|notes)\b|'
        r'from (?:the )?(?:editors?|readers?)\b)'
        r'|^\s*dear (?:editors?|readers?|colleagues?|members?|sir|sirs|madam)\b'),
    # 편집자 주·인사: v3 그대로(감사 오탐 0, 다어절 표제)
    'editor_note': V3['editor_note'],
    # 서평 목록·수령 도서 [A1]·[C] 서평 에세이 포함
    'books_received': (
        r'^\s*(?:books?|publications?|monographs|new books|recent books|new publications|'
        r'recent publications|literature|periodicals|journals|reports|pamphlets|reprints|'
        r'materials?|documents?)\s+'
        r'(?:received|noted|noticed|available|reviewed|for review|in brief|in review|'
        r'recently received|and (?:monographs|films|other|literature|media|journals|reports|'
        r'pamphlets|reviews|periodicals|articles|publications|documents|software|videos|'
        r'the media|materials|booklets|book reviews|bulletins|proceedings|papers|serials))\b'
        r'|^\s*(?:new |recent |current )?' + cw('books', 'publications') + r'\s*(?:$|\s*[:.(/]|\s+[-–]|'
        r'list\b|for (?:review|the)\b|of (?:the (?:month|year|week|quarter)|interest|note)\b|'
        r'in (?:brief|review|print|the news)\b)'
        r'|^\s*(?:recent|new|current) [a-z]+ (?:and [a-z]+ )?(?:books|publications)\s*'
        r'(?:$|\s*[:.(–—]|\s+-|received\b|of\b|in\b)'
        r'|^\s*books? lists?\b|^\s*books reviews?\b|^\s*review articles\s*$'
        r'|^\s*reports (?:&|and) (?:other )?(?:publications|documents)\b'
        r'|^\s*doctoral dissertations (?:in|on|completed|accepted|received|abstracts)\b'
        r'|^\s*reviews? of (?:periodical|recent|current) (?:literature|publications)\b'
        r'|^\s*current literature (?:reviewed|review|abstracts|abstracted)\b'
        r'|^\s*literature reviews? and comment\b'
        r'|^\s*\[?(?:book|books)\s*(?:&|and|/)\s*(?:resource|film|media|journal|software|'
        r'video|other|other media|electronic|multimedia|web)s?\s+(?:reviews?|notes?|notices?)\b'
        r'|^\s*book (?:notes?|notices?|briefs?|section|corner|forum|column|watch|essays?|'
        r'of the (?:month|week|year|quarter)|reviews? (?:section|essay|column|symposium|'
        r'supplement|editor))\b'
        r'|^\s*(?:extended|commissioned|brief|special|critical|featured|essay|double|joint|'
        r'comparative|long|short|mini|classic|graphic|new|recent|invited) '
        r'(?:book|film|media|software) reviews?\b'
        r'|^\s*\[(?:book|film|media)s? reviews?\]'
        r'|^\s*title \((?:book|film) reviews?\)'
        r'|^\s*review (?:essays?|symposi(?:um|a)|section|forum|column|feature|notes?|notices?|'
        r'of books|of recent books|of new books)\s*(?:$|\s*[:.(–—]|\s+-)'
        r'|^\s*reviews\s*[—–-]\s*(?:besprechungen|comptes rendus|book reviews|buchbesprechungen)\b'
        r'|^\s*' + cw('reviews') + r'\s*(?:$|\s*[:.(]|\s+[-–]|of (?:books|recent|new|current|'
        r'periodical)\b|and (?:notices|notes|comments|short notices|announcements|book notes|'
        r'abstracts|reports)\b)'
        r'|^\s*(?:research|book|literature|brief|short|media|film|software|web ?site|resource|'
        r'product|video|recent|critical|journal|periodical|new book|new books|journal article|'
        r'article|shorter|short notices and|briefer) reviews\s*'
        r'(?:$|\s*[:.(–—]|\s+-|and\b|of (?:recent|new|current|the)\b)'
        r'|^\s*(?:buch)?besprechung(?:en)?\b|^\s*rezension(?:en)?\b|^\s*comptes?[- ]rendus?\b'
        r'|^\s*recensioni\b|^\s*recensions?\b|^\s*rese[ñn]as?\b|^\s*livres re[çc]us\b'
        r'|^\s*boekbespreking(?:en)?\b|^\s*bücherschau\b|^\s*neue bücher\b|^\s*literaturbericht\b'
        r'|^\s*notes de lecture\b|^\s*libros recibidos\b'
        r'|^\s*list of (?:publications|books|new books|recent publications|papers|articles|'
        r'references|contributors|participants|members|fellows|officers|delegates|reviewers|'
        r'referees|abbreviations|figures|tables|symbols|plates|illustrations|maps|authors|'
        r'exhibitors|sponsors|speakers|attendees|registrants|advertisers|donors|awards)\b'
        r'|^\s*(?:recent|current|new) (?:publications|literature|books|articles|references|'
        r'titles|releases)\s*(?:$|\s*[:.,(–—]|\s+-|in\b|on\b|of\b|received\b|from\b|relating\b|'
        r'relevant\b)'),
    # 서지 목록 [A1]·[C] 포함
    'bibliography': (
        r'^\s*(?:a |an )?(?:select(?:ed)? |annotated |current |recent |cumulative |classified |'
        r'brief |short |partial |running |annual |supplementary |critical |comprehensive )?'
        + cw('bibliography', 'bibliographies') + r'\s*(?:$|\s*[:.(]|\s+[-–]|of\b|on\b|for\b|'
        r'\s*[—–-]\s*editors[’\']? selection\b)'),
    # 뉴스·학회 소식·행사 안내 [A1]·[A2]·[C] 정책 브리프 포함
    'news': (
        r'^\s*' + cw('news') + r'\s*(?:$|\s*[:&;.(]|\s+[-–]|\s+\d|\s+(?:and|&)\s+(?:views?|notes?|'
        r'notices?|comments?|announcements?|events?|reviews?|reports?|information|updates?|'
        r'features?|letters?|highlights?|briefs?|analysis|opinion|people|appointments|diary|'
        r'calendar|the (?:profession|society|association))\b|\s+in brief\b|\s+briefs?\b|\s+from\b|'
        r'\s+for\b|\s+of the\b|\s+round-?ups?\b|\s+updates?\b|\s+items?\b|\s+notes?\b|'
        r'\s+digest\b|\s+flash\b|\s+releases?\b|\s+views\b|\s+section\b|\s+column\b|\s+page\b|'
        r'\s+desk\b|\s+feature\b|\s+report\b|\s+review\b|\s+watch\b|\s+headlines?\b|'
        r'\s+highlights?\b|\s+corner\b|\s+bulletin\b|\s+summary\b|\s+letter\b|\s+brief\b)'
        r'|^\s*[a-z&’\']+ news\s*$'
        r'|^\s*(?:association|society|institute|industry|member(?:ship)?|members[’\']?|chapter|'
        r'section|division|faculty|department|college|academy|foundation|federation|council|'
        r'committee|company|corporate|campus|staff|alumni|conference|meeting|journal|research|'
        r'science|policy|legislative|regulatory|government|international|national|regional|'
        r'world|european|global|clinical|medical|nursing|hospital|health|technical|technology|'
        r'business|trade|patent|book|publishing|education|product|people|personnel|'
        r'professional|branch|state|local|federal|university|school|library|market|other|'
        r'general|late|latest|breaking|current|recent|brief|short|miscellaneous|sundry|home|'
        r'foreign|overseas)\s+news\s*(?:$|\s*[:.,;(&–—]|\s+-|\s+\d|\s+(?:and|&)\s+(?:views?|'
        r'notes?|notices?|comments?|announcements?|events?|information|updates?)\b|\s+from\b|'
        r'\s+in brief\b|\s+briefs?\b|\s+for\b|\s+of\b|\s+updates?\b|\s+items\b|\s+notes\b|'
        r'\s+section\b|\s+column\b)'
        # [A2] 난 표제 + 난 어휘: watch/roundup/scan/corner/briefing/alerts/monitor/snippets 는 콜론 직결 허용
        r'|^\s*' + NEWS_HEADS + r' (?:round-?ups?|watch|scan|scans|briefing|alerts?|monitor|corner|'
        r'snippets)\s*(?:$|\s*[:.;(–—]|\s+-|\s+\d|\s+monthly\b|\s+weekly\b|\s+quarterly\b|\s+' + MON + r')'
        # [A2] update/highlights/brief/digest/selection/summaries/abstracts 는 날짜형 또는 난 표지 직결형만
        r'|^\s*' + NEWS_HEADS + r' (?:updates?|digest|briefs?|highlights|selections?|summaries|'
        r'abstracts|abstracted)\s*(?:' + DATE_END + r'|\s*[:;–—]\s*' + COL_MARK + r')'
        # [A1] 'DigEST : <연구>' 같은 대소문자 혼합 약어 제외: 꼬리는 전소문자 또는 전대문자만
        # [C] 정책 브리프는 포함(#122 기본안): 'Policy brief: <주제>' 는 [A2] 제외의 예외
        r'|^\s*policy briefs?\s*(?:$|\s*[:.;(–—]|\s+-|\s+\d|\s+' + MON + r')'
        # 'Highlights from the (Flow Chemistry) Literature 2014' 난(연구 리뷰 'Highlights of the literature on X' 제외)
        r'|^\s*highlights (?:from|of) the (?:[a-z]+ ){0,3}(?:literature|latest (?:articles|literature|papers|'
        r'research))\s*(?:$|\s*[:.;(]|\s+\d)'
        r'|^\s*(?:the )?(?:' + CAP + r'[a-z&.’\']*\s+){0,3}' + CAP + r'(?-i:(?:igest|IGEST|ewsletter|'
        r'EWSLETTER|oticeboard|OTICEBOARD|otice board|OTICE BOARD))\s*(?:$|\s*[:.;(]|\s+[-–]|\s+\d|\s+'
        + MON + r')'
        r'|^\s*bulletin board\s*(?:$|\s*[:.;(]|\s+[-–]|\s+\d|\s+' + MON + r')'
        r'|^\s*digest of (?:articles|recent|current|the literature|literature|papers)\b'
        r'|^\s*latest (?:clinical |medical |scientific )?(?:research|literature|evidence|'
        r'publications|papers|articles)\s*(?:$|\s*[:.;(]|\s+[-–]|\s+\d|\s+' + MON + r')'
        # [A2] '<형용사> issues': 쉼표·괄호 제외, 엠대시는 날짜 직결만(콜론형은 2차 판정)
        r'|^\s*(?:clinical|current|topical|professional|practice|policy|regulatory|legal|'
        r'ethical|legislative) issues\s*(?:$|\s*[:;]|\s+[-–]|\s*[–—]\s*(?:\d|' + MON + r')|\s+\d|'
        r'\s+' + MON + r')'
        r'|^\s*(?:articles|papers|publications|books|items|literature) of interest\s*'
        r'(?:$|\s*[:.;(]|\s+[-–]|\s+\d|\s+to\b|\s+' + MON + r')'
        r'|^\s*in the literature\s*(?:$|\s*[:.;(]|\s+[-–]|\s+\d|\s+' + MON + r')'
        r'|^\s*what[’\']?s new\s*(?:$|\?\s*$|\s*[:.;]|\s+[-–]|\s+\d|\s+in this issue\b|'
        r'\s*\(\s*(?:\d|' + MON + r')|\s+' + MON + r')'
        r'|^\s*(?:new year|birthday|queen[’\']?s birthday|king[’\']?s birthday|merit) '
        r'(?:honou?rs|awards)\b'
        r'|^\s*(?:awards?|honou?rs|prizes?|awards and honou?rs|honou?rs and awards|prizes and '
        r'awards|awards and prizes)\s*(?:$|\s+\d{4}|\s+' + MON + r')'
        r'|^\s*(?:upcoming|forthcoming|future|coming) (?:events|meetings|conferences|'
        r'articles|papers|issues|symposia|courses|congresses|workshops|dates|seminars|'
        r'publications|activities|special issues|titles)\b'
        # 단일 일반명사(events·meetings·diary…)는 of/for 뒤를 행사 어휘로 한정("Diary of a working boy" 제외)
        r'|^\s*(?:calendar|diary|diary dates|dates for your diary|events|meetings|'
        r'conferences|courses|congresses|symposia|workshops|seminars|exhibitions|'
        r'meetings? calendar|conference calendar|events calendar|calendar of (?:events|'
        r'meetings|conferences|courses)|meetings? and (?:conferences|courses|events|symposia|'
        r'congresses)|courses and (?:conferences|meetings|events)|conferences and (?:meetings|'
        r'courses|events|symposia)|conferences, congresses,? and symposia|meetings? '
        r'(?:announcements?|notices?|of interest|ahead|diary)|conference (?:announcements?|'
        r'notices?|diary)|congress (?:calendar|diary)|society (?:notices?|announcements?|'
        r'business|affairs|matters|news and notes)|association (?:business|affairs|matters|'
        r'notices?|announcements?))\s*(?:$|\s*[:.;(]|\s+[-–]|\s+\d|\s+(?:for|of)\s+(?:the )?'
        r'(?:month|week|year|\d|interest|societies|society|events|meetings|forthcoming|coming|'
        r'upcoming|note|' + MON + r')\b|\s+' + MON + r')'
        r'|^\s*calls? for (?:papers|abstracts|nominations|applications|proposals|manuscripts|'
        r'submissions|contributions|participation|entries|posters|presentations|reviewers|'
        r'volunteers|articles|chapters|comments|awards?|fellowships?|editors?|book|books|'
        r'expressions)\b'
        r'|^\s*' + cw('notice', 'notices') + r'\s*(?:$|\s*[:.]|\s+[-–]|of (?:meetings?|the annual|'
        r'annual|change|withdrawal|redundant|duplicate|books|forthcoming|elections?|awards?)\b|'
        r'to (?:authors|contributors|members|readers|subscribers|advertisers|our readers)\b)'
        # [A2] 'Miscellanea. <제목>'(Biometrika 연구 노트) 제외 — 단독·날짜형만
        r'|^\s*(?:miscellany|miscellanea)\s*(?:$|\s+\d|\s+' + MON + r')'
        r'|^\s*(?:personalia|personal and miscellaneous|people and places|appointments and '
        r'awards|awards and (?:honou?rs|prizes|appointments)|honou?rs and awards|prizes and '
        r'awards|new members|new fellows|members[’\']? news|member news|'
        r'notes and (?:news|comments|queries|notices|announcements)|odds and ends|'
        r'in brief|briefly|short items|items of interest|in the news|in the journals|in other '
        r'journals|elsewhere in the literature|from the literature|from the journals|from '
        r'other journals|around the (?:world|journals|societies|regions|profession)|abstracts '
        r'from around the world|highlights (?:of|from|in) this issue|in the next issue|coming '
        r'in the next issue|next issue|inside this issue|about this issue|this month[’\']?s '
        r'(?:issue|special|highlights|cover|articles|selections))'
        r'\s*(?:$|\s*[:.;(]|\s+[-–]|\s+\d|\s+from\b|\s+for\b|\s+' + MON + r')'),
    # 색인·목차·판권 [A1]·[A5]
    'index_toc': (
        r'^\s*(?:cumulative |annual |volume |combined |five.year |ten.year |keyword |key ?word |'
        r'name |species |taxonomic |title |citation |chemical |topical |topic |general |'
        r'analytic(?:al)? |systematic |consolidated |complete |alphabetical |classified |'
        r'contributors[’\']? |reviewers[’\']? )?'
        r'(?:' + IDX_STRONG + r'(?: (?:and|&|/) ' + IDX_LIST + r')?|' + IDX_WEAK + r' (?:and|&|/) '
        + IDX_LIST + r') index(?:es|ices)?\s*'
        r'(?:$|\s*[:.,;(–—]|\s+-|\s+\d|\s+to\b|\s+for\b|\s+of (?:vol|volume|authors|subjects|'
        r'the)\b|\s+vol\b|\s+volume\b)'
        # [A5] name/citation/taxonomic index: 단독형과 권·숫자 직결형만
        r'|^\s*' + IDX_WEAK + r' index(?:es|ices)?\s*(?:$|\s*[,:;(–—]?\s*(?:to |for |of )?(?:the )?'
        r'(?:vol|volume|\d)|\s+(?:to|for|of)\s+(?:the )?[^,:;]{0,40}?\b(?:vol|volume)\b)'
        r'|^\s*index (?:of|to|by|for) (?:authors?|subjects?|volumes?|vol\.?|contributors|'
        r'keywords?|titles?|advertisers|papers|articles|abstracts|reviewers|referees|'
        r'book reviews|books reviewed|contents|this (?:issue|volume)|the (?:volume|issue|year)|\d|'
        r'(?:names?|species|genera|taxa)\s*(?:$|[,:;(]|\s+(?:in|to|for|of)\s+(?:vol|volume|this|'
        r'the)\b))'
        r'|^\s*' + cw('index') + r'\s*(?:$|\s*[:.;(]|\s+[-–]|\s*[,–—]\s*(?:vol|volume|\d)|'
        r'\s*,\s*[^,:;]{0,60},\s*(?:vol|volume)\b|\s+to vol|'
        r'\s+vol\b|\s+\d|\s+for (?:volume|vol)\b|\s+of (?:volume|vol|authors|subjects|names|papers)\b)'
        r'|^\s*(?:cumulative|annual|volume|decennial|five.year|ten.year|master|general|'
        r'comprehensive|combined|consolidated|complete|keyword|key ?word|alphabetical|'
        r'classified) (?:index|indexes|indices|contents|table of contents)\s*'
        r'(?:$|\s*[:.,;(–—]|\s+-|\s+\d|\s+to (?:vol|volume)|\s+for (?:vol|volume)|\s+of '
        r'(?:vol|volume|authors|subjects))'
        r'|^\s*' + cw('contents') + r'\s*(?:$|\s*[:;/]|\s+[-–]\s|\s*[,.–—]\s*(?:vol|volume|\d|no\.?\s*\d|'
        r'issue|index|abstracts|masthead|table of contents)|\s+list\b|\s+of (?:vol|volume|this|the '
        r'(?:volume|issue|journal|present))\b|\s+vol\b|\s+volume\b|\s+pages?\b|\s+for\b|\s+\d|'
        r'\s+and (?:index|author index|abstracts|masthead|editorial board)\b|\s+continued\b|'
        r'\s+cont\b|\s+in this issue\b|\s+this issue\b)'
        r'|^\s*(?:volume|issue|journal|annual|cumulative) (?:contents|table of contents|'
        r'index|information|masthead)\s*(?:$|\s*[:.,;(–—]|\s+-|\s+\d|\s+to (?:vol|volume)|'
        r'\s+for (?:vol|volume)|\s+of (?:vol|volume|authors|subjects))'
        r'|^\s*(?:front|back|end|prelim(?:inary)?)\s?(?:matter|pages?)\b'
        r'|^\s*(?:front|back|inside|outside|inside front|inside back|outside front|outside back) '
        r'covers?\b'
        r'|^\s*' + cw('cover', 'covers') + r'\s*(?:$|\s*[:.;(]|\s+[-–]|\s+images?\b|\s+pictures?\b|'
        r'\s+photos?\b|\s+photographs?\b|\s+illustrations?\b|\s+captions?\b|\s+story\b|\s+legends?\b|'
        r'\s+art\b|\s+artwork\b|\s+\d|\s+and (?:contents|table of contents|masthead|front '
        r'matter)\b)'
        r'|^\s*(?:about|on) the covers?\b'
        r'|^\s*(?:instructions?|information|guidelines?|guide|guidance|notes?|advice|notice|'
        r'directions?|requirements?|checklist|suggestions?|rules|policy|policies)'
        r' (?:to|for) (?:the )?(?:authors?|contributors?|prospective authors|reviewers?|'
        r'referees?|advertisers?|subscribers?|readers?|manuscript (?:preparation|submission)|'
        r'submission of (?:manuscripts|papers|articles)|preparation of (?:manuscripts|papers))\b'
        r'|^\s*(?:full|entire|complete|whole|this) issue\s*(?:$|\s*[:.,;(–—]|\s+-|\s+pdf\b|'
        r'\s+in pdf\b|\s+as pdf\b|\s+\d)'
        r'|^\s*issue (?:information|contents|highlights|cover|masthead|table of contents|'
        r'index|editorial board|front matter)\b'
        r'|^\s*(?:editorial board|editorial (?:staff|committee|advisory board|advisers|'
        r'advisors|office)|board of (?:editors|associate editors|reviewers|referees)|advisory '
        r'board|associate editors|reviewing editors|consulting editors|editorial and advisory '
        r'board|international advisory board|scientific advisory board|scientific committee|'
        r'organizing committee|organising committee|programme committee|program committee|'
        r'committee members?|officers and committees?|officers and council|society officers|'
        r'membership list|list of members|roll of members|directory of members|members? '
        r'directory|copyright page|copyright notice|copyright information|'
        r'publication information|subscription information|subscription page|'
        r'advertisers[’\']? index|advertiser index|index to advertisers|'
        r'classified advertisements?|reprint information|title page|'
        r'half.title|list of abbreviations|cumulative contents|contents of volume|volume '
        r'index|blank page|end page|inside pages|annual subscriptions?|subscription '
        r'(?:rates|form|order form|prices)|advertisers? in this (?:issue|number))\s*'
        r'(?:$|\s*[:.,;(–—]|\s+-|\s+\d)'
        # [A5] 단일 명사형 판권 표지: 광고는 단독·권호형만(콜론 직결 제외), 나머지는 콜론까지
        r'|^\s*(?:advertisements?)\s*(?:$|\s+\d|\s*[,:;(–—]\s*(?:vol\b|volume\b|\d))'
        r'|^\s*(?:classifieds|permissions|subscriptions|impressum|colophon|masthead)\s*'
        r'(?:$|\s*[:;(]|\s+[-–]|\s+\d)'),
    # 초록집·학회 요약 [A1]·[A3]·[C] 학회 보고 포함
    'abstracts_meeting': (
        # [A3] 복수형 abstracts 만(단수 'Poster Abstract: <제목>' 은 #79 가 정크에서 뺀 단일 초록)
        r'^\s*(?:selected |poster |oral |speaker |free paper |scientific |meeting |conference |'
        r'congress |session |symposium |invited |accepted |plenary |paper |presentation |'
        r'society |research |trainee |resident |student |fellow |young investigator |'
        r'late.breaking |encore |podium |platform |workshop |seminar |annual meeting |'
        r'supplement |published |additional |further |other |misc(?:ellaneous)? |general |'
        r'clinical |basic science |case report |video |e.?poster |mini.?oral |moderated poster |'
        r'rapid fire |top |best |award |prize )'
        r'abstracts\s*(?:$|\s*[:.,;(–—]|\s+-|\s+\d|\s+of\b|\s+from\b|\s+presented\b|'
        r'\s+accepted\b|\s+for\b|\s+submitted\b|\s+' + MON + r')'
        r'|^\s*abstracts\s+(?:of (?:the |papers|posters|presentations|communications|invited|'
        r'selected|scientific|free|oral|poster|current|recent|accepted|contributed|\d)|'
        r'from (?:the |\d|papers|around|invited|selected|speakers)|presented (?:at|to|during)\b|'
        r'accepted for\b|for (?:the |\d|presentation|poster|oral)|submitted to\b|' + MON + r')'
        r'|^\s*(?:proceedings|transactions|minutes|programme|program|reports?|summary|'
        r'summaries|highlights|papers|communications|presentations|posters|lectures|sessions|'
        r'agenda|records?|report and proceedings|proceedings and abstracts|scientific '
        r'proceedings|selected proceedings|abstracts and proceedings|abstracts and programme)'
        r' (?:of|from|for|at) (?:the )?(?:\d+(?:st|nd|rd|th) |first |second |third |fourth |'
        r'fifth |sixth |seventh |eighth |ninth |tenth |eleventh |twelfth |\d{4} |annual |'
        r'biennial |international |national |joint |spring |fall |autumn |winter |summer |'
        r'regional |european |asian |american |british |world |inaugural |combined |'
        r'scientific |general |business |plenary |mid.?year |midwinter |midsummer |'
        r'[a-z]+ annual )*(?:meeting|conference|congress|symposium|symposia|session|sessions|'
        r'colloquium|convention|assembly|scientific meeting|annual meeting|general meeting|'
        r'business meeting|joint meeting)s?(?:\s+(?:on|of|in|at|held|for)\b|\s*[,;(]|\s*$|'
        r'\s+\d|\s+' + MON + r')'
        r'|^\s*(?:meeting|meetings|conference|congress|symposium|session|plenary|annual '
        r'meeting|society meeting|poster sessions?|oral sessions?|scientific sessions?|plenary '
        r'sessions?|keynote session|business meeting|general meeting|council meeting|board '
        r'meeting)'
        r' (?:highlights?|summaries|summary|reports?|digest|round-?ups?|proceedings|minutes|'
        r'programme|program|abstracts|papers|agenda|announcements?|notices?|in brief|at a '
        r'glance|calendar|diary|news|notes|presentations?|posters?|lectures?|records?|'
        r'schedule|timetable|itinerary|information|details|registration|invitation)s?\s*'
        r'(?:$|\s*[:.,;(–—]|\s+-|\s+\d|\s+of\b|\s+from\b|\s+on\b|\s+at\b|\s+for\b|\s+in\b|'
        r'\s+and\b|\s+' + MON + r')'
        r'|^\s*(?:meeting|conference|congress|symposium|session) overview\s*$'
        # [A3] 'Highlights of/from the X': 100자 안에 학회·호 어휘가 있을 때만
        r'|^\s*' + cw('highlights') + r'\s*(?:$|\s*[:.;(]|\s+[-–]|\s+\d|\s+in this\b|\s+this\b|'
        r'\s+(?:of|from|in)\s+(?:the |this |our )?[^:;]{0,100}?\b' + VENUE + r')'
        r'|^\s*(?:the )?(?:\d+(?:st|nd|rd|th) |first |second |third |fourth |fifth |sixth |'
        r'seventh |eighth |ninth |tenth |\d{4} |annual |biennial |international |national |'
        r'joint |spring |fall |autumn |winter |summer |regional |european |asian |american |'
        r'british |world |inaugural |combined |scientific |general |business |plenary |'
        r'mid.?year )*(?:annual|scientific|general|business|plenary|joint|spring|fall|autumn|'
        r'winter|summer|international|national|regional|biennial|inaugural|combined|'
        r'mid.?year)\s+(?:meeting|conference|congress|symposium|assembly|convention|session)s?'
        r'\s*(?:$|\s*[:.,;(–—]|\s+-|\s+\d|\s+of the\b|\s+of\b|\s+in\b|\s+at\b|\s+programme\b|'
        r'\s+program\b|\s+abstracts\b|\s+report\b|\s+highlights\b|\s+proceedings\b|'
        r'\s+announcement\b|\s+notice\b|\s+' + MON + r')'
        # [A3] 'Programme of/for the X' 는 숫자·학회 어휘 직결형만
        r'|^\s*(?:scientific |final |preliminary |conference |meeting |congress |symposium |'
        r'workshop |seminar |course |annual meeting |technical |educational |social |advance |'
        r'detailed |full |complete |daily |printed )?programme?\s*'
        r'(?:$|\s*[:.,;(–—]|\s+-|\s+\d|\s+(?:of|for)\s+(?:the )?(?:\d|(?:[a-z]+ ){0,3}(?:meeting|'
        r'conference|congress|symposium|session|workshop|course|seminar|colloquium)s?\b)|'
        r'\s+and abstracts\b|\s+at a glance\b|\s+overview\b|\s+schedule\b|\s+committee\b|\s+book\b)'),
    # 증례 기록·퀴즈: v3 그대로 [C] 포함
    'case_record': V3['case_record'],
    # 추모·헌사·회장 연설·감사 [A1]·[A5]
    'tribute_address': (
        r'^\s*(?:a |the |an )?' + cw('tribute', 'tributes') + r'\s*(?:$|\s*[:.;(]|\s+[-–]|\s+to\b|'
        r'\s+for\b|\s+in memory\b|\s+in honou?r\b)'
        r'|^\s*in memoriam\b|^\s*in memory of\b|^\s*in remembrance\b|^\s*in honou?r of\b'
        r'|^\s*(?:a |the )?notes? of (?:thanks|appreciation|gratitude|welcome|farewell|apology)\b'
        r'|^\s*(?:an |a )?' + cw('appreciation', 'appreciations') + r'\s*(?:$|\s*[:;(]|\s+[-–]|\s+to\b|'
        r'\s+of (?:dr\.?|prof\.?|professor|mr\.?|mrs\.?|ms\.?|sir|dame|the late|his|her)\b)'
        r'|^\s*(?:a |an )?eulog(?:y|ies)\s*(?:$|\s*[:;(]|\s+[-–]|\s+to\b|\s+of\b)'
        r'|^\s*(?:a |the )?(?:remembrances?|memorial (?:tribute|note|notice|minute)s?|'
        r'necrolog(?:y|ies)|death notices?|valedictions?|homages?|salutes?|laudatio|'
        r'laudations?|encomi(?:um|a)|panegyrics?|festschrift(?:en)?|gedenkschrift)\s*'
        r'(?:$|\s*[:.;(]|\s+[-–]|\s+to\b|\s+for\b|\s+of\b|\s+on\b|\s+in\b|\s+from\b|\s+by\b|'
        r'\s+\d|\s+dr\b|\s+prof|\s+mr\b|\s+mrs\b|\s+ms\b|\s+sir\b|\s+professor\b|\s+the\b|'
        r'\s+our\b|\s+a\b|\s+an\b)'
        r'|^\s*(?:a |the )?farewells?\s*(?:$|\s*[:;(]|\s+[-–]|\s+from\b|\s+to (?:the editors?|'
        r'our readers|readers|dr\.?|prof\.?|professor|mr\.?|mrs\.?|ms\.?|sir|dame|a friend|an? '
        r'(?:colleague|friend|mentor|editor))\b|\s+address\b|\s+message\b|\s+remarks\b)'
        # [A5] 'Thanks to <주제>' 제외: 역할 명사 직결형만
        r'|^\s*(?:thank you|thanks)\s*(?:$|\s*[:;(]|\s+[-–]|\s+to\s+(?:[\w’\'&.-]+\s+){0,4}'
        r'(?:reviewers|referees|peer reviewers|editors|contributors|'
        r'authors|sponsors|donors|readers|members|volunteers|colleagues|supporters|editorial '
        r'board|board|guest editors|associate editors|panel|committee)\b|\s+reviewers\b|'
        r'\s+referees\b)'
        # [A5] 'Acknowledgment of <주제>' 제외: reviewers/support 류 직결형만, 콜론 직결 제거
        r'|^\s*(?:a |the |an )?' + cw('acknowledgment', 'acknowledgments', 'acknowledgement',
                                        'acknowledgements')
        + r'\s*(?:$|\s*[;(]|\s+[-–]|\s+to\b|\s+for\s+(?:volume|vol|\d|the year|reviewers|referees|'
        r'support|funding|assistance|help)\b|\s+of\s+(?:priority|prior work|related prior work)\b|'
        r'\s+of\s+(?:our |the |all |principal |ad hoc |'
        r'manuscript |guest |external |peer |and |\d{4} |volume \d+ )*(?:reviewers|referees|'
        r'support|funding|sponsors|donors|contributors|assistance|help|editors|editorial board|'
        r'guest editors|financial support|grants?|sources)\b|\s+from\b|\s+\d|\s+dr\b|\s+prof|'
        r'\s+mr\b|\s+mrs\b|\s+ms\b|\s+sir\b|\s+professor\b)'
        r'|^\s*(?:congratulations|felicitations|birthday (?:greetings|tributes?)|anniversary '
        r'tributes?)\s*(?:$|\s*[:.;(]|\s+[-–]|\s+to\b|\s+for\b|\s+on\b|\s+from\b|\s+\d|\s+dr\b|'
        r'\s+prof|\s+mr\b|\s+mrs\b|\s+ms\b|\s+sir\b|\s+professor\b)'
        r'|^\s*(?:a |the )?(?:presidential|president[’\']?s|presidents[’\']?|chairman[’\']?s|'
        r'chair[’\']?s|chairperson[’\']?s|chairwoman[’\']?s|inaugural|opening|closing|'
        r'valedictory|welcome|welcoming|acceptance|banquet|commencement|retiring|retirement|'
        r'introductory|after.dinner|luncheon|dinner|convocation|graduation|installation|'
        r'induction|founders?[’\']?|centennial|centenary|jubilee|dean[’\']?s|director[’\']?s|'
        r'principal[’\']?s|rector[’\']?s|provost[’\']?s|chancellor[’\']?s|governor[’\']?s|'
        r'mayor[’\']?s|minister[’\']?s|secretary[’\']?s|treasurer[’\']?s|master[’\']?s|'
        r'warden[’\']?s|orator[’\']?s|lord mayor[’\']?s|recipient[’\']?s|awardee[’\']?s|'
        r'laureate[’\']?s|honoree[’\']?s|outgoing president[’\']?s|incoming president[’\']?s|'
        r'past president[’\']?s|new president[’\']?s|retiring president[’\']?s)'
        r' (?:address|addresses|remarks|speech|speeches|message|messages|oration|orations|'
        r'welcome|welcomes|greetings?|letters?|column|report|page|corner|forum|statement|'
        r'reflections?|farewells?|valedictions?|acceptance (?:speech|remarks|address))\s*'
        r'(?:$|\s*[:.,;(–—]|\s+-|\s+\d|\s+to\b|\s+of\b|\s+at\b|\s+for\b|\s+on\b|\s+by\b|'
        r'\s+from\b|\s+and\b|\s+' + MON + r')'
        # [A5] 'Reviewers/Referees in|and <주제>' 제외: 맨몸 표제는 in·and·to·the·this 종결을 뺀다
        r'|^\s*(?:list of |our |journal |the |this year[’\']?s |\d{4} |volume \d+ |vol\.? \d+ )?'
        r'(?:reviewers|referees|peer reviewers|manuscript reviewers|guest reviewers|external '
        r'reviewers|ad hoc reviewers|reviewer panel|reviewer board|review panel)\s*'
        r'(?:$|\s*[:.,;(–—]|\s+-|\s+\d|\s+for\b|\s+of (?:the year|volume|vol|\d|manuscripts|papers|'
        r'articles|this)\b|\s+volume\b|\s+vol\b|\s+' + MON + r')'
        r'|^\s*(?:our |journal |the |this year[’\']?s |\d{4} )?(?:reviewer acknowledge?ments?|'
        r'referee acknowledge?ments?|acknowledge?ments? (?:of|to) (?:our )?(?:reviewers|referees)|'
        r'thanks to (?:our )?(?:reviewers|referees)|thank you(?:,)? (?:to )?(?:our )?(?:reviewers|'
        r'referees)|with thanks to (?:our )?(?:reviewers|referees)|in appreciation of (?:our )?'
        r'(?:reviewers|referees)|appreciation to (?:our )?(?:reviewers|referees)|reviewer '
        r'(?:appreciation|thanks|recognition|list|index)|referee (?:appreciation|thanks|'
        r'recognition|list|index)|recognition of (?:our )?(?:reviewers|referees)|list of '
        r'(?:reviewers|referees)|index of (?:reviewers|referees)|(?:reviewers?|referees?) of the '
        r'year|top (?:reviewers|referees)|outstanding (?:reviewers|referees))\s*'
        r'(?:$|\s*[:.,;(–—]|\s+-|\s+\d|\s+for\b|\s+of\b|\s+in\b|\s+to\b|\s+and\b|\s+volume\b|'
        r'\s+vol\b|\s+the\b|\s+this\b|\s+' + MON + r')'),
    # 인터뷰·대담: v3 그대로(감사 오탐 1/40 = ChatGPT 대화 연구; 전방탐색 없이는 좁힐 수 없어 유지)
    'interview': V3['interview'],
    # 철회·정정 고지 [A1]·[A4]
    'retraction_notice': (
        # 단일어 표제(retraction·retracted·withdrawn)는 END1([A1]), 다어절 고지구는 v3 종결 집합 유지
        r'^\s*\[?(?:(?:retraction|retracted|withdrawn)\s*(?:$|\s*[:.;(\]]|\s+[-–])|'
        r'(?:retracted article|withdrawn article|expression of concern|editorial expression of concern|'
        r'notice of (?:retraction|withdrawal|duplicate publication|redundant publication|concern|'
        r'correction|erratum|corrigendum)|statement of retraction|retraction notice|retraction note|'
        r'retraction statement|notice of concern|temporary removal|temporarily removed|removal notice|'
        r'article withdrawn|paper withdrawn|manuscript withdrawn|duplicate publication|'
        r'redundant publication|retraction and republication|partial retraction|editor[’\']?s '
        r'note of concern|editorial note of concern)\s*(?:$|\s*[:.,;(\]–—]|\s+-)|'
        r'(?:retraction|retracted|retracted article|withdrawn|withdrawn article|expression of concern|'
        r'notice of (?:retraction|withdrawal|concern)|retraction notice|temporary removal|removal notice|'
        r'partial retraction)\s+(?:notice\b|to\b|for\b|note\b|statement\b|article\b|paper\b|'
        r'manuscript\b|'
        # [A4] 'Retraction of X': 콜론·인용부호·문헌 명사·숫자·권호 표기 직결형만
        r'of\s*(?::|' + Q + r'|the (?:article|articles|paper|papers|publication|manuscript|report|'
        r'letter|study|abstract|review|editorial|case report|following|above|preceding)\b|\d|'
        r'(?:volume|vol)\b|[^:;]{0,150}(?:,\s*(?:vol|volume)\b|\bvol\.?\s*\d|\bpp\.\s*\d|'
        r'\bcytologia\b))))'
        r'|^\s*withdrawal\s*(?:$|\s*[:]|\s+[-–]|\s+notice\b|\s+of (?:the )?(?:article|paper|'
        r'manuscript|publication|abstract)\b)'
        r'|^\s*(?:publisher|author|authors|editorial|editor[’\']?s|editors[’\']?|journal|'
        r'publisher[’\']?s|editorial office|production|typesetting|printing)\s*'
        r'(?:corrections?|erratum|errata|corrigendum|corrigenda|apolog(?:y|ies)|'
        r'clarifications?|amendments?)\s*(?:$|\s*[:"“‘«\'(–—]|\s+-|\s+to\b|\s+for\b|\s+of\b|'
        r'\s+on\b|\s+regarding\b|\s+concerning\b)'
        # [A4] correction to/for/of: 문헌 명사는 그대로, figure/table/equation/volume/page/number 는 숫자
        # 직결, 저널 약칭은 숫자·괄호·대문자 직결일 때만("Correction for volume of precipitate" 제외)
        r'|^\s*(?:corrections?|erratum|errata|corrigendum|corrigenda|clarifications?|'
        r'amendments?|addend(?:um|a))\s+(?:to|for|in|of|on|regarding|concerning|re)\s+'
        r'(?:the )?(?:article|articles|paper|papers|report|reports|letter|letters|abstract|'
        r'abstracts|title|titles|author|authors|authorship|affiliation|affiliations|reference|'
        r'references|citation|citations|acknowledg[a-z]*|funding|supplement|supplementary|'
        r'appendix|legend|legends|caption|captions)\b'
        r'|^\s*(?:corrections?|erratum|errata|corrigendum|corrigenda|clarifications?|'
        r'amendments?|addend(?:um|a))\s+(?:to|for|in|of|on|regarding|concerning|re)\s+'
        r'(?:the )?(?:(?:figure|figures|fig|table|tables|equation|equations|eq|page|pages|volume|'
        r'vol|issue|number|no)\.?\s*\(?\s*(?:\d|[ivxl]+\b)|(?:figure|figures|fig|table|tables|'
        r'equation|equations|eq)s?\s*[:.])'
        r'|^\s*(?:corrections?|erratum|errata|corrigendum|corrigenda|clarifications?|'
        r'amendments?|addend(?:um|a))\s+(?:to|for|in|of|on|regarding|concerning|re)\s+'
        r'(?:the )?(?:(?:lancet|bmj|jama|nejm|plos|journal|proceedings|proc|annals|archives)\b|j\.|'
        r'(?:nature|science|cell|ann|arch|am|br|eur|int|clin)\b\s*(?:\d|[(:,;.]|' + CAP + r'))'
        r'|^\s*(?:corrections?|erratum|errata|corrigendum|corrigenda|clarifications?|'
        r'amendments?|addend(?:um|a))\s+(?:to|for|in|of|on|regarding|concerning|re)\s+'
        r'(?:\d|"|“|‘|«|\')'
        r'|^\s*(?:corrections?|erratum|errata|corrigendum|corrigenda)\s+(?:published|'
        r'appearing|printed|issued|(?:for|to|in) (?:volume|vol\.?)\s*(?:\d|[ivxl]+\b)|volume\s*\d|'
        r'vol\.?\s*\d|\d)'),
    # [B6] 서평(신설)
    'book_review_of': (
        # 'Review of: X' / 'Review of “X”'(닫는 인용부호 뒤 종결·저자 표지 필수)
        r'^\s*(?:a |an )?(?:book |brief |critical |extended |short )?review of\s*:\s*\S'
        r'|^\s*(?:a |an )?(?:book |brief |critical |extended |short )?review of\s*'
        r'(?:["“]' + CAP + r'[^"“”]{3,200}["”]|[‘\']' + CAP + r'[^‘’\']{3,200}[’\']|«' + CAP
        + r'[^«»]{3,200}»)\s*(?:$|[,.;(]|\s+(?:by|edited|eds?|and|\d{4})\b)'
        # 'Review of <책> by <이름>': by 앞 낱말이 분사(-ed)가 아니고, 이름 뒤가 종결·공저·연도·출판사
        r'|^\s*(?:a |an )?(?:book |brief |critical |extended |short )?review of\s+' + CAP
        + r'[^"“”]{0,200}?' + PREV_OK + r'\s+by\s+' + HON + r'(?-i:' + NAME + NAMEX + r'{1,2})'
        + NAME_END
        # 'Review(s): … <출판 표지>' / 'Review of … <출판 표지>'
        + r'|^\s*(?:book )?reviews?\s*:.{0,250}' + PUB
        + r'|^\s*(?:a |an )?(?:book )?review of\s.{0,250}' + PUB
        # 'Review: <이니셜 포함 저자>, <책>'
        + r'|^\s*reviews?\s*:\s*' + HON + r'(?-i:' + NAMEI + r')\s*,\s*' + CAP),
    # [B7] 이름형 논평·회신(신설)
    'named_reply': (
        # 'Commentary/Comment(s)/Response/Reply/Rejoinder/Critique by <대문자 이름>'(정관사 the 제외)
        r'^\s*(?:a |an |brief |short |further |invited )?(?:commentary|commentaries|comments?|'
        r'responses?|repl(?:y|ies)|rejoinders?|critiques?)\s+by\s+' + HON + r'(?-i:' + NAME + NAMEX
        + r'{0,5})(?:\s*$|\s*[,.:;/(]|\s+(?:and|&|et\s+al|to|on|regarding|re)\b|[’\']s\b)'
        # 'X to|on <이름> et al' / '<이름> (2019)' / '<이름> 2019'
        r'|^\s*' + RP_HEAD + r'\s+(?:to|on)\s+' + HON + r'(?-i:' + NAME + NAMEX + r'{0,3})'
        r'(?:\s+et\s+al\b|\s*\(\d{4}|\s+\d{4}\b)'
        # 'X to|on <성 하나 또는 이니셜 포함>,'
        r'|^\s*' + RP_HEAD + r'\s+(?:to|on)\s+' + HON + r'(?-i:' + NAME + r'|' + NAMEI + r')\s*,'
        # 'X to|on <성> and <성>' + 종결(각 변에 성 하나 또는 이니셜 포함만; 'Complementary and Alternative
        # Medicine in Europe'·'Economic Integration and Network Trade' 제외)
        r'|^\s*' + RP_HEAD + r'\s+(?:to|on)\s+' + HON + r'(?-i:(?:' + NAME + r'|' + NAMEI + r'))'
        r'(?:\s*,\s*' + HON + r'(?-i:(?:' + NAME + r'|' + NAMEI + r')))*,?\s+(?:and|&)\s+' + HON
        + r'(?-i:(?:' + NAME + r'|' + NAMEI + r'))(?:\s*$|\s*[,:;(’\']|\s+et\s+al\b|\s+\d{4}\b)'
        # 'X to|on <이름>'s <comment 류>'
        r'|^\s*' + RP_HEAD + r'\s+(?:to|on)\s+' + HON + r'(?-i:' + NAME + NAMEX + r'{0,3})[’\']s?'
        r'(?:\s*\(\d{4}\))?\s+' + RP_TAIL_NOUN + r'\b'
        # 'Reply/Rejoinder to <이름>$'(1~4어절) — 'Response to <성 하나>$' — 'Response to <경칭·이니셜 이름>$'
        # — 'Response to <이름> Review/Letter/Paper$'. 'Comment(s) on <한 낱말>$'(30% 오탐)은 넣지 않는다.
        r'|^\s*(?:a |an |brief |short |further |our |authors?[’\']?s? )?(?:repl(?:y|ies)|rejoinders?)'
        r'\s+to\s+' + HON + r'(?-i:' + NAME + NAMEX + r'{0,3})\s*$'
        r'|^\s*(?:a |an |brief |short |further |our |authors?[’\']?s? )?responses?\s+to\s+' + HON
        + r'(?-i:' + NAME + r')\s*$'
        r'|^\s*(?:a |an |brief |short |further |our |authors?[’\']?s? )?responses?\s+to\s+'
        r'(?:(?:drs?\.?|profs?\.?|professor|mr\.?|mrs\.?|ms\.?|sir|dame)\s+(?-i:' + NAME + NAMEX
        + r'{0,3})|(?-i:' + NAMEI + r'))\s*$'
        r'|^\s*(?:a |an |brief |short |further |our |authors?[’\']?s? )?responses?\s+to\s+' + HON
        + r'(?-i:' + NAME + NAMEX + r'{0,2})\s+(?:review|letter|paper|commentary|critique|comments?|'
        r'rejoinder|article|essay)\s*$'),
}

# ── 2차 판정 하위 형태(v3.1 적중 안에서 오탐률 >5% 로 실측·추정된 형태) ─────────────────────
# (유형, 이름, 정규식, 선정 이유). 정규식은 (?i) 접두 없이 적고 실행 때 붙인다.
SUBFORMS = [
    ('news', 'issues_colon',
     r'^\s*(?:clinical|current|topical|professional|practice|policy|regulatory|legal|ethical|'
     r'legislative) issues\s*[:;]\s*\S',
     "'<형용사> Issues: <주제>' 콜론형(쉼표형은 [A2] 로 제외). 잔여 표본 40건에 'Professional Issues: Alcohol Abuse "
     "and College Counseling: An Overview of Research and Practice'·'Current Issues: Pediatric Pelvic Fractures' 같은 "
     "리뷰·연구 제목이 2건 이상(≥5%) 섞이고, 나머지도 ASHA Perspectives 의 실무 논문 난이라 모델 판정이 필요하다."),
    ('news', 'column_colon',
     r'^\s*' + NEWS_HEADS + r' (?:round-?ups?|watch|scan|scans|briefing|alerts?|monitor|corner|'
     r'snippets)\s*[:.;(–—]\s*\S',
     "'<난 표제> watch/roundup/scan/corner/briefing/alerts/monitor/snippets: <주제>'. 감사의 update_colon_topic 30% "
     "오탐 가운데 selection·summaries·abstracts 는 [A2] 로 제외했으나, 잔여 표본 40건에 'Practice Briefing: Mergers and "
     "Acquisitions …'·'Technology Corner: Brute Force Password Generation' 같은 실무·튜토리얼 논문이 2~3건(5~8%) 남는다."),
    ('news', 'update_residual',
     r'^\s*' + NEWS_HEADS + r' (?:updates?|digest|briefs?|highlights|selections?|summaries|'
     r'abstracts|abstracted)\s*[:;–—]\s*' + COL_MARK,
     "'<난 표제> update/highlights/digest: (the) latest/recent/monthly/<월> …' — [A2] 로 콜론 직결형을 제외한 뒤 난 표지가 "
     "있을 때만 남긴 잔여(지시의 예시 항목). 표본 40건에 'Research Update: Recent progress in …'(APL Materials 심사 "
     "논문) 2건(5%)이 'recent' 표지로 남는다."),
    ('abstracts_meeting', 'highlights_of_venue',
     r'^\s*highlights\s*(?:[:;]\s*\S|\s+(?:of|from|in)\s+(?:the |this |our )?[^:;]{0,100}?\b(?:meeting|'
     r'conference|symposium|congress|proceedings|abstracts|session|workshop|summit|assembly|convention|'
     r'seminar)s?\b)',
     "'Highlights of/from the <X … meeting/conference/session>' 및 'Highlights: <주제>'. 감사에서 17% 오탐(실험 결과 "
     "보고)이었고 [A3] 로 학회·호 어휘 직결형만 남겼다. 잔여 표본 40건 오탐 0건이나 어휘 휴리스틱이라 'Highlights from "
     "<실험> at the <conference>' 형 물리 발표 논문이 남을 수 있어(지시의 예시 항목) 학회형만 보낸다. 호(issue)·권(volume) "
     "표제형('Highlights from this issue')은 오탐 구조가 없어 뺐다."),
    ('letter', 'letter_colon_topic',
     r'^\s*(?:clinical |readers?[’\']?s? |selected |brief |short )?(?:letters?|correspondence)\s*[:.(]\s*\S',
     "'Letter: <제목>'·'Correspondence: <제목>'. 감사 1/20 오탐 + 경계 3/20 이었고, 이번 표본 40건에서는 물리·IEEE·"
     "분석화학·임상의 짧은 연구 논문(Letter 장르: 'Letter: Predictors of ST-Segment Resolution …'·'LETTER: Cosmological "
     "Constant, …')이 약 15건(37%) 섞였다. v3 와 같은 형태라 정규식으로는 가를 수 없다."),
    ('book_review_of', 'review_of_by_name',
     r'^\s*(?:a |an )?(?:book |brief |critical |extended |short )?review of\s+' + CAP
     + r'[^"“”]{0,200}?' + PREV_OK + r'\s+by\s+' + HON + r'(?-i:' + NAME + NAMEX + r'{1,2})' + NAME_END,
     "'Review of <책> by <이름>'(출판 표지·인용부호 없는 형태). 분사(-ed) 제외·이름 어절 제한 뒤에도 표본 40건에 'A Review "
     "of Ground-Based Remote Sensing … by Passive Microwave Radiometers'·'A Critical Review of Clinical Practice "
     "Guidelines … for Use by Primary Care Practitioners' 2건(5%)이 남는다."),
    ('named_reply', 'response_to_name_end',
     r'^\s*(?:a |an |brief |short |further |our |authors?[’\']?s? )?responses?\s+to\s+' + HON
     + r'(?-i:' + NAME + NAMEX + r'{0,3})\s*$',
     "'Response(s) to <이름>$'. 두 낱말 이상형은 12.5% 오탐('Response to Air Pollution')이라 경칭·이니셜·꼬리 명사형으로 "
     "좁혔고, 남은 성 하나형 표본 40건에도 'Response to Diversity'·'Response to Questions' 같은 개념명 2건(5%)이 섞인다."),
]
# 2차 판정에서 뺀 후보(실측 근거): named_reply/by_name 은 정관사 the 형·'in' 종결을 제외한 뒤 표본 40건 오탐 0,
# named_reply/to_on_and_form('Reply to X and Y') 은 40건 중 1건(2.5%), book_review_of 의 인용부호·출판 표지형은 0건.

AUDIT_BATCHES = [
    ['commentary', 'reply', 'letter', 'editor_note', 'books_received'],
    ['bibliography', 'news', 'index_toc', 'abstracts_meeting', 'case_record'],
    ['tribute_address', 'interview', 'retraction_notice', 'book_review_of', 'named_reply'],
]


def compile_all(pats):
    return {k: re.compile('(?i)' + v) for k, v in pats.items()}


def sql_pat(p):
    return ('(?i)' + p).replace("'", "''")


def con():
    c = duckdb.connect()
    c.execute('SET threads=32')
    return c


def scan():
    """전수 서지에 v3·v3.1 을 나란히 적용해 적중 문헌을 남긴다."""
    compile_all(PATTERNS)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(f'{OUT_DIR}/genre_patterns_v31.json', 'w') as f:
        json.dump(PATTERNS, f, ensure_ascii=False, indent=1)
    c = con()
    v2 = sql_pat(L.JUNK.pattern[4:])
    c3 = ',\n'.join(f"regexp_matches(t, '{sql_pat(p)}') as \"v3_{k}\"" for k, p in V3.items())
    c31 = ',\n'.join(f"regexp_matches(t, '{sql_pat(p)}') as \"v31_{k}\"" for k, p in PATTERNS.items())
    any3 = ' or '.join(f'"v3_{k}"' for k in V3)
    any31 = ' or '.join(f'"v31_{k}"' for k in PATTERNS)
    l3 = ', '.join(f"case when \"v3_{k}\" then '{k}' end" for k in V3)
    l31 = ', '.join(f"case when \"v31_{k}\" then '{k}' end" for k in PATTERNS)
    t0 = time.time()
    c.execute(f"""
      copy (
        with b as (select work_id, coalesce(title_display,'') t from '{L.BIB_STORE}'),
        f as (select work_id, t, regexp_matches(t, '{v2}') v2_hit, {c3}, {c31} from b),
        h as (select * from f where ({any3}) or ({any31}))
        select h.work_id, substr(h.t,1,200) title_head, h.v2_hit,
               (r.work_id is not null) retracted,
               list_filter([{l3}], x -> x is not null) types_v3,
               list_filter([{l31}], x -> x is not null) types_v31,
               m.effective_nano_id nano_id
        from h
        left join (select work_id from '{L.EXCLUSION_FLAGS}' where reason='retracted') r using(work_id)
        left join '{MEM}' m using(work_id)
      ) to '{HITS}' (format parquet)
    """)
    print(f'{HITS} 작성 {time.time() - t0:,.0f}s')


def count():
    """유형별 v3·v3.1 건수(v2 미적중·철회 제외), 제거·추가, 합집합 신규 정크."""
    c = con()
    rows = []
    for k in PATTERNS:
        has3 = f"list_contains(types_v3, '{k}')" if k in V3 else 'false'
        r = c.execute(f"""
          select count(*) filter (where {has3}) v3_docs,
                 count(*) filter (where list_contains(types_v31, '{k}')) v31_docs,
                 count(*) filter (where {has3} and not list_contains(types_v31, '{k}')) removed_docs,
                 count(*) filter (where list_contains(types_v31, '{k}') and not {has3}) added_docs,
                 count(distinct case when list_contains(types_v31, '{k}') then nano_id end) v31_nanos
          from '{HITS}' where not v2_hit and not retracted""").df().iloc[0].to_dict()
        rows.append({'type': k, **{a: int(b) for a, b in r.items()}})
    cnt = pd.DataFrame(rows)
    tot = c.execute(f"""
      select count(*) filter (where len(types_v3) > 0) v3_union,
             count(*) filter (where len(types_v31) > 0) v31_union,
             count(*) filter (where len(types_v31) > 0 and nano_id is not null) v31_union_member,
             count(*) filter (where len(types_v3) > 0 and len(types_v31) = 0) v3_only,
             count(*) filter (where len(types_v31) > 0 and len(types_v3) = 0) v31_only,
             count(*) filter (where len(types_v31) > 0 and list_has_any(types_v31, ['case_record','bibliography'])
                              and not list_has_any(types_v31, [{', '.join(repr(k) for k in PATTERNS if k not in ('case_record','bibliography'))}])) v31_cond_only,
             count(distinct case when len(types_v31) > 0 then nano_id end) v31_nanos
      from '{HITS}' where not v2_hit and not retracted""").df().iloc[0].to_dict()
    tot = {a: int(b) for a, b in tot.items()}
    # 참고: v2·철회를 빼기 전 원 적중 수
    raw = c.execute(f"""
      select count(*) rows_total, count(*) filter (where v2_hit) v2_hit_rows,
             count(*) filter (where retracted and not v2_hit) retracted_not_v2,
             count(*) filter (where len(types_v31) > 0 and retracted and not v2_hit) v31_retracted_not_v2
      from '{HITS}'""").df().iloc[0].to_dict()
    raw = {a: int(b) for a, b in raw.items()}
    cnt.to_parquet(f'{OUT_DIR}/genre_counts_v31.parquet', index=False)
    json.dump({'per_type': cnt.to_dict('records'), 'union': tot, 'raw': raw,
               'basis': 'v2 미적중 · #89 철회(exclusion_flags reason=retracted) 제외'},
              open(f'{OUT_DIR}/genre_counts_v31.json', 'w'), ensure_ascii=False, indent=1)
    pd.set_option('display.width', 200)
    print(cnt.to_string())
    print(tot)
    print(raw)


def second():
    """2차 판정 대상: v3.1 적중(v2 미적중·철회 제외) 가운데 SUBFORMS 에 드는 문헌 + 제목·초록 600자."""
    c = con()
    parts = []
    for typ, name, rx, why in SUBFORMS:
        re.compile('(?i)' + rx)
        parts.append(f"""
          select h.work_id, h.nano_id, '{typ}' as "type", '{name}' as subform
          from '{HITS}' h
          where not h.v2_hit and not h.retracted and list_contains(h.types_v31, '{typ}')
            and regexp_matches(h.title_head, '{sql_pat(rx)}')""")
    c.execute(f"""
      copy (
        with s as ({' union all '.join(f'({p})' for p in parts)})
        select s.work_id, s.nano_id, b.title_display title,
               substr(coalesce(b.abstract_display, ''), 1, {ABS_HEAD_2ND}) abstract_head,
               s."type", s.subform
        from s join '{L.BIB_STORE}' b using(work_id)
        order by s."type", s.subform, md5('{AUDIT_SEED}:' || s.work_id)
      ) to '{OUT_DIR}/second_pass_candidates.parquet' (format parquet)""")
    df = c.execute(f"select \"type\", subform, count(*) n, count(distinct work_id) n_docs, "
                   f"count(*) filter (where abstract_head <> '') with_abstract "
                   f"from '{OUT_DIR}/second_pass_candidates.parquet' group by 1,2 order by 1,2").df()
    n_docs = c.execute(f"select count(distinct work_id) from '{OUT_DIR}/second_pass_candidates.parquet'").fetchone()[0]
    why = {f'{t}/{n}': w for t, n, _, w in SUBFORMS}
    summary = {'n_docs': int(n_docs),
               'subforms': [{'type': r.type, 'subform': r.subform, 'n': int(r.n), 'n_docs': int(r.n_docs),
                             'with_abstract': int(r.with_abstract), 'why': why[f'{r.type}/{r.subform}']}
                            for r in df.itertuples()],
               'default': '2차 판정 전까지는 정크(제외)로 두고, 모델이 연구 논문으로 판정하면 제외가 아니라 표시로 강등한다(#122 ②).'}
    json.dump(summary, open(f'{OUT_DIR}/second_pass_subforms.json', 'w'), ensure_ascii=False, indent=1)
    print(df.to_string())
    print('n_docs', n_docs)


def audit():
    """블라인드 감사 표본: 유형별 40건(md5('v31:'||work_id) 순), 판독자 파일에는 유형·정규식을 넣지 않는다."""
    c = con()
    os.makedirs(SCRATCH, exist_ok=True)
    taken = set()
    key_rows = []
    for bi, types in enumerate(AUDIT_BATCHES):
        rows = []
        for typ in types:
            cand = c.execute(f"""
              select work_id, types_v31 from '{HITS}'
              where not v2_hit and not retracted and list_contains(types_v31, '{typ}')
              order by md5('{AUDIT_SEED}:' || work_id) limit {AUDIT_N * 3}""").df()
            picked = 0
            for r in cand.itertuples():
                if r.work_id in taken:
                    continue
                taken.add(r.work_id)
                key_rows.append({'work_id': r.work_id, 'type': typ, 'batch': bi,
                                 'types_v31_all': list(r.types_v31)})
                rows.append(r.work_id)
                picked += 1
                if picked == AUDIT_N:
                    break
            if picked < AUDIT_N:
                raise SystemExit(f'{typ}: 표본 {picked} < {AUDIT_N}')
        ids = ', '.join(repr(w) for w in rows)
        df = c.execute(f"""
          select work_id, coalesce(title_display,'') title,
                 substr(coalesce(abstract_display,''), 1, {ABS_HEAD_AUDIT}) abstract_head
          from '{L.BIB_STORE}' where work_id in ({ids})
          order by md5('{AUDIT_SEED}:' || work_id)""").df()
        assert len(df) == len(rows), (len(df), len(rows))
        path = f'{SCRATCH}/v31_audit_batch{bi}.jsonl'
        with open(path, 'w') as f:
            for r in df.itertuples():
                f.write(json.dumps({'work_id': r.work_id, 'title': r.title,
                                    'abstract_head': r.abstract_head}, ensure_ascii=False) + '\n')
        print(path, len(df))
    key = pd.DataFrame(key_rows)
    key.to_parquet(f'{OUT_DIR}/v31_audit_key.parquet', index=False)
    print(key.groupby(['batch', 'type']).size().to_string())


def selftest():
    """파이썬 re 와 DuckDB(RE2)의 판정 일치 검사: 적중 문헌 전부(원 제목) + 무작위 0.5%.
    RE2 의 \\s·\\b·\\d 는 ASCII 전용이므로 re.ASCII 로 컴파일한 판정이 정확한 대조이고, 기본(유니코드)
    판정과의 차이는 비ASCII 공백(NBSP 등) 때문이다(A.67 의 5편 차이와 같은 구조)."""
    c = con()
    rx_u = compile_all(PATTERNS)
    rx_a = {k: re.compile('(?i)' + v, re.ASCII) for k, v in PATTERNS.items()}
    hit = c.execute(f"""select h.work_id, coalesce(b.title_display,'') t, h.types_v31
                        from '{HITS}' h join '{L.BIB_STORE}' b using(work_id)""").df()
    bad_u = bad_a = 0
    for r in hit.itertuples():
        duck = set(r.types_v31)
        if {k for k, p in rx_u.items() if p.search(r.t)} != duck:
            bad_u += 1
        pa = {k for k, p in rx_a.items() if p.search(r.t)}
        if pa != duck:
            bad_a += 1
            if bad_a <= 10:
                print('MISMATCH(hit, ASCII)', r.work_id, sorted(pa), sorted(duck), repr(r.t[:100]))
    print(f'적중 {len(hit):,}건 중 불일치: 유니코드 re {bad_u:,}건 · ASCII re {bad_a:,}건')
    rnd = c.execute(f"""select work_id, coalesce(title_display,'') t from '{L.BIB_STORE}'
                        using sample 0.5% (system, 7)""").df()
    hitset = set(hit.work_id[hit.types_v31.map(len) > 0])
    bad2 = 0
    for r in rnd.itertuples():
        py = any(p.search(r.t) for p in rx_a.values())
        if py != (r.work_id in hitset):
            bad2 += 1
            if bad2 <= 10:
                print('MISMATCH(rnd, ASCII)', r.work_id, py, repr(r.t[:100]))
    print(f'무작위 {len(rnd):,}건 중 불일치(ASCII re) {bad2:,}건')
    json.dump({'hits': int(len(hit)), 'mismatch_unicode_re': int(bad_u), 'mismatch_ascii_re': int(bad_a),
               'random_n': int(len(rnd)), 'random_mismatch_ascii_re': int(bad2)},
              open(f'{OUT_DIR}/v31_selftest.json', 'w'), indent=1)


def stats():
    """보고용 부가 실측: 엠대시 제거로 잃은 건수, 신설 유형의 배타 신규분, 유형별 v3.1 배타 기여."""
    c = con()
    r = {}
    r['emdash_loss'] = c.execute(f"""
      select count(*) from '{HITS}' where not v2_hit and not retracted
        and len(types_v3) > 0 and len(types_v31) = 0
        and regexp_matches(title_head, '(?i)^\\s*(?:a |an |the |our |brief |short |further |invited |guest |authors?[’'']?s? |editors?[’'']?s? )?[a-z]+\\s*—')""").fetchone()[0]
    r['comma_loss'] = c.execute(f"""
      select count(*) from '{HITS}' where not v2_hit and not retracted
        and len(types_v3) > 0 and len(types_v31) = 0
        and regexp_matches(title_head, '(?i)^\\s*(?:a |an |the |our |brief |short |further |invited |guest |authors?[’'']?s? |editors?[’'']?s? )?[a-z]+\\s*,')""").fetchone()[0]
    r['exclusive_new_by_type'] = {k: int(v) for k, v in c.execute(f"""
      select t, count(*) from (select unnest(types_v31) t, types_v3 from '{HITS}'
                               where not v2_hit and not retracted and len(types_v3) = 0)
      group by 1 order by 1""").fetchall()}
    r['v3_only_by_type'] = {k: int(v) for k, v in c.execute(f"""
      select t, count(*) from (select unnest(types_v3) t from '{HITS}'
                               where not v2_hit and not retracted and len(types_v31) = 0)
      group by 1 order by 1""").fetchall()}
    r['v31_union_excl_conditional'] = int(c.execute(f"""
      select count(*) from '{HITS}' where not v2_hit and not retracted and len(types_v31) > 0
        and list_has_any(types_v31, [{', '.join(repr(k) for k in PATTERNS if k not in ('case_record', 'bibliography'))}])""").fetchone()[0])
    json.dump(r, open(f'{OUT_DIR}/v31_stats.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(r, ensure_ascii=False, indent=1))


def main():
    step = sys.argv[1] if len(sys.argv) > 1 else 'all'
    steps = {'scan': scan, 'count': count, 'second': second, 'audit': audit, 'selftest': selftest,
             'stats': stats}
    if step == 'all':
        for s in ('scan', 'count', 'second', 'audit', 'selftest', 'stats'):
            steps[s]()
    else:
        steps[step]()


if __name__ == '__main__':
    main()
