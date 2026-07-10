import pandas as pd
from app.data.price_fetcher import fetch_price_data, get_current_price

def test_fetch_price_data_returns_dataframe():
    data, spy_df = fetch_price_data(["AAPL", "MSFT"])
    assert "AAPL" in data
    assert isinstance(data["AAPL"], pd.DataFrame)
    assert len(data["AAPL"]) >= 200
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        assert col in data["AAPL"].columns
    assert isinstance(spy_df, pd.DataFrame)
    assert len(spy_df) >= 200

def test_get_current_price_returns_dict():
    result = get_current_price("AAPL")
    assert "price" in result
    assert "change_pct" in result
    assert "volume" in result
    assert isinstance(result["price"], float)
    assert result["price"] > 0

def test_fetch_price_data_spy_not_in_dict():
    """SPY should be excluded from the result dict even if implicitly added."""
    data, spy_df = fetch_price_data(["AAPL"])
    assert "SPY" not in data
    assert isinstance(spy_df, pd.DataFrame)

def test_fetch_price_data_returns_tuple():
    """fetch_price_data always returns a 2-tuple."""
    result = fetch_price_data(["MSFT"])
    assert isinstance(result, tuple)
    assert len(result) == 2
    data, spy_df = result
    assert isinstance(data, dict)
    assert isinstance(spy_df, pd.DataFrame)
