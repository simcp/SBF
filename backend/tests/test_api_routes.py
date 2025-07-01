import pytest
import json
from datetime import datetime
from decimal import Decimal
from backend.models import TradeOpportunity


def test_health_check(test_client):
    """Test health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"


def test_get_top_losers_empty(test_client):
    """Test getting top losers with no data."""
    response = test_client.get("/api/losers")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert data["count"] == 0
    assert data["data"] == []


def test_get_top_losers_with_limit(test_client):
    """Test getting top losers with limit parameter."""
    response = test_client.get("/api/losers?limit=10")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"


def test_get_opportunities_empty(test_client):
    """Test getting opportunities with no data."""
    response = test_client.get("/api/opportunities")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert data["count"] == 0
    assert data["data"] == []


def test_get_opportunities_with_data(test_client, test_db, sample_trader, sample_position):
    """Test getting opportunities with data."""
    # Create an opportunity
    opportunity = TradeOpportunity(
        position_id=sample_position.id,
        trader_id=sample_trader.id,
        coin="BTC",
        loser_side="LONG",
        suggested_side="SHORT",
        loser_entry_price=Decimal("50000"),
        suggested_entry_price=Decimal("50100"),
        confidence_score=Decimal("85"),
        status="ACTIVE"
    )
    test_db.add(opportunity)
    test_db.commit()
    
    response = test_client.get("/api/opportunities")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert data["count"] == 1
    assert data["data"][0]["coin"] == "BTC"
    assert data["data"][0]["confidence_score"] == 85.0


def test_get_trader_details_not_found(test_client):
    """Test getting trader details for non-existent trader."""
    response = test_client.get("/api/trader/0xnotfound")
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data["status"] == "error"
    assert "not found" in data["message"]


def test_get_trader_details_with_data(test_client, test_db, sample_loser_trader, sample_position):
    """Test getting trader details with data."""
    # Update position to belong to loser trader
    sample_position.trader_id = sample_loser_trader.id
    test_db.commit()
    
    response = test_client.get(f"/api/trader/{sample_loser_trader.address}")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert data["data"]["trader"]["address"] == sample_loser_trader.address
    assert len(data["data"]["performance"]) > 0
    assert len(data["data"]["positions"]) == 1


def test_get_system_performance(test_client, test_db, sample_trader):
    """Test getting system performance metrics."""
    response = test_client.get("/api/performance")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert data["data"]["active_traders"] == 1
    assert data["data"]["total_opportunities"] == 0
    assert data["data"]["active_opportunities"] == 0


def test_collect_trader_data(test_client, mock_hyperliquid_api):
    """Test manually collecting trader data."""
    response = test_client.post("/api/collect/0xtest123")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert "collected" in data["message"]


def test_analyze_positions(test_client, test_db, sample_loser_trader, mock_hyperliquid_api):
    """Test manually triggering position analysis."""
    # Create a position for analysis
    position = Position(
        trader_id=sample_loser_trader.id,
        coin="BTC",
        side="LONG",
        entry_price=Decimal("50000"),
        size=Decimal("1.0"),
        opened_at=datetime.utcnow(),
        status="OPEN"
    )
    test_db.add(position)
    test_db.commit()
    
    response = test_client.post("/api/analyze")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert "Analysis complete" in data["message"]
    assert len(data["data"]) > 0


# Add missing import
from backend.models import Position