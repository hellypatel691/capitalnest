

from django.db import models
from django.contrib.auth.models import User


# =========================
# MASTER DATA MODELS
# =========================

class Stock(models.Model):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    market = models.CharField(max_length=50, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class MutualFund(models.Model):
    CATEGORY_CHOICES = [
        ('Large Cap', 'Large Cap'),
        ('Small Cap', 'Small Cap'),
        ('Hybrid', 'Hybrid'),
        ('Sectoral', 'Sectoral'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Large Cap')
    nav = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    one_year_return = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name


class IPO(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Upcoming', 'Upcoming'),
        ('Closed', 'Closed'),
    ]

    name = models.CharField(max_length=100)
    price_band = models.CharField(max_length=50)
    open_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def __str__(self):
        return self.name


# =========================
# USER CORE MODELS
# =========================

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.user.username} Wallet"


class Portfolio(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, default="My Portfolio")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Portfolio"


# =========================
# TRANSACTIONS & HOLDINGS
# =========================

class StockTransaction(models.Model):
    BUY = 'BUY'
    SELL = 'SELL'

    TRANSACTION_TYPE_CHOICES = [
        (BUY, 'Buy'),
        (SELL, 'Sell'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPE_CHOICES)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} {self.transaction_type} {self.stock.symbol}"


class Holding(models.Model):
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name="holdings"
    )
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    buy_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('portfolio', 'stock')

    def __str__(self):
        return f"{self.stock.symbol} ({self.quantity})"


# =========================
# DEMAT & PROFILE
# =========================

class DematAccount(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    dob = models.DateField()
    email = models.EmailField()
    mobile = models.CharField(max_length=10)

    pan_number = models.CharField(max_length=10)
    aadhaar_number = models.CharField(max_length=12)

    pan_file = models.ImageField(upload_to='kyc/pan/')
    aadhaar_file = models.ImageField(upload_to='kyc/aadhaar/')

    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    ifsc_code = models.CharField(max_length=11)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mobile = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.user.username


# =========================
# IPO APPLICATION SYSTEM
# =========================

class IPOApplication(models.Model):
    STATUS_CHOICES = [
        ("Applied", "Applied"),
        ("Allotted", "Allotted"),
        ("Rejected", "Rejected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ipo_name = models.CharField(max_length=200)

    lot_size = models.IntegerField()
    price_per_share = models.DecimalField(max_digits=10, decimal_places=2)
    lots = models.IntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="Applied"
    )

    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.ipo_name} ({self.status})"
class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("IPO_APPLY", "IPO Apply"),
        ("IPO_REFUND", "IPO Refund"),
        ("IPO_ALLOT", "IPO Allotment"),
        ("STOCK_BUY", "Stock Buy"),
        ("STOCK_SELL", "Stock Sell"),
        ("WALLET_ADD", "Wallet Add"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)

    stock = models.ForeignKey(
        'Stock',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    is_credit = models.BooleanField()

    created_at = models.DateTimeField(auto_now_add=True)
