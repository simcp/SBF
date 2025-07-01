#!/usr/bin/env python3
"""Script to find real active traders on Hyperliquid."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from backend.services import HyperliquidAPI
import json


def find_active_traders():
    """Find real active traders from Hyperliquid."""
    print("\n=== Finding Real Hyperliquid Traders ===\n")
    
    # Try to get leaderboard data
    try:
        # Fetch from the stats API
        response = requests.get("https://stats-data.hyperliquid.xyz/Mainnet/leaderboard")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Found leaderboard data!")
            
            # Save for inspection
            with open("leaderboard_data.json", "w") as f:
                json.dump(data, f, indent=2)
            print(f"✓ Saved raw data to leaderboard_data.json")
            
            # Try to parse the data structure
            if isinstance(data, list) and len(data) > 0:
                print(f"\nFound {len(data)} entries")
                print("\nSample entry structure:")
                print(json.dumps(data[0], indent=2)[:500] + "...")
            elif isinstance(data, dict):
                print("\nData structure:")
                print(f"Keys: {list(data.keys())}")
                
            return data
        else:
            print(f"❌ Failed to fetch leaderboard: {response.status_code}")
    except Exception as e:
        print(f"❌ Error fetching leaderboard: {e}")
    
    # Alternative: Try to get data from the API
    print("\nTrying alternative method...")
    api = HyperliquidAPI()
    
    # Get exchange info
    meta = api.get_meta()
    print(f"\n✓ Connected to Hyperliquid")
    print(f"  Available coins: {len(meta.get('universe', []))} trading pairs")
    
    # Try the info endpoint for leaderboard
    try:
        response = requests.post(
            "https://api.hyperliquid.xyz/info",
            json={"type": "leaderboard"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Got leaderboard via info endpoint")
            with open("leaderboard_info.json", "w") as f:
                json.dump(data, f, indent=2)
            return data
    except Exception as e:
        print(f"Info endpoint error: {e}")
    
    # Try vault endpoint
    try:
        response = requests.post(
            "https://api.hyperliquid.xyz/info",
            json={"type": "vaults"}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"\n✓ Got vault data")
            with open("vault_data.json", "w") as f:
                json.dump(data, f, indent=2)
            
            if isinstance(data, list) and len(data) > 0:
                print(f"Found {len(data)} vaults")
                # Vaults have leaders we can track
                for vault in data[:5]:
                    if 'leader' in vault:
                        print(f"  Vault leader: {vault['leader']}")
            return data
    except Exception as e:
        print(f"Vault endpoint error: {e}")
    
    return None


def analyze_trader(api, address):
    """Analyze a single trader."""
    print(f"\nAnalyzing trader: {address}")
    
    # Get performance
    perf = api.calculate_trader_performance(address, days=30)
    positions = api.get_open_positions(address)
    
    print(f"  → 30-Day PnL: {perf['pnl_percentage']:+.2f}%")
    print(f"  → Win Rate: {perf['win_rate']:.1f}%")
    print(f"  → Total Trades: {perf['total_trades']}")
    print(f"  → Account Value: ${perf['account_value']:,.2f}")
    
    if positions:
        print(f"  → Open Positions:")
        for pos in positions:
            print(f"     • {pos['side']} {pos['size']} {pos['coin']} @ ${float(pos['entry_price']):,.2f}")
    
    return perf, positions


if __name__ == "__main__":
    # Find traders
    data = find_active_traders()
    
    # If we found some addresses, analyze them
    if data:
        print("\n" + "="*80)
        print("Check the generated JSON files to see the data structure.")
        print("We can then extract trader addresses and analyze them.")
        
        # If we found vault data with leaders
        if isinstance(data, list) and len(data) > 0 and 'leader' in data[0]:
            print("\nAnalyzing some vault leaders...")
            api = HyperliquidAPI()
            
            losers = []
            for vault in data[:20]:  # Check first 20 vaults
                if 'leader' in vault:
                    leader = vault['leader']
                    perf, positions = analyze_trader(api, leader)
                    
                    if perf['pnl_percentage'] < 0:  # Found a loser
                        losers.append({
                            'address': leader,
                            'pnl': perf['pnl_percentage'],
                            'win_rate': perf['win_rate'],
                            'positions': positions
                        })
            
            if losers:
                print("\n" + "="*80)
                print("FOUND LOSING TRADERS!")
                print("="*80)
                
                losers.sort(key=lambda x: x['pnl'])  # Sort by worst PnL
                
                for i, loser in enumerate(losers[:5], 1):
                    print(f"\n#{i} Address: {loser['address']}")
                    print(f"    Loss: {loser['pnl']:+.2f}% | Win Rate: {loser['win_rate']:.1f}%")
                    
                    if loser['positions']:
                        print("    ⚠️  ACTIVE POSITIONS - COUNTER TRADE OPPORTUNITIES:")
                        for pos in loser['positions']:
                            opposite = "SHORT" if pos['side'] == "LONG" else "LONG"
                            print(f"       → Do {opposite} {pos['coin']} (they're {pos['side']})")