from django.shortcuts import render
from .models import Stock
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Portfolio, Holding
from .service.portfolio_analysis import analyze_portfolio
from django.http import JsonResponse
from .service.stock_data import get_stock_price
from django.contrib import messages
from .models import DematAccount
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
from openai import OpenAI
from django.core.cache import cache
import requests
def home(request):
    return render(request, 'core/index.html')
from .models import Wallet

def login_view(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            # 🔥 CHECK WALLET AFTER LOGIN
            wallet, _ = Wallet.objects.get_or_create(user=user)

            if wallet.balance == 0:
                return redirect("set_balance")  # 👈 NEW
            else:
                return redirect("dashboard")

        else:
            messages.error(request, "Invalid username or password")

    return render(request, 'core/login.html')

@login_required

@login_required
def set_balance(request):
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    # 🔒 Block access if balance already set
    if wallet.balance > 0:
        return redirect("dashboard")

    if request.method == "POST":
        amount = request.POST.get("balance")

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except:
            messages.error(request, "Enter a valid amount")
            return redirect("set_balance")

        wallet.balance = amount
        wallet.save()

        messages.success(request, "Balance added successfully")
        return redirect("dashboard")

    return render(request, "core/set_balance.html")



from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect


def signup_view(request):
    if request.method == "POST":

        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]

        # 🔐 PASSWORD VALIDATION HERE
        try:
            validate_password(password)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return redirect("signup")

        # If password valid → create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        messages.success(request, "Account created successfully!")
        return redirect("login")

    return render(request, "core/signup.html")
# core/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Holding, Wallet
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Holding, Wallet
import json
from .models import Portfolio, Holding, WalletTransaction

@login_required
def dashboard(request):
    user = request.user

    portfolio = Portfolio.objects.filter(user=user).first()

    if portfolio:
        holdings = Holding.objects.filter(portfolio=portfolio).select_related('stock')
    else:
        holdings = []

    # Calculate stock investments
    stock_invested = Decimal('0.00')
    total_current = Decimal('0.00')
    holdings_data = []
    
    for h in holdings:
        stock_invested_amount = h.quantity * h.buy_price
        stock_current = h.quantity * h.stock.price
        stock_pnl = stock_current - stock_invested_amount
        
        if h.buy_price > 0:
            stock_pnl_pct = (stock_pnl / stock_invested_amount) * 100
        else:
            stock_pnl_pct = Decimal('0.00')
        
        stock_invested += stock_invested_amount
        total_current += stock_current
        
        holdings_data.append({
            'symbol': h.stock.symbol,
            'name': h.stock.name,
            'quantity': h.quantity,
            'invested': stock_invested_amount,
            'current': stock_current,
            'pnl': stock_pnl,
            'pnl_pct': stock_pnl_pct,
        })
    
    # Calculate IPO investments (only Allotted IPOs, matching IPO page logic)
    ipo_invested = IPOApplication.objects.filter(
        user=user,
        status="Allotted"
    ).aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    # Total invested = stocks + IPOs
    total_invested = stock_invested + ipo_invested
    
    # Get wallet balance
    wallet = Wallet.objects.filter(user=user).first()
    available_cash = wallet.balance if wallet else Decimal('0.00')
    
    # Total Net Worth = Stock Portfolio + IPO Investments + Available Cash
    total_net_worth = total_current + ipo_invested + available_cash
    
    # Debug print
    print(f"DEBUG - Stock Portfolio: {total_current}")
    print(f"DEBUG - IPO Invested: {ipo_invested}")
    print(f"DEBUG - Available Cash: {available_cash}")
    print(f"DEBUG - Total Net Worth: {total_net_worth}")
    
    # Sort by P&L percentage for top gainers/losers
    holdings_data_sorted = sorted(holdings_data, key=lambda x: x['pnl_pct'], reverse=True)
    top_gainers = [h for h in holdings_data_sorted if h['pnl_pct'] > 0][:3]
    top_losers = [h for h in holdings_data_sorted if h['pnl_pct'] < 0][-3:]
    
    total_profit = total_current - stock_invested
    
    # Calculate portfolio return percentage (only for stocks)
    if stock_invested > 0:
        portfolio_return_pct = (total_profit / stock_invested) * 100
    else:
        portfolio_return_pct = Decimal('0.00')

    # Fetch Recent Transactions
    recent_transactions = WalletTransaction.objects.filter(
        user=user
    ).select_related('stock').order_by('-created_at')[:5]

    # Generate real portfolio performance data (Stocks + IPOs)
    from datetime import datetime, timedelta
    from django.db.models import Q
    
    # Get all stock transactions ordered by date
    all_stock_transactions = StockTransaction.objects.filter(
        user=user
    ).order_by('created_at')
    
    # Get all IPO applications ordered by date
    all_ipo_applications = IPOApplication.objects.filter(
        user=user
    ).order_by('applied_at')
    
    # Determine if we have any data
    has_stock_data = all_stock_transactions.exists()
    has_ipo_data = all_ipo_applications.exists()
    
    if has_stock_data or has_ipo_data:
        # Get earliest date from either stocks or IPOs
        dates = []
        if has_stock_data:
            dates.append(all_stock_transactions.first().created_at.date())
        if has_ipo_data:
            dates.append(all_ipo_applications.first().applied_at.date())
        
        first_transaction_date = min(dates)
        today = datetime.now().date()
        
        # Generate data points
        portfolio_values = []
        portfolio_labels = []
        
        current_date = first_transaction_date
        
        # Determine interval based on time range
        days_diff = (today - first_transaction_date).days
        
        if days_diff > 180:  # More than 6 months, use monthly
            interval_days = 30
        elif days_diff > 60:  # More than 2 months, use weekly
            interval_days = 7
        else:  # Less than 2 months, use every 3 days
            interval_days = 3
        
        # Calculate portfolio value at different points in time
        while current_date <= today:
            # Calculate stock holdings at this date
            stock_value = Decimal('0.00')
            transactions_till_date = StockTransaction.objects.filter(
                user=user,
                created_at__date__lte=current_date
            )
            
            holdings_at_date = {}
            for txn in transactions_till_date:
                symbol = txn.stock.symbol
                if symbol not in holdings_at_date:
                    holdings_at_date[symbol] = {'quantity': 0, 'stock': txn.stock}
                
                if txn.transaction_type == 'BUY':
                    holdings_at_date[symbol]['quantity'] += txn.quantity
                else:  # SELL
                    holdings_at_date[symbol]['quantity'] -= txn.quantity
            
            for symbol, data in holdings_at_date.items():
                if data['quantity'] > 0:
                    stock_value += data['quantity'] * data['stock'].price
            
            # Calculate IPO value at this date (only allotted IPOs up to this date)
            ipo_value = IPOApplication.objects.filter(
                user=user,
                status='Allotted',
                applied_at__date__lte=current_date
            ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
            
            # Total portfolio = stocks + IPOs
            total_portfolio_value = stock_value + ipo_value
            
            portfolio_values.append(float(total_portfolio_value))
            portfolio_labels.append(current_date.strftime('%b %d'))
            
            # Move to next interval
            current_date += timedelta(days=interval_days)
        
        # Always add today's value as the last point
        if portfolio_labels[-1] != today.strftime('%b %d'):
            portfolio_values.append(float(total_current + ipo_invested))
            portfolio_labels.append(today.strftime('%b %d'))
    else:
        # No transactions yet, show current value only
        portfolio_values = [float(total_current + ipo_invested)]
        portfolio_labels = [datetime.now().strftime('%b %d')]
    
    import json
    chart_data = json.dumps(portfolio_values)
    chart_labels = json.dumps(portfolio_labels)

    context = {
        "total_net_worth": total_net_worth,
        "total_portfolio": total_current,
        "total_invested": total_invested,
        "stock_invested": stock_invested,
        "ipo_invested": ipo_invested,
        "total_profit": total_profit,
        "portfolio_return_pct": portfolio_return_pct,
        "available_cash": available_cash,
        "chart_data": chart_data,
        "chart_labels": chart_labels,
        "recent_transactions": recent_transactions,
        "top_gainers": top_gainers,
        "top_losers": top_losers,
        "total_holdings": len(holdings_data),
    }

    return render(request, "core/dashboard.html", context)


def logout_view(request):
    logout(request)
    return redirect('home')

# def stocks(request):
#     stocks = Stock.objects.all()
#     return render(request, 'core/stocks.html', {'stocks': stocks})
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Portfolio, Holding, Wallet

@login_required
def stocks(request):
    portfolio = Portfolio.objects.filter(user=request.user).first()
    wallet = Wallet.objects.filter(user=request.user).first()

    holdings_data = []
    total_value = Decimal("0.00")
    total_pnl = Decimal("0.00")
    invested_amount = Decimal("0.00")   # ✅ NEW
    wallet_balance = wallet.balance if wallet else Decimal("0.00")

    if portfolio:
        holdings = Holding.objects.select_related("stock").filter(
            portfolio=portfolio
        )

        for h in holdings:
            current_price = h.stock.price
            stock_value = current_price * h.quantity
            pnl = (current_price - h.buy_price) * h.quantity
            
            # Calculate change percentage
            if h.buy_price > 0:
                change_pct = ((current_price - h.buy_price) / h.buy_price) * 100
            else:
                change_pct = Decimal("0.00")

            total_value += stock_value
            total_pnl += pnl
            invested_amount += h.buy_price * h.quantity   # ✅ NEW

            holdings_data.append({
                "symbol": h.stock.symbol,
                "name": h.stock.name,
                "quantity": h.quantity,
                "buy_price": h.buy_price,
                "current_price": current_price,
                "pnl": pnl,
                "change_pct": change_pct,
            })

    context = {
        "holdings": holdings_data,
        "total_value": total_value,
        "day_pnl": total_pnl,
        "wallet_balance": wallet_balance,
        "invested_amount": invested_amount,   # ✅ NEW
    }

    return render(request, "core/stocks.html", context)
from django.contrib.auth.decorators import login_required
from .models import IPOApplication
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from decimal import Decimal
from .models import IPOApplication, Wallet


@login_required
def ipo(request):

    user_apps = IPOApplication.objects.filter(user=request.user)

    applied_count = user_apps.filter(status="Applied").count()
    allotted_count = user_apps.filter(status="Allotted").count()
    rejected_count = user_apps.filter(status="Rejected").count()

    total_applied = user_apps.count()

    # 💰 Total Invested (Allotted IPOs only)
    total_invested = user_apps.filter(
        status="Allotted"
    ).aggregate(Sum("total_amount"))["total_amount__sum"] or Decimal("0")

    # 🏦 Wallet Balance
    wallet, _ = Wallet.objects.get_or_create(user=request.user)

    context = {
        "applied_count": applied_count,
        "allotted_count": allotted_count,
        "rejected_count": rejected_count,
        "total_applied": total_applied,
        "total_invested": total_invested,
        "wallet_balance": wallet.balance,
        "user_apps": user_apps.order_by("-applied_at")
    }

    return render(request, "core/ipo.html", context)

def mutual_funds(request):
    funds = [
        {
            "name": "Axis Bluechip Fund",
            "category": "Large Cap",
            "nav": "₹54.32",
            "returns": "14.2%"
        },
        {
            "name": "SBI Small Cap Fund",
            "category": "Small Cap",
            "nav": "₹138.67",
            "returns": "19.8%"
        },
        {
            "name": "HDFC Balanced Advantage Fund",
            "category": "Hybrid",
            "nav": "₹32.15",
            "returns": "11.6%"
        },
        {
            "name": "ICICI Prudential Technology Fund",
            "category": "Sectoral",
            "nav": "₹178.40",
            "returns": "21.3%"
        },
    ]
    return render(request, 'core/mutual_funds.html', {"funds": funds})




def live_stocks(request):
    stocks = ["RELIANCE.BSE", "TCS.BSE"]

    data = []
    for stock in stocks:
        data.append(get_stock_price(stock))

    return JsonResponse({"stocks": data})

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Portfolio, Holding
import json
from .models import WalletTransaction
from decimal import Decimal

@login_required
def portfolio_view(request):
    user = request.user

    portfolio = Portfolio.objects.filter(user=user).first()

    if portfolio:
        holdings = Holding.objects.filter(portfolio=portfolio).select_related('stock')
    else:
        holdings = Holding.objects.none()

    # --- Calculations ---
    total_invested = sum(
        (h.quantity * h.buy_price for h in holdings),
        Decimal("0")
    )

    total_current = sum(
        (h.quantity * h.stock.price for h in holdings),
        Decimal("0")
    )

    total_profit = total_current - total_invested

    # --- Portfolio Growth % ---
    if total_invested > 0:
        total_return_percent = (total_profit / total_invested) * 100
    else:
        total_return_percent = Decimal("0")

    # --- Risk Score Logic ---
    num_stocks = holdings.count()

    if num_stocks == 0:
        risk_score = 0
    elif num_stocks < 3:
        risk_score = 8.5
    elif num_stocks < 6:
        risk_score = 6.5
    else:
        risk_score = 4.5

    # --- Holdings Breakdown for Pie Chart ---
    holdings_breakdown = []
    for h in holdings:
        holdings_breakdown.append({
            'symbol': h.stock.symbol,
            'value': float(h.quantity * h.stock.price),
            'percentage': float((h.quantity * h.stock.price / total_current * 100) if total_current > 0 else 0)
        })

    # --- Generate Candlestick Data (simulated daily data for last 30 days) ---
    from datetime import datetime, timedelta
    import random
    
    candlestick_data = []
    base_price = float(total_current) if total_current > 0 else 100000
    
    for i in range(30, 0, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        
        # Simulate OHLC data with some randomness
        open_price = base_price * (1 + random.uniform(-0.03, 0.03))
        close_price = open_price * (1 + random.uniform(-0.05, 0.05))
        high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
        low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.02))
        
        candlestick_data.append({
            'date': date,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2)
        })
        
        base_price = close_price

    # --- Top Performers ---
    top_performers = []
    for h in holdings:
        pnl = (h.stock.price - h.buy_price) * h.quantity
        pnl_pct = ((h.stock.price - h.buy_price) / h.buy_price * 100) if h.buy_price > 0 else 0
        
        top_performers.append({
            'symbol': h.stock.symbol,
            'name': h.stock.name,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'current_price': h.stock.price,
            'quantity': h.quantity
        })
    
    top_performers.sort(key=lambda x: x['pnl_pct'], reverse=True)

    # --- Sector Allocation (simplified) ---
    sector_allocation = [
        {'sector': 'Technology', 'percentage': 35},
        {'sector': 'Finance', 'percentage': 25},
        {'sector': 'Healthcare', 'percentage': 20},
        {'sector': 'Energy', 'percentage': 12},
        {'sector': 'Others', 'percentage': 8}
    ]

    # --- Recent Activity (All Transactions) ---
    recent_transactions = WalletTransaction.objects.filter(
        user=user
    ).select_related('stock').order_by('-created_at')[:10]  # Show last 10 transactions

    # --- Portfolio Metrics ---
    avg_return = total_return_percent / num_stocks if num_stocks > 0 else Decimal("0")
    best_performer = top_performers[0] if top_performers else None
    worst_performer = top_performers[-1] if top_performers else None

    import json
    context = {
        "total_current": total_current,
        "total_invested": total_invested,
        "total_profit": total_profit,
        "total_return_percent": total_return_percent,
        "risk_score": risk_score,
        "num_stocks": num_stocks,
        "recent_transactions": recent_transactions,
        "holdings_breakdown": json.dumps(holdings_breakdown),
        "candlestick_data": json.dumps(candlestick_data),
        "top_performers": top_performers[:5],
        "sector_allocation": json.dumps(sector_allocation),
        "avg_return": avg_return,
        "best_performer": best_performer,
        "worst_performer": worst_performer,
    }

    return render(request, "core/portfolio.html", context)

def demat_open(request):
    if request.method == "POST":
        DematAccount.objects.create(
            full_name=request.POST['full_name'],
            dob=request.POST['dob'],
            email=request.POST['email'],
            mobile=request.POST['mobile'],
            pan_number=request.POST['pan'],
            aadhaar_number=request.POST['aadhaar'],
            pan_file=request.FILES['pan_file'],
            aadhaar_file=request.FILES['aadhaar_file'],
            bank_name=request.POST['bank'],
            account_number=request.POST['account'],
            ifsc_code=request.POST['ifsc'],
        )

        messages.success(request, "Demat Account Application Submitted!")
        return redirect('demat_status')

    return render(request, 'core/demat_open.html')


def demat_status(request):
    applications = DematAccount.objects.all().order_by('-created_at')
    return render(request, 'core/demat_status.html', {'applications': applications})

client = OpenAI(
    api_key=settings.AI_API_KEY,
    base_url="https://openrouter.ai/api/v1",
)

@csrf_exempt
@csrf_exempt
def ai_chat(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        data = json.loads(request.body)
        user_message = data.get("message")

        # Get user's portfolio data for personalized insights
        user = request.user
        portfolio = Portfolio.objects.filter(user=user).first()
        
        portfolio_context = ""
        
        if portfolio:
            holdings = Holding.objects.filter(portfolio=portfolio).select_related('stock')
            
            if holdings.exists():
                # Build portfolio summary
                total_invested = Decimal('0.00')
                total_current = Decimal('0.00')
                holdings_list = []
                
                for h in holdings:
                    stock_invested = h.quantity * h.buy_price
                    stock_current = h.quantity * h.stock.price
                    stock_pnl = stock_current - stock_invested
                    pnl_pct = ((stock_pnl / stock_invested) * 100) if stock_invested > 0 else 0
                    
                    total_invested += stock_invested
                    total_current += stock_current
                    
                    holdings_list.append(
                        f"- {h.stock.symbol}: {h.quantity} shares, "
                        f"Buy Price: ₹{h.buy_price}, Current: ₹{h.stock.price}, "
                        f"P&L: ₹{stock_pnl:.2f} ({pnl_pct:.2f}%)"
                    )
                
                total_pnl = total_current - total_invested
                total_return_pct = ((total_pnl / total_invested) * 100) if total_invested > 0 else 0
                
                # Get IPO data
                ipo_invested = IPOApplication.objects.filter(
                    user=user,
                    status='Allotted'
                ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
                
                # Get wallet balance
                wallet = Wallet.objects.filter(user=user).first()
                wallet_balance = wallet.balance if wallet else Decimal('0.00')
                
                portfolio_context = f"""
USER'S PORTFOLIO DATA:
======================
Total Invested in Stocks: ₹{total_invested:.2f}
Current Portfolio Value: ₹{total_current:.2f}
Total P&L: ₹{total_pnl:.2f} ({total_return_pct:.2f}%)
IPO Investments: ₹{ipo_invested:.2f}
Available Cash: ₹{wallet_balance:.2f}

CURRENT HOLDINGS:
{chr(10).join(holdings_list)}

Use this data to provide PERSONALIZED investment advice specific to the user's portfolio.
"""
            else:
                portfolio_context = "User has no current stock holdings. Provide general investment guidance."
        else:
            portfolio_context = "User has no portfolio yet. Provide beginner investment guidance."

        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI investment assistant for CapitalNest. "
                        "Provide PERSONALIZED investment advice based on the user's actual portfolio data. "
                        "Analyze their holdings, suggest when to buy/sell/hold specific stocks, "
                        "identify overvalued/undervalued positions, recommend diversification, "
                        "and provide actionable insights. Be specific and reference their actual stocks. "
                        "Keep responses concise and actionable.\n\n"
                        f"{portfolio_context}"
                    )
                },
                {"role": "user", "content": user_message}
            ],
            extra_headers={
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "CapitalNest AI"
            }
        )

        return JsonResponse({
            "reply": response.choices[0].message.content
        })

    except Exception as e:
        print("OPENROUTER ERROR:", e)
        return JsonResponse({"error": "AI service failed"}, status=500)


def ai_insights_page(request):
    return render(request, "core/ai_insights.html")

import random
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile

OTP_STORE = {}   # for demo / college project only

def forgot_password(request):
    if request.method == 'POST':
        mobile = request.POST['mobile']

        try:
            profile = UserProfile.objects.get(mobile=mobile)
            otp = random.randint(100000, 999999)
            OTP_STORE[mobile] = otp

            print("OTP (for demo):", otp)  # show in terminal
            request.session['reset_mobile'] = mobile

            messages.success(request, "OTP sent to your mobile")
            return redirect('verify_otp')

        except UserProfile.DoesNotExist:
            messages.error(request, "Mobile number not registered")

    return render(request, 'core/forget_password.html')


def verify_otp(request):
    if request.method == 'POST':
        otp_input = request.POST['otp']
        mobile = request.session.get('reset_mobile')

        if mobile and OTP_STORE.get(mobile) == int(otp_input):
            messages.success(request, "OTP verified")
            return redirect('reset_password')
        else:
            messages.error(request, "Invalid OTP")

    return render(request, 'core/verify_otp.html')


def reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        mobile = request.session.get('reset_mobile')

        profile = UserProfile.objects.get(mobile=mobile)
        user = profile.user
        user.set_password(password)
        user.save()

        messages.success(request, "Password reset successfully")
        return redirect('login')

    return render(request, 'core/reset_password.html')


from django.http import JsonResponse
from django.core.cache import cache
from .service.yahoo_data import get_yahoo_stock_data

NIFTY_50 = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "HINDUNILVR.NS", "ITC.NS", "LT.NS", "KOTAKBANK.NS",
    "AXISBANK.NS", "BHARTIARTL.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "SUNPHARMA.NS", "TITAN.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    "ULTRACEMCO.NS", "HCLTECH.NS", "WIPRO.NS", "NTPC.NS", "POWERGRID.NS",
    "ONGC.NS", "COALINDIA.NS", "TECHM.NS", "JSWSTEEL.NS", "TATASTEEL.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "BPCL.NS", "DIVISLAB.NS",
    "DRREDDY.NS", "GRASIM.NS", "HDFCLIFE.NS", "INDUSINDBK.NS",
    "NESTLEIND.NS", "SBILIFE.NS", "EICHERMOT.NS", "HEROMOTOCO.NS",
    "BRITANNIA.NS", "UPL.NS", "CIPLA.NS", "APOLLOHOSP.NS",
    "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "SHREECEM.NS"
]
BANKS_FINANCE = [
    "FEDERALBNK.NS", "IDFCFIRSTB.NS", "PNB.NS", "BANKBARODA.NS",
    "CANBK.NS", "AUBANK.NS", "BANDHANBNK.NS", "YESBANK.NS",
    "CHOLAFIN.NS", "MUTHOOTFIN.NS", "PEL.NS", "LICHSGFIN.NS"
]
IT_TECH = [
    "LTIM.NS", "MPHASIS.NS", "COFORGE.NS", "PERSISTENT.NS",
    "TATAELXSI.NS", "OFSS.NS", "L&TTS.NS", "KPITTECH.NS",
    "ZENSARTECH.NS", "CYIENT.NS"
]
PHARMA = [
    "ALKEM.NS", "AUROPHARMA.NS", "LUPIN.NS", "TORNTPHARM.NS",
    "BIOCON.NS", "GLENMARK.NS", "ABBOTINDIA.NS", "SANOFI.NS",
    "IPCALAB.NS", "PFIZER.NS"
]
METALS_ENERGY = [
    "HINDALCO.NS", "SAIL.NS", "NMDC.NS", "VEDL.NS", "JINDALSTEL.NS",
    "ADANIGREEN.NS", "ADANIPOWER.NS", "ADANITRANS.NS",
    "IOC.NS", "GAIL.NS", "PETRONET.NS", "NHPC.NS"
]
FMCG = [
    "DABUR.NS", "MARICO.NS", "COLPAL.NS", "GODREJCP.NS",
    "UBL.NS", "PIDILITIND.NS", "TATACONSUM.NS",
    "VBL.NS", "DMART.NS"
]
AUTO_MANUFACTURING = [
    "ASHOKLEY.NS", "TVSMOTOR.NS", "ESCORTS.NS",
    "BOSCHLTD.NS", "MOTHERSON.NS", "BALKRISIND.NS",
    "AMARAJABAT.NS", "EXIDEIND.NS"
]


YAHOO_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "HINDUNILVR.NS", "ITC.NS", "LT.NS", "KOTAKBANK.NS",
    "AXISBANK.NS", "BHARTIARTL.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "SUNPHARMA.NS", "TITAN.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    "ULTRACEMCO.NS", "HCLTECH.NS", "WIPRO.NS", "NTPC.NS", "POWERGRID.NS",
    "ONGC.NS", "COALINDIA.NS", "TECHM.NS", "JSWSTEEL.NS", "TATASTEEL.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "BPCL.NS", "DIVISLAB.NS",
    "DRREDDY.NS", "GRASIM.NS", "HDFCLIFE.NS", "INDUSINDBK.NS",
    "NESTLEIND.NS", "SBILIFE.NS", "EICHERMOT.NS", "HEROMOTOCO.NS",
    "BRITANNIA.NS", "UPL.NS", "CIPLA.NS", "APOLLOHOSP.NS",
    "TATAMOTORS.NS", "M&M.NS", "BAJAJ-AUTO.NS", "SHREECEM.NS",
    "FEDERALBNK.NS", "IDFCFIRSTB.NS", "PNB.NS", "BANKBARODA.NS",
    "CANBK.NS", "AUBANK.NS", "BANDHANBNK.NS", "YESBANK.NS",
    "CHOLAFIN.NS", "MUTHOOTFIN.NS", "PEL.NS", "LICHSGFIN.NS",
    "LTIM.NS", "MPHASIS.NS", "COFORGE.NS", "PERSISTENT.NS",
    "TATAELXSI.NS", "OFSS.NS", "KPITTECH.NS",
    "ZENSARTECH.NS", "CYIENT.NS",
    "ALKEM.NS", "AUROPHARMA.NS", "LUPIN.NS", "TORNTPHARM.NS",
    "BIOCON.NS", "GLENMARK.NS", "ABBOTINDIA.NS", "SANOFI.NS",
    "IPCALAB.NS", "PFIZER.NS",
    "HINDALCO.NS", "SAIL.NS", "NMDC.NS", "VEDL.NS", "JINDALSTEL.NS",
    "ADANIGREEN.NS", "ADANIPOWER.NS", "ADANITRANS.NS",
    "IOC.NS", "GAIL.NS", "PETRONET.NS", "NHPC.NS",
    "DABUR.NS", "MARICO.NS", "COLPAL.NS", "GODREJCP.NS",
    "UBL.NS", "PIDILITIND.NS", "TATACONSUM.NS",
    "VBL.NS", "DMART.NS",
    "ASHOKLEY.NS", "TVSMOTOR.NS", "ESCORTS.NS",
    "BOSCHLTD.NS", "MOTHERSON.NS", "BALKRISIND.NS", "EXIDEIND.NS",
]
from django.http import JsonResponse
from django.core.cache import cache
from core.service.yahoo_data import get_yahoo_stock_data
import math



CACHE_KEY = "yahoo_stock_data"
CACHE_TTL = 30  

def clean_number(val):
    if val is None:
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    return float(val)

from django.contrib.auth.decorators import login_required

@login_required
def yahoo_stocks_page(request):
    return render(request, "core/live_stocks.html")



from django.http import JsonResponse
from django.core.cache import cache
from .service.yahoo_data import get_yahoo_stock_data

YAHOO_STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "SBIN.NS", "HINDUNILVR.NS", "ITC.NS", "LT.NS", "KOTAKBANK.NS",
    "AXISBANK.NS", "BHARTIARTL.NS", "ASIANPAINT.NS", "MARUTI.NS",
    "SUNPHARMA.NS", "TITAN.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    "ULTRACEMCO.NS", "HCLTECH.NS", "WIPRO.NS", "NTPC.NS", "POWERGRID.NS",
    "ONGC.NS", "COALINDIA.NS", "TECHM.NS", "JSWSTEEL.NS", "TATASTEEL.NS",
    "ADANIENT.NS", "ADANIPORTS.NS", "BPCL.NS", "DIVISLAB.NS",
    "DRREDDY.NS", "GRASIM.NS", "HDFCLIFE.NS", "INDUSINDBK.NS",
    "NESTLEIND.NS", "SBILIFE.NS", "EICHERMOT.NS", "HEROMOTOCO.NS",
    "BRITANNIA.NS", "UPL.NS", "CIPLA.NS", "APOLLOHOSP.NS", "M&M.NS", "BAJAJ-AUTO.NS", "SHREECEM.NS",
    "FEDERALBNK.NS", "IDFCFIRSTB.NS", "PNB.NS", "BANKBARODA.NS",
    "CANBK.NS", "AUBANK.NS", "BANDHANBNK.NS", "YESBANK.NS",
    "CHOLAFIN.NS", "MUTHOOTFIN.NS", "LICHSGFIN.NS",
    "LTIM.NS", "MPHASIS.NS", "COFORGE.NS", "PERSISTENT.NS",
    "TATAELXSI.NS", "OFSS.NS", "KPITTECH.NS",
    "ZENSARTECH.NS", "CYIENT.NS",
    "ALKEM.NS", "AUROPHARMA.NS", "LUPIN.NS", "TORNTPHARM.NS",
    "BIOCON.NS", "GLENMARK.NS", "ABBOTINDIA.NS", "SANOFI.NS",
    "IPCALAB.NS", "PFIZER.NS",
    "HINDALCO.NS", "SAIL.NS", "NMDC.NS", "VEDL.NS", "JINDALSTEL.NS",
    "ADANIGREEN.NS", "ADANIPOWER.NS",
    "IOC.NS", "GAIL.NS", "PETRONET.NS", "NHPC.NS",
    "DABUR.NS", "MARICO.NS", "COLPAL.NS", "GODREJCP.NS",
    "UBL.NS", "PIDILITIND.NS", "TATACONSUM.NS",
    "VBL.NS", "DMART.NS",
    "ASHOKLEY.NS", "TVSMOTOR.NS", "ESCORTS.NS",
    "BOSCHLTD.NS", "MOTHERSON.NS", "BALKRISIND.NS",
    "AMARAJABAT.NS", "EXIDEIND.NS",
]


CACHE_KEY = "yahoo_stocks_cache"
CACHE_TTL = 30  # seconds

def yahoo_live_stocks_api(request):
    """
    API endpoint: /api/yahoo-stocks/
    Returns Yahoo prices + INTERNAL DB stock_id
    """
    cached_data = cache.get(CACHE_KEY)
    if cached_data:
        return JsonResponse(cached_data, safe=False)

    yahoo_data = get_yahoo_stock_data(YAHOO_STOCKS)

    # 🔥 MAP DB STOCK IDS
    symbols = [s["symbol"] for s in yahoo_data]
    db_stocks = Stock.objects.filter(symbol__in=symbols)
    stock_map = {s.symbol: s.id for s in db_stocks}

    for s in yahoo_data:
        s["id"] = stock_map.get(s["symbol"])  # ✅ THIS FIXES EVERYTHING

    cache.set(CACHE_KEY, yahoo_data, timeout=CACHE_TTL)
    return JsonResponse(yahoo_data, safe=False)



# =========================
# MUTUAL FUNDS (AMFI)
# =========================

AMFI_CACHE_KEY = "amfi_mutual_funds"
AMFI_CACHE_TTL = 60 * 60 * 6  # 6 hours (NAV updates once daily)

def mutual_funds_page(request):
    return render(request, "core/mutualfunds_real.html")

from django.http import JsonResponse
from django.core.cache import cache
import requests

AMFI_URL = "https://api.mfapi.in/mf"
CACHE_KEY = "amfi_mf_limited"
CACHE_TTL = 60 * 60  # 1 hour

from django.http import JsonResponse
import requests


def mutual_funds_api(request):
    import requests

    try:
        res = requests.get("https://api.mfapi.in/mf", timeout=10)
        data = res.json()

        cleaned = []
        for mf in data[:1000]:
            cleaned.append({
                "scheme_code": mf.get("schemeCode"),
                "scheme_name": mf.get("schemeName"),
            })

        return JsonResponse(cleaned, safe=False)

    except Exception as e:
        print("MF API ERROR:", e)
        return JsonResponse([], safe=False)


def mutual_fund_nav_api(request, scheme_code):
    import requests

    try:
        url = f"https://api.mfapi.in/mf/{scheme_code}"
        res = requests.get(url, timeout=10)
        data = res.json()

        latest = data["data"][0]

        return JsonResponse({
            "nav": latest["nav"],
            "date": latest["date"]
        })

    except Exception as e:
        print("NAV FETCH ERROR:", e)
        return JsonResponse({}, safe=False)



from django.http import JsonResponse
from django.shortcuts import render
from django.core.cache import cache
from .service.ipo_data import IPO_DATA

IPO_CACHE_KEY = "ipo_data"
IPO_CACHE_TTL = 30  # seconds

def ipo_real_page(request):
    return render(request, "core/ipo_real.html")

def ipo_api(request):
    cached = cache.get(IPO_CACHE_KEY)
    if cached:
        return JsonResponse(cached, safe=False)

    cache.set(IPO_CACHE_KEY, IPO_DATA, IPO_CACHE_TTL)
    return JsonResponse(IPO_DATA, safe=False)

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
from decimal import Decimal
import json

from .models import (
    Stock,
    Wallet,
    Portfolio,
    Holding,
    StockTransaction,
)

from decimal import Decimal
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction

from .models import Stock, Wallet, Portfolio, Holding, StockTransaction
from .service.yahoo_data import get_yahoo_stock_data

@require_POST
@login_required
@transaction.atomic
def buy_stock(request):
    try:
        data = json.loads(request.body)

        symbol = data.get("symbol")
        quantity = data.get("quantity")

        # =========================
        # VALIDATION
        # =========================
        if not symbol:
            return JsonResponse({"error": "Stock symbol missing"}, status=400)

        if not quantity or int(quantity) <= 0:
            return JsonResponse({"error": "Invalid quantity"}, status=400)

        quantity = int(quantity)

        # =========================
        # FETCH LIVE PRICE (SERVER SIDE)
        # =========================
        stock_data = get_yahoo_stock_data([symbol])

        if not stock_data or not stock_data[0].get("current_price"):
            return JsonResponse({"error": "Live price unavailable"}, status=400)

        buy_price = Decimal(str(stock_data[0]["current_price"]))

        # =========================
        # GET OR CREATE STOCK
        # =========================
        stock, created = Stock.objects.get_or_create(
            symbol=symbol,
            defaults={
                "name": symbol,
                "price": buy_price,
                "market": "NSE",
            }
        )
        
        # ✅ Always update price to latest when buying
        if not created:
            stock.price = buy_price
            stock.save()

        total_cost = buy_price * quantity

        # =========================
        # WALLET
        # =========================
        wallet, _ = Wallet.objects.select_for_update().get_or_create(
            user=request.user
        )

        if wallet.balance < total_cost:
            return JsonResponse({"error": "Insufficient balance"}, status=400)

        wallet.balance -= total_cost
        wallet.save()

        # =========================
        # PORTFOLIO & HOLDING
        # =========================
        portfolio, _ = Portfolio.objects.get_or_create(user=request.user)

        holding, created = Holding.objects.get_or_create(
            portfolio=portfolio,
            stock=stock,
            defaults={
                "quantity": quantity,
                "buy_price": buy_price,
            }
        )

        if not created:
            holding.quantity += quantity
            holding.buy_price = buy_price
            holding.save()

        # =========================
        # TRANSACTION
        # =========================
        StockTransaction.objects.create(
            user=request.user,
            stock=stock,
            transaction_type=StockTransaction.BUY,
            quantity=quantity,
            price=buy_price,
        )

        # =========================
        # WALLET TRANSACTION LOG
        # =========================
        WalletTransaction.objects.create(
            user=request.user,
            transaction_type="STOCK_BUY",
            stock=stock,
            amount=total_cost,
            is_credit=False
        )

        return JsonResponse({
            "success": True,
            "message": "Stock purchased successfully"
        })

    except Exception as e:
        print("BUY STOCK ERROR:", e)
        return JsonResponse({"error": "Internal server error"}, status=500)
@require_POST
@login_required
@transaction.atomic
def sell_stock(request):
    try:
        data = json.loads(request.body)

        symbol = data.get("symbol")
        quantity = data.get("quantity")

        # 🔒 1. HARD VALIDATION
        if not symbol:
            return JsonResponse({"error": "Stock symbol missing"}, status=400)

        try:
            quantity = int(quantity)
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid quantity"}, status=400)

        if quantity <= 0:
            return JsonResponse({"error": "Quantity must be greater than zero"}, status=400)

        # 🔒 2. STOCK MUST EXIST
        stock = Stock.objects.select_for_update().filter(symbol=symbol).first()
        if not stock:
            return JsonResponse({"error": "Stock not found"}, status=404)

        # 🔒 3. PORTFOLIO MUST EXIST
        portfolio = Portfolio.objects.filter(user=request.user).first()
        if not portfolio:
            return JsonResponse({"error": "Portfolio not found"}, status=400)

        # 🔒 4. USER MUST OWN THIS STOCK
        holding = Holding.objects.select_for_update().filter(
            portfolio=portfolio,
            stock=stock
        ).first()

        if not holding:
            return JsonResponse(
                {"error": "You do not own this stock"},
                status=400
            )

        # 🔒 5. CANNOT SELL MORE THAN OWNED
        if quantity > holding.quantity:
            return JsonResponse(
                {"error": f"You only own {holding.quantity} shares"},
                status=400
            )

        # 🔒 6. WALLET MUST EXIST
        wallet, _ = Wallet.objects.select_for_update().get_or_create(
            user=request.user
        )

        sell_price = stock.price
        total_credit = sell_price * Decimal(quantity)

        # 🔒 7. CREDIT WALLET
        wallet.balance += total_credit
        wallet.save()

        # 🔒 8. UPDATE HOLDING
        holding.quantity -= quantity
        if holding.quantity == 0:
            holding.delete()
        else:
            holding.save()

        # 🔒 9. RECORD TRANSACTION
        StockTransaction.objects.create(
            user=request.user,
            stock=stock,
            transaction_type=StockTransaction.SELL,
            quantity=quantity,
            price=sell_price
        )

        # 🔒 10. WALLET TRANSACTION LOG
        WalletTransaction.objects.create(
            user=request.user,
            transaction_type="STOCK_SELL",
            stock=stock,
            amount=total_credit,
            is_credit=True
        )

        return JsonResponse({
            "success": True,
            "message": "Stock sold successfully",
            "symbol": symbol,
            "quantity": quantity,
            "price": str(sell_price),
            "credited": str(total_credit),
        })

    except Exception as e:
        print("SELL STOCK ERROR:", e)
        return JsonResponse(
            {"error": "Internal server error"},
            status=500
        )
    


from django.views.decorators.http import require_POST
from django.db import transaction
from decimal import Decimal
from django.contrib.auth.decorators import login_required
import json

from .models import Wallet, IPOApplication, WalletTransaction


@require_POST
@login_required
@transaction.atomic
# from django.http import JsonResponse
# from django.db import transaction
# from decimal import Decimal
# import json


def apply_ipo(request):
    try:
        if request.method != "POST":
            return JsonResponse({"error": "Invalid request method"}, status=405)

        data = json.loads(request.body)

        ipo_name = data.get("ipo_name")
        lot_size = int(data.get("lot_size"))
        price_per_share = Decimal(str(data.get("price_per_share")))
        lots = int(data.get("lots"))
        frontend_total = Decimal(str(data.get("total_amount")))

        # 🔒 VALIDATIONS
        if not ipo_name or lot_size <= 0 or lots <= 0:
            return JsonResponse({"error": "Invalid IPO data"}, status=400)

        # 🔁 Recalculate total on backend
        backend_total = lot_size * price_per_share * lots

        if backend_total != frontend_total:
            return JsonResponse(
                {"error": "Amount mismatch detected"},
                status=400
            )

        with transaction.atomic():

            # 🔒 Prevent duplicate active application
            existing = IPOApplication.objects.filter(
                user=request.user,
                ipo_name=ipo_name,
                status__in=["Applied", "Allotted"]
            ).exists()

            if existing:
                return JsonResponse(
                    {"error": "You have already applied for this IPO."},
                    status=400
                )

            # 🔒 LOCK WALLET
            wallet, _ = Wallet.objects.select_for_update().get_or_create(
                user=request.user
            )

            if wallet.balance < backend_total:
                return JsonResponse(
                    {"error": "Insufficient wallet balance"},
                    status=400
                )

            # 💰 Deduct balance
            wallet.balance -= backend_total
            wallet.save()

            # 📝 Create IPO Application
            IPOApplication.objects.create(
                user=request.user,
                ipo_name=ipo_name,
                lot_size=lot_size,
                price_per_share=price_per_share,
                lots=lots,
                total_amount=backend_total,
                status="Applied"
            )

            # 📒 Ledger Entry
            WalletTransaction.objects.create(
                user=request.user,
                transaction_type="IPO_APPLY",
                amount=backend_total,
                is_credit=False
            )

        return JsonResponse({
            "success": True,
            "message": "IPO applied successfully"
        })

    except Exception as e:
        print("IPO APPLY ERROR:", e)
        return JsonResponse(
            {"error": "Internal server error"},
            status=500
        )

