import logging
import time
import threading
from datetime import datetime
from typing import List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

from backend.services.data_collector import DataCollector
from backend.services.analyzer import TradingAnalyzer
from backend.services.hyperliquid_api import HyperliquidAPI

logger = logging.getLogger(__name__)

class DataScheduler:
    def __init__(self):
        self.data_collector = DataCollector()
        self.analyzer = TradingAnalyzer()
        self.api = HyperliquidAPI()
        self.running = False
        self.thread = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def start(self):
        """Start the background data collection scheduler."""
        if self.running:
            logger.warning("Scheduler already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Data scheduler started - collecting data every 30 seconds")
        
    def stop(self):
        """Stop the background scheduler."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        self.executor.shutdown(wait=False)
        logger.info("Data scheduler stopped")
        
    def _run_scheduler(self):
        """Main scheduler loop."""
        logger.info("Scheduler thread started")
        
        while self.running:
            try:
                start_time = time.time()
                logger.info("Starting data collection cycle...")
                
                # Run data collection tasks in parallel
                futures = []
                
                # 1. Discover and collect new traders
                futures.append(self.executor.submit(self._discover_and_collect_traders))
                
                # 2. Update existing trader positions
                futures.append(self.executor.submit(self._update_existing_positions))
                
                # 3. Generate new opportunities
                futures.append(self.executor.submit(self._generate_opportunities))
                
                # Wait for all tasks to complete
                for future in futures:
                    try:
                        future.result(timeout=25)  # Give each task max 25 seconds
                    except Exception as e:
                        logger.error(f"Task failed: {e}")
                
                execution_time = time.time() - start_time
                logger.info(f"Data collection cycle completed in {execution_time:.2f}s")
                
                # Sleep for remaining time to maintain 30-second interval
                sleep_time = max(0, 30 - execution_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                time.sleep(5)  # Brief pause on error
                
    def _discover_and_collect_traders(self):
        """Discover new traders from Hyperliquid leaderboard and recent activity."""
        try:
            logger.info("Discovering new traders...")
            
            # Get traders from leaderboard
            leaderboard_data = self.api.get_leaderboard()
            if not leaderboard_data:
                logger.warning("No leaderboard data available")
                return
                
            new_traders = []
            for entry in leaderboard_data.get('leaderboard', [])[:50]:  # Top 50
                address = entry.get('user')
                if address and len(address) == 42:  # Valid Ethereum address
                    new_traders.append(address)
                    
            logger.info(f"Found {len(new_traders)} traders from leaderboard")
            
            # Collect data for new traders (in batches to avoid rate limits)
            batch_size = 5
            for i in range(0, len(new_traders), batch_size):
                batch = new_traders[i:i + batch_size]
                try:
                    self.data_collector.collect_multiple_traders(batch)
                    time.sleep(1)  # Rate limiting pause
                except Exception as e:
                    logger.error(f"Error collecting batch {i//batch_size + 1}: {e}")
                    
        except Exception as e:
            logger.error(f"Error discovering traders: {e}", exc_info=True)
            
    def _update_existing_positions(self):
        """Update positions for existing traders in database."""
        try:
            logger.info("Updating existing trader positions...")
            
            # Get active traders from database
            from backend.database.connection import get_db
            with get_db() as db:
                from backend.models.trader import Trader
                active_traders = db.query(Trader).filter_by(is_active=True).limit(20).all()
                
            trader_addresses = [trader.address for trader in active_traders]
            logger.info(f"Updating positions for {len(trader_addresses)} active traders")
            
            # Update in batches
            batch_size = 3
            for i in range(0, len(trader_addresses), batch_size):
                batch = trader_addresses[i:i + batch_size]
                try:
                    self.data_collector.collect_multiple_traders(batch)
                    time.sleep(0.5)  # Rate limiting pause
                except Exception as e:
                    logger.error(f"Error updating trader batch: {e}")
                    
        except Exception as e:
            logger.error(f"Error updating existing positions: {e}", exc_info=True)
            
    def _generate_opportunities(self):
        """Analyze recent positions to generate new trading opportunities."""
        try:
            logger.info("Generating new opportunities...")
            
            # Analyze new positions for opportunities
            opportunities = self.analyzer.analyze_new_positions()
            logger.info(f"Generated {len(opportunities)} new opportunities")
            
            # Log some details about opportunities found
            if opportunities:
                recent_opps = opportunities[:3]
                for opp in recent_opps:
                    logger.info(f"New opportunity: {opp.coin} {opp.loser_side} -> {opp.suggested_side} "
                               f"(confidence: {opp.confidence_score}%)")
                    
        except Exception as e:
            logger.error(f"Error generating opportunities: {e}", exc_info=True)
            
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status."""
        return {
            "running": self.running,
            "thread_alive": self.thread.is_alive() if self.thread else False,
            "last_update": datetime.now().isoformat()
        }

# Global scheduler instance
_scheduler = None

def get_scheduler() -> DataScheduler:
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = DataScheduler()
    return _scheduler

def start_scheduler():
    """Start the global scheduler."""
    scheduler = get_scheduler()
    scheduler.start()
    
def stop_scheduler():
    """Stop the global scheduler."""
    scheduler = get_scheduler()
    scheduler.stop()