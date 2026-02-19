from datetime import date
IPO_DATA = [
    {
        "name": "ABC Technologies Ltd",
        "open_date": "2026-02-01",
        "close_date": "2026-02-05",
        "price_band": "₹620 – ₹650",
        "gmp": 85,
        "subscription": {"retail": 4.2, "qib": 1.8, "nii": 2.9},
        "listing_gain": 32
    },
    {
        "name": "GreenPower Energy Ltd",
        "open_date": "2026-01-20",
        "close_date": "2026-01-24",
        "price_band": "₹210 – ₹220",
        "gmp": 12,
        "subscription": {"retail": 1.4, "qib": 0.6, "nii": 0.9},
        "listing_gain": 8
    },
    {
        "name": "Nova Infra Solutions Ltd",
        "open_date": "2026-01-30",
        "close_date": "2026-02-02",
        "price_band": "₹95 – ₹100",
        "gmp": 26,
        "subscription": {"retail": 2.6, "qib": 1.2, "nii": 1.8},
        "listing_gain": 18
    },
    {
        "name": "FinEdge Payments Ltd",
        "open_date": "2026-01-28",
        "close_date": "2026-01-31",
        "price_band": "₹410 – ₹430",
        "gmp": 52,
        "subscription": {"retail": 3.9, "qib": 2.1, "nii": 2.4},
        "listing_gain": 27
    },
    {
        "name": "AgroLife Sciences Ltd",
        "open_date": "2026-02-03",
        "close_date": "2026-02-06",
        "price_band": "₹155 – ₹165",
        "gmp": 9,
        "subscription": {"retail": 0.9, "qib": 0.4, "nii": 0.6},
        "listing_gain": 4
    },

    # -------- AUTO-GENERATED REALISTIC IPOs --------

    *[
        {
            "name": f"Company {i} Industries Ltd",
            "open_date": "2025-11-10",
            "close_date": "2025-11-14",
            "price_band": f"₹{80 + i} – ₹{90 + i}",
            "gmp": (i % 60) + 5,
            "subscription": {
                "retail": round(0.8 + (i % 5) * 0.6, 1),
                "qib": round(0.5 + (i % 4) * 0.5, 1),
                "nii": round(0.7 + (i % 6) * 0.4, 1)
            },
            "listing_gain": (i % 35) + 3
        }
        for i in range(6, 101)
    ]
]
