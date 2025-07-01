# Claude Development Notes

## Project Context
This is a Hyperliquid counter-trading system that tracks losing traders and generates counter-trade opportunities. The backend is fully built and tested with real data.

## Environment Setup
- Database: PostgreSQL (installed via brew)
- Database name: `hyperliquid_tracker`
- API runs on port 5001 (due to macOS port 5000 conflict)
- Python virtual environment: `venv/`

## Running Commands
- Always activate virtual environment: `source venv/bin/activate`
- Set PYTHONPATH for imports: `PYTHONPATH=. python backend/app.py`

## Long-Running Processes
**IMPORTANT**: Claude cannot run long-running processes (like servers, background tasks, or processes that don't terminate quickly). For these, ask the user to run them manually in their terminal.

Examples that need user to run:
- `python backend/app.py` (Flask server)
- `python scripts/start_collector.py` (data collector)
- `npm run dev` (frontend dev server)

## Testing Commands
- Find active losers: `python scripts/find_active_losers.py`
- Test API health: `curl http://localhost:5001/health`
- Run tests: `pytest`

## Next Steps
1. Backend is complete and working ✓
2. Database is set up ✓  
3. Need to build React frontend dashboard
4. Focus on terminal-style UI as specified in CURRENT_STATE.md