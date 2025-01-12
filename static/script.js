/* static/script.js */
let currentTab = 'collection';

async function loadSets() {
    const ownedResponse = await fetch('/api/sets?owned=true');
    const wantedResponse = await fetch('/api/sets?wanted=true');
    
    const ownedSets = await ownedResponse.json();
    const wantedSets = await wantedResponse.json();
    
    displaySets('owned-sets', ownedSets);
    displaySets('wanted-sets', wantedSets);
}

function displaySets(containerId, sets) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    
    sets.forEach(set => {
        const card = document.createElement('div');
        card.className = 'set-card';
        const imageUrl = set.image_url || '/static/placeholder.jpg';
        card.innerHTML = `
            <img src="${imageUrl}" alt="${set.name}" onerror="this.src='/static/placeholder.jpg'">
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

function showTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    
    document.getElementById(tab).classList.add('active');
    document.querySelector(`button[onclick="showTab('${tab}')"]`).classList.add('active');
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

// Load sets when the page loads
document.addEventListener('DOMContentLoaded', loadSets);