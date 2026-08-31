# 보유종목 시세판 (KRX 자동 추적)

보유 종목의 시세를 GitHub Actions가 **평일 장 마감 후(16:40 KST) 자동 조회**해서 기록하고,
GitHub Pages가 대시보드(1D~20D 등락 트렌드 포함)를 보여주는 저장소입니다.

## 최초 설정 (약 5분, 1회)

1. **저장소 만들기** — github.com 로그인 → New repository → 이름 예: `krx-tracker` → **Private** 선택 가능 → Create
2. **파일 올리기** — Add file → Upload files → 이 폴더의 내용 전체를 끌어다 놓기 → Commit
   (`.github/workflows/update.yml` 폴더 구조가 유지되어야 합니다. zip을 풀어 폴더째 드래그하세요)
3. **Actions 켜기** — Actions 탭 → 워크플로 사용 승인(버튼 한 번)
4. **Pages 켜기** — Settings → Pages → Source: `Deploy from a branch` → Branch: `main`, 폴더 `/ (root)` → Save
5. 1~2분 후 `https://<아이디>.github.io/krx-tracker/` 에서 대시보드 확인

> Private 저장소에서 Pages를 쓰려면 GitHub Pro가 필요합니다. 무료 계정이면 저장소를 Public으로 하거나,
> 대시보드 없이 data/prices.json만 자동 수집해서 쓰는 것도 가능합니다.

## cron-job.org로 정시 실행 설정 (권장)

GitHub 자체 스케줄은 혼잡 시간에 실행이 밀리거나 누락될 수 있습니다.
cron-job.org가 정해진 시간에 GitHub를 깨우도록 설정하면 거의 정시에 실행됩니다.
(GitHub 자체 스케줄 16:40은 예비용으로 그대로 둡니다 — 둘이 겹쳐도 같은 날짜를 덮어쓸 뿐 문제 없음)

### 1) GitHub 토큰 만들기

GitHub → Settings → Developer settings → **Fine-grained tokens** → Generate new token

- Repository access: **이 저장소만** 선택
- Permissions → Repository permissions → **Actions: Read and write**
- Generate 후 `github_pat_...` 토큰 복사

### 2) cron-job.org에 작업 등록

console.cron-job.org 로그인 → CREATE CRONJOB

| 항목 | 값 |
|---|---|
| Title | KRX 시세 업데이트 |
| URL | `https://api.github.com/repos/<아이디>/<저장소명>/actions/workflows/update.yml/dispatches` |
| Schedule | 타임존 **Asia/Seoul** → 원하는 시각 (아래 참고) |
| Request method (Advanced 탭) | **POST** |
| Headers (Advanced 탭) | `Authorization: Bearer github_pat_...` <br> `Accept: application/vnd.github+json` <br> `User-Agent: cronjob` |
| Request body (Advanced 탭) | `{"ref":"main"}` |

저장 후 **TEST RUN**으로 확인 — 응답 코드 `204`면 성공이고,
저장소 Actions 탭에 "시세 업데이트" 실행이 나타납니다.

### 3) 실행 시각 추천

- **종가만 기록**: 평일 16:40 하루 1회
- **장중에도 갱신**: 평일 10:00~15:00 매시 정각 + 16:40 (마감 확정)
  → 장중 조회는 그 시점 가격을 오늘 날짜로 기록하고, 16:40 실행이 확정 종가로 덮어씁니다

## 매일 운영

아무것도 안 해도 됩니다. 평일 16:40에 자동으로 시세가 기록됩니다.

- **지금 바로 조회** — 대시보드의 [지금 조회 실행] → `Run workflow` 버튼
- **종목 추가/수정/삭제** — 대시보드의 [종목 편집] → `holdings.json` 수정 → Commit
  ```json
  {"code": "005930", "name": "삼성전자", "buy": 254274.0, "qty": 798.0}
  ```
- 수동 기록이 필요하면 로컬에서: `pip install finance-datareader` 후 `python fetch_prices.py` → commit & push

## 파일 구성

| 파일 | 역할 |
|---|---|
| `holdings.json` | 보유 종목 (종목코드·종목명·매입단가·수량) — 직접 관리 |
| `data/prices.json` | 일별 종가 기록 — Actions가 자동 누적 (최근 1년 유지) |
| `fetch_prices.py` | 시세 조회 스크립트 (FinanceDataReader / KRX) |
| `.github/workflows/update.yml` | 자동 실행 스케줄 (평일 16:40 KST + 수동 실행) |
| `index.html` | 대시보드 (GitHub Pages) |

## 대시보드 화면

종목명 · 매입단가 · 매입수량 · 평가금액 · 평가손익 · 수익률 · 현재가 · **1D%~20D%**
(상승 빨강 / 하락 파랑, 등락 폭에 따라 진하게) + 상단 합계 요약. 열 제목 클릭으로 정렬.
