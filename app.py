import os
import requests
from flask import Flask, render_template_string, jsonify
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("API_KEY", "demo")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Alpha Vantage AI Report</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #f0f2f5; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 2rem 1rem; }
    .card { background: white; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); padding: 2rem; width: 100%; max-width: 700px; margin-bottom: 1.5rem; }
    h1 { font-size: 1.4rem; color: #1a1a2e; margin-bottom: 0.5rem; }
    .subtitle { color: #666; font-size: 0.9rem; margin-bottom: 1.5rem; }
    .controls { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }
    select, button { padding: 0.6rem 1.2rem; border-radius: 8px; font-size: 0.95rem; cursor: pointer; }
    select { border: 1.5px solid #ddd; background: white; color: #333; flex: 1; min-width: 180px; }
    button { background: #0061eb; color: white; border: none; font-weight: 600; transition: background 0.2s; }
    button:hover { background: #0051c7; }
    button:disabled { background: #aaa; cursor: not-allowed; }
    #status { font-size: 0.88rem; color: #888; margin-bottom: 1rem; min-height: 1.2em; }
    #result { display: none; }
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.75rem; margin-bottom: 1.5rem; }
    .stat-box { background: #f8f9fa; border-radius: 8px; padding: 0.75rem 1rem; }
    .stat-label { font-size: 0.78rem; color: #888; margin-bottom: 0.25rem; }
    .stat-value { font-size: 1.1rem; font-weight: 600; color: #1a1a2e; }
    .ai-section { background: #f0f7ff; border-left: 4px solid #0061eb; border-radius: 0 8px 8px 0; padding: 1rem 1.25rem; white-space: pre-wrap; line-height: 1.7; color: #222; font-size: 0.95rem; }
    .tag { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.78rem; font-weight: 600; margin-bottom: 1rem; }
    .tag-ollama { background: #e8f5e9; color: #2e7d32; }
    .tag-openai { background: #fff3e0; color: #e65100; }
    .tag-local { background: #e3f2fd; color: #1565c0; }
    table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
    th { background: #f0f2f5; padding: 0.5rem 0.75rem; text-align: left; color: #555; font-weight: 600; }
    td { padding: 0.45rem 0.75rem; border-bottom: 1px solid #f0f2f5; color: #333; }
    tr:last-child td { border-bottom: none; }
    h3 { font-size: 1rem; color: #333; margin-bottom: 0.75rem; }
    .section-gap { margin-top: 1.25rem; }
  </style>
</head>
<body>
  <div class="card">
    <h1>📈 Alpha Vantage AI Report</h1>
    <p class="subtitle">Fetch IBM stock data and get AI-powered analysis</p>
    <div class="controls">
      <select id="aiProvider">
        <option value="ollama_local">🖥️ Ollama (Local)</option>
        <option value="ollama_cloud">☁️ Ollama (Cloud)</option>
        <option value="openai">🤖 OpenAI</option>
      </select>
      <button id="runBtn" onclick="runAnalysis()">▶ Run Analysis</button>
    </div>
    <div id="status">Ready. Select an AI provider and click Run.</div>
    <div id="result">
      <div class="stats-grid" id="statsGrid"></div>
      <h3>Last 5 Trading Days</h3>
      <table id="priceTable">
        <thead><tr><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th></tr></thead>
        <tbody id="priceBody"></tbody>
      </table>
      <div class="section-gap">
        <h3>🤖 AI Analysis <span id="providerTag" class="tag"></span></h3>
        <div class="ai-section" id="aiOutput"></div>
      </div>
    </div>
  </div>
  <script>
    async function runAnalysis() {
      const provider = document.getElementById('aiProvider').value;
      const btn = document.getElementById('runBtn');
      btn.disabled = true;
      document.getElementById('status').textContent = '⏳ Fetching stock data and running AI analysis...';
      document.getElementById('result').style.display = 'none';
      try {
        const res = await fetch('/analyze?provider=' + provider);
        const data = await res.json();
        if (data.error) {
          document.getElementById('status').textContent = '❌ Error: ' + data.error;
        } else {
          document.getElementById('status').textContent = '✅ Done — ' + new Date().toLocaleTimeString();
          renderResult(data);
        }
      } catch(e) {
        document.getElementById('status').textContent = '❌ Request failed: ' + e.message;
      }
      btn.disabled = false;
    }

    function renderResult(data) {
      const stats = data.stats;
      document.getElementById('statsGrid').innerHTML = `
        <div class="stat-box"><div class="stat-label">Symbol</div><div class="stat-value">${stats.symbol}</div></div>
        <div class="stat-box"><div class="stat-label">Latest Close</div><div class="stat-value">$${stats.close_latest}</div></div>
        <div class="stat-box"><div class="stat-label">30d Mean</div><div class="stat-value">$${stats.close_mean}</div></div>
        <div class="stat-box"><div class="stat-label">30d High</div><div class="stat-value">$${stats.close_max}</div></div>
        <div class="stat-box"><div class="stat-label">30d Low</div><div class="stat-value">$${stats.close_min}</div></div>
        <div class="stat-box"><div class="stat-label">Trend</div><div class="stat-value" style="font-size:0.85rem">${stats.trend_note}</div></div>
      `;
      const tbody = document.getElementById('priceBody');
      tbody.innerHTML = '';
      data.recent_days.forEach(row => {
        tbody.innerHTML += `<tr><td>${row.date}</td><td>${row.open}</td><td>${row.high}</td><td>${row.low}</td><td>${row.close}</td><td>${Number(row.volume).toLocaleString()}</td></tr>`;
      });
      const tag = document.getElementById('providerTag');
      tag.textContent = data.provider_label;
      tag.className = 'tag ' + data.provider_class;
      document.getElementById('aiOutput').textContent = data.ai_response;
      document.getElementById('result').style.display = 'block';
    }
  </script>
</body>
</html>
"""

def fetch_stock_data():
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": "IBM",
        "apikey": API_KEY
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    ts = data.get("Time Series (Daily)")
    if not ts:
        raise ValueError("No time series data returned. Check API key.")
    rows = []
    for date, vals in ts.items():
        rows.append({
            "date": date,
            "open": round(float(vals["1. open"]), 2),
            "high": round(float(vals["2. high"]), 2),
            "low": round(float(vals["3. low"]), 2),
            "close": round(float(vals["4. close"]), 2),
            "volume": int(float(vals["5. volume"]))
        })
    rows.sort(key=lambda x: x["date"])
    rows = rows[-30:]
    return rows

def build_stats(rows):
    closes = [r["close"] for r in rows]
    last5 = closes[-5:]
    prev5 = closes[-10:-5]
    trend = "recent 5 days higher than previous 5" if prev5 and sum(last5)/5 > sum(prev5)/len(prev5) else "recent 5 days lower than previous 5"
    return {
        "symbol": "IBM",
        "n_days": len(rows),
        "date_range": f"{rows[0]['date']} to {rows[-1]['date']}",
        "close_min": min(closes),
        "close_max": max(closes),
        "close_mean": round(sum(closes)/len(closes), 2),
        "close_latest": closes[-1],
        "volume_mean": int(sum(r["volume"] for r in rows)/len(rows)),
        "trend_note": trend
    }

def build_prompt(stats, rows):
    recent = rows[-5:]
    table = "\n".join(
        f"  {r['date']}  open={r['open']} high={r['high']} low={r['low']} close={r['close']} vol={r['volume']}"
        for r in recent
    )
    summary = (
        f"Summary statistics:\n"
        f"  Symbol: {stats['symbol']}\n"
        f"  Days: {stats['n_days']} ({stats['date_range']})\n"
        f"  Close price: min {stats['close_min']}, max {stats['close_max']}, mean {stats['close_mean']}, latest {stats['close_latest']}\n"
        f"  Volume (avg): {stats['volume_mean']}\n"
        f"  Trend: {stats['trend_note']}\n"
    )
    return (
        "You are a concise financial data analyst. Below is processed daily stock data from Alpha Vantage.\n\n"
        f"--- DATA ---\n{summary}\nLast 5 days:\n{table}\n--- END DATA ---\n\n"
        "Please respond in this exact format:\n"
        "1. Summary (2-3 sentences): key statistics and what they mean.\n"
        "2. Trends: brief note on recent price/volume pattern.\n"
        "3. Recommendations: 2-3 bullet points (actionable, short).\n"
        "Use plain language and keep the total response under 150 words."
    )

def call_ollama_local(prompt):
    res = requests.post("http://localhost:11434/api/chat", json={
        "model": "gemma3:latest",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }, timeout=60)
    res.raise_for_status()
    return res.json()["message"]["content"]

def call_ollama_cloud(prompt):
    res = requests.post("https://ollama.com/api/chat", json={
        "model": "gpt-oss:20b-cloud",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }, headers={
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }, timeout=60)
    res.raise_for_status()
    return res.json()["message"]["content"]

def call_openai(prompt):
    res = requests.post("https://api.openai.com/v1/chat/completions", json={
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300
    }, headers={
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }, timeout=60)
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"]

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/analyze")
def analyze():
    from flask import request as freq
    provider = freq.args.get("provider", "ollama_local")
    try:
        rows = fetch_stock_data()
        stats = build_stats(rows)
        prompt = build_prompt(stats, rows)

        if provider == "ollama_local":
            ai_response = call_ollama_local(prompt)
            label, cls = "Ollama Local", "tag-local"
        elif provider == "ollama_cloud":
            ai_response = call_ollama_cloud(prompt)
            label, cls = "Ollama Cloud", "tag-ollama"
        else:
            ai_response = call_openai(prompt)
            label, cls = "OpenAI", "tag-openai"

        return jsonify({
            "stats": stats,
            "recent_days": rows[-5:],
            "ai_response": ai_response,
            "provider_label": label,
            "provider_class": cls
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
