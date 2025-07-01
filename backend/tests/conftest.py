import os
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.connection import Base, get_db
from backend.models import Trader, TraderPerformance, Position
from backend.app import create_app

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """Create a test database for each test."""
    # Create engine
    engine = create_engine(TEST_DATABASE_URL)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestSessionLocal()
    
    yield session
    
    # Clean up
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_app(test_db, monkeypatch):
    """Create test Flask app."""
    app = create_app()
    app.config['TESTING'] = True
    
    # Monkey patch the get_db function
    def mock_get_db():
        yield test_db
    
    import backend.database.connection
    monkeypatch.setattr(backend.database.connection, "get_db", mock_get_db)
    
    return app


@pytest.fixture(scope="function")
def test_client(test_app):
    """Create test client."""
    return test_app.test_client()


@pytest.fixture
def sample_trader(test_db):
    """Create a sample trader."""
    trader = Trader(
        address="0x1234567890123456789012345678901234567890",
        first_seen=datetime.utcnow(),
        last_updated=datetime.utcnow(),
        is_active=True
    )
    test_db.add(trader)
    test_db.commit()
    test_db.refresh(trader)
    return trader


@pytest.fixture
def sample_loser_trader(test_db):
    """Create a sample losing trader with bad performance."""
    trader = Trader(
        address="0xbad1234567890123456789012345678901234567",
        first_seen=datetime.utcnow() - timedelta(days=35),
        last_updated=datetime.utcnow(),
        is_active=True
    )
    test_db.add(trader)
    test_db.commit()
    
    # Add bad performance history
    for i in range(30):
        perf = TraderPerformance(
            trader_id=trader.id,
            date=(datetime.utcnow() - timedelta(days=i)).date(),
            pnl_percentage=Decimal("-85.5"),
            pnl_absolute=Decimal("-10000"),
            win_rate=Decimal("15.0"),
            total_trades=100,
            winning_trades=15,
            losing_trades=85,
            avg_win=Decimal("100"),
            avg_loss=Decimal("-150"),
            account_value=Decimal("5000")
        )
        test_db.add(perf)
    
    test_db.commit()
    test_db.refresh(trader)
    return trader


@pytest.fixture
def sample_position(test_db, sample_trader):
    """Create a sample position."""
    position = Position(
        trader_id=sample_trader.id,
        coin="BTC",
        side="LONG",
        entry_price=Decimal("50000"),
        size=Decimal("1.0"),
        leverage=Decimal("10"),
        position_value=Decimal("50000"),
        unrealized_pnl=Decimal("500"),
        margin_used=Decimal("5000"),
        liquidation_price=Decimal("45000"),
        opened_at=datetime.utcnow(),
        status="OPEN"
    )
    test_db.add(position)
    test_db.commit()
    test_db.refresh(position)
    return position


@pytest.fixture
def mock_hyperliquid_api(monkeypatch):
    """Mock Hyperliquid API responses."""
    class MockInfo:
        def user_state(self, address):
            return {
                "marginSummary": {
                    "accountValue": "10000.0",
                    "totalMarginUsed": "5000.0",
                    "withdrawable": "5000.0"
                },
                "assetPositions": [
                    {
                        "position": {
                            "coin": "BTC",
                            "szi": "1.0",
                            "entryPx": "50000.0",
                            "positionValue": "50000.0",
                            "unrealizedPnl": "500.0",
                            "returnOnEquity": "0.1",
                            "liquidationPx": "45000.0"
                        },
                        "leverage": {"value": 10}
                    }
                ]
            }
        
        def user_fills(self, address):
            return [
                {
                    "coin": "BTC",
                    "px": "50000.0",
                    "sz": "1.0",
                    "side": "B",
                    "time": int((datetime.utcnow() - timedelta(days=1)).timestamp() * 1000),
                    "closedPnl": "-100.0"
                },
                {
                    "coin": "ETH",
                    "px": "3000.0",
                    "sz": "2.0",
                    "side": "S",
                    "time": int((datetime.utcnow() - timedelta(days=2)).timestamp() * 1000),
                    "closedPnl": "50.0"
                }
            ]
        
        def all_mids(self):
            return {
                "BTC": 50500.0,
                "ETH": 3100.0,
                "SOL": 100.0
            }
        
        def clearinghouse_state(self, address):
            return {
                "marginSummary": {
                    "accountValue": "10000.0"
                }
            }
    
    def mock_init(self, *args, **kwargs):
        self.info = MockInfo()
    
    from backend.services import hyperliquid_api
    monkeypatch.setattr(hyperliquid_api.HyperliquidAPI, "__init__", mock_init)