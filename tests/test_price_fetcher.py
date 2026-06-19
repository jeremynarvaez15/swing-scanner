import pandas as pd
from app.data.price_fetcher import fetch_price_data, get_current_price

def test_fetch_price_data_returns_dataframe():
    data = fetch_price_data(["AAPL", "MSFT"])
    assert "AAPL" in data
    assert isinstance(data["AAPL"], pd.DataFrame)
    assert len(data["AAPL"]) >= 200
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        assert col in data["AAPL"].columns

def test_get_current_price_returns_dict():
    result = get_current_price("AAPL")
    assert "price" in result
    assert "change_pct" in result
    assert "volume" in result
    assert isinstance(result["price"], float)
    assert result["price"] > 0
