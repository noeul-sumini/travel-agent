# 여행 계획 도우미

AI 기반의 여행 계획 도우미 애플리케이션입니다. 사용자의 선호도와 요구사항을 고려하여 맞춤형 여행 계획을 생성하고, 일정 관리와 예산 계획을 도와줍니다.

## 주요 기능

- 맞춤형 여행 계획 생성
- 일정 관리 및 캘린더 연동
- 예산 계획 및 관리
- 날씨 정보 제공
- 실시간 대화형 인터페이스

## 기술 스택

### 백엔드
- FastAPI
- LangGraph/LangChain
- OpenAI GPT
- Google Maps API
- Google Calendar API

### 프론트엔드
- Streamlit

## 설치 방법

1. 저장소 클론
```bash
git clone <repository-url>
cd travel_agent
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
.\venv\Scripts\activate  # Windows
```

3. 의존성 설치
```bash
# 백엔드 의존성 설치
cd backend
pip install -r requirements.txt

# 프론트엔드 의존성 설치
cd ../frontend
pip install -r requirements.txt
```

4. 환경 변수 설정
```bash
# 백엔드
cp backend/.env.example backend/.env.dev

# 프론트엔드
cp frontend/.env.example frontend/.env.dev
```

## 실행 방법

1. 백엔드 서버 실행
```bash
cd backend
uvicorn app.main:app --reload
```

2. 프론트엔드 서버 실행
```bash
cd frontend
streamlit run app.py
```

## 프로젝트 구조

```
travel_agent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py
│   │   ├── core/
│   │   │   ├── agent/
│   │   │   │   ├── base_agent.py
│   │   │   │   ├── travel_agent.py
│   │   │   │   ├── planner_agent.py
│   │   │   │   ├── calendar_agent.py
│   │   │   │   └── weather_agent.py
│   │   │   └── config.py
│   │   └── main.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── components/
│   │   │   ├── chat.py
│   │   │   └── travel_plan.py
│   │   ├── utils/
│   │   │   └── api.py
│   │   └── main.py
│   └── requirements.txt
└── README.md
```

## 배포 방법

1. 서버에 접속하여 원하는 디렉토리 생성 및 이동
```bash
# 원하는 디렉토리 생성 (예: /home/user/travel_agent)
mkdir -p ~/travel_agent
cd ~/travel_agent
```

2. 최신 코드 가져오기
```bash
git pull origin main
```

3. 배포 스크립트 실행
```bash
chmod +x deploy.sh
./deploy.sh
```

배포 스크립트는 다음 작업을 자동으로 수행합니다:
- 필요한 패키지 설치 (Python 3.11, venv)
- 가상환경 생성 및 활성화
- 의존성 설치
- 환경 변수 설정
- 백엔드 서버 실행 (포트 8000)
- 프론트엔드 서버 실행 (포트 3000)

서버 접속 정보:
- 백엔드 API: http://your-server-ip:8000
- 프론트엔드: http://your-server-ip:3000

## 환경 변수 설정

### 백엔드 (.env.prod)
```
OPENAI_API_KEY=your_openai_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
GOOGLE_CALENDAR_CREDENTIALS=your_google_calendar_credentials
WEATHER_API_KEY=your_weather_api_key
```

### 프론트엔드 (.env.prod)
```
BACKEND_HOST=your_backend_host
BACKEND_PORT=8000
ENV=prod
```

## CI/CD 파이프라인

GitHub Actions를 사용하여 자동화된 CI/CD 파이프라인이 구성되어 있습니다.

### 테스트 (Test)
- Python 3.11 환경에서 테스트 실행
- pytest를 사용한 단위 테스트
- 코드 커버리지 리포트 생성
- Elasticsearch 서비스 컨테이너 실행

### 빌드 (Build)
- Docker 이미지 빌드
- GitHub Container Registry에 이미지 푸시
- Backend와 Frontend 이미지 각각 빌드
- 태그: latest와 커밋 해시

### 배포 (Deploy)
- AWS ECS 서비스 업데이트
- 메인 브랜치 푸시 시에만 배포 실행
- Backend와 Frontend 서비스 동시 배포

### 환경 변수
GitHub Secrets에 다음 값들이 설정되어 있어야 합니다:
- OPENAI_API_KEY
- GOOGLE_API_KEY
- WEATHER_API_KEY
- SKYSCANNER_API_KEY
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- GITHUB_TOKEN
