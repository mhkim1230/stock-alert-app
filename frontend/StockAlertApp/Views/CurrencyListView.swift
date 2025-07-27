import SwiftUI

struct CurrencyListView: View {
    @EnvironmentObject var viewModel: StockViewModel
    @State private var selectedCurrency: Currency?
    
    var body: some View {
        NavigationView {
            List(viewModel.currencies) { currency in
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
            .navigationTitle("환율")
            .refreshable {
                viewModel.fetchStocksAndCurrencies()
            }
        }
    }
}

struct CurrencyDetailView: View {
    let currency: Currency
    @EnvironmentObject var viewModel: StockViewModel
    @State private var showingThresholdAlert = false
    @State private var thresholdValue = ""
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 15) {
                // 환율 기본 정보
                HStack {
                    VStack(alignment: .leading) {
                        Text(currency.code)
                            .font(.title)
                            .fontWeight(.bold)
                        Text(currency.name)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                    
                    Spacer()
                    
                    VStack(alignment: .trailing) {
                        Text("₩\(currency.exchangeRate, specifier: "%.2f")")
                            .font(.title2)
                            .fontWeight(.semibold)
                        
                        Text("\(currency.changePercent, specifier: "%.2f")%")
                            .font(.subheadline)
                            .foregroundColor(currency.changePercent >= 0 ? .green : .red)
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
                    TextField("환율 임계값", text: $thresholdValue)
                        .keyboardType(.decimalPad)
                    
                    Button("설정", action: {
                        if let threshold = Double(thresholdValue) {
                            viewModel.setCurrencyThreshold(currency: currency, threshold: threshold)
                        }
                    })
                    Button("취소", role: .cancel) {}
                }
                
                // 환율 차트 (추후 구현 예정)
                Text("환율 변동 차트")
                    .font(.headline)
                    .padding(.horizontal)
                
                Text("차트 구현 예정")
                    .foregroundColor(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
            }
        }
        .navigationTitle(currency.code)
    }
} 