const relationColors = {
    "Ally": "#32CD32",      // Lime Green
    "Friendly": "#90EE90",  // Light Green
    "Neutral": "#D3D3D3",   // Light Grey
    "Suspicion": "#FFA500", // Orange
    "Enemy": "#FF4500",     // Orange Red
    "War": "#FF0000",       // Red
    "Vassal": "#87CEEB",    // Sky Blue
    "Suzerain": "#C8A2C8",  // Lilac
    "Unknown": "#F5F5F5",   // White Smoke
    "x": "#800080"          // Selected State (Purple)
};

function toggleMapMode() {
    const btn = document.getElementById('toggleMapMode');
    const paths = document.querySelectorAll('#mapBackground path');

    // Use data attribute for state tracking
    const currentMode = btn.getAttribute('data-mode') || 'biome';

    if (currentMode === 'biome') {
        // Switch to State
        btn.innerText = 'Mode: State';
        btn.setAttribute('data-mode', 'state');
        paths.forEach(p => {
            p.setAttribute('fill', p.getAttribute('data-state-color'));
        });
    } else if (currentMode === 'state') {
        // Switch to Heightmap
        btn.innerText = 'Mode: Heightmap';
        btn.setAttribute('data-mode', 'heightmap');

        paths.forEach(p => {
            // Heightmap logic: darken color based on height
            let h = parseInt(p.getAttribute('data-height'));
            let c = 255 - h * 2;
            if (c < 0) c = 0;
            if (p.getAttribute('data-is-water') === 'true') {
                p.setAttribute('fill', `rgb(${c / 2}, ${c / 2}, ${200 + h / 2})`);
            } else {
                p.setAttribute('fill', `rgb(${c}, ${c}, ${c})`);
            }
        });
    } else if (currentMode === 'heightmap') {
        // Switch to Temperature
        btn.innerText = 'Mode: Temperature';
        btn.setAttribute('data-mode', 'temperature');
        paths.forEach(p => {
            const t = parseInt(p.getAttribute('data-temp'));
            p.setAttribute('fill', getColorForTemp(t));
        });
    } else {
        // Switch to Biome
        btn.innerText = 'Mode: Biome';
        btn.setAttribute('data-mode', 'biome');
        paths.forEach(p => {
            p.setAttribute('fill', p.getAttribute('data-biome-color'));
        });
    }
}

function getColorForHeight(h) {
    // Azgaar height range: 0-100 (usually)
    // Water: < 20
    // Land: >= 20

    if (h < 20) {
        // Water: Uniform Deep Blue
        return "#000080";
    } else {
        // Land gradient: Green -> Yellow -> Brown -> White
        if (h < 40) return "#228B22"; // Forest Green (Lowlands)
        if (h < 60) return "#9ACD32"; // Yellow Green (Hills)
        if (h < 80) return "#CD853F"; // Peru (Mountains)
        return "#FFFFFF"; // White (Peaks)
    }
}

function getColorForTemp(t) {
    // Range: approx -30 to 50 (Celsius)
    // Hot (> 30): Red
    // Warm (20-30): Orange
    // Temperate (10-20): Yellow/Green
    // Cool (0-10): Cyan
    // Cold (-10 to 0): Blue
    // Freezing (< -10): Purple

    if (t < -10) return "#4B0082"; // Indigo (Deep Freeze)
    if (t < -5) return "#800080"; // Purple (Freezing)
    if (t < 0) return "#0000FF"; // Blue (Cold)
    if (t < 5) return "#00BFFF"; // Deep Sky Blue (Cool)
    if (t < 10) return "#ADFF2F"; // Green Yellow (Temperate)
    if (t < 15) return "#FFD700"; // Gold (Warm)
    if (t < 20) return "#FF8C00"; // Dark Orange (Hot)
    return "#FF0000"; // Red (Scorching)
}

function updateDiplomacyColors(stateIdentifier) {
    let stateId = null;

    // Try to find state ID
    if (typeof stateIdentifier === 'number') {
        stateId = stateIdentifier;
    } else if (typeof stateIdentifier === 'string') {
        if (stateNameIdMap.hasOwnProperty(stateIdentifier)) {
            stateId = stateNameIdMap[stateIdentifier];
        }
    }

    // FIX: Treat selecting "Neutral" (0) as deselecting
    if (stateId === 0) stateId = null;

    const paths = document.querySelectorAll('#mapBackground path');

    if (stateId !== null && diplomacyMatrix[stateId]) {
        const relations = diplomacyMatrix[stateId];

        paths.forEach(p => {
            const isWater = p.hasAttribute('data-is-water');
            if (isWater) {
                p.setAttribute('fill', '#333333'); // Dark Gray for water
            } else {
                const pStateId = parseInt(p.getAttribute('data-state-id'));

                // FIX: Explicitly handle Neutrals (ID 0)
                if (pStateId === 0 && stateId !== 0) {
                    p.setAttribute('fill', '#ffffff'); // White for Neutrals
                } else if (!isNaN(pStateId) && pStateId < relations.length) {
                    const relation = relations[pStateId];
                    // Highlight self differently?
                    let color = relationColors[relation] || relationColors['Unknown'];
                    if (pStateId === stateId) color = relationColors['x'];

                    p.setAttribute('fill', color);
                }
            }
        });
    } else {
        // Reset to State Colors if no state selected
        paths.forEach(p => {
            const isWater = p.hasAttribute('data-is-water');
            if (isWater) {
                p.setAttribute('fill', '#333333'); // Dark Gray
            } else {
                // Revert to state color
                p.setAttribute('fill', p.getAttribute('data-state-color'));
            }
        });
    }
}
