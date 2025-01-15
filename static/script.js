/* static/script.js */
const PLACEHOLDER_IMAGE = 'static/placeholder.jpg'

let currentTab = 'collection';

async function loadSets() {
    const response = await fetch('/api/sets');
    const sets = await response.json();
    
    // Populate theme filter options
    const themes = [...new Set(sets.map(set => set.theme).filter(theme => theme))];
    const themeSelect = document.getElementById('theme-filter');
    themeSelect.innerHTML = '<option value="">All Themes</option>';
    themes.sort().forEach(theme => {
        themeSelect.innerHTML += `<option value="${theme}">${theme}</option>`;
    });
    
    // Store sets in memory for filtering
    window.allSets = sets;
    applyFilters();
}

function applyFilters() {
    const searchTerm = document.getElementById('search-input').value.toLowerCase();
    const themeFilter = document.getElementById('theme-filter').value;
    const statusFilter = document.getElementById('status-filter').value;
    
    let filteredSets = window.allSets;
    
    // Apply search filter
    if (searchTerm) {
        filteredSets = filteredSets.filter(set => 
            set.name.toLowerCase().includes(searchTerm) ||
            set.set_number.toLowerCase().includes(searchTerm)
        );
    }
    
    // Apply theme filter
    if (themeFilter) {
        filteredSets = filteredSets.filter(set => set.theme === themeFilter);
    }
    
    // Apply status filter
    if (statusFilter) {
        filteredSets = filteredSets.filter(set => 
            statusFilter === 'owned' ? set.owned : set.wanted
        );
    }
    
    displaySets('all-sets', filteredSets);
}

function displaySets(containerId, sets) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    if (sets.length === 0) {
        container.innerHTML = '<div class="no-results">No sets found matching the selected filters</div>';
        return;
    }
    
    sets.forEach(set => {
        const card = document.createElement('div');
        card.className = 'set-card';
        const imageUrl = set.image_url || PLACEHOLDER_IMAGE;
        const status = set.owned ? 'Owned' : 'Wanted';
        const statusClass = set.owned ? 'status-owned' : 'status-wanted';
        
        card.innerHTML = `
            <div class="set-status ${statusClass}">${status}</div>
            <img src="${imageUrl}" alt="${set.name}" onerror="this.src='${PLACEHOLDER_IMAGE}'">
            <div class="set-info">
                <h3>${set.name}</h3>
                <p>Set #: ${set.set_number}</p>
                ${set.theme ? `<p>Theme: ${set.theme}</p>` : ''}
                ${set.piece_count ? `<p>Pieces: ${set.piece_count}</p>` : ''}
                ${set.current_price ? `<p>Current Price: $${set.current_price}</p>` : ''}
                <button onclick="editSet(${set.id})">Edit</button>
                <button onclick="deleteSet(${set.id})">Delete</button>
            </div>
        `;
        container.appendChild(card);
    });
}

function showForm() {
    document.getElementById('set-form').classList.add('active');
    document.getElementById('lego-form').reset();
    document.getElementById('set-id').value = '';
}

function closeForm() {
    document.getElementById('set-form').classList.remove('active');
}

async function handleSubmit(event) {
    event.preventDefault();
    
    const formData = {
        set_number: document.getElementById('set-number').value,
        name: document.getElementById('name').value,
        piece_count: parseInt(document.getElementById('piece-count').value) || null,
        theme: document.getElementById('theme').value || null,
        year_released: parseInt(document.getElementById('year').value) || null,
        owned: document.querySelector('input[name="status"]:checked').value === 'owned',
        wanted: document.querySelector('input[name="status"]:checked').value === 'wanted'
    };
    
    const setId = document.getElementById('set-id').value;
    
    try {
        if (setId) {
            await fetch(`/api/sets/${setId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(formData)
            });
        } else {
            await fetch('/api/sets', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(formData)
            });
        }
        
        closeForm();
        loadSets();
    } catch (error) {
        console.error('Error saving set:', error);
        alert('Error saving set. Please try again.');
    }
}

async function editSet(setId) {
    const response = await fetch(`/api/sets/${setId}`);
    const set = await response.json();
    
    document.getElementById('set-id').value = set.id;
    document.getElementById('set-number').value = set.set_number;
    document.getElementById('name').value = set.name;
    document.getElementById('piece-count').value = set.piece_count || '';
    document.getElementById('theme').value = set.theme || '';
    document.getElementById('year').value = set.year_released || '';
    
    const statusRadio = document.querySelector(`input[name="status"][value="${set.owned ? 'owned' : 'wanted'}"]`);
    if (statusRadio) statusRadio.checked = true;
    
    document.getElementById('set-form').classList.add('active');
}

async function deleteSet(setId) {
    if (!confirm('Are you sure you want to delete this set?')) {
        return;
    }
    
    try {
        await fetch(`/api/sets/${setId}`, {
            method: 'DELETE'
        });
        loadSets();
    } catch (error) {
        console.error('Error deleting set:', error);
        alert('Error deleting set. Please try again.');
    }
}

async function checkRebrickableStatus() {
    try {
        const response = await fetch('/api/rebrickable/status');
        const data = await response.json();
        return data.connected;
    } catch (error) {
        console.error('Error checking Rebrickable status:', error);
        return false;
    }
}

async function showRebrickableForm() {
    const formHtml = `
        <div class="modal-content">
            <h2>Connect to Rebrickable</h2>
            <form id="rebrickable-form" onsubmit="handleRebrickableSubmit(event)">
                <div class="form-group">
                    <label for="username">Rebrickable Username:</label>
                    <input type="text" id="username" required>
                </div>
                <div class="form-group">
                    <label for="password">Rebrickable Password:</label>
                    <input type="password" id="password" required>
                </div>
                <div class="form-actions">
                    <button type="submit">Connect</button>
                    <button type="button" onclick="closeRebrickableForm()">Cancel</button>
                </div>
            </form>
        </div>
    `;
    
    const modal = document.createElement('div');
    modal.id = 'rebrickable-modal';
    modal.className = 'modal active';
    modal.innerHTML = formHtml;
    document.body.appendChild(modal);
}

async function handleRebrickableSync() {
    const isConnected = await checkRebrickableStatus();
    if (!isConnected) {
        showRebrickableForm();
    } else {
        // TODO: Implement actual sync logic
        alert('Already connected to Rebrickable. Sync feature coming soon!');
    }
}

async function handleRebrickableSubmit(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
        const response = await fetch('/api/rebrickable/connect', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Successfully connected to Rebrickable!');
            closeRebrickableForm();
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert('Error connecting to Rebrickable. Please try again.');
    }
}

function closeRebrickableForm() {
    const modal = document.getElementById('rebrickable-modal');
    if (modal) {
        modal.remove();
    }
}

// Add this function to handle sync button clicks
document.querySelector('.sync-btn').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/rebrickable/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Sync failed');
        }
        
        // Refresh the sets display
        loadSets();
        alert('Successfully synced with Rebrickable!');
    } catch (error) {
        alert('Error syncing with Rebrickable: ' + error.message);
    }
});

// Initialize correct tab on page load
document.addEventListener('DOMContentLoaded', () => {
    loadSets();
    const syncBtn = document.querySelector('.sync-btn');
    if (syncBtn) {
        syncBtn.addEventListener('click', handleRebrickableSync);
    }
});