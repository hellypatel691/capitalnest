import yfinance as yf
def get_yahoo_stock_data(symbols):
    clean_results = []

    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            prev_price = info.get("previousClose")
            curr_price = info.get("currentPrice")

            # ❌ HARD FILTER – skip broken Yahoo data
            if (
                prev_price is None
                or curr_price is None
                or prev_price == 0
            ):
                continue

            percent_change = round(
                ((curr_price - prev_price) / prev_price) * 100, 2
            )

            clean_results.append({
                "symbol": symbol,
                "previous_price": round(prev_price, 2),
                "current_price": round(curr_price, 2),
                "percent_change": percent_change,
            })

        except Exception as e:
            # ❌ skip symbol if Yahoo fails
            print(f"Yahoo failed for {symbol}: {e}")
            continue

    return clean_results

