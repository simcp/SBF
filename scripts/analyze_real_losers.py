#!/usr/bin/env python3
"""Analyze real traders from Hyperliquid leaderboard to find losers."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from backend.services import HyperliquidAPI


def find_bottom_traders():
    """Find the worst performing traders from leaderboard data."""
    print("\n=== Analyzing Hyperliquid Leaderboard for Worst Traders ===\n")
    
    # Load leaderboard data
    with open("leaderboard_data.json", "r") as f:
        data = json.load(f)
    
    leaderboard = data.get("leaderboardRows", [])
    print(f"Found {len(leaderboard)} traders on leaderboard")
    
    # Extract trader performance
    traders = []
    for row in leaderboard:
        address = row.get("ethAddress")
        display_name = row.get("displayName", "Unknown")
        account_value = float(row.get("accountValue", 0))
        
        # Get 30-day (month) performance
        month_perf = None
        for window in row.get("windowPerformances", []):
            if window[0] == "month":
                month_perf = window[1]
                break
        
        if month_perf:
            pnl = float(month_perf.get("pnl", 0))
            roi = float(month_perf.get("roi", 0))
            roi_percent = roi * 100  # Convert to percentage
            
            traders.append({
                "address": address,
                "name": display_name,
                "account_value": account_value,
                "pnl_30d": pnl,
                "roi_30d_percent": roi_percent,
                "volume_30d": float(month_perf.get("vlm", 0))
            })
    
    # Sort by ROI (worst first)
    traders.sort(key=lambda x: x["roi_30d_percent"])
    
    # Get bottom 5
    bottom_5 = traders[:5]
    
    print("\n" + "="*80)
    print("BOTTOM 5 TRADERS BY 30-DAY ROI")
    print("="*80)
    
    for i, trader in enumerate(bottom_5, 1):
        print(f"\n#{i} {trader['name']} ({trader['address'][:10]}...{trader['address'][-6:]})")
        print(f"   30-Day ROI: {trader['roi_30d_percent']:+.2f}%")
        print(f"   30-Day PnL: ${trader['pnl_30d']:+,.2f}")
        print(f"   Account Value: ${trader['account_value']:,.2f}")
        print(f"   30-Day Volume: ${trader['volume_30d']:,.2f}")
    
    # Now let's check their actual positions
    print("\n" + "="*80)
    print("CHECKING CURRENT POSITIONS FOR COUNTER-TRADING")
    print("="*80)
    
    api = HyperliquidAPI()
    opportunities = []
    
    for trader in bottom_5:
        print(f"\nAnalyzing {trader['name']}...")
        
        try:
            # Get current positions
            positions = api.get_open_positions(trader['address'])
            
            if positions:
                print(f"  ✓ Found {len(positions)} open positions:")
                for pos in positions:
                    opposite = "SHORT" if pos['side'] == "LONG" else "LONG"
                    print(f"    • {pos['side']} {pos['size']} {pos['coin']} @ ${float(pos['entry_price']):,.2f}")
                    print(f"      → COUNTER-TRADE: {opposite} {pos['coin']}")
                    
                    opportunities.append({
                        "loser": trader['name'],
                        "loser_roi": trader['roi_30d_percent'],
                        "coin": pos['coin'],
                        "loser_side": pos['side'],
                        "suggested_side": opposite,
                        "size": float(pos['size']),
                        "entry_price": float(pos['entry_price'])
                    })
            else:
                print(f"  → No open positions")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    if opportunities:
        print("\n" + "="*80)
        print("💡 TOP COUNTER-TRADING OPPORTUNITIES")
        print("="*80)
        
        # Sort by loser's negative ROI (worst losers first)
        opportunities.sort(key=lambda x: x['loser_roi'])
        
        for i, opp in enumerate(opportunities[:10], 1):
            print(f"\n{i}. {opp['suggested_side']} {opp['coin']}")
            print(f"   Why: {opp['loser']} (ROI: {opp['loser_roi']:+.2f}%) is {opp['loser_side']}")
            print(f"   Their position: {opp['size']} @ ${opp['entry_price']:,.2f}")
    
    # Also find losing traders with negative ROI
    losing_traders = [t for t in traders if t['roi_30d_percent'] < 0]
    print(f"\n\n📊 STATISTICS:")
    print(f"  • Total traders on leaderboard: {len(traders)}")
    print(f"  • Traders with negative 30-day ROI: {len(losing_traders)}")
    print(f"  • Worst ROI: {traders[0]['roi_30d_percent']:+.2f}%")
    print(f"  • Best ROI: {traders[-1]['roi_30d_percent']:+.2f}%")
    
    return bottom_5, opportunities


if __name__ == "__main__":
    try:
        bottom_traders, opportunities = find_bottom_traders()
        
        # Save results
        results = {
            "bottom_5_traders": bottom_traders,
            "counter_trade_opportunities": opportunities
        }
        
        with open("analysis_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print("\n✓ Analysis complete! Results saved to analysis_results.json")
        
    except FileNotFoundError:
        print("❌ Error: leaderboard_data.json not found")
        print("Run find_real_traders.py first to fetch the data")
    except Exception as e:
        print(f"❌ Error: {e}")