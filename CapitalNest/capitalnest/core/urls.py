from django.urls import path
from . import views
from .views import live_stocks
from .service import portfolio_analysis
from .views import portfolio_view
from .views import buy_stock
from .views import sell_stock

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('stocks/', views.stocks, name='stocks'),
    path('ipo/', views.ipo, name='ipo'),
    path('mutual-funds/', views.mutual_funds, name='mutual_funds'),
    path("api/stocks/", live_stocks, name="live_stocks"),
    path("portfolio/", portfolio_view, name="portfolio"),
    path('demat/open/', views.demat_open, name='demat_open'),
    path('demat/open/', views.demat_open, name='demat_open'),
    path('demat/status/', views.demat_status, name='demat_status'),
    path("ai/insights/", views.ai_insights_page, name="ai_insights_page"),
    path("ai/chat/", views.ai_chat, name="ai_chat"),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path("api/yahoo-stocks/", views.yahoo_live_stocks_api, name="yahoo_stocks"),
    path("live-stocks/", views.yahoo_stocks_page, name="yahoo_stocks_page"),
    path("mutualfunds_real/", views.mutual_funds_page, name="mutual_funds_page"),
    path("api/mutual-funds/", views.mutual_funds_api, name="mutual_funds_api"),
    path("api/mutual-funds/<int:scheme_code>/", views.mutual_fund_nav_api),
    path("ipo_real/", views.ipo_real_page, name="ipo_real_page"),
    path("api/ipo/", views.ipo_api, name="ipo_api"),
    path("buy-stock/", buy_stock, name="buy_stock"),
    path("sell-stock/", sell_stock, name="sell_stock"),
    path("set-balance/", views.set_balance, name="set_balance"),
    path("ipo/apply/", views.apply_ipo, name="apply_ipo"),
]

