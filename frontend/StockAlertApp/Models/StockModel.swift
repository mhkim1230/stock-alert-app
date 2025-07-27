import Foundation

struct Stock: Identifiable, Codable {
    let id = UUID()
    let symbol: String
    let name: String
    let currentPrice: Double
    let changePercent: Double
    let historicalPrices: [StockPrice]?
}

struct Currency: Identifiable, Codable {
    let id = UUID()
    let code: String
    let name: String
    let exchangeRate: Double
    let changePercent: Double
    let historicalRates: [CurrencyRate]?
}

struct StockAlert: Identifiable, Codable {
    let id = UUID()
    let stock: Stock
    let threshold: Double
    var isTriggered: Bool = false
}

struct CurrencyAlert: Identifiable, Codable {
    let id = UUID()
    let currency: Currency
    let threshold: Double
    var isTriggered: Bool = false
}

struct StockPrice: Identifiable, Codable {
    let id = UUID()
    let date: Date
    let price: Double
    
    enum CodingKeys: String, CodingKey {
        case date, price
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        date = try container.decode(Date.self, forKey: .date)
        price = try container.decode(Double.self, forKey: .price)
    }
}

struct CurrencyRate: Identifiable, Codable {
    let id = UUID()
    let date: Date
    let rate: Double
    
    enum CodingKeys: String, CodingKey {
        case date, rate
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        date = try container.decode(Date.self, forKey: .date)
        rate = try container.decode(Double.self, forKey: .rate)
    }
} 