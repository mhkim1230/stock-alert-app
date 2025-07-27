import WidgetKit
import SwiftUI

@main
struct StockWidgetBundle: WidgetBundle {
    @WidgetBundleBuilder
    var body: some Widget {
        StockWidget()
        CurrencyWidget()
    }
} 