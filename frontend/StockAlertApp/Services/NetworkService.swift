import Foundation
import Combine

class NetworkService {
    static let shared = NetworkService()

    private var baseURL: String {
        if let customURL = UserDefaults.standard.string(forKey: "appServerBaseURL"),
           !customURL.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            return customURL
        }
        #if DEBUG
        return "http://localhost:8000"
        #else
        return "https://YOUR_RENDER_APP_NAME.onrender.com"
        #endif
    }

    private struct WatchlistItemDTO: Decodable {
        let symbol: String
    }

    private struct StockQuoteDTO: Decodable {
        let symbol: String
        let name: String
        let price: Double
        let changePercent: Double?
    }

    private struct NewsArticleDTO: Decodable {
        let title: String
        let summary: String
        let url: String
    }

    private struct ExchangeRateDTO: Decodable {
        let baseCurrency: String
        let targetCurrency: String
        let rate: Double

        enum CodingKeys: String, CodingKey {
            case baseCurrency = "base_currency"
            case targetCurrency = "target_currency"
            case rate
        }
    }

    private init() {}

    private var adminKey: String {
        UserDefaults.standard.string(forKey: "adminApiKey") ?? ""
    }

    private func authorizedRequest(url: URL, method: String = "GET") -> URLRequest {
        var request = URLRequest(url: url)
        request.httpMethod = method
        if !adminKey.isEmpty {
            request.setValue(adminKey, forHTTPHeaderField: "X-Admin-Key")
        }
        return request
    }

    private func decode<T: Decodable>(_ type: T.Type, from request: URLRequest) -> AnyPublisher<T, Error> {
        URLSession.shared.dataTaskPublisher(for: request)
            .map(\.data)
            .decode(type: type, decoder: JSONDecoder())
            .eraseToAnyPublisher()
    }

    func fetchStocks() -> AnyPublisher<[Stock], Error> {
        guard let watchlistURL = URL(string: "\(baseURL)/watchlist") else {
            return Fail(error: URLError(.badURL)).eraseToAnyPublisher()
        }

        return decode([WatchlistItemDTO].self, from: authorizedRequest(url: watchlistURL))
            .flatMap { items -> AnyPublisher<[Stock], Error> in
                if items.isEmpty {
                    return Just([]).setFailureType(to: Error.self).eraseToAnyPublisher()
                }

                let publishers = items.compactMap { item -> AnyPublisher<Stock, Error>? in
                    guard let quoteURL = URL(string: "\(baseURL)/stocks/\(item.symbol)") else {
                        return nil
                    }
                    return self.decode(StockQuoteDTO.self, from: self.authorizedRequest(url: quoteURL))
                        .map {
                            Stock(
                                symbol: $0.symbol,
                                name: $0.name,
                                currentPrice: $0.price,
                                changePercent: $0.changePercent ?? 0,
                                historicalPrices: nil
                            )
                        }
                        .eraseToAnyPublisher()
                }

                return Publishers.MergeMany(publishers)
                    .collect()
                    .eraseToAnyPublisher()
            }
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    func fetchCurrencies() -> AnyPublisher<[Currency], Error> {
        let pairs = [("USD", "KRW"), ("EUR", "KRW"), ("JPY", "KRW"), ("CNY", "KRW")]
        let publishers = pairs.compactMap { base, target -> AnyPublisher<Currency, Error>? in
            var components = URLComponents(string: "\(baseURL)/currency/rate")
            components?.queryItems = [
                URLQueryItem(name: "base", value: base),
                URLQueryItem(name: "target", value: target),
            ]
            guard let url = components?.url else { return nil }
            return decode(ExchangeRateDTO.self, from: authorizedRequest(url: url))
                .map {
                    Currency(
                        code: "\($0.baseCurrency)/\($0.targetCurrency)",
                        name: "\($0.baseCurrency) to \($0.targetCurrency)",
                        exchangeRate: $0.rate,
                        changePercent: 0,
                        historicalRates: nil
                    )
                }
                .eraseToAnyPublisher()
        }

        return Publishers.MergeMany(publishers)
            .collect()
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    func fetchNewsForStock(_ symbol: String) -> AnyPublisher<[(title: String, description: String, url: String)], Error> {
        var components = URLComponents(string: "\(baseURL)/news")
        components?.queryItems = [URLQueryItem(name: "query", value: symbol)]
        guard let url = components?.url else {
            return Fail(error: URLError(.badURL)).eraseToAnyPublisher()
        }

        return decode([NewsArticleDTO].self, from: authorizedRequest(url: url))
            .map { articles in
                articles.map { ($0.title, $0.summary, $0.url) }
            }
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    func fetchStockHistoricalData(_ symbol: String) -> AnyPublisher<[StockPrice], Error> {
        Just([]).setFailureType(to: Error.self).eraseToAnyPublisher()
    }

    func fetchCurrencyHistoricalData(_ code: String) -> AnyPublisher<[CurrencyRate], Error> {
        Just([]).setFailureType(to: Error.self).eraseToAnyPublisher()
    }

    func fetchInvestmentRecommendations() -> AnyPublisher<[InvestmentRecommendation], Error> {
        Just([]).setFailureType(to: Error.self).eraseToAnyPublisher()
    }

    func fetchInvestmentAnalysis(symbol: String) -> AnyPublisher<InvestmentAnalysis, Error> {
        Fail(error: NetworkError.serverError(statusCode: 501)).eraseToAnyPublisher()
    }

    func registerDeviceToken(_ token: String) -> AnyPublisher<Bool, Error> {
        guard let url = URL(string: "\(baseURL)/device-tokens") else {
            return Fail(error: NetworkError.invalidURL).eraseToAnyPublisher()
        }

        var request = authorizedRequest(url: url, method: "POST")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let payload = ["token": token, "platform": "iOS"]

        do {
            request.httpBody = try JSONEncoder().encode(payload)
        } catch {
            return Fail(error: NetworkError.encodingError).eraseToAnyPublisher()
        }

        return URLSession.shared.dataTaskPublisher(for: request)
            .tryMap { _, response -> Bool in
                guard let httpResponse = response as? HTTPURLResponse else {
                    throw NetworkError.invalidResponse
                }
                switch httpResponse.statusCode {
                case 200...299:
                    return true
                default:
                    throw NetworkError.serverError(statusCode: httpResponse.statusCode)
                }
            }
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    func addWatchlistSymbol(_ symbol: String) -> AnyPublisher<Bool, Error> {
        guard let url = URL(string: "\(baseURL)/watchlist") else {
            return Fail(error: NetworkError.invalidURL).eraseToAnyPublisher()
        }

        var request = authorizedRequest(url: url, method: "POST")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            request.httpBody = try JSONEncoder().encode(["symbol": symbol.uppercased()])
        } catch {
            return Fail(error: NetworkError.encodingError).eraseToAnyPublisher()
        }

        return URLSession.shared.dataTaskPublisher(for: request)
            .tryMap { _, response -> Bool in
                guard let httpResponse = response as? HTTPURLResponse else {
                    throw NetworkError.invalidResponse
                }
                switch httpResponse.statusCode {
                case 200...299:
                    return true
                default:
                    throw NetworkError.serverError(statusCode: httpResponse.statusCode)
                }
            }
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    func removeWatchlistSymbol(_ symbol: String) -> AnyPublisher<Bool, Error> {
        guard let encoded = symbol.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed),
              let url = URL(string: "\(baseURL)/watchlist/\(encoded)") else {
            return Fail(error: NetworkError.invalidURL).eraseToAnyPublisher()
        }

        let request = authorizedRequest(url: url, method: "DELETE")

        return URLSession.shared.dataTaskPublisher(for: request)
            .tryMap { _, response -> Bool in
                guard let httpResponse = response as? HTTPURLResponse else {
                    throw NetworkError.invalidResponse
                }
                switch httpResponse.statusCode {
                case 200...299:
                    return true
                default:
                    throw NetworkError.serverError(statusCode: httpResponse.statusCode)
                }
            }
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }

    enum NetworkError: Error {
        case invalidURL
        case invalidResponse
        case encodingError
        case serverError(statusCode: Int)
    }
}
