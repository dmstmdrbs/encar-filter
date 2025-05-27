# Encar Simple Alert

엔카(Encar) 중고차 매물 사이트에서 원하는 조건의 차량이 새로 등록되었을 때 자동으로 감지하고, 이메일로 알림을 보내주는 Python 기반 크롤러입니다.
Cursor에서 Agent모드를 이용해 작성된 코드입니다.

---

## 주요 기능

- **엔카 검색 URL 기반 매물 모니터링**
- **성능기록부 조건 필터링**
  - 교환 이력: 1건 이하 (`없음` 또는 `1건`)
  - 판금 이력: 0건 (`없음`)
  - 부식 이력: 0건 (`없음`)
- **용도이력(특이사항): '없음'만 허용**
- **조건에 맞는 차량만 별도 저장**
- **새 매물 발견 시 이메일 알림**
- **매물 중복 감지 및 저장**

---

## 폴더 구조 예시

```
financial-news/
├── encar_direct_url_simple.py
├── known_listings.json
├── good_cars.json
├── requirements.txt
└── README.md
```

---

## 설치 및 환경설정

### 1. Python 가상환경(venv) 생성 및 활성화

```bash
python3 -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
```

### 2. 필수 패키지 설치

```bash
pip install selenium
```

> (추가로 필요하다면 `requirements.txt`에 패키지 목록을 작성해두세요.)

### 3. 크롬드라이버 설치

- [크롬드라이버 다운로드](https://chromedriver.chromium.org/downloads)
- 크롬 버전에 맞는 드라이버를 받아서, 실행 파일이 PATH에 있거나,  
  `encar_direct_url_simple.py`에서 직접 경로를 지정해 주세요.

---

## 사용법

### 1. **코드 내 설정값 수정**

`encar_direct_url_simple.py`의 아래 부분을 본인 환경에 맞게 수정하세요.

```python
search_url = "엔카에서 복사한 검색 URL"
check_interval = 600  # (초 단위, 예: 600초 = 10분)
repo = CarListingRepository("known_listings.json", "good_cars.json")
crawler = EncarCrawler()
filter = CarConditionFilter()
notifier = EmailNotifier("your_email@gmail.com", "your_app_password")  # Gmail 앱 비밀번호 사용
email_to = "받을_이메일주소@gmail.com"
monitor = EncarMonitor(search_url, check_interval, repo, crawler, filter, notifier, email_to)
monitor.run()
```

- **search_url**: 엔카에서 원하는 조건으로 검색 후, 주소창의 URL 전체를 복사해서 입력
- **이메일**: Gmail을 사용하는 경우 [앱 비밀번호](https://support.google.com/accounts/answer/185833?hl=ko) 필요

---

### 2. **실행**

```bash
python encar_direct_url_simple.py
```

---

## 동작 방식

1. 지정한 엔카 검색 URL에서 매물 목록을 주기적으로 크롤링합니다.
2. 각 매물의 상세 페이지에서 성능기록부와 용도이력(특이사항)을 파싱합니다.
3. 아래 조건을 모두 만족하는 차량만 "조건에 맞는 차량"으로 분류합니다.
   - 교환 이력: 1건 이하
   - 판금 이력: 0건
   - 부식 이력: 0건
   - 특이사항(용도이력): 없음
4. 조건에 맞는 차량이 새로 발견되면 이메일로 알림을 보냅니다.
5. 이미 확인한 매물은 중복 체크하여 다시 알림하지 않습니다.

---

## 참고/유의사항

- **크롬드라이버**는 크롬 브라우저 버전과 반드시 맞아야 합니다.
- 엔카 사이트 구조가 변경되면 selector도 수정이 필요할 수 있습니다.
- Gmail 외의 메일을 사용할 경우 SMTP 설정을 직접 변경해야 합니다.
- 장시간 실행 시 크롬드라이버가 자동으로 닫히지 않으면 수동으로 프로세스를 종료해 주세요.

---

## 기여 및 문의

- 버그 제보, 기능 제안, 코드 개선 PR 환영합니다!

---

**엔카 사이트의 이용약관 및 로봇 정책을 준수해 주세요.**  
이 코드는 개인적/비상업적 용도로만 사용하시기 바랍니다.

필요에 따라 예시 코드, 환경 변수, 상세 설명 등을 추가로 넣을 수 있습니다.
추가로 원하는 항목이 있으면 말씀해 주세요!
