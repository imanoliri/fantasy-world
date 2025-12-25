/* Dropdown Logic */
function toggleDropdown(id) {
    document.getElementById(id).classList.toggle("show");
}

function showStateTooltip(e, content) {
    const tooltip = document.getElementById('tooltip');
    tooltip.innerHTML = content;
    tooltip.style.display = 'block';

    // Position near the cursor
    let left = e.clientX + 15;
    let top = e.clientY + 15;

    // Adjust if going off screen
    if (left + 220 > window.innerWidth) {
        left = e.clientX - 230;
    }

    if (top + 150 > window.innerHeight) {
        top = e.clientY - 160;
    }

    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
}

function hideTooltip() {
    const tooltip = document.getElementById('tooltip');
    tooltip.style.display = 'none';
}

function toggleFoodTrades() {
    const btn = document.getElementById('toggleFoodTrades');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        document.body.classList.add('show-food-trades');
    } else {
        document.body.classList.remove('show-food-trades');
    }
}

function toggleGoldTrades() {
    const btn = document.getElementById('toggleGoldTrades');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        document.body.classList.add('show-gold-trades');
    } else {
        document.body.classList.remove('show-gold-trades');
    }
}

function toggleCapitals() {
    const btn = document.getElementById('toggleCapitals');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        document.body.classList.add('show-capitals');
    } else {
        document.body.classList.remove('show-capitals');
    }
}

function toggleTable() {
    const btn = document.getElementById('toggleTable');
    const container = document.getElementById('burgTableContainer');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        container.classList.remove('hidden');
    } else {
        container.classList.add('hidden');
    }
    window.dispatchEvent(new Event('resize'));
}

function toggleStateTable() {
    const btn = document.getElementById('toggleStateTable');
    const container = document.getElementById('stateTableContainer');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        container.classList.remove('hidden');
    } else {
        container.classList.add('hidden');
    }
    window.dispatchEvent(new Event('resize'));
}

function toggleFoodTradeTable() {
    const btn = document.getElementById('toggleFoodTradeTable');
    const container = document.getElementById('foodTradeTableContainer');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        container.classList.remove('hidden');
    } else {
        container.classList.add('hidden');
    }
    window.dispatchEvent(new Event('resize'));
}

function toggleGoldTradeTable() {
    const btn = document.getElementById('toggleGoldTradeTable');
    const container = document.getElementById('goldTradeTableContainer');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        container.classList.remove('hidden');
    } else {
        container.classList.add('hidden');
    }
    window.dispatchEvent(new Event('resize'));
}

function toggleMap() {
    const btn = document.getElementById('toggleMap');
    const mapGroup = document.getElementById('mapBackground');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        mapGroup.style.display = 'block';
    } else {
        mapGroup.style.display = 'none';
    }
}
