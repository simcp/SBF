#!/usr/bin/env python3
"""Load real data from JSON files into database."""

import sys
import os
import json
from decimal import Decimal
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import get_db
from backend.models import Trader, TraderPerformance, Position, TradeOpportunity

def main():
    """Load real data from find_active_losers output into database."""
    print("Loading real trader data into database...")
    
    # Check if we have the JSON file with real data
    json_file = 'active_losers.json'
    if not os.path.exists(json_file):
        print(f"Error: {json_file} not found. Run find_active_losers.py first.")
        return
    
    with open(json_file, 'r') as f:
        data = json.load(f)
        traders = data.get('traders', [])
    
    if not traders:
        print("No trader data found in JSON file.")
        return
    
    print(f"Loading {len(traders)} traders into database...")
    
    with get_db() as db:
        for i, trader_data in enumerate(traders):
            print(f"Processing trader {i+1}/{len(traders)}: {trader_data['address'][:10]}...")
            
            try:
                # Create or get trader
                trader = db.query(Trader).filter_by(address=trader_data['address']).first()
                if not trader:
                    trader = Trader(
                        address=trader_data['address'],
                        first_seen=datetime.utcnow(),
                        last_updated=datetime.utcnow(),
                        is_active=True
                    )
                    db.add(trader)
                    db.flush()  # Get the ID
                
                # Add performance data
                today = date.today()
                existing_perf = db.query(TraderPerformance).filter_by(
                    trader_id=trader.id,
                    date=today
                ).first()
                
                if not existing_perf:
                    perf = TraderPerformance(
                        trader_id=trader.id,
                        date=today,
                        pnl_percentage=Decimal(str(trader_data['roi_30d_percent'])),
                        pnl_absolute=Decimal(str(trader_data['pnl_30d'])),
                        account_value=Decimal(str(trader_data['account_value'])),
                        win_rate=Decimal('0'),  # Not in our data
                        total_trades=0,
                        winning_trades=0,
                        losing_trades=0,
                        avg_win=Decimal('0'),
                        avg_loss=Decimal('0')
                    )
                    db.add(perf)
                
                # Add positions
                for pos_data in trader_data.get('positions', []):
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
                            entry_price=Decimal(str(pos_data['entry_price'])),
                            size=Decimal(str(pos_data['size'])),
                            leverage=Decimal(str(pos_data.get('leverage', 1))),
                            position_value=Decimal(str(pos_data.get('position_value', 0))),
                            unrealized_pnl=Decimal(str(pos_data.get('unrealized_pnl', 0))),
                            margin_used=Decimal(str(pos_data.get('margin_used', 0))),
                            liquidation_price=Decimal(str(pos_data.get('liquidation_price', 0))),
                            opened_at=datetime.utcnow(),
                            status='OPEN'
                        )
                        db.add(position)
                        
                        # Create trade opportunity
                        suggested_side = 'SHORT' if pos_data['side'] == 'LONG' else 'LONG'
                        confidence = 95 if trader_data['roi_30d_percent'] < -90 else 80
                        
                        opportunity = TradeOpportunity(
                            position_id=None,  # Will be set after position is committed
                            trader_id=trader.id,
                            coin=pos_data['coin'],
                            loser_side=pos_data['side'],
                            suggested_side=suggested_side,
                            loser_entry_price=Decimal(str(pos_data['entry_price'])),
                            suggested_entry_price=Decimal(str(pos_data['entry_price'])),
                            confidence_score=Decimal(str(confidence)),
                            status='ACTIVE'
                        )
                        db.add(opportunity)
                
                db.commit()
                print(f"  ✓ Added {len(trader_data.get('positions', []))} positions")
                
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