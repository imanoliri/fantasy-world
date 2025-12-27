
// Adventure Mode Module

const AdventureManager = {
    active: false,
    party: {
        cell: 0,
        soldiers: 10,
        food: 50,
        gold: 10
    },
    partyElement: null,
    isMoving: false,

    init() {
        if (this.partyElement) return;

        // Create party element (circle)
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("r", "6");
        circle.setAttribute("fill", "#e67e22"); // Pumpkin color
        circle.setAttribute("stroke", "#2c3e50");
        circle.setAttribute("stroke-width", "2");
        circle.setAttribute("pointer-events", "none");
        circle.setAttribute("id", "partyMarker");
        circle.style.zIndex = "100";
        circle.style.transition = "cx 0.2s linear, cy 0.2s linear";
        circle.style.display = "none";

        // Append to mapSvg but ensure it's on top. 
        // We can append to the end.
        const svg = document.getElementById('mapSvg');
        svg.appendChild(circle);
        this.partyElement = circle;
    },

    toggle() {
        this.active = !this.active;
        const btn = document.getElementById('toggleAdventure');
        const stats = document.getElementById('adventureStats');

        if (this.active) {
            btn.classList.add('active');
            stats.style.display = 'inline-flex';
            this.init(); // Ensure element exists
            if (this.party.cell === 0) {
                this.start();
            } else {
                this.partyElement.style.display = "block";
                this.render();
            }
        } else {
            btn.classList.remove('active');
            stats.style.display = 'none';
            if (this.partyElement) this.partyElement.style.display = 'none';
        }
    },

    start() {
        // Pick random start cell that is not water
        // We can try to pick a burg's cell if possible
        let startCell = -1;

        // Try to find a burg to start at
        // We don't have direct access to burg objects easily unless we parse DOM
        // The DOM burgs have x,y. We can find closest cell.
        // OR we just pick a random cell from graphData that has h >= 20

        const validCells = graphData.filter(c => c.h >= 20);
        if (validCells.length > 0) {
            const random = validCells[Math.floor(Math.random() * validCells.length)];
            startCell = random.i;
        }

        if (startCell !== -1) {
            this.party.cell = startCell;
            this.party.soldiers = 10;
            this.party.food = 50;
            this.party.gold = 10;
            this.partyElement.style.display = "block";
            this.updateStats();
            this.render();

            // Initial message
            this.showFeedback("Adventure started! Click to move.");
        } else {
            console.error("No valid land cell found");
        }
    },

    async handleClick(target) {
        if (!this.active || this.isMoving) return;

        let cellId = null;

        if (target.tagName === 'path') {
            const id = target.getAttribute('data-cell-id');
            if (id) cellId = parseInt(id);
        } else if (target.classList.contains('burg-dot')) {
            // Find closest cell to burg
            // We can read x,y from circle
            const cx = parseFloat(target.getAttribute('cx'));
            const cy = parseFloat(target.getAttribute('cy'));
            cellId = this.findCellAt(cx, cy);
        }

        if (cellId !== null) {
            // Check if water
            if (graphData[cellId].h < 20) {
                this.showFeedback("Cannot move to water!");
                return;
            }

            // Pathfinding
            const path = this.findPath(this.party.cell, cellId);
            if (path && path.length > 0) {
                await this.moveAlongPath(path);
            } else {
                this.showFeedback("No path found (or too far/blocked)!");
            }
        }
    },

    findCellAt(x, y) {
        // Simple search for closest cell
        // Optimization: iterate all cells? Expensive? 
        // 10k cells is fine for click event usually.
        let minDist = Infinity;
        let closest = -1;

        for (let i = 0; i < graphData.length; i++) {
            const c = graphData[i];
            const dx = c.p[0] - x;
            const dy = c.p[1] - y;
            const dist = dx * dx + dy * dy;
            if (dist < minDist) {
                minDist = dist;
                closest = i;
            }
        }
        return closest;
    },

    findPath(start, end) {
        if (start === end) return [];

        // BFS
        const queue = [start];
        const cameFrom = {}; // path reconstruction
        cameFrom[start] = null;

        // Limit search depth/nodes to avoid freeze on large maps
        let visited = 0;
        const limit = 5000;

        while (queue.length > 0) {
            const current = queue.shift();
            visited++;
            if (visited > limit) return null; // Too far

            if (current === end) break;

            const neighbors = graphData[current].c;
            for (let next of neighbors) {
                // Check bounds and water
                if (graphData[next] && graphData[next].h >= 20) {
                    if (!(next in cameFrom)) {
                        queue.push(next);
                        cameFrom[next] = current;
                    }
                }
            }
        }

        if (!(end in cameFrom)) return null;

        // Reconstruct path
        const path = [];
        let curr = end;
        while (curr !== start) {
            path.push(curr);
            curr = cameFrom[curr];
        }
        // path is reversed (end -> start)
        return path.reverse();
    },

    async moveAlongPath(path) {
        this.isMoving = true;

        for (let nextCell of path) {
            if (this.party.food <= 0) {
                this.showFeedback("Out of food! Party is starving.");
                // Maybe penalty?
                this.party.soldiers = Math.max(0, this.party.soldiers - 1);
                if (this.party.soldiers === 0) {
                    this.showFeedback("Game Over! All soldiers died.");
                    this.isMoving = false;
                    return;
                }
            }

            this.party.cell = nextCell;
            this.party.food--;
            this.updateStats();
            this.render();

            // Wait for animation
            await new Promise(r => setTimeout(r, 150));
        }

        this.isMoving = false;
    },

    render() {
        const cell = graphData[this.party.cell];
        if (cell && this.partyElement) {
            // cell.p is [x, y]
            this.partyElement.setAttribute('cx', cell.p[0]);
            this.partyElement.setAttribute('cy', cell.p[1]);
        }
    },

    updateStats() {
        document.getElementById('advSoldiers').textContent = this.party.soldiers;
        document.getElementById('advFood').textContent = this.party.food;
        document.getElementById('advGold').textContent = this.party.gold;
    },

    showFeedback(msg) {
        const t = document.getElementById('tooltip');
        t.innerHTML = msg;
        t.style.display = 'block';
        // Center tooltip or show at party location
        // For now just somewhere visible? Or let user clear it.
        // Let's fade it out
        t.style.left = window.innerWidth / 2 + 'px';
        t.style.top = '100px';
        setTimeout(() => t.style.display = 'none', 2000);
    }
};

window.toggleAdventureMode = () => AdventureManager.toggle();
window.AdventureManager = AdventureManager;
