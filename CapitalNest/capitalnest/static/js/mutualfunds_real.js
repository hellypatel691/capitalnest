let allFunds = [];
let displayedFunds = [];

// Utility: Detect fund type from scheme name
function getFundType(schemeName) {
    const name = schemeName.toLowerCase();
    if (name.includes('equity') || name.includes('growth') || name.includes('mid cap') || name.includes('small cap') || name.includes('large cap')) {
        return { class: 'type-equity', label: 'Equity' };
    } else if (name.includes('debt') || name.includes('bond') || name.includes('gilt') || name.includes('liquid')) {
        return { class: 'type-debt', label: 'Debt' };
    } else if (name.includes('hybrid') || name.includes('balanced') || name.includes('multi asset')) {
        return { class: 'type-hybrid', label: 'Hybrid' };
    }
    return { class: 'type-other', label: 'Other' };
}

// Utility: Format number with commas
function formatAmount(amount) {
    return parseFloat(amount).toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 4
    });
}

// Utility: Animate number counting
function animateValue(id, start, end, duration) {
    const obj = document.getElementById(id);
    const range = end - start;
    const minTimer = 50;
    let stepTime = Math.abs(Math.floor(duration / range));
    stepTime = Math.max(stepTime, minTimer);
    
    let startTime = new Date().getTime();
    let endTime = startTime + duration;
    let timer;
    
    function run() {
        let now = new Date().getTime();
        let remaining = Math.max((endTime - now) / duration, 0);
        let value = Math.round(end - (remaining * range));
        obj.innerHTML = value.toLocaleString();
        if (value == end) {
            clearInterval(timer);
        }
    }
    
    timer = setInterval(run, stepTime);
    run();
}

// Render funds table
function renderFunds(funds) {
    const tbody = document.getElementById("mf-body");
    displayedFunds = funds;
    
    // Update counts
    document.getElementById('showing-count').textContent = funds.length;
    document.getElementById('total-count').textContent = allFunds.length;
    
    if (funds.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="3">
                    <div class="empty-state">
                        <div class="empty-icon">
                            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="11" cy="11" r="8"></circle>
                                <path d="m21 21-4.35-4.35"></path>
                            </svg>
                        </div>
                        <div class="empty-title">No funds found</div>
                        <div class="empty-text">Try adjusting your search terms</div>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = "";
    
    funds.forEach((f, index) => {
        const fundType = getFundType(f.scheme_name);
        const row = document.createElement('tr');
        row.style.animationDelay = `${index * 0.03}s`;
        row.className = 'animate-in';
        
        row.innerHTML = `
            <td data-label="Scheme">
                <div class="fund-name">${f.scheme_name}</div>
                <span class="fund-type ${fundType.class}">${fundType.label}</span>
            </td>
            <td data-label="NAV">
                <a href="#" 
                   class="view-nav-btn"
                   data-code="${f.scheme_code}"
                   onclick="handleNavClick(event, this)">
                   <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                       <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                       <circle cx="12" cy="12" r="3"></circle>
                   </svg>
                   View NAV
                </a>
            </td>
            <td data-label="Date" class="nav-date">—</td>
        `;
        
        tbody.appendChild(row);
    });
}

// Handle NAV click with loading state
function handleNavClick(e, element) {
    e.preventDefault();
    
    const schemeCode = element.dataset.code;
    const row = element.closest("tr");
    const dateCell = row.querySelector(".nav-date");
    
    // Set loading state
    element.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="animation: spin 1s linear infinite;">
            <circle cx="12" cy="12" r="10" stroke-dasharray="60" stroke-dashoffset="20"></circle>
        </svg>
        Loading...
    `;
    element.style.opacity = '0.7';
    element.style.pointerEvents = 'none';
    
    fetch(`/api/mutual-funds/${schemeCode}/`)
        .then(res => {
            if (!res.ok) throw new Error('Network response was not ok');
            return res.json();
        })
        .then(data => {
            if (!data || !data.nav) {
                element.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="15" y1="9" x2="9" y2="15"></line>
                        <line x1="9" y1="9" x2="15" y2="15"></line>
                    </svg>
                    Unavailable
                `;
                element.style.background = '#94a3b8';
                element.style.boxShadow = 'none';
                return;
            }

            // Success state
            element.outerHTML = `<span class="nav-value">₹${formatAmount(data.nav)}</span>`;
            
            dateCell.textContent = data.date;
            dateCell.classList.add('updated');
            
            // Add subtle highlight animation
            row.style.background = 'linear-gradient(135deg, rgba(0, 212, 170, 0.1) 0%, rgba(0, 104, 255, 0.1) 100%)';
            setTimeout(() => {
                row.style.background = '';
            }, 1000);
        })
        .catch(err => {
            console.error("NAV fetch error:", err);
            element.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                Error
            `;
            element.style.background = '#ef4444';
            element.style.boxShadow = '0 4px 15px rgba(239, 68, 68, 0.3)';
            
            setTimeout(() => {
                element.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                        <circle cx="12" cy="12" r="3"></circle>
                    </svg>
                    Retry
                `;
                element.style.background = '';
                element.style.boxShadow = '';
                element.style.opacity = '1';
                element.style.pointerEvents = 'auto';
            }, 2000);
        });
}

// Load mutual funds data
function loadMutualFunds() {
    fetch("/api/mutual-funds/")
        .then(res => {
            if (!res.ok) throw new Error('Network response was not ok');
            return res.json();
        })
        .then(data => {
            allFunds = data || [];
            
            // Animate total funds count
            animateValue("total-funds", 0, allFunds.length, 1000);
            
            renderFunds(allFunds);
        })
        .catch(err => {
            console.error("Mutual fund fetch error:", err);
            document.getElementById("mf-body").innerHTML = `
                <tr>
                    <td colspan="3">
                        <div class="empty-state">
                            <div class="empty-icon" style="background: #fee2e2; color: #dc2626;">
                                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <circle cx="12" cy="12" r="10"></circle>
                                    <line x1="12" y1="8" x2="12" y2="12"></line>
                                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                                </svg>
                            </div>
                            <div class="empty-title">Failed to load data</div>
                            <div class="empty-text">Please refresh the page to try again</div>
                        </div>
                    </td>
                </tr>
            `;
        });
}

// Search functionality with debounce
let searchTimeout;
document.getElementById("mf-search")?.addEventListener("input", e => {
    clearTimeout(searchTimeout);
    
    searchTimeout = setTimeout(() => {
        const q = e.target.value.toLowerCase().trim();
        
        if (q === '') {
            renderFunds(allFunds);
            return;
        }
        
        const filtered = allFunds.filter(f => 
            f.scheme_name.toLowerCase().includes(q) ||
            (f.scheme_code && f.scheme_code.toString().includes(q))
        );
        
        renderFunds(filtered);
    }, 300);
});

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
    loadMutualFunds();
    
    // Add pulse animation to live badge
    const badge = document.getElementById('live-badge');
    setInterval(() => {
        badge.style.opacity = badge.style.opacity === '0.6' ? '1' : '0.6';
    }, 2000);
});