
console.log("Yahoo stocks JS loaded");

let allStocks = [];

/* =========================
   SAFE NUMBER
========================= */
function safeNumber(val) {
    const num = Number(val);
    return isNaN(num) ? null : num;
}

/* =========================
   LAST UPDATED
========================= */
function updateLastUpdatedTime() {
    const el = document.getElementById("last-updated");
    if (el) el.innerText = new Date().toLocaleString();
}

function getCSRFToken() {
    const name = "csrftoken";
    const cookies = document.cookie.split(";");

    for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + "=")) {
            return decodeURIComponent(cookie.substring(name.length + 1));
        }
    }
    return "";
}

function buyStock(stockId, symbol, price) {
    // 🔒 HARD GUARD (THIS FIXES EVERYTHING)
    if (price === null || price === undefined || isNaN(price)) {
        alert("❌ Live price unavailable. Please try again later.");
        return;
    }

    const qty = prompt(`Enter quantity to BUY for ${symbol}:`);
    if (qty === null) return;

    const quantity = Number(qty);
    if (isNaN(quantity) || quantity <= 0) {
        alert("❌ Invalid quantity. Please enter a positive number.");
        return;
    }

    fetch("/buy-stock/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({
            symbol: symbol,
            price: price,        // ✅ GUARANTEED VALID NOW
            quantity: quantity
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert(
                `✅ BUY SUCCESSFUL\n\n` +
                `Stock: ${symbol}\n` +
                `Quantity: ${quantity}\n` +
                `Price: ₹${price}`
            );
            location.reload();
        } else {
            alert(`❌ ${data.error}`);
        }
    })
    .catch(err => {
        console.error("Buy error:", err);
        alert("❌ Server error while buying stock");
    });
}
/* =========================
   MAIN TABLE RENDER
========================= */
function renderStocks(stocks) {
    const tbody = document.getElementById("stocks-body");
    if (!tbody) return;

    tbody.innerHTML = "";

    stocks.forEach(stock => {
        const prev = safeNumber(stock.previous_price);
        const curr = safeNumber(stock.current_price);
        const change = safeNumber(stock.percent_change);

        if (prev === null || curr === null || change === null) return;

        const isUp = change >= 0;

        tbody.innerHTML += `
            <tr>
                <td><span class="stock-badge">${stock.symbol}</span></td>

                <td class="text-end">₹${prev.toFixed(2)}</td>

                <td class="text-end">₹${curr.toFixed(2)}</td>

                <td class="text-end">
                    <span class="change-badge ${isUp ? "change-up" : "change-down"}">
                        ${isUp ? "+" : ""}${change.toFixed(2)}%
                    </span>
                </td>

                <td class="text-center">
                    <button class="btn btn-success btn-sm me-1"
                        onclick="buyStock(${stock.id}, '${stock.symbol}', ${curr})">
                        Buy
                    </button>
                    <button class="btn btn-danger btn-sm"
                        onclick="sellStock('${stock.symbol}', ${curr})">
                        Sell
                    </button>
                </td>
            </tr>
        `;
    });
}

/* =========================
   TOP GAINERS / LOSERS
========================= */
function updateTopMovers(stocks) {
    const gainers = document.getElementById("top-gainers");
    const losers = document.getElementById("top-losers");
    if (!gainers || !losers) return;

    gainers.innerHTML = "";
    losers.innerHTML = "";

    const valid = stocks.filter(s =>
        typeof s.percent_change === "number" && !isNaN(s.percent_change)
    );

    const sorted = [...valid].sort((a, b) => b.percent_change - a.percent_change);

    sorted.slice(0, 5).forEach(s => {
        gainers.innerHTML += `
            <li class="list-group-item d-flex justify-content-between">
                <span>${s.symbol}</span>
                <span class="text-success fw-bold">+${s.percent_change.toFixed(2)}%</span>
            </li>`;
    });

    sorted.slice(-5).reverse().forEach(s => {
        losers.innerHTML += `
            <li class="list-group-item d-flex justify-content-between">
                <span>${s.symbol}</span>
                <span class="text-danger fw-bold">${s.percent_change.toFixed(2)}%</span>
            </li>`;
    });
}

/* =========================
   FETCH DATA
========================= */
function loadYahooStocks() {
    fetch("/api/yahoo-stocks/")
        .then(res => res.json())
        .then(data => {
            allStocks = data || [];
            renderStocks(allStocks);
            updateTopMovers(allStocks);
            updateLastUpdatedTime();
        })
        .catch(err => console.error("Yahoo fetch error:", err));
}

/* =========================
   SEARCH
========================= */
document.getElementById("stock-search")?.addEventListener("input", e => {
    const q = e.target.value.toUpperCase();
    const filtered = allStocks.filter(s =>
        s.symbol.toUpperCase().includes(q)
    );
    renderStocks(filtered);
});

/* =========================
   INIT
========================= */
document.addEventListener("DOMContentLoaded", () => {
    loadYahooStocks();
    setInterval(loadYahooStocks, 15000);
});


// GLOBAL VARIABLES (top of JS file)
let sellStockId = null;
let sellMaxQty = 0;

function sellStock(symbol) {
    const qty = prompt(`Enter quantity to SELL for ${symbol}:`);
    if (qty === null) return;

    const quantity = Number(qty);
    if (!quantity || quantity <= 0) {
        alert("❌ Invalid quantity");
        return;
    }

    fetch("/sell-stock/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify({
            symbol: symbol,
            quantity: quantity
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            alert(
                `✅ SELL SUCCESSFUL\n\n` +
                `Stock: ${data.symbol}\n` +
                `Quantity: ${data.quantity}\n` +
                `Price: ₹${data.price}\n` +
                `Credited: ₹${data.credited}`
            );
            location.reload();
        } else {
            alert(`❌ ${data.error}`);
        }
    })
    .catch(() => {
        alert("❌ Server error");
    });
}

