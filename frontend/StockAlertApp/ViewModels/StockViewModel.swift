import Foundation
import Combine
import UserNotifications

class StockViewModel: ObservableObject {
    @Published var stocks: [Stock] = []
    @Published var currencies: [Currency] = []
    @Published var stockAlerts: [StockAlert] = []
    @Published var currencyAlerts: [CurrencyAlert] = []
    @Published var stockNews: [(title: String, description: String, url: String)] = []
    @Published var stockHistoricalPrices: [StockPrice] = []
    @Published var currencyHistoricalRates: [CurrencyRate] = []
    @Published var investmentRecommendations: [InvestmentRecommendation] = []
    @Published var selectedStockAnalysis: InvestmentAnalysis?
    
    private var cancellables = Set<AnyCancellable>()
    private let networkService = NetworkService()
    
    init() {
        // 초기 데이터 로드 및 주기적 업데이트 설정
        fetchStocksAndCurrencies()
        setupPeriodicUpdates()
        requestNotificationPermission()
    }
    
    func fetchStocksAndCurrencies() {
        // 주식 데이터 가져오기
        networkService.fetchStocks()
            .receive(on: DispatchQueue.main)
            .sink(receiveCompletion: { completion in
                switch completion {
                case .finished:
                    break
                case .failure(let error):
                    print("주식 데이터 로딩 실패: \(error)")
                }
            }, receiveValue: { [weak self] fetchedStocks in
                self?.stocks = fetchedStocks
                self?.checkStockAlerts()
            })
            .store(in: &cancellables)
        
        // 환율 데이터 가져오기
        networkService.fetchCurrencies()
            .receive(on: DispatchQueue.main)
            .sink(receiveCompletion: { completion in
                switch completion {
                case .finished:
                    break
                case .failure(let error):
                    print("환율 데이터 로딩 실패: \(error)")
                }
            }, receiveValue: { [weak self] fetchedCurrencies in
                self?.currencies = fetchedCurrencies
                self?.checkCurrencyAlerts()
            })
            .store(in: &cancellables)
    }
    
    private func setupPeriodicUpdates() {
        // 5분마다 데이터 업데이트
        Timer.publish(every: 300, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                self?.fetchStocksAndCurrencies()
            }
            .store(in: &cancellables)
    }
    
    func fetchNewsForStock(_ stock: Stock) {
        networkService.fetchNewsForStock(stock.symbol)
            .receive(on: DispatchQueue.main)
            .sink(receiveCompletion: { completion in
                switch completion {
                case .finished:
                    break
                case .failure(let error):
                    print("뉴스 로딩 실패: \(error)")
                }
            }, receiveValue: { [weak self] news in
                self?.stockNews = news
            })
            .store(in: &cancellables)
    }
    
    // 주식 알림 관련 메서드
    func setStockThreshold(stock: Stock, threshold: Double) {
        // 기존 알림 제거 후 새 알림 추가
        removeStockAlert(stock: stock)
        
        let newAlert = StockAlert(stock: stock, threshold: threshold)
        stockAlerts.append(newAlert)
    }
    
    func removeStockAlert(stock: Stock) {
        stockAlerts.removeAll { $0.stock.symbol == stock.symbol }
    }
    
    // 환율 알림 관련 메서드
    func setCurrencyThreshold(currency: Currency, threshold: Double) {
        // 기존 알림 제거 후 새 알림 추가
        removeCurrencyAlert(currency: currency)
        
        let newAlert = CurrencyAlert(currency: currency, threshold: threshold)
        currencyAlerts.append(newAlert)
    }
    
    func removeCurrencyAlert(currency: Currency) {
        currencyAlerts.removeAll { $0.currency.code == currency.code }
    }
    
    // 모든 알림 초기화
    func clearAllAlerts() {
        stockAlerts.removeAll()
        currencyAlerts.removeAll()
    }
    
    // 알림 체크 메서드
    private func checkStockAlerts() {
        for (index, alert) in stockAlerts.enumerated() {
            let currentStock = stocks.first { $0.symbol == alert.stock.symbol }
            
            if let stock = currentStock, stock.currentPrice <= alert.threshold {
                // 알림 트리거
                stockAlerts[index].isTriggered = true
                sendNotification(title: "주식 알림", body: "\(stock.symbol)의 가격이 \(alert.threshold)원 이하로 떨어졌습니다.")
            }
        }
    }
    
    private func checkCurrencyAlerts() {
        for (index, alert) in currencyAlerts.enumerated() {
            let currentCurrency = currencies.first { $0.code == alert.currency.code }
            
            if let currency = currentCurrency, currency.exchangeRate <= alert.threshold {
                // 알림 트리거
                currencyAlerts[index].isTriggered = true
                sendNotification(title: "환율 알림", body: "\(currency.code)의 환율이 \(alert.threshold)원 이하로 떨어졌습니다.")
            }
        }
    }
    
    // 알림 권한 요청
    private func requestNotificationPermission() {
        UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
            if granted {
                print("알림 권한 승인")
            } else {
                print("알림 권한 거부")
            }
        }
    }
    
    // 로컬 알림 전송
    private func sendNotification(title: String, body: String) {
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = .default
        
        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 1, repeats: false)
        let request = UNNotificationRequest(identifier: UUID().uuidString, content: content, trigger: trigger)
        
        UNUserNotificationCenter.current().add(request)
    }
    
    // 주식 과거 데이터 가져오기
    func fetchStockHistoricalData(_ stock: Stock) {
        networkService.fetchStockHistoricalData(stock.symbol)
            .receive(on: DispatchQueue.main)
            .sink(receiveCompletion: { completion in
                switch completion {
                case .finished:
                    break
                case .failure(let error):
                    print("주식 과거 데이터 로딩 실패: \(error)")
                }
            }, receiveValue: { [weak self] historicalPrices in
                self?.stockHistoricalPrices = historicalPrices
            })
            .store(in: &cancellables)
    }
    
    // 환율 과거 데이터 가져오기
    func fetchCurrencyHistoricalData(_ currency: Currency) {
        networkService.fetchCurrencyHistoricalData(currency.code)
            .receive(on: DispatchQueue.main)
            .sink(receiveCompletion: { completion in
                switch completion {
                case .finished:
                    break
                case .failure(let error):
                    print("환율 과거 데이터 로딩 실패: \(error)")
                }
            }, receiveValue: { [weak self] historicalRates in
                self?.currencyHistoricalRates = historicalRates
            })
            .store(in: &cancellables)
    }
    
    // 검색 기능 추가
    func searchStocks(query: String) -> [Stock] {
        return stocks.filter { stock in
            stock.symbol.localizedCaseInsensitiveContains(query) ||
            stock.name.localizedCaseInsensitiveContains(query)
        }
    }
    
    func searchCurrencies(query: String) -> [Currency] {
        return currencies.filter { currency in
            currency.code.localizedCaseInsensitiveContains(query) ||
            currency.name.localizedCaseInsensitiveContains(query)
        }
    }
    
    // 투자 추천 데이터 가져오기
    func fetchInvestmentRecommendations() {
        networkService.fetchInvestmentRecommendations()
            .receive(on: DispatchQueue.main)
            .sink(receiveCompletion: { completion in
                switch completion {
                case .finished:
                    break
                case .failure(let error):
                    print("투자 추천 데이터 로딩 실패: \(error)")
                }
            }, receiveValue: { [weak self] recommendations in
                self?.investmentRecommendations = recommendations
            })
            .store(in: &cancellables)
    }
    
    // 특정 주식에 대한 투자 분석 데이터 가져오기
    func fetchInvestmentAnalysis(for stock: Stock) {
        networkService.fetchInvestmentAnalysis(symbol: stock.symbol)
            .receive(on: DispatchQueue.main)
            .sink(receiveCompletion: { completion in
                switch completion {
                case .finished:
                    break
                case .failure(let error):
                    print("투자 분석 데이터 로딩 실패: \(error)")
                }
            }, receiveValue: { [weak self] analysis in
                self?.selectedStockAnalysis = analysis
            })
            .store(in: &cancellables)
    }
    
    // 투자 추천 필터링 메서드
    func filterRecommendations(type: InvestmentRecommendation.RecommendationType? = nil, 
                                minConfidence: Double = 0.0) -> [InvestmentRecommendation] {
        return investmentRecommendations.filter { recommendation in
            (type == nil || recommendation.recommendationType == type) &&
            recommendation.confidence >= minConfidence
        }
    }
} 