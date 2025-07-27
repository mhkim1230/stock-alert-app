import SwiftUI
import Charts

struct StockListView: View {
    @EnvironmentObject var viewModel: StockViewModel
    @State private var selectedStock: Stock?
    
    var body: some View {
        NavigationView {
            List(viewModel.stocks) { stock in
                NavigationLink(destination: StockDetailView(stock: stock)) {
                    HStack {
                        VStack(alignment: .leading) {
                            Text(stock.symbol)
                                .font(.headline)
                            Text(stock.name)
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                        
                        VStack(alignment: .trailing) {
                            Text("₩\(stock.currentPrice, specifier: "%.2f")")
                                .font(.headline)
                            
                            Text("\(stock.changePercent, specifier: "%.2f")%")
                                .font(.subheadline)
                                .foregroundColor(stock.changePercent >= 0 ? .green : .red)
                        }
                    }
                }
            }
            .navigationTitle("주식 종목")
            .refreshable {
                viewModel.fetchStocksAndCurrencies()
            }
        }
    }
}

struct StockDetailView: View {
    let stock: Stock
    @EnvironmentObject var viewModel: StockViewModel
    @State private var newsArticles: [(title: String, description: String, url: String)] = []
    @State private var historicalPrices: [StockPrice] = []
    @State private var showingThresholdAlert = false
    @State private var thresholdValue = ""
    @State private var selectedPriceRange: PriceRange = .oneMonth
    
    enum PriceRange {
        case oneWeek, oneMonth, threeMonths, oneYear
        
        var title: String {
            switch self {
            case .oneWeek: return "1주"
            case .oneMonth: return "1개월"
            case .threeMonths: return "3개월"
            case .oneYear: return "1년"
            }
        }
    }
    
    var filteredPrices: [StockPrice] {
        let calendar = Calendar.current
        let now = Date()
        
        return historicalPrices.filter { price in
            switch selectedPriceRange {
            case .oneWeek:
                return calendar.dateComponents([.day], from: price.date, to: now).day ?? 0 <= 7
            case .oneMonth:
                return calendar.dateComponents([.month], from: price.date, to: now).month ?? 0 < 1
            case .threeMonths:
                return calendar.dateComponents([.month], from: price.date, to: now).month ?? 0 < 3
            case .oneYear:
                return calendar.dateComponents([.year], from: price.date, to: now).year ?? 0 < 1
            }
        }
    }
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 15) {
                // 주식 기본 정보
                HStack {
                    VStack(alignment: .leading) {
                        Text(stock.symbol)
                            .font(.title)
                            .fontWeight(.bold)
                        Text(stock.name)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    VStack(alignment: .trailing) {
                        Text("₩\(stock.currentPrice, specifier: "%.2f")")
                            .font(.title2)
                            .fontWeight(.semibold)
                        
                        Text("\(stock.changePercent, specifier: "%.2f")%")
                            .font(.subheadline)
                            .foregroundColor(stock.changePercent >= 0 ? .green : .red)
                    }
                }
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(10)
                
                // 알림 설정 버튼
                Button(action: {
                    showingThresholdAlert = true
                }) {
                    HStack {
                        Image(systemName: "bell.badge")
                        Text("알림 설정")
                    }
                    .frame(maxWidth: .infinity)
                    .padding()
                    .background(Color.blue.opacity(0.1))
                    .cornerRadius(10)
                }
                .alert("알림 임계값 설정", isPresented: $showingThresholdAlert) {
                    TextField("가격 임계값", text: $thresholdValue)
                        .keyboardType(.decimalPad)
                    
                    Button("설정", action: {
                        if let threshold = Double(thresholdValue) {
                            viewModel.setStockThreshold(stock: stock, threshold: threshold)
                        }
                    })
                    Button("취소", role: .cancel) {}
                }
                
                // 주식 차트
                VStack(alignment: .leading) {
                    Text("주가 변동")
                        .font(.headline)
                    
                    Picker("기간", selection: $selectedPriceRange) {
                        ForEach([PriceRange.oneWeek, .oneMonth, .threeMonths, .oneYear], id: \.self) { range in
                            Text(range.title).tag(range)
                        }
                    }
                    .pickerStyle(SegmentedPickerStyle())
                    .padding(.horizontal)
                    
                    if !filteredPrices.isEmpty {
                        StockChartView(stockPrices: filteredPrices)
                    } else {
                        Text("데이터 없음")
                            .foregroundColor(.secondary)
                            .frame(maxWidth: .infinity, alignment: .center)
                    }
                }
                .padding(.vertical)
                
                // 관련 뉴스
                Text("관련 뉴스")
                    .font(.headline)
                    .padding(.horizontal)
                
                if newsArticles.isEmpty {
                    Text("뉴스 로딩 중...")
                        .foregroundColor(.secondary)
                        .frame(maxWidth: .infinity, alignment: .center)
                } else {
                    ForEach(newsArticles.indices, id: \.self) { index in
                        NewsArticleView(article: newsArticles[index])
                    }
                }
            }
        }
        .navigationTitle(stock.symbol)
        .onAppear {
            viewModel.fetchNewsForStock(stock)
            viewModel.fetchStockHistoricalData(stock)
            
            newsArticles = viewModel.stockNews
            historicalPrices = viewModel.stockHistoricalPrices
        }
    }
}

struct NewsArticleView: View {
    let article: (title: String, description: String, url: String)
    
    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            Text(article.title)
                .font(.headline)
            
            Text(article.description)
                .font(.subheadline)
                .foregroundColor(.secondary)
                .lineLimit(2)
            
            HStack {
                Spacer()
                Link("기사 보기", destination: URL(string: article.url)!)
                    .font(.caption)
                    .foregroundColor(.blue)
            }
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(10)
        .padding(.horizontal)
    }
} 