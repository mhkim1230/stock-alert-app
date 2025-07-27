import SwiftUI
import AppIntents

struct ViewStockIntent: AppIntent {
    static var title: LocalizedStringResource = "주식 보기"
    
    @Parameter(title: "주식 심볼")
    var symbol: String
    
    init() {}
    
    init(symbol: String) {
        self.symbol = symbol
    }
    
    func perform() async throws -> some IntentResult {
        // 주식 상세 페이지로 이동하는 로직 구현
        return .result()
    }
}

struct ViewCurrencyIntent: AppIntent {
    static var title: LocalizedStringResource = "환율 보기"
    
    @Parameter(title: "통화 코드")
    var code: String
    
    init() {}
    
    init(code: String) {
        self.code = code
    }
    
    func perform() async throws -> some IntentResult {
        // 환율 상세 페이지로 이동하는 로직 구현
        return .result()
    }
}

struct SetAlertIntent: AppIntent {
    static var title: LocalizedStringResource = "알림 설정"
    
    @Parameter(title: "심볼/코드")
    var identifier: String
    
    @Parameter(title: "임계값")
    var threshold: Double
    
    init() {}
    
    init(identifier: String, threshold: Double) {
        self.identifier = identifier
        self.threshold = threshold
    }
    
    func perform() async throws -> some IntentResult {
        // 알림 설정 로직 구현
        return .result()
    }
}

struct StockAlertAppShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: ViewStockIntent(),
            phrases: [
                "주식 \(.applicationName)",
                "주식 보기 \(.applicationName)",
                "주식 정보 확인 \(.applicationName)"
            ]
        )
        
        AppShortcut(
            intent: ViewCurrencyIntent(),
            phrases: [
                "환율 \(.applicationName)",
                "환율 보기 \(.applicationName)",
                "환율 정보 확인 \(.applicationName)"
            ]
        )
        
        AppShortcut(
            intent: SetAlertIntent(),
            phrases: [
                "알림 설정 \(.applicationName)",
                "가격 알림 \(.applicationName)",
                "임계값 알림 \(.applicationName)"
            ]
        )
    }
} 