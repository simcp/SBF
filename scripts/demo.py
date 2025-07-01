#!/usr/bin/env python3
"""Demo script to show backend capabilities."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services import HyperliquidAPI, DataCollector
from backend.database.connection import init_db, test_connection
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_find_losers():
    """Demonstrate finding bottom traders using Hyperliquid API."""
    print("\n=== Hyperliquid Counter-Trading System Demo ===\n")
    
    # Initialize API
    api = HyperliquidAPI()
    print("✓ Connected to Hyperliquid API (Mainnet)")
    
    # Some known addresses to demo (these are examples - replace with real addresses)
    # In production, these would come from the leaderboard API
    demo_addresses = [
        # Example addresses - in real use, we'd discover these from the leaderboard
        "0x0000000000000000000000000000000000000001",
        "0x0000000000000000000000000000000000000002",
        "0x0000000000000000000000000000000000000003",
        "0x0000000000000000000000000000000000000004",
        "0x0000000000000000000000000000000000000005",
    ]
    
    print("\nFetching trader performance data...")
    print("-" * 80)
    
    traders_data = []
    
    for i, address in enumerate(demo_addresses, 1):
        print(f"\n[{i}/5] Checking trader: {address[:10]}...{address[-6:]}")
        
        # Get user state
        user_state = api.get_user_state(address)
        if not user_state:
            print("  → No data available")
            continue
            
        # Get performance metrics
        performance = api.calculate_trader_performance(address, days=30)
        
        # Get open positions
        positions = api.get_open_positions(address)
        
        trader_info = {
            "address": address,
            "account_value": performance["account_value"],
            "pnl_30d": performance["pnl_percentage"],
            "win_rate": performance["win_rate"],
            "total_trades": performance["total_trades"],
            "open_positions": len(positions),
            "positions": positions
        }
        
        traders_data.append(trader_info)
        
        # Display trader info
        print(f"  → Account Value: ${performance['account_value']:,.2f}")
        print(f"  → 30-Day PnL: {performance['pnl_percentage']:+.2f}%")
        print(f"  → Win Rate: {performance['win_rate']:.1f}%")
        print(f"  → Total Trades (30d): {performance['total_trades']}")
        print(f"  → Open Positions: {len(positions)}")
        
        if positions:
            print("  → Current Positions:")
            for pos in positions:
                print(f"     • {pos['side']} {pos['size']} {pos['coin']} @ ${float(pos['entry_price']):,.2f}")
    
    # Sort by PnL (worst first)
    traders_data.sort(key=lambda x: x["pnl_30d"])
    
    print("\n" + "=" * 80)
    print("BOTTOM 5 TRADERS (30-Day Performance)")
    print("=" * 80)
    
    for i, trader in enumerate(traders_data[:5], 1):
        print(f"\n#{i} Trader: {trader['address'][:10]}...{trader['address'][-6:]}")
        print(f"   Loss: {trader['pnl_30d']:+.2f}% | Win Rate: {trader['win_rate']:.1f}% | Trades: {trader['total_trades']}")
        
        if trader['open_positions'] > 0:
            print(f"   ⚠️  ACTIVE POSITIONS:")
            for pos in trader['positions']:
                opposite = "SHORT" if pos['side'] == "LONG" else "LONG"
                print(f"      → They're {pos['side']} {pos['coin']} - We should {opposite}!")
    
    print("\n" + "=" * 80)
    print("💡 TRADING OPPORTUNITIES")
    print("=" * 80)
    
    opportunities = []
    for trader in traders_data[:5]:
        for pos in trader.get('positions', []):
            opposite = "SHORT" if pos['side'] == "LONG" else "LONG"
            opportunities.append({
                "trader": trader['address'][:10] + "...",
                "action": f"{opposite} {pos['coin']}",
                "reason": f"Trader is {pos['side']} with {trader['pnl_30d']:.1f}% loss rate"
            })
    
    if opportunities:
        for opp in opportunities[:5]:  # Show top 5 opportunities
            print(f"\n• Action: {opp['action']}")
            print(f"  Reason: {opp['reason']}")
    else:
        print("\nNo active positions found among bottom traders.")
    
    print("\n✓ Demo complete!")


def demo_with_real_data():
    """Demo with real trader addresses if available."""
    print("\n=== LIVE DEMO - Fetching Real Hyperliquid Data ===\n")
    
    api = HyperliquidAPI()
    
    # Try to get some real addresses from the exchange
    # Note: You'd need actual trader addresses from the leaderboard
    # This is just showing the capability
    
    print("To run with real data:")
    print("1. Get trader addresses from https://app.hyperliquid.xyz/leaderboard")
    print("2. Replace demo_addresses in the script with real addresses")
    print("3. Run the script again")
    
    # Example of what we can fetch
    print("\nExample API capabilities:")
    print("- Get all trading pairs:", list(api.get_all_mids().keys())[:10], "...")
    print("- Exchange metadata available:", bool(api.get_meta()))


if __name__ == "__main__":
    try:
        # Run basic demo
        demo_find_losers()
        
        print("\n" + "-" * 80)
        
        # Show real data capabilities
        demo_with_real_data()
        
    except Exception as e:
        logger.error(f"Demo error: {e}")
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have:")
        print("1. Python dependencies installed (pip install -r requirements.txt)")
        print("2. Valid network connection")
        print("3. Set HYPERLIQUID_ENV=mainnet in .env file")