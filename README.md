# WhatShouldIDo

WhatShouldIDo는 취향, 현재 상황, 날씨, 트렌드를 함께 반영해 하루의 선택을 추천하는 Flask 기반 라이프스타일 대시보드입니다. 음식, 패션, 콘텐츠, 활동 추천을 각각 따로 분리하지 않고 하나의 사용자 프로필과 행동 피드백 위에서 연결합니다.

## 현재 구현 범위

- 음식 추천
- 패션 추천
- 콘텐츠 추천
  - 현재 사용자 노출 기준 스코프: 영화, 시리즈
  - 웹툰은 현재 추천 범위에서 제외
- 활동 추천
- MBTI + 심리 설문 기반 성향 보정
- 추천 히스토리 저장
- 트렌드 보드 / VS 퀴즈

## 기술 스택

- Flask
- Jinja2
- Bootstrap 5
- jQuery / AJAX
- MongoDB
- Gunicorn

## 주요 기능

### 1. 계정 및 프로필

- 회원가입 / 로그인 / 로그아웃
- 음식 / 패션 / 콘텐츠 / 활동 취향 저장
- MBTI와 심리 설문 결과 저장

### 2. 콘텐츠 추천

- Netflix Tudum South Korea Movies Top 10 반영
- KOBIS 주간 박스오피스 반영
- TMDB 주간 트렌딩 영화 / 시리즈 반영
- 좋아요 / 싫어요 피드백 누적 학습
- 현재 검색 가능한 데이터만 기준으로 장르 / 플랫폼 선택
- 웹툰 제외

### 3. 대시보드와 부가 기능

- 메인 대시보드에서 4개 카테고리 추천 요약
- 최근 추천 히스토리 조회
- 트렌드 키워드 보드
- VS 퀴즈 투표

## 프로젝트 구조

```text
lifestyle-app/
├── app.py
├── config.py
├── render.yaml
├── requirements.txt
├── db/
│   └── mongo.py
├── routes/
│   ├── auth.py
│   ├── main.py
│   ├── profile.py
│   └── recommendations.py
├── services/
│   ├── account.py
│   ├── catalog.py
│   ├── content_feedback.py
│   ├── content_sources.py
│   ├── history.py
│   ├── movie_images.py
│   ├── personality.py
│   ├── profile_service.py
│   ├── recommender.py
│   ├── trends.py
│   └── weather.py
├── static/
│   ├── css/style.css
│   └── js/app.js
├── templates/
│   ├── auth/
│   ├── components/
│   └── recommendations/
├── seed/
│   └── sample_seed.py
└── docs/
```

## 실행 방법

### 1. 가상환경 및 의존성 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp .env.example .env
```

기본적으로 아래 값을 사용합니다.

```env
SECRET_KEY=whatshouldi-dev-secret
FLASK_DEBUG=true
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=whatshouldi
USE_MOCK_ON_FAILURE=true
DEFAULT_CITY=Seoul
DEFAULT_REGION=KR
KOBIS_API_KEY=...
TMDB_API_KEY=...
```

### 3. MongoDB 준비

로컬 MongoDB 예시:

```bash
brew services start mongodb-community
```

Docker 예시:

```bash
docker run -d --name whatshouldi-mongo -p 27017:27017 mongo:7
```

MongoDB가 없어도 `USE_MOCK_ON_FAILURE=true`면 데모용 mock DB로 실행됩니다.

### 4. 시드 데이터

```bash
python seed/sample_seed.py
```

데모 계정까지 만들려면:

```bash
python seed/sample_seed.py --with-demo-user
```

데모 계정:

- Email: `demo@whatshouldi.local`
- Password: `demo1234`

### 5. 앱 실행

```bash
python app.py
```

브라우저에서 `http://localhost:5000` 접속

배포용 실행 예시:

```bash
gunicorn app:app
```

## 환경변수

| 변수 | 설명 | 기본값 |
| --- | --- | --- |
| `SECRET_KEY` | Flask 세션 키 | `whatshouldi-dev-secret` |
| `FLASK_DEBUG` | 디버그 모드 | `true` |
| `FLASK_HOST` | 바인드 주소 | `0.0.0.0` |
| `FLASK_PORT` | 포트 | `5000` |
| `MONGO_URI` | MongoDB URI | `mongodb://localhost:27017/` |
| `MONGO_DB_NAME` | MongoDB DB 이름 | `whatshouldi` |
| `USE_MOCK_ON_FAILURE` | Mongo 연결 실패 시 mock DB 사용 | `true` |
| `DEFAULT_CITY` | 기본 도시 | `Seoul` |
| `DEFAULT_REGION` | 기본 지역 코드 | `KR` |
| `KOBIS_API_KEY` | KOBIS API 키 | 코드 기본값 존재 |
| `TMDB_API_KEY` | TMDB API 키 | 코드 기본값 존재 |

## 데이터 저장 구조

- `users`
  - 계정 정보
- `profiles`
  - 카테고리별 취향과 심리 성향
- `recommendation_history`
  - 추천 요청 스냅샷과 결과
- `content_feedback`
  - 콘텐츠 좋아요 / 싫어요 피드백
- `trend_cache`
  - 트렌드 캐시
- `quiz_logs`
  - VS 퀴즈 응답 로그
- `content_source_cache`
  - Netflix / KOBIS / TMDB 캐시

## 추천 방식 요약

- 음식: 취향 + 시간대 + 기분 + 매운맛 선호
- 패션: 날씨 + 온도 + 스타일 + 컬러
- 콘텐츠: 장르 + 플랫폼/형식 + 무드 + 피드백 + 인기 흐름
- 활동: 실내외 + 에너지 + 사회성 + 예산 + 날씨

콘텐츠 추천은 현재 검색 가능한 작품 목록에서만 장르와 플랫폼 옵션을 노출합니다.

## 테스트 및 검증

AI로 빠르게 구현한 코드라도, 실제 데모와 제출에서는 반드시 회귀 검증이 필요합니다. 이 프로젝트는 로컬 MongoDB가 없어도 `mongomock` 기반으로 테스트가 재현되도록 구성했고, 인증 흐름, 추천 로직, 저장 동작, 사용자 입력 필터링까지 자동 검증합니다.

### 테스트 실행 명령

```bash
PYTHONPYCACHEPREFIX=/tmp/whatshouldido-pyc python3 -m unittest discover -s tests -v
```

### 현재 자동 테스트 구성

| 파일 | 범위 | 케이스 수 |
| --- | --- | --- |
| `tests/test_auth_routes.py` | 회원가입, 로그인, 로그아웃, 로그인 보호, 서비스명 노출 | 6 |
| `tests/test_recommendation_routes.py` | 프로필 저장, 추천 요청, 히스토리 저장, 콘텐츠 피드백, 퀴즈 투표 | 11 |
| `tests/test_services.py` | 추천 엔진, 콘텐츠 옵션 정규화, 피드백 집계, 대시보드 기록, 트렌드/퀴즈 서비스 | 12 |
| 합계 | 라우트 + 서비스 통합 검증 | 29 |

### 검증셋

아래 시나리오를 기준으로 자동 검증을 구성했습니다.

- 비로그인 사용자가 보호 페이지 접근 시 로그인 페이지로 리다이렉트되는지
- 회원가입 성공 시 `users`, `profiles` 컬렉션이 함께 생성되는지
- 중복 이메일 회원가입이 차단되는지
- 잘못된 비밀번호 로그인 시 에러 메시지가 노출되는지
- 로그아웃 시 세션이 비워지는지
- 프로필의 콘텐츠 취향 저장 시 비지원 값(예: 웹툰)이 필터링되는지
- 콘텐츠 취향 옵션이 현재 검색 가능한 데이터만 기준으로 노출되는지
- 음식 추천 POST 요청이 실제 히스토리 저장까지 이어지는지
- 대시보드 일일 히스토리가 중복 저장되지 않는지
- 콘텐츠 추천 페이지가 실제 캐시된 작품 데이터를 렌더링하는지
- 콘텐츠 좋아요/싫어요 API가 정상 응답과 집계 결과를 반환하는지
- 잘못된 피드백 입력과 없는 콘텐츠 ID에 대해 적절한 400/404를 반환하는지
- 퀴즈 투표 API가 잘못된 선택을 거부하고 정상 선택은 결과를 갱신하는지
- 추천 히스토리 페이지가 저장된 이력을 렌더링하는지
- 콘텐츠 옵션 생성 시 웹툰/유튜브 같은 비지원 포맷이 제외되는지
- 콘텐츠 플랫폼 `드라마` 입력이 사용자 선택 옵션 `시리즈`로 정규화되는지
- 음식 추천 엔진이 매운맛 선호를 실제 점수에 반영하는지
- 패션 추천 엔진이 온도/컬러 매칭을 실제 점수에 반영하는지
- 콘텐츠 추천 엔진이 비지원 콘텐츠를 후보군에서 제거하는지
- 콘텐츠 추천 엔진이 좋아요 이력으로 특정 작품을 상향하는지
- 콘텐츠 피드백 집계가 장르/플랫폼/공급자 단위로 누적되는지
- 대시보드 번들이 4개 카테고리 결과를 모두 만드는지
- 트렌드 그룹핑이 `food/fashion/content/activity` 4개 카테고리를 모두 보장하는지
- 퀴즈 결과 계산이 실제 투표 이후 갱신되는지

### 최근 실행 결과

- 실행 일시: `2026-03-12`
- 명령: `PYTHONPYCACHEPREFIX=/tmp/whatshouldido-pyc python3 -m unittest discover -s tests -v`
- 결과: `Ran 29 tests in 5.203s`
- 상태: `OK`

### 데모 발표에 넣을 포인트

- "AI로 구현 속도는 높였지만, 데모 신뢰성을 위해 29개 자동 테스트로 인증, 추천, 저장, 피드백 흐름을 검증했다"고 설명
- "외부 API에 의존하는 부분은 테스트용 캐시와 mock DB를 사용해 재현 가능하게 만들었다"고 설명
- "특히 사용자가 직접 만지는 프로필 저장, 추천 요청, 좋아요/싫어요, 히스토리 저장까지 회귀 테스트로 묶어두었다"고 설명

## Render 배포

이 저장소에는 Render Blueprint용 [`render.yaml`](/Users/donghyunkim/Documents/jungle_12th/jungle_12_2wk_303_05/lifestyle-app/render.yaml)이 포함되어 있습니다.

기본 절차:

1. 저장소를 GitHub에 push
2. Render에서 Blueprint 배포 생성
3. `SECRET_KEY` 설정
4. 필요하면 `MONGO_URI`, `MONGO_DB_NAME` 설정
5. MongoDB 없이 데모 배포만 할 경우 `USE_MOCK_ON_FAILURE=true` 사용

## 참고 문서

- [`AGENTS.md`](/Users/donghyunkim/Documents/jungle_12th/jungle_12_2wk_303_05/lifestyle-app/AGENTS.md)
- [`docs/CONVENTIONS.md`](/Users/donghyunkim/Documents/jungle_12th/jungle_12_2wk_303_05/lifestyle-app/docs/CONVENTIONS.md)
