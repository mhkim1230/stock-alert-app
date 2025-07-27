import Foundation

struct InvestmentRecommendation: Identifiable, Codable {
    let id = UUID()
    let stock: Stock
    let recommendationType: RecommendationType
    let confidence: Double
    let rationale: String
    
    enum RecommendationType: String, Codable {
        case strongBuy = "강력 매수"
        case buy = "매수"
        case hold = "보유"
        case sell = "매도"
        case strongSell = "강력 매도"
    }
}

struct InvestmentAnalysis: Codable {
    let historicalPerformance: [PerformanceMetric]
    let financialIndicators: FinancialIndicators
    let marketSentiment: MarketSentiment
}

struct PerformanceMetric: Codable {
    let date: Date
    let price: Double
    let volume: Int
}

struct FinancialIndicators: Codable {
    let peRatio: Double
    let dividendYield: Double
    let returnOnEquity: Double
    let debtToEquityRatio: Double
}

struct MarketSentiment: Codable {
    let newsScore: Double
    let socialMediaScore: Double
    let analystRecommendations: [String: Int]
} 