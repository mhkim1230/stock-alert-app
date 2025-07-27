import WidgetKit
import SwiftUI

struct StockWidgetProvider: TimelineProvider {
    func placeholder(in context: Context) -> StockEntry {
        StockEntry(date: Date(), stock: Stock(symbol: "AAPL", name: "Apple Inc.", currentPrice: 150.0, changePercent: 1.5, historicalPrices: nil))
    }
    
    func getSnapshot(in context: Context, completion: @escaping (StockEntry) -> Void) {
        let entry = StockEntry(date: Date(), stock: Stock(symbol: "AAPL", name: "Apple Inc.", currentPrice: 150.0, changePercent: 1.5, historicalPrices: nil))
        completion(entry)
    }
    
    func getTimeline(in context: Context, completion: @escaping (Timeline<StockEntry>) -> Void) {
        let networkService = NetworkService()
        
        networkService.fetchStocks()
            .sink(receiveCompletion: { _ in }, receiveValue: { stocks in
                let entries = stocks.map { stock in
                    StockEntry(date: Date(), stock: stock)
                }
                
                let timeline = Timeline(entries: entries, policy: .atEnd)
                completion(timeline)
            })
            .cancel()
    }
}

struct StockEntry: TimelineEntry {
    let date: Date
    let stock: Stock
}

struct StockWidgetEntryView: View {
    var entry: StockWidgetProvider.Entry
    
    var body: some View {
        VStack(alignment: .leading) {
            HStack {
                Text(entry.stock.symbol)
                    .font(.headline)
                Spacer()
                Text("₩\(entry.stock.currentPrice, specifier: "%.2f")")
                    .font(.subheadline)
            }
            
            Text(entry.stock.name)
                .font(.caption)
                .foregroundColor(.secondary)
            
            HStack {
                Spacer()
                Text("\(entry.stock.changePercent, specifier: "%.2f")%")
                    .font(.caption)
                    .foregroundColor(entry.stock.changePercent >= 0 ? .green : .red)
            }
        }
        .padding()
        .background(Color.white)
        .cornerRadius(10)
    }
}

struct StockWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: "com.stockalert.stock", provider: StockWidgetProvider()) { entry in
            StockWidgetEntryView(entry: entry)
        }
        .configurationDisplayName("주식 위젯")
        .description("실시간 주식 정보를 확인하세요.")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
} 