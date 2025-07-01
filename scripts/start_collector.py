#!/usr/bin/env python3
"""Script to start the data collector."""

import sys
import os
import time
import logging
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services import DataCollector, TradingAnalyzer
from backend.config import POLL_INTERVAL_SECONDS, POSITION_CHECK_INTERVAL

logger = logging.getLogger(__name__)


def main():
    """Run the data collector."""
    print("Starting Hyperliquid data collector...")
    
    collector = DataCollector()
    analyzer = TradingAnalyzer()
    
    # Example trader addresses to track (replace with real ones)
    # These would normally come from discovering top losers
    tracked_addresses = [
        # Add real addresses here
    ]
    
    last_position_check = time.time()
    
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Running collection cycle...")
            
            # Get top losers if we don't have any addresses yet
            if not tracked_addresses:
                print("Fetching top losers...")
                losers = collector.get_top_losers(limit=10)
                tracked_addresses = [loser["address"] for loser in losers]
                print(f"Tracking {len(tracked_addresses)} traders")
            
            # Collect data for tracked traders
            if tracked_addresses:
                print(f"Collecting data for {len(tracked_addresses)} traders...")
                results = collector.collect_multiple_traders(tracked_addresses)
                success_count = sum(1 for success in results.values() if success)
                print(f"Successfully collected data for {success_count}/{len(tracked_addresses)} traders")
            
            # Check for new positions periodically
            if time.time() - last_position_check >= POSITION_CHECK_INTERVAL:
                print("Analyzing new positions...")
                opportunities = analyzer.analyze_new_positions()
                if opportunities:
                    print(f"Generated {len(opportunities)} new trade opportunities!")
                    for opp in opportunities:
                        print(f"  - {opp.coin}: {opp.loser_side} → {opp.suggested_side} (confidence: {opp.confidence_score}%)")
                
                # Expire old opportunities
                analyzer.expire_old_opportunities()
                last_position_check = time.time()
            
            # Sleep until next cycle
            print(f"Sleeping for {POLL_INTERVAL_SECONDS} seconds...")
            time.sleep(POLL_INTERVAL_SECONDS)
            
    except KeyboardInterrupt:
        print("\nShutting down collector...")
        return 0
    except Exception as e:
        logger.error(f"Error in collector: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())