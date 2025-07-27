import SwiftUI

struct SearchView: View {
    @EnvironmentObject var viewModel: StockViewModel
    @State private var searchQuery = ""
    @State private var selectedSearchType: SearchType = .stocks
    
    enum SearchType {
        case stocks, currencies
    }
    
    var searchResults: [Any] {
        switch selectedSearchType {
        case .stocks:
            return viewModel.searchStocks(query: searchQuery)
        case .currencies:
            return viewModel.searchCurrencies(query: searchQuery)
        }
    }
    
    var body: some View {
        NavigationView {
            VStack {
                // 검색 타입 선택
                Picker("검색 유형", selection: $selectedSearchType) {
                    Text("주식").tag(SearchType.stocks)
                    Text("환율").tag(SearchType.currencies)
                }
                .pickerStyle(SegmentedPickerStyle())
                .padding()
                
                // 검색창
                HStack {
                    Image(systemName: "magnifyingglass")
                        .foregroundColor(.gray)
                    
                    TextField("검색어를 입력하세요", text: $searchQuery)
                        .textFieldStyle(PlainTextFieldStyle())
                }
                .padding()
                .background(Color.gray.opacity(0.1))
                .cornerRadius(10)
                .padding(.horizontal)
                
                // 검색 결과
                List(searchResults, id: \.self) { result in
                    switch selectedSearchType {
                    case .stocks:
                        if let stock = result as? Stock {
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
                    case .currencies:
                        if let currency = result as? Currency {
                            NavigationLink(destination: CurrencyDetailView(currency: currency)) {
                                HStack {
                                    VStack(alignment: .leading) {
                                        Text(currency.code)
                                            .font(.headline)
                                        Text(currency.name)
                                            .font(.subheadline)
                                            .foregroundColor(.secondary)
                                    }
                                    
                                    Spacer()
                                    
                                    VStack(alignment: .trailing) {
                                        Text("₩\(currency.exchangeRate, specifier: "%.2f")")
                                            .font(.headline)
                                        
                                        Text("\(currency.changePercent, specifier: "%.2f")%")
                                            .font(.subheadline)
                                            .foregroundColor(currency.changePercent >= 0 ? .green : .red)
                                    }
                                }
                            }
                        }
                    }
                }
                .listStyle(PlainListStyle())
            }
            .navigationTitle("검색")
        }
    }
} 