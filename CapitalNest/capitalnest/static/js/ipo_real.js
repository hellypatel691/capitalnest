




console.log("IPO JS loaded");

/* ================================
   GLOBAL VARIABLES
================================ */
let allIPOsData = []; 
let currentSearchTerm = "";

/* ================================
   COMPANY NAMES
================================ */
const COMPANY_NAMES = [
    "Aarohan Financial Services Ltd", "BluePeak Technologies Ltd", 
    "Suryodaya Energy Systems Ltd", "Vistara Infra Developers Ltd",
    "Trident FinServe Ltd", "Navkaar Retail Solutions Ltd",
    "GreenHorizon Renewables Ltd", "Apex Mobility Technologies Ltd",
    "Silverline Logistics Ltd", "Orion Consumer Products Ltd",
    "Zenith Healthcare Ltd", "Prakriti AgroTech Ltd",
    "NextGen AI Systems Ltd", "UrbanNest Realty Ltd",
    "CloudAxis Technologies Ltd", "IndusPay Digital Ltd",
    "TrueMart Retail Ltd", "CoreEdge Cybersecurity Ltd",
    "EcoFuel Mobility Ltd", "Vertex Engineering Ltd",
    "Pulse Diagnostics Ltd", "NeoGrid Power Ltd",
    "Skyline Cements Ltd", "InnoWealth FinTech Ltd",
    "BlueOrbit Space Systems Ltd", "AlphaShip Logistics Ltd",
    "MediCrest Lifesciences Ltd", "SolarNova Energy Ltd",
    "UrbanCart Commerce Ltd", "SmartRail Systems Ltd",
    "AgriGrow Foods Ltd", "DataBridge Analytics Ltd",
    "FastTrack Warehousing Ltd", "AquaPure Water Solutions Ltd",
    "SecureNet Technologies Ltd", "OmniRetail Solutions Ltd",
    "BioZen Pharmaceuticals Ltd", "Electra Mobility Ltd",
    "TrueBuild Infra Ltd", "FreshLeaf Consumer Ltd"
];

/* ================================
   HELPERS
================================ */
function formatDate(date) {
    const d = new Date(date);
    return d.toISOString().split('T')[0];
}

function addDays(date, days) {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
}

function daysLeft(closeDateStr) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const close = new Date(closeDateStr);
    close.setHours(0, 0, 0, 0);
    const diff = Math.ceil((close - today) / 86400000);
    
    if (diff < 0) return "Closed";
    if (diff === 0) return "Closing Today";
    if (diff === 1) return "1 day left";
    return `${diff} days left`;
}

function rand(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
}

/* ================================
   SEARCH
================================ */
function filterIPOs(searchTerm) {
    if (!searchTerm || searchTerm.trim() === "") return allIPOsData;
    const term = searchTerm.toLowerCase().trim();
    return allIPOsData.filter((ipo) => {
        const name = COMPANY_NAMES[ipo.originalIndex % COMPANY_NAMES.length].toLowerCase();
        return name.includes(term);
    });
}

function highlightText(text, searchTerm) {
    if (!searchTerm) return text;
    return text.replace(new RegExp(`(${searchTerm})`, 'gi'), '<mark style="background:#fde047;color:#854d0e;padding:0 2px;border-radius:2px;">$1</mark>');
}

function renderIPOs(data) {
    const openBox = document.getElementById("open-ipos");
    const upcomingBox = document.getElementById("upcoming-ipos");
    const closedBox = document.getElementById("closed-ipos");

    const today = new Date();
    let openCount = 0, upcomingCount = 0, closedCount = 0;

    openBox.innerHTML = "";
    upcomingBox.innerHTML = "";
    closedBox.innerHTML = "";

    data.forEach((ipo) => {
        const originalIndex = ipo.originalIndex;
        const name = COMPANY_NAMES[originalIndex % COMPANY_NAMES.length];
        const displayName = highlightText(name, currentSearchTerm);
        const status = ipo.status;

        // STEADY VALUES (single source of truth)
        const openDate = new Date(ipo.openDate);
        const closeDate = new Date(ipo.closeDate);
        const lotSize = ipo.lotSize;
        const gain = ipo.gain;

        // SAFE PRICE EXTRACTION (upper band)
        let pricePerShare = 0;
        if (ipo.price_band) {
            const prices = ipo.price_band.match(/\d+/g);
            pricePerShare = prices ? parseInt(prices[prices.length - 1]) : 0;
        }

        // LIVE FEEL (only for OPEN)
        const gmp = status === "OPEN" ? rand(5, 120) : ipo.gmp;
        const retail = status === "OPEN" ? rand(1, 6) : ipo.retail;

        /* ================= OPEN ================= */
        if (status === "OPEN") {
            openCount++;
            const daysText = daysLeft(closeDate);

            openBox.innerHTML += `
            <div class="col-md-4">
                <div class="card ipo-card border-success">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-3">
                            <span class="days-badge">${daysText}</span>
                            <span class="gmp-badge">GMP ₹${gmp}</span>
                        </div>

                        <h6 class="company-name">${displayName}</h6>

                        <div class="metric-row">
                            <span class="metric-label">Price Band</span>
                            <span class="metric-value">${ipo.price_band}</span>
                        </div>

                        <div class="metric-row">
                            <span class="metric-label">Closes On</span>
                            <span class="metric-value text-success">${formatDate(closeDate)}</span>
                        </div>

                        <div class="metric-row">
                            <span class="metric-label">Retail Subscription</span>
                            <span class="metric-value text-success">${retail}x</span>
                        </div>

                        <div class="metric-row">
                            <span class="metric-label">Lot Size</span>
                            <span class="metric-value">${lotSize} Shares</span>
                        </div>

                        <button class="btn btn-success w-100 mt-3"
                            onclick="openApplyModal(
                                '${name}',
                                ${pricePerShare},
                                ${lotSize}
                            )">
                            Apply Now →
                        </button>
                    </div>
                </div>
            </div>`;
        }

        /* ================= UPCOMING ================= */
        else if (status === "UPCOMING") {
            upcomingCount++;
            const daysUntilOpen = Math.ceil((openDate - today) / 86400000);

            upcomingBox.innerHTML += `
            <div class="col-md-4">
                <div class="card ipo-card border-warning">
                    <div class="card-body">
                        <div class="mb-3">
                            <span class="badge bg-warning bg-opacity-10 text-warning border rounded-pill px-3 py-2">
                                📅 Opens ${formatDate(openDate)}
                            </span>
                        </div>

                        <h6 class="company-name">${displayName}</h6>

                        <div class="metric-row">
                            <span class="metric-label">Expected Band</span>
                            <span class="metric-value text-muted">${ipo.price_band}</span>
                        </div>

                        <div class="metric-row">
                            <span class="metric-label">Lot Size</span>
                            <span class="metric-value text-muted">${lotSize} Shares</span>
                        </div>

                        <button class="btn btn-secondary w-100 mt-3" disabled>
                            🔒 Opens in ${daysUntilOpen} days
                        </button>
                    </div>
                </div>
            </div>`;
        }

        /* ================= CLOSED ================= */
        else {
            closedCount++;

            closedBox.innerHTML += `
            <li class="list-group-item d-flex justify-content-between align-items-center py-3 px-4 border-0 border-bottom">
                <div class="d-flex align-items-center gap-3">
                    <div class="bg-light rounded-circle d-flex align-items-center justify-content-center"
                         style="width:40px;height:40px;">📊</div>
                    <div>
                        <span class="fw-bold text-dark d-block">${displayName}</span>
                        <small class="text-muted">
                            Closed on ${formatDate(closeDate)} • Lot: ${lotSize}
                        </small>
                    </div>
                </div>
                <span class="badge bg-success bg-opacity-10 text-success px-3 py-2 rounded-pill">
                    +${gain}% Listed
                </span>
            </li>`;
        }
    });

    // Update counters
    document.getElementById('open-count').textContent = openCount;
    document.getElementById('upcoming-count').textContent = upcomingCount;
    document.getElementById('closed-count').textContent = closedCount;

    // Search stats
    const searchStats = document.getElementById('searchStats');
    if (currentSearchTerm && searchStats) {
        searchStats.innerHTML = `Found <strong>${openCount + upcomingCount + closedCount}</strong> results`;
    } else if (searchStats) {
        searchStats.innerHTML = '';
    }
}


/* ================================
   INITIALIZE (STEADY DATA)
================================ */
function processInitialData(data) {
    const today = new Date();
    return data.map((item, index) => {
        let status = "UPCOMING";
        if (index < 25) status = "CLOSED";
        else if (index < 45) status = "OPEN";
        
        let openDate, closeDate;
        
        if (status === "OPEN") {
            openDate = addDays(today, -rand(1,3)); // Opened 1-3 days ago
            closeDate = addDays(today, rand(1,5)); // Closing in 1-5 days
        } else if (status === "UPCOMING") {
            openDate = addDays(today, rand(2,15));
            closeDate = addDays(openDate, rand(3,5));
        } else {
            closeDate = addDays(today, -rand(2,30));
            openDate = addDays(closeDate, -3);
        }
        
        return {
            ...item,
            originalIndex: index,
            status: status,
            openDate: openDate.toISOString(),
            closeDate: closeDate.toISOString(),
            lotSize: rand(10, 150), // STEADY: Set once and store
            gain: rand(5, 45),      // STEADY: Historical listing gain
            gmp: rand(5, 120),      // Initial GMP
            retail: rand(1, 6)      // Initial retail
        };
    });
}

/* ================================
   LOAD & REFRESH LOGIC
================================ */
function loadIPO() {
    // If data exists, just re-render (updates GMP/Retail dynamically)
    if (allIPOsData.length > 0) {
        const filtered = filterIPOs(currentSearchTerm);
        renderIPOs(filtered);
        return;
    }
    
    // First load only
    fetch("/api/ipo/")
        .then(res => res.json())
        .then(data => {
            allIPOsData = processInitialData(data);
            renderIPOs(allIPOsData);
        })
        .catch(err => console.error("IPO API error:", err));
}

function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearSearch');
    
    if (!searchInput) return;
    
    searchInput.addEventListener('input', (e) => {
        currentSearchTerm = e.target.value;
        if (clearBtn) clearBtn.style.display = currentSearchTerm ? 'flex' : 'none';
        
        const filtered = filterIPOs(currentSearchTerm);
        renderIPOs(filtered);
    });
    
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            searchInput.value = '';
            currentSearchTerm = '';
            clearBtn.style.display = 'none';
            renderIPOs(allIPOsData);
            searchInput.focus();
        });
    }
}

function updateMarketStatus() {
    const now = new Date();
    const istOffset = 330;
    const istTime = new Date(now.getTime() + (now.getTimezoneOffset() * 60000) + (istOffset * 60000));
    const day = istTime.getDay();
    const currentTime = istTime.getHours() * 60 + istTime.getMinutes();
    const isActive = (day >= 1 && day <= 5 && currentTime >= 555 && currentTime <= 930);
    
    const marketStat = document.getElementById('market-stat-value');
    if (marketStat) {
        marketStat.textContent = isActive ? 'Active' : 'Closed';
        marketStat.style.color = isActive ? '#10b981' : '#ef4444';
    }
    
    const pulse = document.querySelector('.pulse');
    if (pulse) pulse.style.display = isActive ? 'block' : 'none';
}

document.addEventListener("DOMContentLoaded", () => {
    loadIPO(); // Initial load with steady dates
    setupSearch();
    updateMarketStatus();
    
    // KEEP GMP/RETAIL UPDATING: Refresh every 12 seconds WITHOUT changing dates
    setInterval(() => {
        loadIPO(); 
    }, 12000);
    
    setInterval(updateMarketStatus, 60000);
});


let selectedPrice = 0;
let selectedLotSize = 0;

function openApplyModal(company, price, lotSize) {
    selectedPrice = price;
    selectedLotSize = lotSize;

    document.getElementById("modal-company").innerText = company;
    document.getElementById("modal-price").value = price;
    document.getElementById("modal-lot-size").value = lotSize;
    document.getElementById("modal-lots").value = 1;

    calculateTotal();

    const modal = new bootstrap.Modal(
        document.getElementById("applyModal")
    );
    modal.show();
}

async function confirmApply() {
    console.log("CONFIRM BUTTON CLICKED");
    const company = document.getElementById("modal-company").innerText;
    const lotSize = parseInt(document.getElementById("modal-lot-size").value);
    const price = parseFloat(document.getElementById("modal-price").value);
    const lots = parseInt(document.getElementById("modal-lots").value);

    if (!lots || lots <= 0) {
        alert("Enter valid number of lots");
        return;
    }

    const totalAmount = lotSize * price * lots;

    try {
        const response = await fetch("/ipo/apply/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken"),
            },
            body: JSON.stringify({
                ipo_name: company,
                lot_size: lotSize,
                price_per_share: price,
                lots: lots,
                total_amount: totalAmount
            })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            alert("IPO applied successfully ✅");

            const modalEl = document.getElementById("applyModal");
            const modalInstance = bootstrap.Modal.getInstance(modalEl);
            if (modalInstance) modalInstance.hide();

            location.reload();  // refresh to reflect wallet deduction
        } else {
            alert(data.error || "Application failed");
        }

    } catch (error) {
        console.error("IPO APPLY ERROR:", error);
        alert("Something went wrong");
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}



window.openApplyModal = openApplyModal;
window.confirmApply = confirmApply;


function calculateTotal() {
    const lots = parseInt(document.getElementById("modal-lots").value || 1);
    const total = lots * selectedLotSize * selectedPrice;
    document.getElementById("modal-total").innerText = total.toLocaleString();
}

document.addEventListener("input", (e) => {
    if (e.target.id === "modal-lots") {
        calculateTotal();
    }
});
