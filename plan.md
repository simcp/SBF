# Hyperliquid Counter-Trading System Plan

## Overview
Build a local system that tracks the top 500 losing traders on Hyperliquid exchange over the past 30 days and identifies opportunities to take opposing positions to their trades.

## Core Strategy
- Track traders with worst PnL% and win rates over 30-day rolling window
- When identified losers open positions, suggest opposite trades
- If loser goes long → we go short
- If loser goes short → we go long

## Architecture: Lightweight Local Solution

### Tech Stack
- **Backend**: Python 3.10+
- **Database**: PostgreSQL (local)
- **API Layer**: Flask/FastAPI
- **Frontend**: React with Vite
- **Data Processing**: Pandas, NumPy
- **Scheduling**: APScheduler
- **WebSocket**: Socket.io (optional for real-time)

### System Components

#### 1. Data Collection Service (Python)
- **Purpose**: Continuously fetch and process trader data from Hyperliquid
- **Responsibilities**:
  - Poll Hyperliquid API for trader positions and PnL data
  - Calculate 30-day performance metrics
  - Identify top 500 losers
  - Store historical data for analysis
- **Run frequency**: Every 5-15 minutes (based on API limits)

#### 2. PostgreSQL Database
- **Tables**:
  - `traders`: Basic trader info and current metrics
  - `performance_history`: Daily snapshots of trader performance
  - `positions`: All positions opened by tracked traders
  - `trade_opportunities`: Generated counter-trade suggestions
  - `api_logs`: Track API usage and rate limits

#### 3. Analysis Engine
- **Purpose**: Process trader data and generate trade signals
- **Features**:
  - Calculate rolling 30-day PnL%, win rate, total losses
  - Rank traders by "badness" score
  - Detect when top losers open new positions
  - Generate counter-trade recommendations

#### 4. Flask/FastAPI Backend
- **Endpoints**:
  - `GET /api/losers` - Top 500 losers with metrics
  - `GET /api/opportunities` - Current counter-trade opportunities
  - `GET /api/performance` - System performance metrics
  - `GET /api/trader/{id}/history` - Individual trader analysis
  - `WebSocket /ws/trades` - Real-time trade updates (optional)

#### 5. React Dashboard
- **Key Views**:
  - **Loser Leaderboard**: Sortable table of worst performers
  - **Trade Opportunities**: Active counter-trade suggestions
  - **Performance Dashboard**: Track success of counter-trades
  - **Trader Detail**: Deep dive into specific trader's history

## Implementation Phases

### Phase 1: Research & Setup (Day 1-2)
1. Study Hyperliquid API documentation
2. Verify what trader data is publicly accessible
3. Set up development environment
4. Create PostgreSQL database
5. Initialize Git repository structure

### Phase 2: Data Collection (Day 3-5)
1. Build Hyperliquid API client
2. Implement rate limiting and error handling
3. Create data models for traders and positions
4. Build performance calculation logic
5. Set up scheduled data collection

### Phase 3: Analysis Engine (Day 6-7)
1. Implement 30-day rolling window calculations
2. Create loser ranking algorithm
3. Build position detection system
4. Generate counter-trade logic
5. Add backtesting capabilities

### Phase 4: API Development (Day 8-9)
1. Design RESTful API structure
2. Implement all endpoints
3. Add authentication (basic token)
4. Create API documentation
5. Add error handling and logging

### Phase 5: Frontend Dashboard (Day 10-12)
1. Set up React with Vite
2. Create component library
3. Build main dashboard views
4. Implement data visualization
5. Add filtering and sorting

### Phase 6: Testing & Refinement (Day 13-14)
1. End-to-end testing
2. Performance optimization
3. UI/UX improvements
4. Documentation
5. Deployment scripts

## Project Structure
```
cp-intro/
├── backend/
│   ├── app.py                 # Flask application
│   ├── config.py              # Configuration
│   ├── models/               
│   │   ├── trader.py         
│   │   ├── position.py       
│   │   └── opportunity.py    
│   ├── services/
│   │   ├── hyperliquid_api.py # API client
│   │   ├── data_collector.py  # Data fetching
│   │   └── analyzer.py        # Analysis logic
│   ├── api/
│   │   └── routes.py         # API endpoints
│   └── database/
│       ├── schema.sql        
│       └── connection.py     
├── frontend/
│   ├── src/
│   │   ├── components/       
│   │   ├── pages/           
│   │   ├── services/        # API calls
│   │   └── utils/           
│   └── package.json
├── scripts/
│   ├── setup_db.py          # Database initialization
│   ├── start_collector.py   # Run data collection
│   └── backtest.py         # Backtesting script
├── requirements.txt
├── README.md
└── .env.example

```

## Key Considerations

### API Rate Limits
- Implement exponential backoff
- Cache frequently accessed data
- Use batch requests where possible
- Monitor API usage in database

### Data Quality
- Handle missing data gracefully
- Validate all calculations
- Store raw data for reprocessing
- Log anomalies for investigation

### Performance
- Index database properly
- Implement pagination
- Use connection pooling
- Cache expensive calculations

### Security
- Store API keys in environment variables
- Implement basic authentication for dashboard
- Sanitize all user inputs
- Use HTTPS for production

## Success Metrics
- System uptime
- Data collection success rate
- Counter-trade win rate
- Average profit per trade
- Reduction in API errors

## Future Enhancements
1. Machine learning for loser pattern recognition
2. Integration with trading execution
3. Multi-exchange support
4. Mobile app
5. Advanced backtesting suite

## Development Timeline
- **Week 1**: Phases 1-3 (Core functionality)
- **Week 2**: Phases 4-6 (API & Frontend)
- **Week 3**: Testing, optimization, and deployment

## Getting Started
1. Clone repository
2. Install PostgreSQL locally
3. Set up Python virtual environment
4. Configure Hyperliquid API credentials
5. Run database setup script
6. Start data collector
7. Launch Flask API
8. Start React development server