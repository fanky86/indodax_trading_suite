# web_dashboard.py
from flask import Flask, render_template_string, jsonify
from flask_socketio import SocketIO, emit
import threading
import json
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

latest_data = {}

html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Indodax AI Dashboard</title>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial; margin: 20px; background: #1e1e2f; color: white; }
        .card { background: #2d2d44; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        canvas { max-width: 100%; background: #0f0f1a; border-radius: 8px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #444; }
        .buy { color: #00ffaa; }
        .sell { color: #ff5555; }
    </style>
</head>
<body>
    <h1>📊 INDODAX AI TRADING SUITE</h1>
    <div class="card">
        <h3>Live Price Chart</h3>
        <canvas id="priceChart" width="800" height="400"></canvas>
    </div>
    <div class="card">
        <h3>Real-time Signals</h3>
        <table id="signalsTable">
            <thead><tr><th>Pair</th><th>Price</th><th>Signal</th><th>RSI</th><th>Time</th></tr></thead>
            <tbody></tbody>
        </table>
    </div>
    <script>
        var socket = io();
        var ctx = document.getElementById('priceChart').getContext('2d');
        var chart = new Chart(ctx, {
            type: 'line',
            data: { labels: [], datasets: [{ label: 'Price (last 20 pairs)', data: [], borderColor: 'cyan' }] }
        });
        socket.on('update', function(data) {
            var labels = Object.keys(data).slice(-20);
            var prices = labels.map(k => data[k].price);
            chart.data.labels = labels;
            chart.data.datasets[0].data = prices;
            chart.update();
            var tbody = document.querySelector('#signalsTable tbody');
            tbody.innerHTML = '';
            for (var pair in data) {
                var row = `<tr>
                    <td>${pair}</td>
                    <td>${data[pair].price}</td>
                    <td class="${data[pair].signal.toLowerCase().includes('buy') ? 'buy' : (data[pair].signal.toLowerCase().includes('sell') ? 'sell' : '')}">${data[pair].signal}</td>
                    <td>${data[pair].rsi}</td>
                    <td>${data[pair].time}</td>
                </tr>`;
                tbody.innerHTML += row;
            }
        });
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

@socketio.on('connect')
def handle_connect():
    emit('update', latest_data)

def update_dashboard(pair, price, volume, signal=None, rsi=None):
    """Dipanggil dari scanner atau websocket"""
    latest_data[pair] = {
        'price': price,
        'signal': signal or 'HOLD',
        'rsi': rsi or 0,
        'time': datetime.now().strftime("%H:%M:%S")
    }
    socketio.emit('update', latest_data)

def run_dashboard():
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
