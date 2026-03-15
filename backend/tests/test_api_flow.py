import pytest

from src.api.routes import internal_routes


@pytest.mark.asyncio
async def test_requires_admin_key(client):
    response = await client.get("/watchlist")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_session_login_allows_cookie_access(logged_in_client):
    me = await logged_in_client.get("/session/me")
    assert me.status_code == 200
    assert me.json()["authenticated"] is True

    watchlist = await logged_in_client.get("/watchlist")
    assert watchlist.status_code == 200


@pytest.mark.asyncio
async def test_watchlist_and_alert_crud(client, auth_headers):
    create_watchlist = await client.post("/watchlist", json={"symbol": "AAPL"}, headers=auth_headers)
    assert create_watchlist.status_code == 201
    assert create_watchlist.json()["symbol"] == "AAPL"

    list_watchlist = await client.get("/watchlist", headers=auth_headers)
    assert list_watchlist.status_code == 200
    assert len(list_watchlist.json()) == 1

    create_alert = await client.post(
        "/alerts/stocks",
        json={"stock_symbol": "AAPL", "target_price": 100.0, "condition": "above"},
        headers=auth_headers,
    )
    assert create_alert.status_code == 201
    stock_alert = create_alert.json()
    assert stock_alert["stock_symbol"] == "AAPL"

    list_alerts = await client.get("/alerts/stocks", headers=auth_headers)
    assert list_alerts.status_code == 200
    assert len(list_alerts.json()) == 1

    delete_alert = await client.delete(f"/alerts/stocks/{stock_alert['id']}", headers=auth_headers)
    assert delete_alert.status_code == 204


@pytest.mark.asyncio
async def test_internal_alert_runner_creates_notification(client, auth_headers, monkeypatch):
    await client.post(
        "/alerts/stocks",
        json={"stock_symbol": "TSLA", "target_price": 100.0, "condition": "above"},
        headers=auth_headers,
    )
    await client.post(
        "/device-tokens",
        json={"token": "device-token-1", "platform": "iOS"},
        headers=auth_headers,
    )

    async def fake_quote(symbol: str):
        return {
            "symbol": symbol,
            "name": symbol,
            "price": 150.0,
            "change": 1.0,
            "change_percent": 1.0,
            "currency": "USD",
            "source": "test",
        }

    monkeypatch.setattr(internal_routes.alert_service.stock_service, "get_stock_quote", fake_quote)

    response = await client.post("/internal/run-alert-checks", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["triggered"] == 1

    notifications = await client.get("/notifications", headers=auth_headers)
    assert notifications.status_code == 200
    body = notifications.json()
    assert len(body) == 1
    assert body[0]["alert_type"] == "stock"
