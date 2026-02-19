# from .stock_data import get_stock_price

# def analyze_portfolio(holdings):
#     total_invested = 0
#     total_current_value = 0
#     details = []

#     allocation = {
#     "Stocks": total_current_value,
#     "Mutual Funds": 0,
# }

#     for holding in holdings:
#         stock_data = get_stock_price(holding.stock.symbol)
#         current_price = float(stock_data["price"])

#         invested = holding.quantity * float(holding.buy_price)
#         current_value = holding.quantity * current_price
#         pnl = current_value - invested

#         total_invested += invested
#         total_current_value += current_value

#         details.append({
#             "symbol": holding.stock.symbol,
#             "quantity": holding.quantity,
#             "buy_price": float(holding.buy_price),
#             "current_price": current_price,
#             "invested": invested,
#             "current_value": current_value,
#             "pnl": pnl,
#         })

#     total_return_pct = (
#         ((total_current_value - total_invested) / total_invested) * 100
#         if total_invested > 0 else 0
#     )

#     return {
#         "total_invested": total_invested,
#         "total_value": total_current_value,
#         "total_pnl": total_current_value - total_invested,
#         "return_pct": total_return_pct,
#         "holdings": details,
#     }



from .stock_data import get_stock_price

def analyze_portfolio(holdings):
    total_invested = 0
    total_current_value = 0
    details = []

    for holding in holdings:
        # Get current stock price
        stock_data = get_stock_price(holding.stock_name)
        
        # Handle case where price is not available
        if stock_data["price"] == "N/A" or stock_data["price"] is None:
            current_price = float(holding.buy_price)
        else:
            try:
                current_price = float(stock_data["price"])
            except (ValueError, TypeError):
                current_price = float(holding.buy_price)

        # Calculate values
        buy_price = float(holding.buy_price)
        quantity = int(holding.quantity)
        
        invested = quantity * buy_price
        current_value = quantity * current_price
        pnl = current_value - invested
        
        # Calculate percentage change
        if buy_price > 0:
            change_percent = ((current_price - buy_price) / buy_price) * 100
        else:
            change_percent = 0

        total_invested += invested
        total_current_value += current_value

        details.append({
            "symbol": holding.stock_name,
            "stock_name": holding.stock_name,
            "quantity": quantity,
            "buy_price": buy_price,
            "current_price": current_price,
            "invested": invested,
            "current_value": current_value,
            "pnl": pnl,
            "change_percent": change_percent,
        })

    total_return_pct = (
        ((total_current_value - total_invested) / total_invested) * 100
        if total_invested > 0 else 0
    )

    return {
        "total_invested": total_invested,
        "total_value": total_current_value,
        "total_pnl": total_current_value - total_invested,
        "return_pct": total_return_pct,
        "holdings": details,
    }
