// Map Interactions
svg.addEventListener('click', (e) => {
    if (e.target.classList.contains('burg-dot')) {
        const id = e.target.getAttribute('data-id');
        selectBurg(id);
    } else {
        // Deselect if clicking empty space
        // selectBurg(null);
    }
});

svg.addEventListener('mousemove', (e) => {
    if (e.target.classList.contains('burg-dot')) {
        const name = e.target.getAttribute('data-name');
        const pop = parseInt(e.target.getAttribute('data-pop')).toLocaleString();
        const type = e.target.getAttribute('data-type');
        const state = e.target.getAttribute('data-state');
        const gold = e.target.getAttribute('data-gold');
        const food = e.target.getAttribute('data-food');
        const quartiers = e.target.getAttribute('data-quartiers');
        const isCapital = e.target.classList.contains('capital');

        let displayName = isCapital ? `★ ${name}` : name;

        let tooltipContent = `<strong>${displayName}</strong><br>State: ${state}<br>Type: ${type}<br>Pop: ${pop}<br>Food: ${food}<br>Gold: ${gold}`;
        if (quartiers) {
            tooltipContent += `<hr style="margin: 5px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.3);">${quartiers}`;
        }

        tooltip.innerHTML = tooltipContent;
        tooltip.style.display = 'block';

        // Smart positioning to keep within viewport
        let top = e.clientY + 10;
        let left = e.clientX + 10;

        // Check if tooltip goes off bottom
        if (top + 100 > window.innerHeight) {
            top = e.clientY - 100; // Move above cursor
        }

        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
    } else if (e.target.tagName === 'path') {
        const btn = document.getElementById('toggleMapMode');
        const mode = btn.getAttribute('data-mode') || 'biome';

        let content = '';
        if (mode === 'biome') {
            const biome = e.target.getAttribute('data-biome');
            if (biome) content = `<strong>Biome:</strong> ${biome}`;
        } else if (mode === 'state') {
            const state = e.target.getAttribute('data-state');
            if (state) content = `<strong>State:</strong> ${state}`;
        } else if (mode === 'heightmap') {
            const h = e.target.getAttribute('data-height');
            if (h) content = `<strong>Height:</strong> ${h}`;
        } else if (mode === 'temperature') {
            const t = e.target.getAttribute('data-temp');
            if (t) content = `<strong>Temp:</strong> ${t}°C`;
        }

        if (content) {
            tooltip.innerHTML = content;
            tooltip.style.display = 'block';
            tooltip.style.left = (e.clientX + 15) + 'px';
            tooltip.style.top = (e.clientY + 15) + 'px';
        } else {
            tooltip.style.display = 'none';
        }
    } else {
        tooltip.style.display = 'none';
    }
});

// Table Tooltip Interactions
table.addEventListener('mousemove', (e) => {
    if (e.target.classList.contains('quartier-cell')) {
        const details = e.target.getAttribute('data-details');
        if (details) {
            tooltip.innerHTML = details;
            tooltip.style.display = 'block';
            tooltip.style.left = (e.clientX + 10) + 'px';
            tooltip.style.top = (e.clientY + 10) + 'px';
        }
    } else {
        // Only hide if not over map dot (which is separate)
        // But we are in table container, so map tooltip is not active
        tooltip.style.display = 'none';
    }
});

table.addEventListener('mouseleave', () => {
    tooltip.style.display = 'none';
});

// Pan and Zoom (Basic)
let isPanning = false;
let startX, startY;
let viewBox = svg.getAttribute('viewBox').split(' ').map(parseFloat);

mapContainer.addEventListener('mousedown', (e) => {
    if (e.target === svg || e.target.tagName === 'circle' || e.target.tagName === 'line' || e.target.tagName === 'path') {
        isPanning = true;
        startX = e.clientX;
        startY = e.clientY;
        mapContainer.style.cursor = 'grabbing';
    }
});

mapContainer.addEventListener('mousemove', (e) => {
    if (!isPanning) return;
    e.preventDefault();
    const dx = (e.clientX - startX) * (viewBox[2] / mapContainer.clientWidth);
    const dy = (e.clientY - startY) * (viewBox[3] / mapContainer.clientHeight);

    viewBox[0] -= dx;
    viewBox[1] -= dy;
    svg.setAttribute('viewBox', viewBox.join(' '));

    startX = e.clientX;
    startY = e.clientY;
});

mapContainer.addEventListener('mouseup', () => {
    isPanning = false;
    mapContainer.style.cursor = 'default';
});

mapContainer.addEventListener('mouseleave', () => {
    isPanning = false;
    mapContainer.style.cursor = 'default';
});

mapContainer.addEventListener('wheel', (e) => {
    e.preventDefault();
    const scale = e.deltaY > 0 ? 1.1 : 0.9;
    const w = viewBox[2];
    const h = viewBox[3];

    viewBox[2] *= scale;
    viewBox[3] *= scale;

    // Zoom towards center
    viewBox[0] -= (viewBox[2] - w) / 2;
    viewBox[1] -= (viewBox[3] - h) / 2;

    svg.setAttribute('viewBox', viewBox.join(' '));
});
