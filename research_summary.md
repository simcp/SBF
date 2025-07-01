# Hyperliquid Counter-Trading Research Summary

## Key Findings

### 1. **API Capabilities**
- **Public Access**: All trader data is accessible without authentication using wallet addresses
- **Official Python SDK**: `pip install hyperliquid-python-sdk`
- **Rate Limits**: 1200 weight points/minute for REST, 1000 WebSocket subscriptions per IP
- **Key Endpoints**:
  - User state/positions: `info.user_state(address)`
  - Portfolio history: Includes 30+ days of PnL data
  - Leaderboard: `https://stats-data.hyperliquid.xyz/Mainnet/leaderboard`
  - Real-time updates via WebSocket

### 2. **Available Trader Data**
- **Performance Metrics**: Daily/weekly/monthly/all-time PnL
- **Position Data**: Current positions with entry prices, sizes, unrealized PnL
- **Trade History**: All fills with timestamps, prices, sizes
- **Account Values**: Historical account value tracking
- **Win Rates**: Calculable from fills data
- **Volume Data**: Trading volume across time periods

### 3. **Technical Requirements**
- **Polling Intervals**: 5-10 seconds for active positions, 30-60 seconds for account states
- **Storage Needs**: ~15-20GB for 500 traders over 30 days (without order book data)
- **Architecture**: Hybrid approach - WebSocket for real-time, REST for historical
- **Database**: PostgreSQL recommended (used by community projects)

### 4. **Existing Solutions**
- **Commercial**: SuperX (Telegram bot), Mizar, HyperDash
- **Open Source**: 
  - `lucyCooked/hyperliquid-copytrader` - Dedicated copy trading
  - `oni-giri/hyperliquid-monitor` - Real-time monitoring
  - Several trading bots with strategy implementations

### 5. **Implementation Considerations**
- **No authentication needed** for reading trader data
- **Traders identified by wallet addresses** (no usernames)
- **WebSocket preferred** for real-time position tracking
- **Batch operations** recommended to minimize API calls
- **Circuit breakers** needed for API failures

## Recommended Approach

1. **Start Simple**: Use REST API to fetch top losers daily
2. **Track Performance**: Store 30-day rolling metrics in PostgreSQL
3. **Monitor Positions**: Use WebSocket for real-time position updates
4. **Generate Signals**: Detect new positions and suggest counter-trades
5. **Scale Later**: Add more traders, reduce latency as needed

## Next Steps

1. Set up Python environment with official SDK
2. Create database schema for trader tracking
3. Build data collector to identify top 500 losers
4. Implement position monitoring system
5. Create simple dashboard for monitoring opportunities