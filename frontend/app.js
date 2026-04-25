// API Base URL
const API_URL = window.location.origin;

// DOM Elements
const generateBtn = document.getElementById('generateBtn');
const reconcileBtn = document.getElementById('reconcileBtn');
const refreshBtn = document.getElementById('refreshBtn');
const statusMessage = document.getElementById('statusMessage');
const summaryCards = document.getElementById('summaryCards');

// Tab Elements
const tabs = document.querySelectorAll('.tab');
const tabContents = document.querySelectorAll('.tab-content');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    loadTransactions();
});

// Event Listeners
function setupEventListeners() {
    generateBtn.addEventListener('click', generateData);
    reconcileBtn.addEventListener('click', runReconciliation);
    refreshBtn.addEventListener('click', loadTransactions);
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
}

// Tab Switching
function switchTab(tabName) {
    tabs.forEach(t => t.classList.remove('active'));
    tabContents.forEach(c => c.classList.remove('active'));
    
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(tabName).classList.add('active');
}

// Show Status Message
function showStatus(message, type = 'loading') {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
}

function hideStatus() {
    statusMessage.className = 'status-message';
}

// Format Currency
function formatCurrency(amount, currency) {
    const formatted = new Intl.NumberFormat('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
    
    const symbol = currency === 'USD' ? '$' : '₹';
    return `${symbol}${formatted}`;
}

// Format Date
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Generate Test Data
async function generateData() {
    generateBtn.disabled = true;
    showStatus('Generating test data...', 'loading');
    
    try {
        const response = await fetch(`${API_URL}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ num_txns: 40 })
        });
        
        if (!response.ok) throw new Error('Failed to generate data');
        
        const data = await response.json();
        showStatus(`✅ ${data.message}`, 'success');
        
        await loadTransactions();
        
        // Hide summary cards until reconciliation
        summaryCards.style.display = 'none';
        
    } catch (error) {
        showStatus(`❌ Error: ${error.message}`, 'error');
    } finally {
        generateBtn.disabled = false;
    }
}

// Load Transactions
async function loadTransactions() {
    try {
        const response = await fetch(`${API_URL}/transactions`);
        
        if (!response.ok) {
            if (response.status === 404) {
                renderEmptyState();
                return;
            }
            throw new Error('Failed to load transactions');
        }
        
        const data = await response.json();
        renderTransactions(data);
        
    } catch (error) {
        console.error('Error loading transactions:', error);
    }
}

// Render Transactions
function renderTransactions(data) {
    const platformTable = document.getElementById('platformTable').querySelector('tbody');
    const bankTable = document.getElementById('bankTable').querySelector('tbody');
    
    // Update counts
    document.getElementById('platformCount').textContent = data.platform.length;
    document.getElementById('bankCount').textContent = data.bank.length;
    
    // Render Platform Transactions
    if (data.platform.length === 0) {
        platformTable.innerHTML = '<tr><td colspan="5" class="empty-state">No transactions. Click "Generate Test Data" to start.</td></tr>';
    } else {
        platformTable.innerHTML = data.platform.map(txn => `
            <tr>
                <td><code>${txn.txn_id}</code></td>
                <td class="${txn.currency === 'USD' ? 'currency-usd' : 'currency-inr'}">${formatCurrency(txn.amount, txn.currency)}</td>
                <td>${txn.currency}</td>
                <td>${formatDate(txn.date)}</td>
                <td><span class="type-badge">${txn.type}</span></td>
            </tr>
        `).join('');
    }
    
    // Render Bank Transactions
    if (data.bank.length === 0) {
        bankTable.innerHTML = '<tr><td colspan="5" class="empty-state">No transactions</td></tr>';
    } else {
        bankTable.innerHTML = data.bank.map(txn => `
            <tr>
                <td><code>${txn.txn_id}</code></td>
                <td class="${txn.currency === 'USD' ? 'currency-usd' : 'currency-inr'}">${formatCurrency(txn.amount, txn.currency)}</td>
                <td>${txn.currency}</td>
                <td>${formatDate(txn.date)}</td>
                <td><span class="type-badge">${txn.type}</span></td>
            </tr>
        `).join('');
    }
}

// Render Empty State
function renderEmptyState() {
    const platformTable = document.getElementById('platformTable').querySelector('tbody');
    const bankTable = document.getElementById('bankTable').querySelector('tbody');
    
    platformTable.innerHTML = '<tr><td colspan="5" class="empty-state">No transactions. Click "Generate Test Data" to start.</td></tr>';
    bankTable.innerHTML = '<tr><td colspan="5" class="empty-state">No transactions</td></tr>';
    
    document.getElementById('platformCount').textContent = '0';
    document.getElementById('bankCount').textContent = '0';
}

// Run Reconciliation
async function runReconciliation() {
    reconcileBtn.disabled = true;
    showStatus('Running reconciliation...', 'loading');
    
    try {
        const response = await fetch(`${API_URL}/reconcile`, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to reconcile');
        }
        
        const report = await response.json();
        showStatus('✅ Reconciliation complete!', 'success');
        
        renderReport(report);
        switchTab('report');
        
    } catch (error) {
        showStatus(`❌ Error: ${error.message}`, 'error');
    } finally {
        reconcileBtn.disabled = false;
    }
}

// Render Report
function renderReport(report) {
    // Show summary cards
    summaryCards.style.display = 'grid';
    
    // Filter results by status
    const results = report.results || [];
    const matched = results.filter(r => r.status === 'MATCHED' || r.status === 'ROUNDING_DIFF' || r.status === 'REFUND_MATCHED');
    const missingInBank = results.filter(r => r.status === 'MISSING_IN_BANK');
    const extraInBank = results.filter(r => r.status === 'EXTRA_IN_BANK');
    const amountMismatches = results.filter(r => r.status === 'AMOUNT_MISMATCH');
    const duplicates = results.filter(r => r.status === 'DUPLICATE_IN_BANK');
    const currencyConversions = results.filter(r => r.is_currency_conversion === true);
    
    // Update summary
    const summary = report.summary || {};
    document.getElementById('totalTxns').textContent = summary.total || 0;
    document.getElementById('matchedCount').textContent = matched.length;
    document.getElementById('missingCount').textContent = missingInBank.length;
    document.getElementById('extraCount').textContent = extraInBank.length;
    document.getElementById('mismatchCount').textContent = amountMismatches.length;
    document.getElementById('currencyCount').textContent = currencyConversions.length;
    document.getElementById('matchRate').textContent = `${summary.match_rate || 0}%`;
    
    // Render Matched Transactions
    const matchedTable = document.getElementById('matchedTable').querySelector('tbody');
    if (matched.length === 0) {
        matchedTable.innerHTML = '<tr><td colspan="5" class="empty-state">No matched transactions</td></tr>';
    } else {
        matchedTable.innerHTML = matched.map(item => `
            <tr>
                <td><code>${item.txn_id}</code></td>
                <td>${formatCurrency(item.platform_amount || 0, 'INR')}</td>
                <td>${formatCurrency(item.bank_amount || 0, 'INR')}</td>
                <td>${item.platform_currency || 'INR'}</td>
                <td>${formatDate(item.platform_date || item.bank_date)}</td>
            </tr>
        `).join('');
    }
    
    // Render Missing in Bank
    const missingTable = document.getElementById('missingTable').querySelector('tbody');
    if (missingInBank.length === 0) {
        missingTable.innerHTML = '<tr><td colspan="5" class="empty-state">No missing transactions</td></tr>';
    } else {
        missingTable.innerHTML = missingInBank.map(item => `
            <tr>
                <td><code>${item.txn_id}</code></td>
                <td>${formatCurrency(item.platform_amount || 0, 'INR')}</td>
                <td>${item.platform_currency || 'INR'}</td>
                <td>${formatDate(item.platform_date)}</td>
                <td>${item.platform_type || '-'}</td>
            </tr>
        `).join('');
    }
    
    // Render Extra in Bank
    const extraTable = document.getElementById('extraTable').querySelector('tbody');
    if (extraInBank.length === 0) {
        extraTable.innerHTML = '<tr><td colspan="5" class="empty-state">No extra transactions</td></tr>';
    } else {
        extraTable.innerHTML = extraInBank.map(item => `
            <tr>
                <td><code>${item.txn_id}</code></td>
                <td>${formatCurrency(item.bank_amount || 0, 'INR')}</td>
                <td>INR</td>
                <td>${formatDate(item.bank_date)}</td>
                <td>${item.bank_type || '-'}</td>
            </tr>
        `).join('');
    }
    
    // Render Amount Mismatches
    const mismatchTable = document.getElementById('mismatchTable').querySelector('tbody');
    if (amountMismatches.length === 0) {
        mismatchTable.innerHTML = '<tr><td colspan="5" class="empty-state">No amount mismatches</td></tr>';
    } else {
        mismatchTable.innerHTML = amountMismatches.map(item => {
            const diff = (item.bank_amount || 0) - (item.platform_amount || 0);
            const diffClass = diff > 0 ? 'diff-positive' : 'diff-negative';
            const diffSign = diff > 0 ? '+' : '';
            return `
                <tr>
                    <td><code>${item.txn_id}</code></td>
                    <td>${formatCurrency(item.platform_amount || 0, 'INR')}</td>
                    <td>${formatCurrency(item.bank_amount || 0, 'INR')}</td>
                    <td class="${diffClass}">${diffSign}${formatCurrency(diff, 'INR')}</td>
                    <td>${formatDate(item.platform_date || item.bank_date)}</td>
                </tr>
            `;
        }).join('');
    }
    
    // Render Duplicates
    const duplicateTable = document.getElementById('duplicateTable').querySelector('tbody');
    if (duplicates.length === 0) {
        duplicateTable.innerHTML = '<tr><td colspan="5" class="empty-state">No duplicates found</td></tr>';
    } else {
        duplicateTable.innerHTML = duplicates.map(item => `
            <tr>
                <td><code>${item.txn_id}</code></td>
                <td>${formatCurrency(item.bank_amount || 0, 'INR')}</td>
                <td>INR</td>
                <td>${formatDate(item.bank_date)}</td>
                <td><span class="count-badge">Duplicate</span></td>
            </tr>
        `).join('');
    }
    
    // Render Currency Conversions (USD to INR)
    const currencyTable = document.getElementById('currencyTable').querySelector('tbody');
    if (currencyConversions.length === 0) {
        currencyTable.innerHTML = '<tr><td colspan="6" class="empty-state">No USD → INR conversions found</td></tr>';
    } else {
        currencyTable.innerHTML = currencyConversions.map(item => {
            const usdAmount = item.platform_original_amount || 0;
            const expectedInr = item.platform_amount || 0;
            const actualInr = item.bank_amount || 0;
            const diff = actualInr - expectedInr;
            const diffClass = Math.abs(diff) <= 2 ? 'diff-ok' : (diff > 0 ? 'diff-positive' : 'diff-negative');
            const diffSign = diff > 0 ? '+' : '';
            const statusClass = item.status === 'MATCHED' || item.status === 'ROUNDING_DIFF' ? 'status-ok' : 'status-issue';
            const statusText = item.status === 'MATCHED' ? '✓ Matched' : 
                              item.status === 'ROUNDING_DIFF' ? '≈ Rounding' : 
                              '✗ Mismatch';
            return `
                <tr>
                    <td><code>${item.txn_id}</code></td>
                    <td class="currency-usd">$${usdAmount.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                    <td>${formatCurrency(expectedInr, 'INR')}</td>
                    <td>${formatCurrency(actualInr, 'INR')}</td>
                    <td class="${diffClass}">${diffSign}${formatCurrency(diff, 'INR')}</td>
                    <td><span class="${statusClass}">${statusText}</span></td>
                </tr>
            `;
        }).join('');
    }
}

// Auto-hide success messages after 5 seconds
setInterval(() => {
    if (statusMessage.classList.contains('success')) {
        setTimeout(hideStatus, 5000);
    }
}, 1000);
