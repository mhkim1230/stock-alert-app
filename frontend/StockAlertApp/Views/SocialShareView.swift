import SwiftUI

struct SocialShareView: UIViewControllerRepresentable {
    let shareItems: [Any]
    
    func makeUIViewController(context: Context) -> UIActivityViewController {
        let controller = UIActivityViewController(
            activityItems: shareItems,
            applicationActivities: nil
        )
        return controller
    }
    
    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {}
}

extension View {
    func shareStock(_ stock: Stock) -> some View {
        let shareText = """
        📈 주식 정보 공유
        
        종목: \(stock.symbol) - \(stock.name)
        현재가: ₩\(stock.currentPrice, specifier: "%.2f")
        변동률: \(stock.changePercent, specifier: "%.2f")%
        
        #주식 #투자 #StockAlert
        """
        
        return self.modifier(ShareButtonModifier(shareItems: [shareText]))
    }
    
    func shareCurrency(_ currency: Currency) -> some View {
        let shareText = """
        💱 환율 정보 공유
        
        통화: \(currency.code) - \(currency.name)
        현재 환율: ₩\(currency.exchangeRate, specifier: "%.2f")
        변동률: \(currency.changePercent, specifier: "%.2f")%
        
        #환율 #외환 #StockAlert
        """
        
        return self.modifier(ShareButtonModifier(shareItems: [shareText]))
    }
    
    func shareInvestmentRecommendation(_ recommendation: InvestmentRecommendation) -> some View {
        let shareText = """
        🚀 투자 추천 정보
        
        종목: \(recommendation.stock.symbol) - \(recommendation.stock.name)
        추천: \(recommendation.recommendationType.rawValue)
        신뢰도: \(recommendation.confidence * 100, specifier: "%.1f")%
        
        추천 근거:
        \(recommendation.rationale)
        
        #투자추천 #주식투자 #StockAlert
        """
        
        return self.modifier(ShareButtonModifier(shareItems: [shareText]))
    }
}

struct ShareButtonModifier: ViewModifier {
    let shareItems: [Any]
    @State private var isSharePresented = false
    
    func body(content: Content) -> some View {
        content
            .onTapGesture {
                isSharePresented = true
            }
            .sheet(isPresented: $isSharePresented) {
                SocialShareView(shareItems: shareItems)
            }
    }
} 