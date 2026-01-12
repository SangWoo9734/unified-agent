# Unified Agent 구축 완료 ✅

모든 파일이 생성되었습니다!

## 📁 생성된 구조

```
unified-agent/
├── main.py                           # ✅ 메인 실행 파일
├── requirements.txt                  # ✅ 패키지 목록 (PyYAML 추가됨)
├── README.md                         # ✅ 사용 가이드
├── BLOG_GUIDE.md                     # ✅ 블로그 작성 참고 자료
├── .env.example                      # ✅ 환경변수 템플릿
├── .gitignore                        # ✅ Git 제외 파일
│
├── config/
│   ├── products.yaml                 # ✅ 프로덕트 설정 (수정 필요)
│   └── .gitkeep
│
├── core/
│   ├── __init__.py
│   ├── collectors/                   # ✅ 기존 파일 복사됨
│   │   ├── __init__.py
│   │   ├── gsc_collector.py
│   │   ├── ga4_collector.py
│   │   ├── trends_collector.py
│   │   └── adsense_collector.py      # ✅ 신규 (AdSense 수집)
│   │
│   ├── analyzers/                    # ✅ 기존 파일 + 신규
│   │   ├── __init__.py
│   │   ├── claude_analyzer.py
│   │   ├── claude_analyzer_v2.py
│   │   └── comparative_analyzer.py   # ✅ 신규 (비교 분석)
│   │
│   └── utils/                        # ✅ 기존 파일 복사됨
│       ├── __init__.py
│       └── formatter.py
│
├── reports/                          # 리포트 저장 위치
│   ├── .gitkeep
│   ├── qr-generator/
│   ├── convert-image/
│   └── comparison/                   # 통합 리포트
│
└── logs/                             # 로그 저장
    └── .gitkeep
```

## ✅ 완료된 작업

1. ✅ 폴더 구조 생성
2. ✅ 기존 코드 복사 (convert-image/agent에서)
3. ✅ 신규 파일 작성:
   - `comparative_analyzer.py` - 프로덕트 비교 분석
   - `adsense_collector.py` - AdSense 데이터 수집
   - `main.py` - Orchestrator
   - `products.yaml` - 프로덕트 설정
4. ✅ 문서 작성:
   - `README.md` - 사용 가이드
   - `BLOG_GUIDE.md` - 블로그 작성 참고
5. ✅ 환경 설정:
   - `requirements.txt` 업데이트 (PyYAML 추가)
   - `.env.example` 작성
   - `.gitignore` 작성

## 🚀 다음 단계

### 1. 환경 설정 (5분)

```bash
cd unified-agent

# 가상환경 생성
python3 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. Google 인증 파일 복사 (1분)

```bash
# 기존 파일 복사
cp ../convert-image/agent/config/gsc_credentials.json config/
```

### 3. products.yaml 설정 (5분)

`config/products.yaml` 파일을 열어서 다음 값을 실제 값으로 변경:

```yaml
qr-generator:
  gsc_property_url: "REPLACE_WITH_YOUR_QR_GENERATOR_DOMAIN"  # ← 변경 필요
  ga4_property_id: "REPLACE_WITH_GA4_PROPERTY_ID"            # ← 변경 필요

convert-image:
  ga4_property_id: "REPLACE_WITH_GA4_PROPERTY_ID"            # ← 변경 필요
```

**확인 필요:**
- QR Generator의 Google Search Console에 서비스 계정 권한 추가됐는지
- QR Generator의 GA4에 서비스 계정 권한 추가됐는지

### 4. 환경변수 설정 (2분)

```bash
cp .env.example .env
```

`.env` 파일 편집:
```env
ANTHROPIC_API_KEY=sk-ant-xxxxx  # 실제 API 키

# AdSense (선택사항 - QR Generator 데이터)
ADSENSE_REVENUE=18.50
ADSENSE_IMPRESSIONS=12450
ADSENSE_CLICKS=89
```

### 5. 첫 실행! (1분)

```bash
python main.py
```

예상 출력:
```
🚀 Unified Multi-Product Agent 시작
📦 발견된 프로덕트: 2개
   - QR Studio (qr-generator)
   - ConvertKits (convert-image)

📊 QR Studio (qr-generator) 데이터 수집 중...
  🔍 GSC 데이터 수집...
     ✓ 1,234개 검색어 수집 완료
  📈 GA4 데이터 수집...
     ✓ GA4 데이터 수집 완료
  ...

🤖 Claude AI 통합 비교 분석 중...

✨ 분석 완료!
📄 통합 리포트: reports/comparison/2026-01-11_multi_product_analysis.md
```

### 6. 리포트 확인

생성된 파일 열기:
```bash
cat reports/comparison/2026-01-11_multi_product_analysis.md
```

## 📊 핵심 파일 설명

### main.py
- 전체 프로세스 조율
- 각 프로덕트 데이터 수집
- Claude 분석 요청
- 리포트 저장

### comparative_analyzer.py
- **가장 중요한 파일**
- 여러 프로덕트를 비교 분석
- 리소스 배분 추천 생성
- Claude에게 보낼 프롬프트 구성

### products.yaml
- 프로덕트별 설정 중앙 관리
- 우선순위, AdSense 여부 등 정의

### adsense_collector.py
- AdSense 데이터 수집
- 현재는 환경변수에서 읽음
- 향후 API 통합 가능

## 🎯 블로그 작성할 때

`BLOG_GUIDE.md` 파일을 참고하세요!

**핵심 내용:**
- 문제 정의: 두 프로덕트, 어디에 리소스 집중?
- 설계 과정: 왜 모노레포가 아닌가?
- 구현: comparative_analyzer.py 중심으로
- 결과: 데이터 기반 의사결정 자동화

**포함하면 좋은 것:**
- `products.yaml` 설정 예시
- Claude 프롬프트 구조
- 생성된 리포트 스니펫
- Before/After 비교

## ⚠️ 주의사항

1. **실행 전 반드시:**
   - `config/products.yaml`의 REPLACE 값들 변경
   - Google 인증 파일 (`gsc_credentials.json`) 확인
   - `.env` 파일 생성 및 API 키 입력

2. **QR Generator 설정:**
   - Search Console에 서비스 계정 권한 추가
   - GA4에 서비스 계정 권한 추가
   - 도메인 확인

3. **AdSense 데이터:**
   - 선택사항 (없어도 실행 가능)
   - 환경변수로 수동 입력
   - 향후 API 통합 가능

## 💡 다음 개선 사항 (선택)

- [ ] AdSense Management API 통합
- [ ] Slack 알림 추가
- [ ] Cron 자동화 설정
- [ ] 개별 프로덕트 상세 리포트 생성
- [ ] 시계열 데이터 추적 (주간 비교)

## 🤝 도움이 필요하면

- `README.md` - 전체 가이드
- `BLOG_GUIDE.md` - 블로그 작성 참고
- 각 Python 파일의 docstring 참고

---

**준비 완료!** 🎉

이제 설정만 하면 바로 실행할 수 있습니다.
