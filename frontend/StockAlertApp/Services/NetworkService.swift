import Foundation
import Combine

class NetworkService {
    static let shared = NetworkService()
    private let baseURL = "http://localhost:8000"
    
    private init() {}
    
    // 주식 데이터 가져오기 (Combine 사용)
    func fetchStocks() -> AnyPublisher<[Stock], Error> {
        guard let url = URL(string: "\(baseURL)/stocks") else {
            return Fail(error: URLError(.badURL)).eraseToAnyPublisher()
        }
        
        return URLSession.shared.dataTaskPublisher(for: url)
            .map { $0.data }
            .decode(type: [Stock].self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }
    
    // 환율 데이터 가져오기 (Combine 사용)
    func fetchCurrencies() -> AnyPublisher<[Currency], Error> {
        guard let url = URL(string: "\(baseURL)/currency") else {
            return Fail(error: URLError(.badURL)).eraseToAnyPublisher()
        }
        
        return URLSession.shared.dataTaskPublisher(for: url)
            .map { $0.data }
            .decode(type: [Currency].self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }
    
    // 주식 관련 뉴스 가져오기 (Combine 사용)
    func fetchNewsForStock(_ symbol: String) -> AnyPublisher<[(title: String, description: String, url: String)], Error> {
        guard let url = URL(string: "\(baseURL)/news?symbol=\(symbol)") else {
            return Fail(error: URLError(.badURL)).eraseToAnyPublisher()
        }
        
        return URLSession.shared.dataTaskPublisher(for: url)
            .map { $0.data }
            .decode(type: [(title: String, description: String, url: String)].self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }
    
    // 주식 과거 데이터 가져오기
    func fetchStockHistoricalData(_ symbol: String) -> AnyPublisher<[StockPrice], Error> {
        guard let url = URL(string: "\(baseURL)/stocks/historical?symbol=\(symbol)") else {
            return Fail(error: URLError(.badURL)).eraseToAnyPublisher()
        }
        
        return URLSession.shared.dataTaskPublisher(for: url)
            .map { $0.data }
            .decode(type: [StockPrice].self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }
    
    // 환율 과거 데이터 가져오기
    func fetchCurrencyHistoricalData(_ code: String) -> AnyPublisher<[CurrencyRate], Error> {
        guard let url = URL(string: "\(baseURL)/currency/historical?code=\(code)") else {
            return Fail(error: URLError(.badURL)).eraseToAnyPublisher()
        }
        
        return URLSession.shared.dataTaskPublisher(for: url)
            .map { $0.data }
            .decode(type: [CurrencyRate].self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }
    
    // 투자 추천 데이터 가져오기
    func fetchInvestmentRecommendations() -> AnyPublisher<[InvestmentRecommendation], Error> {
        guard let url = URL(string: "\(baseURL)/recommendations") else {
            return Fail(error: URLError(.badURL)).eraseToAnyPublisher()
        }
        
        return URLSession.shared.dataTaskPublisher(for: url)
            .map { $0.data }
            .decode(type: [InvestmentRecommendation].self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }
    
    // 특정 주식에 대한 투자 분석 데이터 가져오기
    func fetchInvestmentAnalysis(symbol: String) -> AnyPublisher<InvestmentAnalysis, Error> {
        guard let url = URL(string: "\(baseURL)/investment-analysis?symbol=\(symbol)") else {
            return Fail(error: URLError(.badURL)).eraseToAnyPublisher()
        }
        
        return URLSession.shared.dataTaskPublisher(for: url)
            .map { $0.data }
            .decode(type: InvestmentAnalysis.self, decoder: JSONDecoder())
            .receive(on: DispatchQueue.main)
            .eraseToAnyPublisher()
    }
    
    // 디바이스 토큰 등록 메서드
    func registerDeviceToken(_ token: String) -> AnyPublisher<Bool, Error> {
        guard let url = URL(string: "\(baseURL)/auth/register-device") else {
            return Fail(error: NetworkError.invalidURL).eraseToAnyPublisher()
        }
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // 인증 토큰 추가 (필요한 경우)
        if let authToken = UserDefaults.standard.string(forKey: "authToken") {
            request.setValue("Bearer \(authToken)", forHTTPHeaderField: "Authorization")
        }
        
        let payload = ["device_token": token]
        
        do {
            request.httpBody = try JSONEncoder().encode(payload)
        } catch {
            return Fail(error: NetworkError.encodingError).eraseToAnyPublisher()
        }
        
        return URLSession.shared.dataTaskPublisher(for: request)
            .tryMap { data, response -> Bool in
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
    
    // 네트워크 오류 열거형
    enum NetworkError: Error {
        case invalidURL
        case invalidResponse
        case encodingError
        case serverError(statusCode: Int)
    }
} 