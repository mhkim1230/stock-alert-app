import SwiftUI

struct MainTabView: View {
    @StateObject private var viewModel = StockViewModel()
    
    var body: some View {
        TabView {
            // 주식 탭
            StockListView()
                .tabItem {
                    Image(systemName: "chart.line.uptrend.xyaxis")
                    Text("주식")
                }
            
            // 환율 탭
            CurrencyListView()
                .tabItem {
                    Image(systemName: "dollarsign.circle")
                    Text("환율")
                }
            
            // 투자 추천 탭
            InvestmentRecommendationView()
                .tabItem {
                    Image(systemName: "lightbulb")
                    Text("투자 추천")
                }
            
            // 검색 탭
            SearchView()
                .tabItem {
                    Image(systemName: "magnifyingglass")
                    Text("검색")
                }
            
            // 알림 탭
            AlertSettingsView()
                .tabItem {
                    Image(systemName: "bell.badge")
                    Text("알림")
                }
            
            // 설정 탭
            AppSettingsView()
                .tabItem {
                    Image(systemName: "gear")
                    Text("설정")
                }
        }
        .environmentObject(viewModel)
    }
} 