#!/usr/bin/env python3
"""Find losing traders who are still actively trading."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from backend.services import HyperliquidAPI


def find_active_losers():
    """Find traders with negative ROI who still have capital and positions."""
    print("\n=== Finding Active Losing Traders ===\n")
    
    # Load leaderboard data
    with open("leaderboard_data.json", "r") as f:
        data = json.load(f)
    
    leaderboard = data.get("leaderboardRows", [])
    
    # Find traders with negative ROI but positive account value
    active_losers = []
    
    for row in leaderboard:
        account_value = float(row.get("accountValue", 0))
        
        # Skip if account is empty
        if account_value < 1000:  # At least $1000 to be worth tracking
            continue
        
        # Get 30-day performance
        month_perf = None
        for window in row.get("windowPerformances", []):
            if window[0] == "month":
                month_perf = window[1]
                break
        
        if month_perf:
            roi = float(month_perf.get("roi", 0))
            roi_percent = roi * 100
            
            # Only interested in losers
            if roi_percent < -10:  # At least -10% loss
                active_losers.append({
                    "address": row.get("ethAddress"),
                    "name": row.get("displayName", "Unknown"),
                    "account_value": account_value,
                    "roi_30d_percent": roi_percent,
                    "pnl_30d": float(month_perf.get("pnl", 0)),
                    "volume_30d": float(month_perf.get("vlm", 0))
                })
    
    # Sort by ROI (worst first)
    active_losers.sort(key=lambda x: x["roi_30d_percent"])
    
    print(f"Found {len(active_losers)} active traders with >10% losses and >$1000 capital")
    
    # Check top 10 for positions
    api = HyperliquidAPI()
    traders_with_positions = []
    
    print("\nChecking for open positions...")
    for i, trader in enumerate(active_losers[:20]):  # Check top 20 losers
        print(f"\r  Checking trader {i+1}/20...", end="", flush=True)
        
        try:
            positions = api.get_open_positions(trader['address'])
            if positions:
                trader['positions'] = positions
                traders_with_positions.append(trader)
        except:
            pass
    
    print("\n\n" + "="*80)
    print("ACTIVE LOSING TRADERS WITH OPEN POSITIONS")
    print("="*80)
    
    opportunities = []
    
    for i, trader in enumerate(traders_with_positions[:5], 1):
        print(f"\n#{i} {trader['name']} ({trader['address'][:10]}...)")
        print(f"   30-Day Loss: {trader['roi_30d_percent']:+.2f}% (${trader['pnl_30d']:+,.2f})")
        print(f"   Current Capital: ${trader['account_value']:,.2f}")
        print(f"   Open Positions:")
        
        for pos in trader['positions']:
            opposite = "SHORT" if pos['side'] == "LONG" else "LONG"
            pnl = float(pos.get('unrealized_pnl', 0))
            
            print(f"     • {pos['side']} {float(pos['size']):.4f} {pos['coin']} @ ${float(pos['entry_price']):,.2f}")
            print(f"       Unrealized PnL: ${pnl:+,.2f}")
            print(f"       → COUNTER: {opposite} {pos['coin']}")
            
            opportunities.append({
                "trader_name": trader['name'],
                "trader_loss": trader['roi_30d_percent'],
                "coin": pos['coin'],
                "action": f"{opposite} {pos['coin']}",
                "reason": f"Trader with {trader['roi_30d_percent']:.1f}% monthly loss is {pos['side']}",
                "confidence": min(95, 70 + abs(trader['roi_30d_percent']) * 0.5)  # Higher loss = higher confidence
            })
    
    print("\n" + "="*80)
    print("🎯 HIGH-CONFIDENCE COUNTER-TRADE OPPORTUNITIES")
    print("="*80)
    
    # Sort by confidence
    opportunities.sort(key=lambda x: x['confidence'], reverse=True)
    
    for i, opp in enumerate(opportunities[:10], 1):
        print(f"\n{i}. {opp['action']} (Confidence: {opp['confidence']:.0f}%)")
        print(f"   {opp['reason']}")
    
    return traders_with_positions, opportunities


if __name__ == "__main__":
    try:
        traders, opportunities = find_active_losers()
        
        print(f"\n\n✓ Found {len(traders)} active losing traders with positions")
        print(f"✓ Generated {len(opportunities)} counter-trade opportunities")
        
        # Save for the app
        with open("active_losers.json", "w") as f:
            json.dump({
                "traders": traders[:10],  # Top 10
                "opportunities": opportunities[:20]  # Top 20 opportunities
            }, f, indent=2)
        
        print("✓ Data saved to active_losers.json")
        
    except Exception as e:
        print(f"❌ Error: {e}")