# 🚀 지금 바로 PC 끄고 24시간 돌리는 법 (클라우드 배포 가이드)

이 가이드만 따라 하면 15분 안에 PC를 꺼도 앱이 24시간 작동하게 됩니다.

## 1단계: GitHub에 코드 올리기

1. GitHub.com에 로그인하고 우측 상단 `+` 버튼 -> **New repository** 클릭
2. Repository name에 `stock-alert-app` 입력 -> **Create repository** 클릭
3. 아래 명령어를 터미널에 한 줄씩 복사해서 붙여넣으세요:

```bash
# git 설정이 안 되어 있다면 먼저 실행
git init
git add .
git commit -m "클라우드 배포 준비 완료"
git branch -M main

# [중요] 아래 주소는 방금 만든 본인의 레포지토리 주소로 바꿔야 합니다!
git remote add origin https://github.com/YOUR_USERNAME/stock-alert-app.git
git push -u origin main
```

## 2단계: 무료 데이터베이스 만들기 (Supabase)

1. [Supabase.com](https://supabase.com) 접속 -> **Start your project**
2. **New Project** 클릭
   - Name: `StockAlertDB`
   - Database Password: **강력한 비밀번호 생성 후 꼭 메모장에 적어두세요!**
   - Region: `Korea`가 있다면 선택, 없다면 `Singapore` 또는 `Tokyo`
3. 프로젝트가 생성될 때까지 기다립니다 (약 1-2분).
4. 생성 후 왼쪽 메뉴 **Project Settings (톱니바퀴)** -> **Database** 클릭
5. **Connection String** -> **URI** 탭 클릭
6. 주소 복사해두기 (예: `postgresql://postgres:[PASSWORD]@...`)
   - `[PASSWORD]` 부분을 아까 설정한 비밀번호로 바꿔야 합니다.

## 3단계: 서버 배포하기 (Render)

1. [Render.com](https://render.com) 접속 -> **Get Started** (GitHub 아이디로 로그인)
2. **New +** 버튼 -> **Blueprints** 클릭
3. **Connect a repository** -> 방금 올린 `stock-alert-app` 선택 -> **Connect**
4. `Service Group Name`에 `stock-alert-service` 입력 -> **Apply** 클릭
5. 환경 변수 입력 창이 뜨면 다음 내용 채우기:
   - `DATABASE_URL`: 아까 Supabase에서 복사한 주소 붙여넣기
   - `SUPABASE_URL`: Supabase 프로젝트 URL (Settings -> API에서 확인)
   - `SUPABASE_KEY`: Supabase anon key (Settings -> API에서 확인)
   - 나머지 APNS 관련은 일단 비워두거나 나중에 설정해도 됩니다.
6. 배포가 시작됩니다. 약 5~10분 정도 걸립니다.
7. 배포가 완료되면 `https://stock-alert-api-xxxx.onrender.com` 같은 주소가 생깁니다. 이 주소를 복사하세요.

## 4단계: 아이폰 앱에 주소 넣기

1. Cursor에서 `frontend/StockAlertApp/Services/NetworkService.swift` 파일 열기
2. 아래 부분을 찾아서 변경:
```swift
#if DEBUG
return "http://localhost:8000"
#else
// 여기를 아까 복사한 Render 주소로 변경!
return "https://stock-alert-api-xxxx.onrender.com"
#endif
```
3. 앱을 다시 빌드해서 아이폰에 넣으면 끝!

---

## 💡 팁
- 이제 터미널을 닫고 PC를 꺼도 Render 서버와 Supabase DB가 알아서 돌아갑니다.
- 비용은 **완전 0원**입니다.
- 앱 업데이트가 필요하면 코드를 수정하고 `git push`만 하면 자동으로 서버도 업데이트됩니다.

