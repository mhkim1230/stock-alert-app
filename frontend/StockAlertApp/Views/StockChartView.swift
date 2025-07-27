import SwiftUI
import Charts

struct StockChartView: View {
    let stockPrices: [StockPrice]
    
    var body: some View {
        Chart(stockPrices) { price in
            LineMark(
                x: .value("날짜", price.date),
                y: .value("가격", price.price)
            )
            .interpolationMethod(.cardinal)
            .foregroundStyle(price.price >= stockPrices.first!.price ? .green : .red)
            
            PointMark(
                x: .value("날짜", price.date),
                y: .value("가격", price.price)
            )
            .foregroundStyle(price.price >= stockPrices.first!.price ? .green : .red)
        }
        .chartYAxis {
            AxisMarks(position: .leading)
        }
        .chartXAxis {
            AxisMarks(values: .stride(by: .day)) { _ in
                AxisGridLine()
                AxisTick()
                AxisValueLabel(format: .dateTime.month(.abbreviated).day())
            }
        }
        .frame(height: 250)
        .padding()
    }
}

struct CurrencyChartView: View {
    let currencyRates: [CurrencyRate]
    
    var body: some View {
        Chart(currencyRates) { rate in
            LineMark(
                x: .value("날짜", rate.date),
                y: .value("환율", rate.rate)
            )
            .interpolationMethod(.cardinal)
            .foregroundStyle(rate.rate >= currencyRates.first!.rate ? .green : .red)
            
            PointMark(
                x: .value("날짜", rate.date),
                y: .value("환율", rate.rate)
            )
            .foregroundStyle(rate.rate >= currencyRates.first!.rate ? .green : .red)
        }
        .chartYAxis {
            AxisMarks(position: .leading)
        }
        .chartXAxis {
            AxisMarks(values: .stride(by: .day)) { _ in
                AxisGridLine()
                AxisTick()
                AxisValueLabel(format: .dateTime.month(.abbreviated).day())
            }
        }
        .frame(height: 250)
        .padding()
    }
}

// 데이터 모델 추가
struct StockPrice: Identifiable {
    let id = UUID()
    let date: Date
    let price: Double
}

struct CurrencyRate: Identifiable {
    let id = UUID()
    let date: Date
    let rate: Double
} 