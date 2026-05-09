# web_dashboard.py
from flask import Flask, render_template_string, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

latest_data = {}

html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes, viewport-fit=cover">
    <title>Indodax AI Trading Suite | Professional Dashboard</title>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            background: linear-gradient(135deg, #0a0f1e 0%, #0c1222 100%);
            font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, sans-serif;
            color: #eef2ff;
            padding: 1rem;
            min-height: 100vh;
        }

        ::-webkit-scrollbar {
            width: 4px;
            height: 4px;
        }
        ::-webkit-scrollbar-track {
            background: #1e1f2c;
        }
        ::-webkit-scrollbar-thumb {
            background: #2dd4bf;
            border-radius: 4px;
        }

        .dashboard-container {
            max-width: 1600px;
            margin: 0 auto;
        }

        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }
        .title-section h1 {
            font-size: 1.6rem;
            font-weight: 600;
            background: linear-gradient(120deg, #a5f3fc, #2dd4bf);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            letter-spacing: -0.3px;
        }
        .title-section p {
            color: #8b92b0;
            font-size: 0.75rem;
        }
        .stats-grid {
            display: flex;
            gap: 1rem;
            background: rgba(15, 20, 35, 0.7);
            backdrop-filter: blur(8px);
            padding: 0.5rem 1rem;
            border-radius: 48px;
            border: 1px solid rgba(45, 212, 191, 0.3);
            flex-wrap: wrap;
        }
        .stat-item {
            text-align: center;
            padding: 0 0.5rem;
        }
        .stat-label {
            font-size: 0.65rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #7c83a2;
        }
        .stat-value {
            font-size: 1.2rem;
            font-weight: 700;
            color: #cbd5ff;
        }
        .live-badge {
            background: #10b981;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 4px;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { opacity: 0.4; transform: scale(0.8);}
            100% { opacity: 1; transform: scale(1.2);}
        }

        .card {
            background: rgba(18, 24, 40, 0.7);
            backdrop-filter: blur(12px);
            border-radius: 24px;
            border: 1px solid rgba(45, 212, 191, 0.2);
            padding: 1.2rem;
            margin-bottom: 1.5rem;
            transition: all 0.2s;
        }
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1rem;
        }
        .card-header h3 {
            font-size: 1.1rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .icon {
            color: #2dd4bf;
        }

        .chart-container {
            position: relative;
            height: 280px;
            width: 100%;
        }
        @media (min-width: 768px) {
            .chart-container { height: 380px; }
            body { padding: 1.5rem; }
            .card { padding: 1.5rem; }
            .title-section h1 { font-size: 1.8rem; }
        }
        @media (max-width: 480px) {
            .stats-grid { gap: 0.8rem; padding: 0.4rem 0.8rem; }
            .stat-value { font-size: 1rem; }
            .card-header h3 { font-size: 0.95rem; }
        }

        .table-wrapper {
            overflow-x: auto;
            border-radius: 20px;
            -webkit-overflow-scrolling: touch;
        }
        table {
            width: 100%;
            min-width: 500px;
            border-collapse: collapse;
            font-size: 0.75rem;
        }
        th {
            text-align: left;
            padding: 0.7rem 0.6rem;
            background: rgba(30, 36, 56, 0.8);
            color: #b9c3e6;
            font-weight: 500;
            font-size: 0.7rem;
        }
        td {
            padding: 0.6rem 0.6rem;
            border-bottom: 1px solid rgba(45, 55, 80, 0.5);
        }
        tr:hover td {
            background: rgba(45, 212, 191, 0.05);
        }
        .signal-badge {
            display: inline-block;
            padding: 3px 10px;
            border-radius: 40px;
            font-size: 0.65rem;
            font-weight: 600;
            text-align: center;
            min-width: 75px;
            background: #2d3748;
            color: #cbd5e1;
        }
        .signal-buy { background: #10b98120; color: #34d399; border: 1px solid #10b98160; }
        .signal-sell { background: #ef444420; color: #f87171; border: 1px solid #ef444460; }
        .signal-strong-buy { background: #10b98130; color: #6ee7b7; border: 1px solid #10b981; font-weight: bold; }
        .signal-strong-sell { background: #ef444430; color: #fca5a5; border: 1px solid #ef4444; font-weight: bold; }
        .price-value { font-weight: 500; color: #f0f3ff; font-size: 0.75rem; }
        .rsi-value { font-family: monospace; font-size: 0.7rem; }
        .time-col { color: #7e89ac; font-size: 0.65rem; }

        .footer-note {
            text-align: center;
            margin-top: 1.5rem;
            font-size: 0.6rem;
            color: #4c5470;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 0.8rem;
        }
    </style>
</head>
<body>
<div class="dashboard-container">
    <div class="header">
        <div class="title-section">
            <h1><i class="fas fa-chart-line icon"></i> INDODAX AI</h1>
            <p>LSTM | SMC | Real-time Whale</p>
        </div>
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-label">Markets</div>
                <div class="stat-value" id="totalMarkets">0</div>
            </div>
            <div class="stat-item">
                <div class="stat-label"><span class="live-badge"></span> Status</div>
                <div class="stat-value" id="wsStatus">Live</div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Signals</div>
                <div class="stat-value" id="activeSignals">0</div>
            </div>
        </div>
    </div>

    <div class="card">
        <div class="card-header">
            <h3><i class="fas fa-chart-scatter icon"></i> Price Index (Top 20)</h3>
            <div style="font-size:0.65rem;"><i class="fas fa-sync-alt"></i> real-time</div>
        </div>
        <div class="chart-container">
            <canvas id="priceChart"></canvas>
        </div>
    </div>

    <div class="card">
        <div class="card-header">
            <h3><i class="fas fa-bolt icon"></i> Multi‑Timeframe Signals</h3>
            <div style="font-size:0.65rem;"><i class="fas fa-robot"></i> AI scoring</div>
        </div>
        <div class="table-wrapper">
            <table id="signalsTable">
                <thead>
                    <tr><th>Pair</th><th>Price</th><th>Signal (1h)</th><th>RSI</th><th>Time</th></tr>
                </thead>
                <tbody><tr><td colspan="5" style="text-align:center;">Waiting for data......</tbody>
            </table>
        </div>
    </div>
    <div class="footer-note">
        <span>⚡ Auto mode: <span id="tradeMode">SIMULATION</span></span>
        <span>🐋 Whale >5000 USDT</span>
        <span>📡 WS + scanner 60s</span>
    </div>
</div>

<script>
    const ctx = document.getElementById('priceChart').getContext('2d');
    let priceChart = new Chart(ctx, {
        type: 'line',
        data: { labels: [], datasets: [{ label: 'Price', data: [], borderColor: '#2dd4bf', backgroundColor: 'rgba(45,212,191,0.05)', borderWidth: 2, pointRadius: 1.5, tension: 0.2, fill: true }] },
        options: { responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: '#cbd5e6', font: { size: 10 } } } }, scales: { y: { grid: { color: '#1e293b' }, ticks: { color: '#94a3b8' } }, x: { ticks: { color: '#94a3b8', maxRotation: 25 } } } }
    });

    const socket = io();
    function updateStats(markets, signalCount) {
        document.getElementById('totalMarkets').innerText = markets;
        document.getElementById('activeSignals').innerText = signalCount;
    }

    socket.on('update', function(data) {
        let pairs = Object.keys(data);
        updateStats(pairs.length, pairs.filter(p => data[p].signal && (data[p].signal.includes('BUY') || data[p].signal.includes('SELL'))).length);
        let sorted = pairs.slice().sort().slice(-20);
        priceChart.data.labels = sorted;
        priceChart.data.datasets[0].data = sorted.map(p => data[p].price);
        priceChart.update();

        let tbody = document.querySelector('#signalsTable tbody');
        tbody.innerHTML = '';
        for (let pair of sorted) {
            let item = data[pair];
            let signalText = item.signal || 'HOLD';
            let signalClass = '';
            if (signalText === 'STRONG BUY') signalClass = 'signal-strong-buy';
            else if (signalText === 'BUY') signalClass = 'signal-buy';
            else if (signalText === 'STRONG SELL') signalClass = 'signal-strong-sell';
            else if (signalText === 'SELL') signalClass = 'signal-sell';
            else signalClass = 'signal-badge';
            let priceFormatted = new Intl.NumberFormat('id-ID').format(item.price);
            let rsiVal = (item.rsi && item.rsi !== 0) ? item.rsi : '—';
            tbody.innerHTML += `<tr>
                <td style="font-weight:500;">${pair}</td>
                <td class="price-value">${priceFormatted}</td>
                <td><span class="signal-badge ${signalClass}">${signalText}</span></td>
                <td class="rsi-value">${rsiVal}</td>
                <td class="time-col">${item.time || '--:--:--'}</td>
            </tr>`;
        }
        if (!sorted.length) tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">⏳ Waiting......</tbody>';
    });

    socket.on('connect', () => document.getElementById('wsStatus').innerHTML = '<i class="fas fa-circle" style="color:#10b981; font-size:0.6rem;"></i> Live');
    socket.on('disconnect', () => document.getElementById('wsStatus').innerHTML = '<i class="fas fa-circle" style="color:#f97316;"></i> Reconnect');

    fetch('/api/trading_mode').then(res => res.json()).then(data => document.getElementById('tradeMode').innerText = data.mode === true ? 'REAL ORDER' : 'SIMULATION').catch(()=>{});
</script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(html_template)

@app.route('/api/data')
def api_data():
    return jsonify(latest_data)

@app.route('/api/trading_mode')
def trading_mode():
    from config import Config
    return jsonify({"mode": Config.ALLOW_REAL_ORDER})

@socketio.on('connect')
def handle_connect():
    emit('update', latest_data)

def update_dashboard(pair, price, signal=None, rsi=None):
    latest_data[pair] = {
        'price': price,
        'signal': signal or 'HOLD',
        'rsi': rsi or 0,
        'time': datetime.now().strftime("%H:%M:%S")
    }
    socketio.emit('update', latest_data)

def run_dashboard():
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
