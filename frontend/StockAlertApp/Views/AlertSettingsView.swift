import SwiftUI

struct AlertSettingsView: View {
    @EnvironmentObject var viewModel: StockViewModel
    
    var body: some View {
        NavigationView {
            List {
                Section(header: Text("주식 알림")) {
                    ForEach(viewModel.stockAlerts) { alert in
                        HStack {
                            VStack(alignment: .leading) {
                                Text(alert.stock.symbol)
                                    .font(.headline)
                                Text(alert.stock.name)
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                            }
                            
                            Spacer()
                            
                            VStack(alignment: .trailing) {
                                Text("임계값: ₩\(alert.threshold, specifier: "%.2f")")
                                    .font(.caption)
                                
                                Text(alert.isTriggered ? "알림 발생" : "대기 중")
                                    .font(.caption)
                                    .foregroundColor(alert.isTriggered ? .red : .green)
                            }
                        }
                    }
                    .onDelete(perform: deleteStockAlert)
                }
                
                Section(header: Text("환율 알림")) {
                    ForEach(viewModel.currencyAlerts) { alert in
                        HStack {
                            VStack(alignment: .leading) {
                                Text(alert.currency.code)
                                    .font(.headline)
                                Text(alert.currency.name)
                                    .font(.subheadline)
                                    .foregroundColor(.secondary)
                            }
                            
                            Spacer()
                            
                            VStack(alignment: .trailing) {
                                Text("임계값: ₩\(alert.threshold, specifier: "%.2f")")
                                    .font(.caption)
                                
                                Text(alert.isTriggered ? "알림 발생" : "대기 중")
                                    .font(.caption)
                                    .foregroundColor(alert.isTriggered ? .red : .green)
                            }
                        }
                    }
                    .onDelete(perform: deleteCurrencyAlert)
                }
            }
            .listStyle(InsetGroupedListStyle())
            .navigationTitle("알림 설정")
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        // 알림 설정 초기화
                        viewModel.clearAllAlerts()
                    }) {
                        Image(systemName: "trash")
                    }
                }
            }
        }
    }
    
    private func deleteStockAlert(at offsets: IndexSet) {
        offsets.forEach { index in
            let alert = viewModel.stockAlerts[index]
            viewModel.removeStockAlert(stock: alert.stock)
        }
    }
    
    private func deleteCurrencyAlert(at offsets: IndexSet) {
        offsets.forEach { index in
            let alert = viewModel.currencyAlerts[index]
            viewModel.removeCurrencyAlert(currency: alert.currency)
        }
    }
} 