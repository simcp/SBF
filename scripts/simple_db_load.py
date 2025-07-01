#!/usr/bin/env python3
"""Simple script to load leaderboard data into database."""

import sys
import os
import json
from decimal import Decimal
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.connection import get_db
from backend.models import Trader, TraderPerformance, Position, TradeOpportunity
from backend.services import HyperliquidAPI

def main():
    """Load data from existing leaderboard JSON into database."""
    print("Loading leaderboard data into database...")
    
    # Load leaderboard data
    with open("leaderboard_data.json", "r") as f:
        data = json.load(f)
    
    leaderboard = data.get("leaderboardRows", [])
    print(f"Found {len(leaderboard)} traders in leaderboard")
    
    # Filter for losing traders with capital
    active_losers = []
    for row in leaderboard:
        account_value = float(row.get("accountValue", 0))
        if account_value < 1000:
            continue
            
        month_perf = None
        for window in row.get("windowPerformances", []):
            if window[0] == "month":
                month_perf = window[1]
                break
        
        if month_perf:
            roi = float(month_perf.get("roi", 0))
            roi_percent = roi * 100
            
            if roi_percent < -10:  # At least -10% loss
                active_losers.append({
                    "address": row.get("ethAddress"),
                    "account_value": account_value,
                    "roi_30d_percent": roi_percent,
                    "pnl_30d": float(month_perf.get("pnl", 0)),
                    "volume_30d": float(month_perf.get("volume", 0))
                })
    
    print(f"Found {len(active_losers)} losing traders with >$1000 capital")
    
    # Sort by worst performance and take top 50
    active_losers.sort(key=lambda x: x["roi_30d_percent"])
    test_traders = active_losers[:50]
    
    print(f"Loading top {len(test_traders)} worst performers into database...")
    
    api = HyperliquidAPI()
    
    with get_db() as db:
        for i, trader_data in enumerate(test_traders):
            address = trader_data["address"]
            print(f"Processing {i+1}/{len(test_traders)}: {address[:10]}... ({trader_data['roi_30d_percent']:.1f}%)")
            
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
                        pnl_percentage=Decimal(str(trader_data["roi_30d_percent"])),
                        pnl_absolute=Decimal(str(trader_data["pnl_30d"])),
                        account_value=Decimal(str(trader_data["account_value"])),
                        win_rate=Decimal('0'),
                        total_trades=0,
                        winning_trades=0,
                        losing_trades=0,
                        avg_win=Decimal('0'),
                        avg_loss=Decimal('0')
                    )
                    db.add(perf)
                
                # Get positions from API
                try:
                    user_state = api.get_user_state(address)
                    if user_state and 'assetPositions' in user_state:
                        positions = user_state['assetPositions']
                        position_count = 0
                        
                        for pos in positions:
                            if 'position' in pos and pos['position']['szi'] != '0':
                                pos_data = pos['position']
                                size = float(pos_data['szi'])
                                side = 'LONG' if size > 0 else 'SHORT'
                                
                                existing_pos = db.query(Position).filter_by(
                                    trader_id=trader.id,
                                    coin=pos_data['coin'],
                                    side=side,
                                    status='OPEN'
                                ).first()
                                
                                if not existing_pos:
                                    position = Position(
                                        trader_id=trader.id,
                                        coin=pos_data['coin'],
                                        side=side,
                                        entry_price=Decimal(str(pos_data.get('entryPx', 0))),
                                        size=Decimal(str(abs(size))),
                                        leverage=Decimal('1'),
                                        position_value=Decimal(str(pos_data.get('positionValue', 0))),
                                        unrealized_pnl=Decimal(str(pos_data.get('unrealizedPnl', 0))),
                                        margin_used=Decimal('0'),
                                        liquidation_price=Decimal('0'),
                                        opened_at=datetime.utcnow(),
                                        status='OPEN'
                                    )
                                    db.add(position)
                                    position_count += 1
                                    
                                    # Create opportunity
                                    suggested_side = 'SHORT' if side == 'LONG' else 'LONG'
                                    confidence = 95 if trader_data["roi_30d_percent"] < -90 else 85
                                    
                                    opportunity = TradeOpportunity(
                                        trader_id=trader.id,
                                        coin=pos_data['coin'],
                                        loser_side=side,
                                        suggested_side=suggested_side,
                                        loser_entry_price=Decimal(str(pos_data.get('entryPx', 0))),
                                        suggested_entry_price=Decimal(str(pos_data.get('entryPx', 0))),
                                        confidence_score=Decimal(str(confidence)),
                                        status='ACTIVE'
                                    )
                                    db.add(opportunity)
                        
                        print(f"  ✓ Added {position_count} positions")
                except Exception as e:
                    print(f"  ⚠ Could not get positions: {e}")
                
                db.commit()
                
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