// Team Skills Management System - Enterprise Edition
// No animations, strict functionality.

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    initializeAlerts();
    initializeTooltips();
    console.log('✓ System Loaded');
}

// Simple Auto-dismiss alerts (No fade animation logic)
function initializeAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.remove();
        }, 5000);
    });
}

// Standard Confirmation
function confirmDelete(message) {
    return confirm(message || 'Confirm deletion? This action cannot be undone.');
}

// Clean Table Search
function searchTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const table = document.getElementById(tableId);
    
    if (!input || !table) return;

    input.addEventListener('keyup', function() {
        const filter = input.value.toUpperCase();
        const rows = table.getElementsByTagName('tr');
        
        // Loop through all table rows, hide those who don't match the search query
        for (let i = 1; i < rows.length; i++) {
            const row = rows[i];
            const cells = row.getElementsByTagName('td');
            let found = false;
            
            for (let j = 0; j < cells.length; j++) {
                const cell = cells[j];
                if (cell) {
                    const textValue = cell.textContent || cell.innerText;
                    if (textValue.toUpperCase().indexOf(filter) > -1) {
                        found = true;
                        break;
                    }
                }
            }
            
            // Simple display toggle, no animation
            row.style.display = found ? '' : 'none';
        }
    });
}

// Table Sorting (Functional, no visual animation)
function sortTable(tableId, columnIndex) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const tbody = table.querySelector('tbody') || table;
    const rows = Array.from(tbody.rows);
    const currentOrder = table.dataset.sortOrder || 'none';
    const currentColumn = parseInt(table.dataset.sortColumn || -1);
    
    let newOrder;
    if (currentColumn !== columnIndex) {
        newOrder = 'asc';
    } else {
        newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
    }
    
    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();
        
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return newOrder === 'asc' ? aNum - bNum : bNum - aNum;
        }
        
        return newOrder === 'asc' 
            ? aValue.localeCompare(bValue, undefined, { numeric: true, sensitivity: 'base' })
            : bValue.localeCompare(aValue, undefined, { numeric: true, sensitivity: 'base' });
    });
    
    rows.forEach(row => tbody.appendChild(row));
    
    table.dataset.sortOrder = newOrder;
    table.dataset.sortColumn = columnIndex;
    
    updateSortIndicators(table, columnIndex, newOrder);
}

function updateSortIndicators(table, activeColumn, order) {
    const headers = table.querySelectorAll('th');
    headers.forEach((header, index) => {
        const existingIcon = header.querySelector('.sort-icon');
        if (existingIcon) existingIcon.remove();
        
        if (index === activeColumn) {
            const icon = document.createElement('i');
            icon.className = `bi bi-chevron-${order === 'asc' ? 'up' : 'down'} ms-1 sort-icon small text-muted`;
            header.appendChild(icon);
        }
    });
}

function copyToClipboard(text) {
    if (!navigator.clipboard) {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showToast('Copied to clipboard');
        return;
    }
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard');
    }).catch(err => {
        console.error('Failed to copy', err);
    });
}

// Minimal Toast (Bottom Right, no bounce)
function showToast(message) {
    let toastContainer = document.getElementById('toastContainer');
    
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'position-fixed bottom-0 end-0 p-4';
        document.body.appendChild(toastContainer);
    }
    
    // Simple dark toast
    const toastHTML = `
        <div class="toast align-items-center text-white bg-dark border-0 show" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        </div>
    `;
    
    // Create temp wrapper to parse HTML
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = toastHTML.trim();
    const toastEl = tempDiv.firstChild;
    
    toastContainer.appendChild(toastEl);
    
    // Remove after 3s
    setTimeout(() => {
        if(toastEl && toastEl.parentNode) {
            toastEl.remove();
        }
    }, 3000);
}

function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}