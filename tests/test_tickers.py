from app.data.tickers import get_sp500_tickers, get_nasdaq100_tickers, get_all_tickers

def test_sp500_returns_list_of_strings():
    tickers = get_sp500_tickers()
    assert isinstance(tickers, list)
    assert len(tickers) >= 490
    assert all(isinstance(t, str) for t in tickers)
    assert "AAPL" in tickers

def test_nasdaq100_returns_list_of_strings():
    tickers = get_nasdaq100_tickers()
    assert isinstance(tickers, list)
    assert len(tickers) >= 95
    assert "MSFT" in tickers

def test_all_tickers_deduped():
    tickers = get_all_tickers()
    assert len(tickers) == len(set(tickers))
    assert len(tickers) >= 500
