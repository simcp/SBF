#!/usr/bin/env python3
"""Directly load data into database using the working Hyperliquid API calls."""

import sys
import os
from decimal import Decimal
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import get_db
from backend.models import Trader, TraderPerformance, Position, TradeOpportunity
from backend.services.hyperliquid_api import HyperliquidAPI

def main():
    """Load live data directly into database."""
    print("Loading live Hyperliquid data into database...")
    
    api = HyperliquidAPI()
    
    # Get leaderboard data (this is the working call from find_active_losers.py)
    print("Fetching leaderboard data...")
    leaderboard = api.get_leaderboard()
    if not leaderboard:
        print("Failed to fetch leaderboard data")
        return
    
    print(f"Got {len(leaderboard)} traders from leaderboard")
    
    # Filter for losing traders with >$1000 capital
    losing_traders = []
    for trader in leaderboard:
        roi = trader.get('accountValue', 0)
        pnl_30d = trader.get('pnl30dPercent', 0)
        
        if roi > 1000 and pnl_30d < -10:  # More than $1k and >10% loss
            losing_traders.append(trader)
    
    print(f"Found {len(losing_traders)} losing traders with >$1000 capital")
    
    # Take top 20 worst performers for testing
    losing_traders.sort(key=lambda x: x.get('pnl30dPercent', 0))
    test_traders = losing_traders[:20]
    
    print(f"Processing top {len(test_traders)} worst performers...")
    
    with get_db() as db:
        for i, trader_data in enumerate(test_traders):
            address = trader_data['address']
            print(f"Processing trader {i+1}/{len(test_traders)}: {address[:10]}...")
            
            try:
                # Create trader
                trader = db.query(Trader).filter_by(address=address).first()
                if not trader:
                    trader = Trader(
                        address=address,
                        first_seen=datetime.utcnow(),
                        last_updated=datetime.utcnow(),
                        is_active=True
                    )
                    db.add(trader)
                    db.flush()
                
                # Add performance
                today = date.today()
                existing_perf = db.query(TraderPerformance).filter_by(
                    trader_id=trader.id,
                    date=today
                ).first()
                
                if not existing_perf:
                    perf = TraderPerformance(
                        trader_id=trader.id,
                        date=today,
                        pnl_percentage=Decimal(str(trader_data.get('pnl30dPercent', 0))),
                        pnl_absolute=Decimal(str(trader_data.get('pnl30d', 0))),
                        account_value=Decimal(str(trader_data.get('accountValue', 0))),
                        win_rate=Decimal('0'),
                        total_trades=0,
                        winning_trades=0,
                        losing_trades=0,
                        avg_win=Decimal('0'),
                        avg_loss=Decimal('0')
                    )
                    db.add(perf)
                
                # Get positions for this trader
                positions = api.get_open_positions(address)
                position_count = 0
                
                for pos_data in positions:
                    existing_pos = db.query(Position).filter_by(
                        trader_id=trader.id,
                        coin=pos_data['coin'],
                        side=pos_data['side'],
                        status='OPEN'
                    ).first()
                    
                    if not existing_pos:
                        position = Position(
                            trader_id=trader.id,
                            coin=pos_data['coin'],
                            side=pos_data['side'],
                            entry_price=Decimal(str(pos_data['entryPx'])),
                            size=Decimal(str(abs(pos_data['szi']))),
                            leverage=Decimal(str(pos_data.get('leverage', 1))),
                            position_value=Decimal(str(pos_data.get('positionValue', 0))),
                            unrealized_pnl=Decimal(str(pos_data.get('unrealizedPnl', 0))),
                            margin_used=Decimal(str(pos_data.get('marginUsed', 0))),
                            liquidation_price=Decimal(str(pos_data.get('liquidationPx', 0))),
                            opened_at=datetime.utcnow(),
                            status='OPEN'
                        )
                        db.add(position)
                        position_count += 1
                        
                        # Create opportunity
                        suggested_side = 'SHORT' if pos_data['side'] == 'LONG' else 'LONG'
                        confidence = 95 if trader_data.get('pnl30dPercent', 0) < -90 else 85
                        
                        opportunity = TradeOpportunity(
                            trader_id=trader.id,
                            coin=pos_data['coin'],
                            loser_side=pos_data['side'],
                            suggested_side=suggested_side,
                            loser_entry_price=Decimal(str(pos_data['entryPx'])),
                            suggested_entry_price=Decimal(str(pos_data['entryPx'])),
                            confidence_score=Decimal(str(confidence)),
                            status='ACTIVE'
                        )
                        db.add(opportunity)
                
                db.commit()
                print(f"  ✓ Added {position_count} positions")
                
            except Exception as e:
                print(f"  ✗ Error: {e}")
                db.rollback()
    
    # Check final counts
    with get_db() as db:
        trader_count = db.query(Trader).count()
        position_count = db.query(Position).count()
        opp_count = db.query(TradeOpportunity).count()
        
    print(f"\nDatabase loaded successfully!")
    print(f"  Traders: {trader_count}")
    print(f"  Positions: {position_count}")  
    print(f"  Opportunities: {opp_count}")
    print("\nRefresh the frontend to see the data!")

if __name__ == "__main__":
    main()