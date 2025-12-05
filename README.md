# 🌱 Area Backend – Walking & Carbon Tracking API

사용자의 산책 데이터를 기반으로  
걷기 기록, 코스 추천, 누적 통계, 탄소 절감량 계산 등을 제공하는 FastAPI 기반 백엔드 서비스입니다.

---

## 1. 프로젝트 개요

Area 백엔드는 단순 산책 기록을 넘어서,

- 이동 데이터 기반 탄소 절감량 산출
- 산책 코스(사진/태그 포함) 추천 및 좋아요 시스템
- 사용자 맞춤 통계(걸음 수, 이동 거리, 탄소량)
- 마이페이지/프로필 관리
- 실시간 거리 계산 및 이미지 S3 업로드

등을 제공하는 **Location-based Wellness Service**를 목표로 설계되었습니다.

---

## 2. 기술 스택

### Backend
- FastAPI  
- Python 3.11  
- SQLAlchemy ORM  
- Pydantic v2  
- PyMySQL  

### Auth / Security
- JWT (python-jose)  
- passlib[bcrypt]  

### Infra
- MySQL (Local + Railway Managed DB)  
- Railway (Server Hosting)  
- AWS S3 (이미지 저장)  

### Utils
- geopy (거리 계산)  
- boto3 (S3 업로드)

---

## 3. 디렉토리 구조 요약

```
app/
 ├─ api/
 │   ├─ auth.py        # 회원가입 / 로그인
 │   ├─ paths.py       # 산책 코스 등록 / 목록 / 상세 / 좋아요
 │   ├─ walking.py     # 걷기 세션 기록 / 통계
 │   └─ mypage.py      # 마이페이지(프로필/누적 정보)
 ├─ models/
 │   ├─ user.py        # User, 누적 통계 필드
 │   ├─ path.py        # Path, PathImage, PathTag
 │   ├─ like.py        # Like (중복 좋아요 방지)
 │   └─ walking_history.py
 ├─ schemas/
 │   ├─ user.py        # UserSignup, UserLogin, UserResponse, ...
 │   ├─ path.py        # PathResponse, PathListResponse, ...
 │   ├─ walking.py     # WalkingStart, WalkingEnd, WalkingStatsResponse
 │   └─ common.py      # ApiResponse 공통 응답 구조
 ├─ utils/
 │   ├─ auth.py        # 비밀번호 해시, JWT 발급/검증
 │   ├─ dependencies.py# get_current_user (JWT 인증 의존성)
 │   ├─ distance.py    # 거리/시간/탄소 계산 함수
 │   └─ s3.py          # S3 업로드/삭제 유틸
 ├─ database.py        # DB 세션, Base, get_db
 ├─ config.py          # 환경 변수 & DATABASE_URL 설정
 └─ utils/exceptions.py# 전역 예외 핸들러
main.py                # FastAPI 엔트리포인트 (Railway 구동 기준)

```

---

## 4. 도메인 모델 설계

### **User**
- email / password / nickname / profile_image  
- 누적 통계 필드  
  - total_steps  
  - total_distance (km)  
  - carbon_saved (kg)  
- 관계  
  - paths, likes, walking_histories

### **Path / PathImage / PathTag**
- Path: 거리, 예상 시간, 소개, 좋아요 수  
- PathImage: S3 URL + 대표 이미지 여부  
- PathTag: 감성길, 자연길 등  

### **Like**
- user_id + path_id UniqueConstraint  
- 좋아요 토글 기반 구조

### **WalkingHistory**
- steps, duration, distance(m), 완료 여부  
- walk-at timestamp 포함  

---

## 5. 핵심 기능 요약

### ✔️ **산책 코스 등록 기능**
- 위경도 기반 거리 자동 계산  
- 평균 보폭/보행 속도 기반 예상 시간 계산  
- 이미지 S3 업로드  
- 태그 저장  

### ✔️ **걷기 세션 기능**
- 세션 시작 / 종료  
- steps / duration / distance 기록  
- 완료 여부 구분  
- User 누적 통계 자동 업데이트  

### ✔️ **누적 통계**
- 총 세션 수  
- 완료 세션 수  
- 누적 걸음 수  
- 누적 이동 거리 (km)  
- 이동 거리 기반 탄소 절감량 계산  

### ✔️ **좋아요 토글 기능**
- 좋아요 or 좋아요 취소  
- likes_count 자동 증가/감소  
- 좋아요 목록 조회 API  

### ✔️ **마이페이지**
- 프로필 조회  
- 닉네임 변경  
- 프로필 이미지 수정  
- 누적 정보 연동  

---

## 6. 거리·시간·탄소량 계산 로직

### **1) 거리 계산 (위경도 기반)**

```python
geodesic((lat1, lng1), (lat2, lng2)).kilometers
```

### **2) 예상 시간 계산**
보행 속도 4km/h 기준  
```
time_minutes = (distance_km / 4) * 60
```

### **3) 탄소 절감량 계산**

```
carbon_saved = distance_km * 0.21  # kgCO₂/km
```

근거: 국토교통부, UNEP, IPCC 평균 승용차 배출량 표준.

---

## 7. 공통 Response Format

```json
{
  "isSuccess": true,
  "code": "SUCCESS_200",
  "httpStatus": 200,
  "message": "요청이 완료되었습니다.",
  "data": { ... },
  "timeStamp": "2025-12-06 10:52:31"
}
```

전 API 동일 규칙 적용.

---

## 8. 배포 구조

### **Railway**
- develop → 자동 배포  
- main.py 기준 실행  

### **AWS S3**
- 경로 `paths/{pathId}/image.png`  
- 업로드 후 즉시 public URL 반환  

### **MySQL**
- local / railway / RDS 변환 용이하도록 `DATABASE_URL` 우선 구조  
- 비밀번호 암호화 및 보안 적용  

---

## 9. 트러블슈팅 (기술적으로 의미 있는 인사이트 중심)

### **1) 정적/동적 라우트 충돌 문제 해결 → API 라우팅 설계 원칙 수립**

#### 문제
`/paths/likes` 요청이  
FastAPI의 트리 기반 라우팅에서 `/paths/{path_id}`에 의해 가로채져  
문자열 `"likes"`가 정수 path_id로 파싱됨 → 422 오류.

#### 해결
- 정적 라우트(`/paths/likes`)를 동적 라우트보다 먼저 선언  
- 라우팅 우선순위 문서화  
- 앞으로 API 설계 시 “동적 > 정적 충돌 규칙”을 체크리스트화

#### 기술적 교훈
웹 프레임워크는 선언 순서에 따라 동작 방식이 다르므로  
**RESTful API URL 구조는 데이터 모델보다 먼저 설계해야 한다.**

---

### **2) MySQL SUM() 결과 Decimal → float 연산 오류 해결**

#### 문제
MySQL의 집계 결과는 Decimal 타입  
float과 계산 시 TypeError 발생.

#### 해결
```
total_distance_km = float(total_distance_m or 0) / 1000
```

#### 기술적 교훈
DB → ORM → Pydantic 변환 과정에서  
**타입이 한 번도 섞이지 않도록 명시적 타입 정규화 규칙**을 팀 규칙으로 도입.

---

### **3) 좋아요 토글 로직 Atomicity 확립**

경쟁 상황(동시 요청)에서  
좋아요 + 좋아요 취소가 레이스 컨디션을 일으킬 가능성 발견.

#### 해결
- UniqueConstraint 기반 toggle 설계  
- DB commit 이전 likes_count 동기화  
- 나중에 Redis + 분산락 구조 도입 가능성 검토  

#### 기술적 교훈
"토글" 기능은 단순히 조건문 `if exists else create`가 아니라  
**원자적 상태 전환(atomic state transition)**으로 설계해야 한다.

---

### **4) 산책 기록 누적 업데이트에서 데이터 무결성 강화**

여러 세션 데이터를 합산할 때  
중간에 숫자/None/Decimal 등이 섞이면 누적 데이터가 깨질 위험이 있었다.

#### 해결
- 모든 누적 필드 정규화 후 업데이트  
- 타입 혼합을 원천 차단  

#### 기술적 교훈
누적형 데이터는 “단 한 번이라도 잘못 누적되면 복구가 어렵기 때문에”
**정규화-합산-검증의 3단계 패턴**을 항상 강제해야 한다.

---

### **5) S3 업로드 오류 분석 → 파일 스트림 관리 규칙 정립**

초기 개발에서는 파일 스트림을 한 번 읽고 나면 재사용할 수 없어서  
S3 업로드 실패 후 이미지가 DB에는 기록되는 문제 발생.

#### 해결
- 파일 읽기 후 `await file.seek(0)` 수행  
- 업로드와 DB 기록을 일치시키는 트랜잭션 구조 도입  

#### 기술적 교훈
비동기 파일 스트림은 재사용 시 반드시 seek() 필요.  
**I/O 기반 로직은 항상 “실패 → 복구 → 재시도” 시나리오를 고려해야 한다.**

---

### **6) JWT 인증 미들웨어에서 subtile bug 제거**

JWT decode에서 sub/email 누락 시 401이 아닌 500이 발생하는 케이스 발견.

#### 해결
- TokenData null 체크 처리  
- email null → 명확히 401 반환  

#### 기술적 교훈
보안 관련 예외는 항상  
“예상된 실패”와 “비정상 실패”를 구분하여  
**명확한 HTTP Status Code 체계를 적용해야 한다.**

---

## 10. 전체 시스템 아키텍처

```
[Client]
   ↓ REST API
[FastAPI Backend]
   ├─ Auth(JWT)
   ├─ Walking Session
   ├─ Paths + S3 Upload
   ├─ Likes Toggle
   ├─ MyPage
   └─ Common Response Handler
   ↓
[MySQL Database]
   |
[AWS S3 Bucket]
   (이미지 업로드)
```

---
## 11. 마무리

이 프로젝트에서는 FastAPI + MySQL + S3 + Railway라는 풀 파이프라인을 직접 구성하고,

JWT 인증, 공통 응답 포맷, 전역 예외 핸들러, Swagger 문서화까지
실서비스에 가까운 백엔드 구조를 설계·구현했습니다.

특히 걷기 데이터 → 거리 → 탄소 절감량으로 이어지는 수치적 로직을
논문/가이드의 공식을 참고하여 모델링하고,

좋아요, 마이페이지, 걷기 세션/통계 등의 기능을
“사용자 경험 + 데이터 일관성” 관점에서 다듬었습니다.

추가적으로 CI/CD(Docker + GitHub Actions + AWS EC2/RDS)로 확장하거나,
실시간 랭킹/추천 알고리즘, 사용자별 맞춤 탄소 리포트 등으로 확장할 수 있는 구조를 염두에 두고 설계된 프로젝트입니다.

## 12. 앞으로의 발전 방향

- Redis 기반 좋아요 Rate Limit + Atomic Counter  
- WebSocket 기반 실시간 산책 트래킹  
- ML 기반 코스 추천 알고리즘  
- 개인별 Carbon Score 분석 리포트 생성  

---

## 13. 실행 방법

```
pip install -r requirements.txt
uvicorn main:app --reload
```

.env 예시는 다음과 같음:

```
DATABASE_URL=mysql+pymysql://user:pwd@host:3306/area
AWS_S3_BUCKET=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

---
