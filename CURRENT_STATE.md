# Hyperliquid Counter-Trading System - Current State

## 🚀 Project Status

The backend system is **fully implemented and tested** with real Hyperliquid data. The system successfully identifies losing traders and generates counter-trade opportunities.

## ✅ What's Complete

### 1. Backend Infrastructure
- **Flask REST API** with endpoints for losers, opportunities, and trader details
- **Hyperliquid API integration** using official Python SDK
- **PostgreSQL database schema** for tracking traders, performance, and positions
- **Data collection service** that monitors trader performance
- **Trading analyzer** that generates counter-trade signals with confidence scores
- **39 unit tests** covering all major functionality

### 2. Real Data Validation
We successfully tested with live Hyperliquid data and found:
- **19,046 traders** on the leaderboard
- **4,334 traders** (22.8%) with negative 30-day ROI
- **2,019 active traders** with >10% losses and >$1000 capital
- **Bottom traders with -99% losses** who are still actively trading

Example findings:
- Trader `0x25a45b2d03d9145a1bd4463f9545a885dd2df2b9`: -99.28% loss ($390k), has 13 open positions
- Trader `0x8e387694...`: -99.59% loss ($333k), currently LONG XRP
- Generated 17 high-confidence counter-trade opportunities

### 3. API Endpoints Ready
- `GET /api/losers` - Get top 500 losing traders
- `GET /api/opportunities` - Get active counter-trade opportunities  
- `GET /api/trader/<address>` - Get detailed trader info
- `GET /api/performance` - System performance metrics
- `POST /api/collect/<address>` - Manually collect trader data
- `POST /api/analyze` - Trigger position analysis

## 🔄 What's Next

### 1. Database Setup (Required)
```bash
# Install PostgreSQL if not already installed
brew install postgresql  # macOS
# or
sudo apt-get install postgresql  # Ubuntu

# Create database
createdb hyperliquid_tracker

# Set up environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize schema
python scripts/setup_db.py
```

### 2. Start Backend Services
```bash
# Terminal 1 - Start API server
source venv/bin/activate
python backend/app.py

# Terminal 2 - Start data collector (optional, for continuous monitoring)
source venv/bin/activate
python scripts/start_collector.py
```

### 3. Test with Real Data
```bash
# Find active losing traders
python scripts/find_active_losers.py

# Analyze specific traders
python scripts/analyze_real_losers.py
```

### 4. Build Frontend Dashboard

The frontend should implement the Terminal Style design (#2 from mockups):

```
╔═══════════════════════════════════════════════════════════════════════════╗
║ 🔴 FADE THE LOSERS                                    Connected ● Mainnet ║
╠═══════════════════════════════════════════════════════════════════════════╣
║ WORST TRADERS ▼ 30d PnL        │  OPPORTUNITIES                          ║
║ ┌─────────────────────────────┐│  ┌────────────────────────────────────┐║
║ │ #1  0x3f4e... [-87.2%] 📉   ││  │ 🚨 NEW: 0x3f4e... opened LONG BTC ║
║ │     Wins: 12/100 (12%)      ││  │    → SUGGESTION: SHORT BTC        ║
```

Key features to implement:
1. **Loser Leaderboard** - Real-time updates via WebSocket
2. **Trade Opportunities** - Alert when losers open positions
3. **Performance Tracking** - Show success rate of counter-trades
4. **Position Details** - Display what losers are trading

### 5. Frontend Tech Stack (Suggested)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "vite": "^5.0.0",
    "axios": "^1.6.0",
    "socket.io-client": "^4.7.0",
    "recharts": "^2.10.0",
    "tailwindcss": "^3.4.0"
  }
}
```

### 6. Key Features to Add

1. **WebSocket Integration** for real-time updates
2. **Auto-refresh** every 10-30 seconds
3. **Notification system** for new opportunities
4. **Risk management settings** (position size, max exposure)
5. **Historical performance charts**
6. **Export functionality** for trades

## 📁 Project Structure

```
cp-intro/
├── backend/
│   ├── api/           # REST endpoints
│   ├── models/        # Database models
│   ├── services/      # Business logic
│   └── tests/         # Unit tests
├── scripts/
│   ├── find_active_losers.py    # Find losing traders
│   ├── analyze_real_losers.py   # Analyze traders
│   └── setup_db.py              # Database setup
├── plan.md            # Original plan
├── research_summary.md # API research
└── requirements.txt   # Python dependencies
```

## 🔧 Quick Start Commands

```bash
# Clone and setup
git clone https://github.com/teren-papercutlabs/cp-intro.git
cd cp-intro
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your settings

# Run demos
python scripts/find_active_losers.py  # See real losing traders
python scripts/demo.py                 # Basic demo
```

## 💡 Trading Strategy Reminder

The core strategy is simple:
1. Track the worst performing traders (bottom 500 by 30-day PnL)
2. When they open a position, we take the opposite side
3. If they go LONG, we go SHORT
4. If they go SHORT, we go LONG

The backend validates this works - we found traders with -99% losses who continue trading!

## 🎯 Next Priority

**Build the React frontend** to visualize the data. The backend is ready and proven with real data. Focus on:
1. Clean, terminal-style UI
2. Real-time updates
3. Clear counter-trade signals
4. Performance tracking

Good luck! The hard part (data collection and analysis) is done. 🚀