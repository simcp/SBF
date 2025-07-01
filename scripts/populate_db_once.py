#!/usr/bin/env python3
"""One-time script to populate database with current loser data."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services import DataCollector, TradingAnalyzer
import json

def main():
    """Populate database with current data."""
    print("Populating database with current losing trader data...")
    
    collector = DataCollector()
    analyzer = TradingAnalyzer()
    
    # Load the data from our JSON file
    try:
        with open('active_losers.json', 'r') as f:
            data = json.load(f)
            traders = data.get('traders', [])
    except:
        print("No active_losers.json found, fetching fresh data...")
        # Get fresh data from API
        traders = []
    
    if not traders:
        print("Fetching top losers from Hyperliquid...")
        losers = collector.get_top_losers(limit=50)
        print(f"Found {len(losers)} losing traders")
        
        # Collect detailed data for each
        addresses = [loser["address"] for loser in losers]
        print(f"Collecting detailed data for {len(addresses)} traders...")
        
        results = collector.collect_multiple_traders(addresses)
        success_count = sum(1 for success in results.values() if success)
        print(f"Successfully stored {success_count}/{len(addresses)} traders in database")
    else:
        print(f"Processing {len(traders)} traders from JSON...")
        for i, trader in enumerate(traders):
            print(f"Processing trader {i+1}/{len(traders)}: {trader['address'][:10]}...")
            try:
                collector.collect_trader_data(trader['address'])
            except Exception as e:
                print(f"  Failed: {e}")
    
    # Analyze positions to generate opportunities
    print("Analyzing positions for trade opportunities...")
    opportunities = analyzer.analyze_new_positions()
    print(f"Generated {len(opportunities)} trade opportunities!")
    
    for opp in opportunities[:10]:  # Show first 10
        print(f"  - {opp.coin}: {opp.loser_side} → {opp.suggested_side} (confidence: {opp.confidence_score}%)")
    
    print("\nDatabase population complete!")
    print("You can now refresh the frontend to see the data.")

if __name__ == "__main__":
    main()