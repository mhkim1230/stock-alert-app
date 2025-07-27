import SwiftUI
import UserNotifications

struct AppSettingsView: View {
    @AppStorage("darkMode") private var darkMode = false
    @AppStorage("notificationsEnabled") private var notificationsEnabled = true
    @AppStorage("updateFrequency") private var updateFrequency = 5 // 분 단위
    @State private var showingNotificationAlert = false
    
    var body: some View {
        NavigationView {
            Form {
                Section(header: Text("디스플레이")) {
                    Toggle("다크 모드", isOn: $darkMode)
                }
                
                Section(header: Text("알림")) {
                    Toggle("알림 활성화", isOn: $notificationsEnabled)
                        .onChange(of: notificationsEnabled) { newValue in
                            if newValue {
                                requestNotificationPermission()
                            } else {
                                disableNotifications()
                            }
                        }
                    
                    if !notificationsEnabled {
                        Text("푸시 알림이 비활성화되었습니다.")
                            .foregroundColor(.secondary)
                    }
                    
                    Picker("데이터 업데이트 주기", selection: $updateFrequency) {
                        Text("5분").tag(5)
                        Text("10분").tag(10)
                        Text("15분").tag(15)
                        Text("30분").tag(30)
                        Text("1시간").tag(60)
                    }
                }
                
                Section(header: Text("알림 설정")) {
                    NavigationLink(destination: NotificationPreferencesView()) {
                        Text("알림 환경설정")
                    }
                }
                
                Section(header: Text("데이터 관리")) {
                    NavigationLink(destination: WatchlistView()) {
                        Text("관심 종목 관리")
                    }
                    
                    Button("캐시 초기화") {
                        clearAppCache()
                    }
                    .foregroundColor(.red)
                }
                
                Section(header: Text("정보")) {
                    HStack {
                        Text("버전")
                        Spacer()
                        Text("1.0.0")
                    }
                    
                    NavigationLink(destination: PrivacyPolicyView()) {
                        Text("개인정보 처리방침")
                    }
                    
                    NavigationLink(destination: TermsOfServiceView()) {
                        Text("서비스 이용약관")
                    }
                }
            }
            .navigationTitle("설정")
            .onChange(of: darkMode) { newValue in
                // 다크 모드 설정 적용
                UIApplication.shared.windows.first?.rootViewController?.overrideUserInterfaceStyle = newValue ? .dark : .light
            }
        }
    }
    
    private func clearAppCache() {
        // 앱 캐시 초기화 로직
        let fileManager = FileManager.default
        let cacheURL = fileManager.urls(for: .cachesDirectory, in: .userDomainMask).first!
        
        do {
            let fileURLs = try fileManager.contentsOfDirectory(at: cacheURL, includingPropertiesForKeys: nil)
            for fileURL in fileURLs {
                try fileManager.removeItem(at: fileURL)
            }
        } catch {
            print("캐시 초기화 중 오류 발생: \(error)")
        }
    }
    
    private func requestNotificationPermission() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
            DispatchQueue.main.async {
                if granted {
                    notificationsEnabled = true
                    UIApplication.shared.registerForRemoteNotifications()
                } else {
                    notificationsEnabled = false
                    showingNotificationAlert = true
                }
            }
        }
    }
    
    private func disableNotifications() {
        // iOS에서 알림 완전 비활성화는 설정앱에서만 가능
        // 여기서는 앱 내 알림 수신 설정만 변경
        UIApplication.shared.unregisterForRemoteNotifications()
    }
}

struct WatchlistView: View {
    @EnvironmentObject var viewModel: StockViewModel
    @State private var editMode = EditMode.inactive
    
    var body: some View {
        List {
            Section(header: Text("관심 주식")) {
                ForEach(viewModel.stocks) { stock in
                    Text(stock.symbol)
                }
                .onDelete(perform: deleteStock)
            }
            
            Section(header: Text("관심 환율")) {
                ForEach(viewModel.currencies) { currency in
                    Text(currency.code)
                }
                .onDelete(perform: deleteCurrency)
            }
        }
        .listStyle(InsetGroupedListStyle())
        .navigationTitle("관심 종목")
        .environment(\.editMode, $editMode)
        .toolbar {
            EditButton()
        }
    }
    
    private func deleteStock(at offsets: IndexSet) {
        // 관심 주식 삭제 로직
    }
    
    private func deleteCurrency(at offsets: IndexSet) {
        // 관심 환율 삭제 로직
    }
}

struct PrivacyPolicyView: View {
    var body: some View {
        ScrollView {
            Text("개인정보 처리방침")
                .font(.title)
                .padding()
            
            Text("이 앱은 사용자의 개인정보를 소중히 다룹니다...")
                .padding()
        }
        .navigationTitle("개인정보 처리방침")
    }
}

struct TermsOfServiceView: View {
    var body: some View {
        ScrollView {
            Text("서비스 이용약관")
                .font(.title)
                .padding()
            
            Text("이 앱을 사용함으로써 다음 약관에 동의합니다...")
                .padding()
        }
        .navigationTitle("서비스 이용약관")
    }
}

struct NotificationPreferencesView: View {
    @State private var stockAlertEnabled = true
    @State private var currencyAlertEnabled = true
    @State private var newsAlertEnabled = false
    
    var body: some View {
        Form {
            Section(header: Text("알림 환경설정")) {
                Toggle("주식 알림", isOn: $stockAlertEnabled)
                Toggle("환율 알림", isOn: $currencyAlertEnabled)
                Toggle("뉴스 알림", isOn: $newsAlertEnabled)
            }
            
            Section {
                Button("저장") {
                    saveNotificationPreferences()
                }
            }
        }
        .navigationTitle("알림 환경설정")
    }
    
    private func saveNotificationPreferences() {
        // 알림 환경설정 저장 로직
        UserDefaults.standard.set(stockAlertEnabled, forKey: "stockAlertEnabled")
        UserDefaults.standard.set(currencyAlertEnabled, forKey: "currencyAlertEnabled")
        UserDefaults.standard.set(newsAlertEnabled, forKey: "newsAlertEnabled")
    }
}

struct AppSettingsView_Previews: PreviewProvider {
    static var previews: some View {
        AppSettingsView()
    }
} 