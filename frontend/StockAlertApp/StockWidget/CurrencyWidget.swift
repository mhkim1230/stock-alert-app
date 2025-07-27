import WidgetKit
import SwiftUI

struct CurrencyWidgetProvider: TimelineProvider {
    func placeholder(in context: Context) -> CurrencyEntry {
        CurrencyEntry(date: Date(), currency: Currency(code: "USD", name: "미국 달러", exchangeRate: 1300.0, changePercent: 0.5, historicalRates: nil))
    }
    
    func getSnapshot(in context: Context, completion: @escaping (CurrencyEntry) -> Void) {
        let entry = CurrencyEntry(date: Date(), currency: Currency(code: "USD", name: "미국 달러", exchangeRate: 1300.0, changePercent: 0.5, historicalRates: nil))
        completion(entry)
    }
    
    func getTimeline(in context: Context, completion: @escaping (Timeline<CurrencyEntry>) -> Void) {
        let networkService = NetworkService()
        
        networkService.fetchCurrencies()
            .sink(receiveCompletion: { _ in }, receiveValue: { currencies in
                let entries = currencies.map { currency in
                    CurrencyEntry(date: Date(), currency: currency)
                }
                
                let timeline = Timeline(entries: entries, policy: .atEnd)
                completion(timeline)
            })
            .cancel()
    }
}

struct CurrencyEntry: TimelineEntry {
    let date: Date
    let currency: Currency
}

struct CurrencyWidgetEntryView: View {
    var entry: CurrencyWidgetProvider.Entry
    
    var body: some View {
        VStack(alignment: .leading) {
            HStack {
                Text(entry.currency.code)
                    .font(.headline)
                Spacer()
                Text("₩\(entry.currency.exchangeRate, specifier: "%.2f")")
                    .font(.subheadline)
            }
            
            Text(entry.currency.name)
                .font(.caption)
                .foregroundColor(.secondary)
            
            HStack {
                Spacer()
                Text("\(entry.currency.changePercent, specifier: "%.2f")%")
                    .font(.caption)
                    .foregroundColor(entry.currency.changePercent >= 0 ? .green : .red)
            }
        }
        .padding()
        .background(Color.white)
        .cornerRadius(10)
    }
}

struct CurrencyWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: "com.stockalert.currency", provider: CurrencyWidgetProvider()) { entry in
            CurrencyWidgetEntryView(entry: entry)
        }
        .configurationDisplayName("환율 위젯")
        .description("실시간 환율 정보를 확인하세요.")
        .supportedFamilies([.systemSmall, .systemMedium])
    }
} 