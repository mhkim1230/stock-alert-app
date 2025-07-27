import SwiftUI
import Charts

struct InvestmentRecommendationView: View {
    @EnvironmentObject var viewModel: StockViewModel
    @State private var selectedRecommendationType: InvestmentRecommendation.RecommendationType?
    @State private var minConfidence: Double = 0.7
    
    var filteredRecommendations: [InvestmentRecommendation] {
        viewModel.filterRecommendations(type: selectedRecommendationType, minConfidence: minConfidence)
    }
    
    var body: some View {
        NavigationView {
            VStack {
                // 필터링 옵션
                HStack {
                    Picker("추천 유형", selection: $selectedRecommendationType) {
                        Text("전체").tag(nil as InvestmentRecommendation.RecommendationType?)
                        ForEach(InvestmentRecommendation.RecommendationType.allCases, id: \.self) { type in
                            Text(type.rawValue).tag(type as InvestmentRecommendation.RecommendationType?)
                        }
                    }
                    .pickerStyle(MenuPickerStyle())
                    
                    Slider(value: $minConfidence, in: 0...1, step: 0.1) {
                        Text("신뢰도")
                    }
                    .frame(width: 150)
                }
                .padding()
                
                // 추천 목록
                List(filteredRecommendations) { recommendation in
                    NavigationLink(destination: InvestmentDetailView(recommendation: recommendation)) {
                        HStack {
                            VStack(alignment: .leading) {
                                Text(recommendation.stock.symbol)
                                    .font(.headline)
                                Text(recommendation.stock.name)
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                            }
                            
                            Spacer()
                            
                            VStack(alignment: .trailing) {
                                Text(recommendation.recommendationType.rawValue)
                                    .font(.headline)
                                    .foregroundColor(recommendationColor(for: recommendation.recommendationType))
                                
                                Text("신뢰도: \(recommendation.confidence * 100, specifier: "%.1f")%")
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }
                .listStyle(PlainListStyle())
            }
            .navigationTitle("투자 추천")
            .onAppear {
                viewModel.fetchInvestmentRecommendations()
            }
        }
    }
    
    private func recommendationColor(for type: InvestmentRecommendation.RecommendationType) -> Color {
        switch type {
        case .strongBuy, .buy:
            return .green
        case .hold:
            return .orange
        case .sell, .strongSell:
            return .red
        }
    }
}

struct InvestmentDetailView: View {
    let recommendation: InvestmentRecommendation
    @EnvironmentObject var viewModel: StockViewModel
    @State private var showFullAnalysis = false
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 15) {
                // 주식 기본 정보
                HStack {
                    VStack(alignment: .leading) {
                        Text(recommendation.stock.symbol)
                            .font(.title)
                            .fontWeight(.bold)
                        Text(recommendation.stock.name)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    VStack(alignment: .trailing) {
                        Text(recommendation.recommendationType.rawValue)
                            .font(.title2)
                            .foregroundColor(recommendationColor(for: recommendation.recommendationType))
                        
                        Text("신뢰도: \(recommendation.confidence * 100, specifier: "%.1f")%")
                            .font(.subheadline)
                    }
                }
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(10)
                
                // 추천 근거
                Text("추천 근거")
                    .font(.headline)
                Text(recommendation.rationale)
                    .font(.body)
                    .foregroundColor(.secondary)
                
                // 투자 분석 상세 정보
                if let analysis = viewModel.selectedStockAnalysis {
                    VStack(alignment: .leading, spacing: 10) {
                        Text("투자 분석")
                            .font(.headline)
                        
                        // 재무 지표
                        FinancialIndicatorsView(indicators: analysis.financialIndicators)
                        
                        // 시장 센티먼트
                        MarketSentimentView(sentiment: analysis.marketSentiment)
                        
                        // 성과 차트
                        PerformanceChartView(performanceMetrics: analysis.historicalPerformance)
                    }
                } else {
                    ProgressView()
                        .frame(maxWidth: .infinity, alignment: .center)
                }
            }
            .padding()
        }
        .navigationTitle(recommendation.stock.symbol)
        .onAppear {
            viewModel.fetchInvestmentAnalysis(for: recommendation.stock)
        }
    }
    
    private func recommendationColor(for type: InvestmentRecommendation.RecommendationType) -> Color {
        switch type {
        case .strongBuy, .buy:
            return .green
        case .hold:
            return .orange
        case .sell, .strongSell:
            return .red
        }
    }
}

struct FinancialIndicatorsView: View {
    let indicators: FinancialIndicators
    
    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            Text("재무 지표")
                .font(.subheadline)
                .fontWeight(.bold)
            
            HStack {
                VStack(alignment: .leading) {
                    Text("P/E 비율")
                    Text("배당 수익률")
                    Text("자기자본이익률")
                    Text("부채비율")
                }
                
                Spacer()
                
                VStack(alignment: .trailing) {
                    Text("\(indicators.peRatio, specifier: "%.2f")")
                    Text("\(indicators.dividendYield * 100, specifier: "%.2f")%")
                    Text("\(indicators.returnOnEquity * 100, specifier: "%.2f")%")
                    Text("\(indicators.debtToEquityRatio, specifier: "%.2f")")
                }
            }
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(10)
    }
}

struct MarketSentimentView: View {
    let sentiment: MarketSentiment
    
    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            Text("시장 센티먼트")
                .font(.subheadline)
                .fontWeight(.bold)
            
            HStack {
                VStack(alignment: .leading) {
                    Text("뉴스 점수")
                    Text("소셜 미디어 점수")
                    Text("애널리스트 추천")
                }
                
                Spacer()
                
                VStack(alignment: .trailing) {
                    Text("\(sentiment.newsScore * 100, specifier: "%.2f")%")
                    Text("\(sentiment.socialMediaScore * 100, specifier: "%.2f")%")
                    Text(formatAnalystRecommendations(sentiment.analystRecommendations))
                }
            }
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(10)
    }
    
    private func formatAnalystRecommendations(_ recommendations: [String: Int]) -> String {
        let total = recommendations.values.reduce(0, +)
        let strongBuy = recommendations["strongBuy"] ?? 0
        let buy = recommendations["buy"] ?? 0
        let hold = recommendations["hold"] ?? 0
        let sell = recommendations["sell"] ?? 0
        let strongSell = recommendations["strongSell"] ?? 0
        
        return "\(Double(strongBuy + buy) / Double(total) * 100, specifier: "%.1f")% 긍정적"
    }
}

struct PerformanceChartView: View {
    let performanceMetrics: [PerformanceMetric]
    
    var body: some View {
        VStack(alignment: .leading, spacing: 5) {
            Text("주가 성과")
                .font(.subheadline)
                .fontWeight(.bold)
            
            Chart(performanceMetrics) { metric in
                LineMark(
                    x: .value("날짜", metric.date),
                    y: .value("가격", metric.price)
                )
                .interpolationMethod(.cardinal)
                .foregroundStyle(metric.price >= performanceMetrics.first!.price ? .green : .red)
                
                PointMark(
                    x: .value("날짜", metric.date),
                    y: .value("가격", metric.price)
                )
                .foregroundStyle(metric.price >= performanceMetrics.first!.price ? .green : .red)
            }
            .chartYAxis {
                AxisMarks(position: .leading)
            }
            .chartXAxis {
                AxisMarks(values: .stride(by: .month)) { _ in
                    AxisGridLine()
                    AxisTick()
                    AxisValueLabel(format: .dateTime.month(.abbreviated))
                }
            }
            .frame(height: 200)
        }
        .padding()
        .background(Color.gray.opacity(0.1))
        .cornerRadius(10)
    }
} 