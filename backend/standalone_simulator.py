#!/usr/bin/env python3
"""
독립적인 주식 알림 시뮬레이터
백엔드 API 없이도 작동합니다
"""

import http.server
import socketserver
import json
import urllib.parse
import random
import datetime

class StockSimulatorHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        """GET 요청 처리"""
        
        if self.path == '/':
            self.send_html_response(self.get_main_page())
        elif self.path.startswith('/api/stocks'):
            self.send_json_response(self.get_stock_data())
        elif self.path.startswith('/api/currency'):
            self.send_json_response(self.get_currency_data())
        elif self.path == '/health':
            self.send_json_response({"status": "healthy", "simulator": "running"})
        else:
            super().do_GET()
    
    def send_html_response(self, content):
        """HTML 응답 전송"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def send_json_response(self, data):
        """JSON 응답 전송"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def get_stock_data(self):
        """시뮬레이션 주식 데이터 생성"""
        stocks = [
            {'symbol': 'AAPL', 'name': 'Apple Inc.', 'name_kr': '애플'},
            {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'name_kr': '구글'},
            {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'name_kr': '마이크로소프트'},
            {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'name_kr': '테슬라'},
            {'symbol': 'NVDA', 'name': 'NVIDIA Corp.', 'name_kr': '엔비디아'},
            {'symbol': 'META', 'name': 'Meta Platforms Inc.', 'name_kr': '메타'},
        ]
        
        stock_data = []
        for stock in stocks:
            # 랜덤 주가 생성
            base_price = random.uniform(100, 300)
            change_percent = random.uniform(-5, 5)
            
            stock_data.append({
                **stock,
                'current_price': round(base_price, 2),
                'change_percent': round(change_percent, 2),
                'high': round(base_price * 1.05, 2),
                'low': round(base_price * 0.95, 2),
                'volume': random.randint(1000000, 10000000),
                'timestamp': datetime.datetime.now().isoformat()
            })
        
        return stock_data
    
    def get_currency_data(self):
        """시뮬레이션 환율 데이터 생성"""
        currencies = [
            {'base': 'USD', 'target': 'KRW', 'name': '달러/원'},
            {'base': 'EUR', 'target': 'KRW', 'name': '유로/원'},
            {'base': 'JPY', 'target': 'KRW', 'name': '엔/원'},
            {'base': 'CNY', 'target': 'KRW', 'name': '위안/원'},
        ]
        
        exchange_rates = []
        for currency in currencies:
            base_rate = random.uniform(1000, 1400) if currency['target'] == 'KRW' else random.uniform(0.7, 1.3)
            change_percent = random.uniform(-2, 2)
            
            exchange_rates.append({
                **currency,
                'rate': round(base_rate, 2),
                'change_percent': round(change_percent, 2),
                'timestamp': datetime.datetime.now().isoformat()
            })
        
        return exchange_rates
    
    def get_main_page(self):
        """메인 페이지 HTML 생성"""
        return '''
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📱 주식 알림 시뮬레이터</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; color: white; margin-bottom: 30px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { font-size: 1.2em; opacity: 0.9; }
        .card { 
            background: white; 
            border-radius: 15px; 
            padding: 25px; 
            margin: 20px 0; 
            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
        }
        .section-title { 
            font-size: 1.5em; 
            margin-bottom: 20px; 
            color: #4a5568;
            display: flex;
            align-items: center;
        }
        .section-title::before { 
            content: "📊"; 
            margin-right: 10px; 
            font-size: 1.2em;
        }
        .stock-grid, .currency-grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 15px; 
        }
        .item { 
            background: #f8fafc; 
            border-radius: 10px; 
            padding: 15px; 
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
        }
        .item:hover { transform: translateY(-2px); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .symbol { font-weight: bold; font-size: 1.1em; color: #2d3748; }
        .name { color: #718096; font-size: 0.9em; }
        .price { font-size: 1.3em; font-weight: bold; color: #2b6cb0; }
        .change { font-size: 0.9em; padding: 4px 8px; border-radius: 4px; }
        .positive { background: #c6f6d5; color: #22543d; }
        .negative { background: #fed7d7; color: #c53030; }
        .neutral { background: #e2e8f0; color: #4a5568; }
        .controls { text-align: center; margin: 20px 0; }
        .btn { 
            background: #667eea; 
            color: white; 
            border: none; 
            padding: 12px 24px; 
            border-radius: 8px; 
            cursor: pointer; 
            font-size: 1em;
            margin: 0 10px;
            transition: all 0.3s ease;
        }
        .btn:hover { background: #5a67d8; transform: translateY(-1px); }
        .status { 
            text-align: center; 
            padding: 10px; 
            background: #edf2f7; 
            border-radius: 8px; 
            margin: 10px 0;
            color: #4a5568;
        }
        .timestamp { 
            text-align: right; 
            color: #a0aec0; 
            font-size: 0.8em; 
            margin-top: 10px; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 주식 알림 시뮬레이터</h1>
            <p>실시간 주식 & 환율 데이터 시뮬레이션</p>
        </div>
        
        <div class="card">
            <div class="section-title">실시간 주식 현황</div>
            <div class="controls">
                <button class="btn" onclick="refreshStocks()">🔄 주식 데이터 새로고침</button>
                <button class="btn" onclick="simulateAlert()">🔔 알림 시뮬레이션</button>
            </div>
            <div class="status" id="stock-status">데이터를 불러오는 중...</div>
            <div class="stock-grid" id="stock-grid"></div>
        </div>
        
        <div class="card">
            <div class="section-title">실시간 환율 현황</div>
            <div class="controls">
                <button class="btn" onclick="refreshCurrency()">🔄 환율 데이터 새로고침</button>
            </div>
            <div class="status" id="currency-status">데이터를 불러오는 중...</div>
            <div class="currency-grid" id="currency-grid"></div>
        </div>
    </div>

    <script>
        let alertCount = 0;
        
        async function fetchData(url) {
            try {
                const response = await fetch(url);
                return await response.json();
            } catch (error) {
                console.error('데이터 불러오기 실패:', error);
                return null;
            }
        }
        
        async function refreshStocks() {
            document.getElementById('stock-status').textContent = '주식 데이터를 업데이트하는 중...';
            const data = await fetchData('/api/stocks');
            
            if (data) {
                displayStocks(data);
                document.getElementById('stock-status').textContent = `✅ 주식 데이터 업데이트 완료 (${new Date().toLocaleTimeString()})`;
            } else {
                document.getElementById('stock-status').textContent = '❌ 주식 데이터 업데이트 실패';
            }
        }
        
        async function refreshCurrency() {
            document.getElementById('currency-status').textContent = '환율 데이터를 업데이트하는 중...';
            const data = await fetchData('/api/currency');
            
            if (data) {
                displayCurrency(data);
                document.getElementById('currency-status').textContent = `✅ 환율 데이터 업데이트 완료 (${new Date().toLocaleTimeString()})`;
            } else {
                document.getElementById('currency-status').textContent = '❌ 환율 데이터 업데이트 실패';
            }
        }
        
        function displayStocks(stocks) {
            const grid = document.getElementById('stock-grid');
            grid.innerHTML = stocks.map(stock => `
                <div class="item">
                    <div class="item-header">
                        <div>
                            <div class="symbol">${stock.symbol}</div>
                            <div class="name">${stock.name_kr}</div>
                        </div>
                        <div class="price">$${stock.current_price}</div>
                    </div>
                    <div class="change ${stock.change_percent >= 0 ? 'positive' : 'negative'}">
                        ${stock.change_percent >= 0 ? '+' : ''}${stock.change_percent}%
                    </div>
                </div>
            `).join('');
        }
        
        function displayCurrency(currencies) {
            const grid = document.getElementById('currency-grid');
            grid.innerHTML = currencies.map(currency => `
                <div class="item">
                    <div class="item-header">
                        <div>
                            <div class="symbol">${currency.base}/${currency.target}</div>
                            <div class="name">${currency.name}</div>
                        </div>
                        <div class="price">${currency.rate}</div>
                    </div>
                    <div class="change ${currency.change_percent >= 0 ? 'positive' : 'negative'}">
                        ${currency.change_percent >= 0 ? '+' : ''}${currency.change_percent}%
                    </div>
                </div>
            `).join('');
        }
        
        function simulateAlert() {
            alertCount++;
            const alerts = [
                '🔔 AAPL이 목표가 $180에 도달했습니다!',
                '📈 TSLA 주가가 5% 상승했습니다!',
                '💰 USD/KRW 환율이 변동했습니다!',
                '⚡ NVDA에 대한 뉴스 알림이 있습니다!',
                '📊 설정한 알림 조건에 도달했습니다!'
            ];
            
            const randomAlert = alerts[Math.floor(Math.random() * alerts.length)];
            
            // 브라우저 알림 시뮬레이션
            if ('Notification' in window) {
                if (Notification.permission === 'granted') {
                    new Notification('주식 알림', { body: randomAlert, icon: '📱' });
                } else if (Notification.permission !== 'denied') {
                    Notification.requestPermission().then(permission => {
                        if (permission === 'granted') {
                            new Notification('주식 알림', { body: randomAlert, icon: '📱' });
                        }
                    });
                }
            }
            
            // 화면 알림
            alert(`📱 알림 #${alertCount}\\n${randomAlert}`);
        }
        
        // 자동 새로고침
        function autoRefresh() {
            refreshStocks();
            refreshCurrency();
        }
        
        // 페이지 로드 시 실행
        window.onload = () => {
            autoRefresh();
            // 30초마다 자동 새로고침
            setInterval(autoRefresh, 30000);
        };
    </script>
</body>
</html>
        '''

if __name__ == "__main__":
    PORT = 8090
    print("🚀 독립적인 주식 알림 시뮬레이터 시작!")
    print(f"📱 URL: http://localhost:{PORT}")
    print("🔔 알림 기능 포함")
    print("⏹️  서버 종료: Ctrl+C")
    print("-" * 50)
    
    try:
        with socketserver.TCPServer(("", PORT), StockSimulatorHandler) as httpd:
            print(f"✅ 시뮬레이터 서버 시작됨: http://localhost:{PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ 시뮬레이터가 정상적으로 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 시뮬레이터 오류: {e}") 