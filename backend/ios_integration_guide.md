# 📱 iOS 앱 완전 무료 알림 시스템 연동 가이드

## 💰 비용 절약 효과
- **이전**: APNs $99/년
- **현재**: ₩0 (완전 무료!)
- **연간 절약**: $99+ (약 13만원)

## 🎯 지원 알림 채널
1. **Firebase FCM** (무료) - iOS/Android 푸시
2. **Gmail SMTP** (무료) - 이메일 알림
3. **텔레그램 봇** (무료) - 메신저 알림
4. **웹 푸시** (무료) - 브라우저 알림

---

## 🔧 1단계: Firebase 프로젝트 설정

### A. Firebase 콘솔에서 프로젝트 생성
```bash
# 1. Firebase Console 접속
open https://console.firebase.google.com

# 2. "프로젝트 추가" 클릭
# 3. 프로젝트 이름: "stock-alert-free"
# 4. Google Analytics 사용 (선택사항)
# 5. 무료 Spark 플랜 선택
```

### B. iOS 앱 추가
```bash
# 1. 프로젝트 개요에서 iOS 아이콘 클릭
# 2. 번들 ID 입력: com.yourname.stockalert
# 3. 앱 닉네임: Stock Alert
# 4. GoogleService-Info.plist 다운로드
```

---

## 🔧 2단계: Xcode 프로젝트 설정

### A. Firebase SDK 추가 (Swift Package Manager)
```swift
// 1. Xcode에서 File → Add Package Dependencies
// 2. URL 입력: https://github.com/firebase/firebase-ios-sdk
// 3. 버전: Up to Next Major Version (최신)
// 4. 필요한 패키지 선택:
//    - FirebaseMessaging (FCM 푸시)
//    - FirebaseAnalytics (선택사항)
```

### B. GoogleService-Info.plist 추가
```bash
# 1. 다운로드한 GoogleService-Info.plist를 Xcode 프로젝트에 드래그
# 2. "Copy items if needed" 체크
# 3. Target에 앱 추가
# 4. Bundle Resources에 포함되는지 확인
```

### C. 앱 설정 파일 수정

#### Info.plist 수정
```xml
<!-- 푸시 알림 권한 요청 메시지 -->
<key>NSUserNotificationAlertStyle</key>
<string>alert</string>

<!-- 백그라운드 모드 활성화 -->
<key>UIBackgroundModes</key>
<array>
    <string>remote-notification</string>
    <string>background-fetch</string>
</array>
```

---

## 🔧 3단계: Swift 코드 구현

### A. AppDelegate 설정
```swift
import UIKit
import Firebase
import FirebaseMessaging
import UserNotifications

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
    
    func application(_ application: UIApplication, 
                    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {
        
        // Firebase 초기화
        FirebaseApp.configure()
        
        // FCM 델리게이트 설정
        Messaging.messaging().delegate = self
        
        // 푸시 알림 권한 요청
        UNUserNotificationCenter.current().delegate = self
        requestNotificationPermission()
        
        // APNs 토큰 등록
        application.registerForRemoteNotifications()
        
        return true
    }
    
    // 푸시 알림 권한 요청
    func requestNotificationPermission() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
            print("푸시 알림 권한: \\(granted)")
            if let error = error {
                print("권한 요청 오류: \\(error)")
            }
        }
    }
    
    // APNs 토큰 등록 성공
    func application(_ application: UIApplication, didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data) {
        Messaging.messaging().apnsToken = deviceToken
        print("APNs 토큰 등록 성공")
    }
    
    // APNs 토큰 등록 실패
    func application(_ application: UIApplication, didFailToRegisterForRemoteNotificationsWithError error: Error) {
        print("APNs 토큰 등록 실패: \\(error)")
    }
}

// MARK: - MessagingDelegate
extension AppDelegate: MessagingDelegate {
    func messaging(_ messaging: Messaging, didReceiveRegistrationToken fcmToken: String?) {
        guard let fcmToken = fcmToken else { return }
        print("FCM 토큰: \\(fcmToken)")
        
        // 서버에 FCM 토큰 전송
        sendFCMTokenToServer(fcmToken)
    }
    
    // 서버에 FCM 토큰 전송
    func sendFCMTokenToServer(_ token: String) {
        let url = URL(string: "http://localhost:8000/free-notifications/register-free-token")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = [
            "token": token,
            "token_type": "fcm",
            "platform": "ios"
        ]
        
        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)
            
            URLSession.shared.dataTask(with: request) { data, response, error in
                if let error = error {
                    print("FCM 토큰 전송 실패: \\(error)")
                } else {
                    print("FCM 토큰 전송 성공")
                }
            }.resume()
        } catch {
            print("JSON 직렬화 오류: \\(error)")
        }
    }
}

// MARK: - UNUserNotificationCenterDelegate
extension AppDelegate: UNUserNotificationCenterDelegate {
    // 앱이 포그라운드에 있을 때 알림 표시
    func userNotificationCenter(_ center: UNUserNotificationCenter, 
                               willPresent notification: UNNotification, 
                               withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void) {
        completionHandler([.alert, .sound, .badge])
    }
    
    // 알림 탭 시 처리
    func userNotificationCenter(_ center: UNUserNotificationCenter, 
                               didReceive response: UNNotificationResponse, 
                               withCompletionHandler completionHandler: @escaping () -> Void) {
        let userInfo = response.notification.request.content.userInfo
        print("알림 탭됨: \\(userInfo)")
        
        // 알림 타입에 따른 처리
        if let alertType = userInfo["alert_type"] as? String {
            handleNotificationTap(alertType: alertType, userInfo: userInfo)
        }
        
        completionHandler()
    }
    
    // 알림 탭 처리
    func handleNotificationTap(alertType: String, userInfo: [AnyHashable: Any]) {
        switch alertType {
        case "stock":
            // 주식 알림 처리 - 해당 주식 상세 화면으로 이동
            if let symbol = userInfo["symbol"] as? String {
                print("주식 알림: \\(symbol)")
                // NavigationManager.shared.navigateToStock(symbol)
            }
        case "currency":
            // 환율 알림 처리 - 환율 화면으로 이동
            if let pair = userInfo["currency_pair"] as? String {
                print("환율 알림: \\(pair)")
                // NavigationManager.shared.navigateToCurrency(pair)
            }
        case "news":
            // 뉴스 알림 처리 - 뉴스 상세 화면으로 이동
            if let newsUrl = userInfo["url"] as? String {
                print("뉴스 알림: \\(newsUrl)")
                // NavigationManager.shared.navigateToNews(newsUrl)
            }
        default:
            print("알 수 없는 알림 타입: \\(alertType)")
        }
    }
}
```

### B. 알림 서비스 클래스
```swift
import Foundation
import FirebaseMessaging

class FreeNotificationService: ObservableObject {
    static let shared = FreeNotificationService()
    
    private let baseURL = "http://localhost:8000"
    
    private init() {}
    
    // MARK: - 주식 알림 생성
    func createStockAlert(symbol: String, targetPrice: Double, condition: String) async throws {
        let url = URL(string: "\\(baseURL)/alerts/stock")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = [
            "symbol": symbol,
            "target_price": targetPrice,
            "condition": condition,
            "notification_channels": ["fcm", "email"]
        ] as [String : Any]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
            print("주식 알림 생성 성공: \\(symbol)")
        } else {
            throw NSError(domain: "StockAlert", code: 1, userInfo: [NSLocalizedDescriptionKey: "주식 알림 생성 실패"])
        }
    }
    
    // MARK: - 환율 알림 생성
    func createCurrencyAlert(baseCurrency: String, targetCurrency: String, targetRate: Double) async throws {
        let url = URL(string: "\\(baseURL)/alerts/currency")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = [
            "base_currency": baseCurrency,
            "target_currency": targetCurrency,
            "target_rate": targetRate,
            "notification_channels": ["fcm", "email"]
        ] as [String : Any]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
            print("환율 알림 생성 성공: \\(baseCurrency)/\\(targetCurrency)")
        } else {
            throw NSError(domain: "CurrencyAlert", code: 1, userInfo: [NSLocalizedDescriptionKey: "환율 알림 생성 실패"])
        }
    }
    
    // MARK: - 뉴스 알림 생성
    func createNewsAlert(keywords: [String]) async throws {
        let url = URL(string: "\\(baseURL)/alerts/news")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = [
            "keywords": keywords,
            "notification_channels": ["fcm", "email"]
        ] as [String : Any]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
            print("뉴스 알림 생성 성공: \\(keywords)")
        } else {
            throw NSError(domain: "NewsAlert", code: 1, userInfo: [NSLocalizedDescriptionKey: "뉴스 알림 생성 실패"])
        }
    }
    
    // MARK: - 테스트 알림 전송
    func sendTestNotification() async throws {
        let url = URL(string: "\\(baseURL)/free-notifications/send-test-notification")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = [
            "message": "iOS 앱에서 테스트 알림 전송",
            "channels": ["fcm"]
        ] as [String : Any]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 {
            print("테스트 알림 전송 성공")
        } else {
            throw NSError(domain: "TestNotification", code: 1, userInfo: [NSLocalizedDescriptionKey: "테스트 알림 전송 실패"])
        }
    }
}
```

### C. SwiftUI 뷰 예제
```swift
import SwiftUI

struct NotificationSettingsView: View {
    @StateObject private var notificationService = FreeNotificationService.shared
    @State private var stockSymbol = "AAPL"
    @State private var targetPrice = "200"
    @State private var baseCurrency = "USD"
    @State private var targetCurrency = "KRW"
    @State private var targetRate = "1400"
    @State private var showingAlert = false
    @State private var alertMessage = ""
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("💰 완전 무료 알림 시스템")) {
                    HStack {
                        Text("💸 월 비용")
                        Spacer()
                        Text("₩0")
                            .foregroundColor(.green)
                            .fontWeight(.bold)
                    }
                    
                    HStack {
                        Text("💵 연간 절약")
                        Spacer()
                        Text("$99+")
                            .foregroundColor(.blue)
                            .fontWeight(.bold)
                    }
                }
                
                Section(header: Text("📈 주식 알림")) {
                    HStack {
                        Text("심볼")
                        TextField("AAPL", text: $stockSymbol)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    HStack {
                        Text("목표 가격")
                        TextField("200", text: $targetPrice)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .keyboardType(.decimalPad)
                    }
                    
                    Button("주식 알림 생성") {
                        createStockAlert()
                    }
                    .foregroundColor(.blue)
                }
                
                Section(header: Text("💱 환율 알림")) {
                    HStack {
                        Text("기준 통화")
                        TextField("USD", text: $baseCurrency)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    HStack {
                        Text("대상 통화")
                        TextField("KRW", text: $targetCurrency)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                    }
                    
                    HStack {
                        Text("목표 환율")
                        TextField("1400", text: $targetRate)
                            .textFieldStyle(RoundedBorderTextFieldStyle())
                            .keyboardType(.decimalPad)
                    }
                    
                    Button("환율 알림 생성") {
                        createCurrencyAlert()
                    }
                    .foregroundColor(.blue)
                }
                
                Section(header: Text("🧪 테스트")) {
                    Button("테스트 알림 전송") {
                        sendTestNotification()
                    }
                    .foregroundColor(.green)
                }
            }
            .navigationTitle("무료 알림 설정")
            .alert("알림", isPresented: $showingAlert) {
                Button("확인") { }
            } message: {
                Text(alertMessage)
            }
        }
    }
    
    // MARK: - Actions
    private func createStockAlert() {
        guard let price = Double(targetPrice) else {
            showAlert("올바른 가격을 입력하세요")
            return
        }
        
        Task {
            do {
                try await notificationService.createStockAlert(
                    symbol: stockSymbol,
                    targetPrice: price,
                    condition: "above"
                )
                showAlert("주식 알림이 생성되었습니다!")
            } catch {
                showAlert("주식 알림 생성 실패: \\(error.localizedDescription)")
            }
        }
    }
    
    private func createCurrencyAlert() {
        guard let rate = Double(targetRate) else {
            showAlert("올바른 환율을 입력하세요")
            return
        }
        
        Task {
            do {
                try await notificationService.createCurrencyAlert(
                    baseCurrency: baseCurrency,
                    targetCurrency: targetCurrency,
                    targetRate: rate
                )
                showAlert("환율 알림이 생성되었습니다!")
            } catch {
                showAlert("환율 알림 생성 실패: \\(error.localizedDescription)")
            }
        }
    }
    
    private func sendTestNotification() {
        Task {
            do {
                try await notificationService.sendTestNotification()
                showAlert("테스트 알림이 전송되었습니다!")
            } catch {
                showAlert("테스트 알림 전송 실패: \\(error.localizedDescription)")
            }
        }
    }
    
    private func showAlert(_ message: String) {
        alertMessage = message
        showingAlert = true
    }
}

struct NotificationSettingsView_Previews: PreviewProvider {
    static var previews: some View {
        NotificationSettingsView()
    }
}
```

---

## 🔧 4단계: 테스트 및 검증

### A. 시뮬레이터에서 테스트
```bash
# 1. iOS 시뮬레이터 실행
open -a Simulator

# 2. 백엔드 서버 실행
cd backend
./run_server.sh

# 3. iOS 앱 빌드 및 실행
# Xcode에서 Command+R

# 4. 알림 권한 허용
# 5. 테스트 알림 전송 버튼 클릭
# 6. 주식/환율 알림 생성 테스트
```

### B. 실제 기기에서 테스트
```bash
# 1. Apple Developer 계정 필요 (무료 계정 가능)
# 2. Xcode에서 Signing & Capabilities 설정
# 3. Push Notifications 권한 추가
# 4. 실제 기기에 앱 설치
# 5. 백엔드 서버 IP를 실제 IP로 변경
```

---

## 🎯 5단계: 프로덕션 배포

### A. 서버 설정 변경
```swift
// 개발 환경
private let baseURL = "http://localhost:8000"

// 프로덕션 환경
private let baseURL = "https://your-domain.com"
```

### B. Firebase 프로덕션 설정
```bash
# 1. Firebase Console에서 프로덕션 키 생성
# 2. 서버 환경변수 업데이트
export FCM_SERVER_KEY="your-production-server-key"

# 3. APNs 인증서 업로드 (선택사항)
# Firebase Console → 프로젝트 설정 → Cloud Messaging → APNs 인증서
```

---

## 🎉 완성!

### ✅ 구현 완료 체크리스트
- [ ] Firebase 프로젝트 생성
- [ ] iOS 앱에 Firebase SDK 추가
- [ ] GoogleService-Info.plist 추가
- [ ] AppDelegate 설정
- [ ] 알림 서비스 클래스 구현
- [ ] SwiftUI 뷰 구현
- [ ] 시뮬레이터 테스트
- [ ] 실제 기기 테스트
- [ ] 프로덕션 배포

### 🎊 최종 결과
- **💰 비용**: ₩0 (완전 무료!)
- **📱 지원 플랫폼**: iOS, Android, Web, Desktop
- **🔔 알림 채널**: 4개 (FCM, 이메일, 텔레그램, 웹푸시)
- **⚡ 성능**: 실시간 알림, 5분 간격 체크
- **🔒 안정성**: 자동 백업 채널, 오류 처리

**연간 $99+ 절약하면서 기능은 4배 향상! 🚀** 