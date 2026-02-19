from django.contrib import admin
from django.contrib import messages
from django.db import transaction
import random

from .models import (
    Stock,
    Portfolio,
    Holding,
    IPO,
    MutualFund,
    DematAccount,
    IPOApplication,
    WalletTransaction,
    Wallet,
)

# =========================
# STOCKS
# =========================

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name")
    search_fields = ("symbol", "name")


# =========================
# PORTFOLIO
# =========================

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("user",)
    search_fields = ("user__username",)


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "stock", "quantity", "buy_price")
    list_filter = ("stock",)
    search_fields = ("stock__symbol",)


# =========================
# IPO LISTING
# =========================

@admin.register(IPO)
class IPOAdmin(admin.ModelAdmin):
    list_display = ("name", "price_band", "open_date", "status")
    list_filter = ("status",)
    search_fields = ("name",)


# =========================
# MUTUAL FUNDS
# =========================

@admin.register(MutualFund)
class MutualFundAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "nav", "one_year_return")
    list_filter = ("category",)
    search_fields = ("name",)


# =========================
# DEMAT
# =========================

@admin.register(DematAccount)
class DematAdmin(admin.ModelAdmin):
    list_display = ("full_name", "pan_number", "status")
    list_filter = ("status",)
    search_fields = ("full_name", "pan_number")


# =========================
# IPO APPLICATIONS (WITH RESULT PROCESSING)
# =========================

@admin.register(IPOApplication)
class IPOApplicationAdmin(admin.ModelAdmin):
    list_display = ("user", "ipo_name", "lots", "total_amount", "status", "applied_at")
    list_filter = ("status",)
    search_fields = ("user__username", "ipo_name")
    actions = ["process_results"]

    @admin.action(description="Process IPO Results (50-50 Random)")
    def process_results(self, request, queryset):

        applied_apps = queryset.filter(status="Applied")

        if not applied_apps.exists():
            self.message_user(
                request,
                "No applied IPOs selected.",
                level=messages.WARNING
            )
            return

        for app in applied_apps:
            with transaction.atomic():

                wallet = Wallet.objects.select_for_update().get(user=app.user)

                if random.choice([True, False]):
                    # Allotted
                    app.status = "Allotted"
                    app.save()

                    WalletTransaction.objects.create(
                        user=app.user,
                        transaction_type="IPO_ALLOT",
                        amount=app.total_amount,
                        is_credit=False
                    )

                else:
                    # Rejected → Refund
                    app.status = "Rejected"
                    app.save()

                    wallet.balance += app.total_amount
                    wallet.save()

                    WalletTransaction.objects.create(
                        user=app.user,
                        transaction_type="IPO_REFUND",
                        amount=app.total_amount,
                        is_credit=True
                    )

        self.message_user(
            request,
            "IPO results processed successfully.",
            level=messages.SUCCESS
        )


# =========================
# WALLET TRANSACTIONS
# =========================

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "transaction_type", "amount", "is_credit", "created_at")
    list_filter = ("transaction_type", "is_credit")
    search_fields = ("user__username",)
