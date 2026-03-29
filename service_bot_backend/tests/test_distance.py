from unittest.mock import patch, MagicMock
import math


def test_haversine_known_distance():
    """Johannesburg to Cape Town is roughly 1260 km."""
    from services.distance import _haversine
    # Johannesburg: -26.2041, 28.0473
    # Cape Town: -33.9249, 18.4241
    dist = _haversine(-26.2041, 28.0473, -33.9249, 18.4241)
    assert 1200 < dist < 1320


def test_haversine_same_point():
    from services.distance import _haversine
    assert _haversine(0, 0, 0, 0) == 0.0


def test_geocode_not_found():
    """If Nominatim returns empty, geocode returns None."""
    from services.distance import geocode
    with patch("services.distance.httpx.Client") as mock:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = []
        mock.return_value.__enter__ = MagicMock(return_value=MagicMock(get=MagicMock(return_value=mock_resp)))
        mock.return_value.__exit__ = MagicMock(return_value=False)
        result = geocode("nonexistent place xyz123")
        assert result is None


def test_geocode_success():
    from services.distance import geocode
    with patch("services.distance.httpx.Client") as mock:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = [{"lat": "-26.2041", "lon": "28.0473"}]
        mock.return_value.__enter__ = MagicMock(return_value=MagicMock(get=MagicMock(return_value=mock_resp)))
        mock.return_value.__exit__ = MagicMock(return_value=False)
        result = geocode("Johannesburg")
        assert result == (-26.2041, 28.0473)


def test_calculate_distance_no_business(monkeypatch):
    monkeypatch.setattr("services.distance.cfg.BUSINESS_ADDRESS", "")
    monkeypatch.setattr("services.distance.cfg.BUSINESS_LAT", 0.0)
    monkeypatch.setattr("services.distance.cfg.BUSINESS_LNG", 0.0)
    from services.distance import calculate_distance
    result = calculate_distance("Somewhere")
    assert "error" in result


@patch("services.distance.geocode")
def test_calculate_distance_success(mock_geocode, monkeypatch):
    monkeypatch.setattr("services.distance.cfg.BUSINESS_ADDRESS", "Sandton")
    monkeypatch.setattr("services.distance.cfg.BUSINESS_LAT", -26.1076)
    monkeypatch.setattr("services.distance.cfg.BUSINESS_LNG", 28.0567)
    # Customer in Pretoria
    mock_geocode.return_value = (-25.7479, 28.2293)
    from services.distance import calculate_distance
    result = calculate_distance("Pretoria")
    assert "distance_km" in result
    assert 30 < result["distance_km"] < 50  # ~42 km


@patch("services.distance.geocode")
def test_calculate_distance_customer_not_found(mock_geocode, monkeypatch):
    monkeypatch.setattr("services.distance.cfg.BUSINESS_ADDRESS", "Sandton")
    monkeypatch.setattr("services.distance.cfg.BUSINESS_LAT", -26.1076)
    monkeypatch.setattr("services.distance.cfg.BUSINESS_LNG", 28.0567)
    mock_geocode.return_value = None
    from services.distance import calculate_distance
    result = calculate_distance("Nonexistent Place XYZ")
    assert "error" in result
