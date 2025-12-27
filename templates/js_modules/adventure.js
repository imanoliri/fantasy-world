
// Adventure Mode Module

const AdventureManager = {
    active: false,
    party: {
        cell: 0,
        soldiers: 10,
        food: 50,
        gold: 10,
        tools: 10
    },
    partyElement: null,
    partyElement: null,
    pathElement: null,
    previewPathElement: null,
    popupElement: null,
    isMoving: false,
    movementId: 0,
    knownBurgs: {},

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

        // Create path element (polyline)
        const pathLine = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
        pathLine.setAttribute("fill", "none");
        pathLine.setAttribute("stroke", "#ff0000"); // Red
        pathLine.setAttribute("stroke-width", "3");
        pathLine.setAttribute("stroke-dasharray", "5,5");
        pathLine.setAttribute("pointer-events", "none");
        pathLine.style.opacity = "0.8";
        pathLine.style.display = "none";

        // Create preview path element (polyline) different style
        const previewLine = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
        previewLine.setAttribute("fill", "none");
        previewLine.setAttribute("stroke", "#00ffff"); // Cyan
        previewLine.setAttribute("stroke-width", "3");
        previewLine.setAttribute("stroke-dasharray", "5,5"); // Same dash as normal
        previewLine.setAttribute("pointer-events", "none");
        previewLine.style.opacity = "0.8";
        previewLine.style.display = "none";

        const svg = document.getElementById('mapSvg');
        svg.appendChild(previewLine);
        svg.appendChild(pathLine);
        svg.appendChild(circle); // Append circle after to be on top

        this.partyElement = circle;
        this.pathElement = pathLine;
        this.previewPathElement = previewLine;
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
            this.party.tools = 10;
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
        if (!this.active) return;

        // Clear preview on click
        this.drawPreviewPath([]);

        // if moving, we override. No return.

        // Increment movementId to invalidate previous moves
        this.movementId++;

        const cellId = this.getTargetCellId(target);

        if (cellId !== null) {
            // Check if water
            if (graphData[cellId].h < 20) {
                this.showFeedback("Cannot move to water!");
                return;
            }

            // Pathfinding
            const path = this.findPath(this.party.cell, cellId);
            if (path && path.length > 0) {
                this.drawPath(path);
                await this.moveAlongPath(path);
                this.drawPath([]); // Clear after
            } else {
                this.showFeedback("No path found (or too far/blocked)!");
            }
        }
    },

    handleRightClick(target) {
        if (!this.active) return;

        const cellId = this.getTargetCellId(target);
        if (cellId !== null) {
            // Pathfinding Preview
            if (graphData[cellId].h < 20) {
                this.showFeedback("Cannot preview path to water!");
                return;
            }
            const path = this.findPath(this.party.cell, cellId);
            if (path && path.length > 0) {
                this.drawPreviewPath(path);
                this.showFeedback(`Path distance: ${path.length} steps`);
            } else {
                this.showFeedback("No path possible");
            }
        }
    },

    getTargetCellId(target) {
        let cellId = null;
        if (target.tagName === 'path') {
            const id = target.getAttribute('data-cell-id');
            if (id) cellId = parseInt(id);
        } else if (target.classList.contains('burg-dot')) {
            const cx = parseFloat(target.getAttribute('cx'));
            const cy = parseFloat(target.getAttribute('cy'));
            cellId = this.findCellAt(cx, cy);
        }
        return cellId;
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
        const currentId = this.movementId;

        for (let nextCell of path) {
            // Check if superseded
            if (this.movementId !== currentId) {
                // Determine if we should clear path or not. 
                // The new click will call drawPath with new path, so we don't need to do anything.
                // Just stop this loop.
                return;
            }

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

            // Update path visual (remove visited nodes)
            // path is the full path. We are iterating it.
            // We want to show from current nextCell to end.
            const remainingIndex = path.indexOf(nextCell);
            if (remainingIndex > -1) {
                this.drawPath(path.slice(remainingIndex));
            }

            // Wait for animation
            await new Promise(r => setTimeout(r, 150));
        }

        this.isMoving = false;

        // Check for arrival at burg
        this.checkForArrival();
    },

    checkForArrival() {
        // We know where the party is: this.party.cell
        // We need to find if there is a burg at this cell. Easiest is to search burgs_data (global var)
        const burg = burgsData.find(b => b.cell_id === this.party.cell);

        if (burg) {
            this.showBurgPopup(burg);
        }
    },

    showBurgPopup(burg) {
        // Create popup if doesn't exist
        if (!this.popupElement) {
            this.popupElement = document.createElement('div');
            this.popupElement.className = 'burg-popup';
            document.body.appendChild(this.popupElement);
        }

        // Calculate Surplus and Reset Logic
        let notificationHtml = '';
        const netFood = parseFloat(burg.net_food); // Ensure number

        if (netFood > 0) {
            // Only refill if current food is LESS than the surplus capacity
            const surplusCap = Math.floor(netFood * 10);
            if (this.party.food < surplusCap) {
                this.party.food = surplusCap;
                notificationHtml = `<div class="notification">Abundant food! Supplies reset to ${surplusCap}.</div>`;
                this.updateStats();
            }
        }

        // Ensure overlay exists
        let overlay = document.getElementById('modalOverlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'modalOverlay';
            overlay.className = 'modal-overlay';
            document.body.appendChild(overlay);
        }
        overlay.style.display = 'block';

        const craftsmanQuartiers = burg.craftsman_quartiers || 0;
        const toolsAmount = Math.min(craftsmanQuartiers, 5);
        const canBuyTools = craftsmanQuartiers > 0;

        const soldierQuartiers = burg.soldier_quartiers || 0;
        const soldierCost = Math.max(1, 6 - soldierQuartiers);
        const canRecruit = soldierQuartiers >= 1;

        this.popupElement.innerHTML = `
            <h2>${burg.name}</h2>
            <div class="content-wrapper">
                <div class="info">
                    Type: ${burg.type}<br>
                    Pop: ${burg.population_fmt}<br>
                    Food Surplus: ${parseFloat(burg.net_food).toFixed(2)}
                </div>
                ${notificationHtml}
            </div>
            <div class="actions">
                <button class="btn-buy" onclick="AdventureManager.buyFood(10, 1)" title="1 Gold for 10 Food">Buy 10 Food (1 💰)</button>
                ${canRecruit ? `<button class="btn-recruit" onclick="AdventureManager.recruitSoldiers(5, ${soldierCost}, ${burg.cell_id})" title="Recruit 5 soldiers for 5 Tools and 5 Gold. Each extra soldier over 1 in the burg decreases the gold cost by one (down to a minimum of 1)">Recruit 5 Soldiers (${soldierCost} 💰, 5 🛠️)</button>` : ''}
                ${canBuyTools ? `<button class="btn-buy" onclick="AdventureManager.buyTools(${toolsAmount}, 1)" title="1 Gold for an amount of Tools equal to Craftsmen in the burg (max 5)">Buy ${toolsAmount} Tools (1 💰)</button>` : ''}
                <button class="btn-leave" onclick="AdventureManager.closePopup()">Leave</button>
            </div>
        `;

        this.popupElement.style.display = 'block';
    },

    closePopup() {
        if (this.popupElement) {
            this.popupElement.style.display = 'none';
        }
        const overlay = document.getElementById('modalOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    },

    buyFood(amount, cost) {
        if (this.party.gold >= cost) {
            this.party.gold -= cost;
            this.party.food += amount;
            this.updateStats();
            this.showFeedback(`Bought ${amount} food!`);
        } else {
            this.showFeedback("Not enough gold!");
        }
    },

    buyTools(amount, cost) {
        if (this.party.gold >= cost) {
            this.party.gold -= cost;
            this.party.tools += amount;
            this.updateStats();
            this.showFeedback(`Bought ${amount} tools!`);
        } else {
            this.showFeedback("Not enough gold!");
        }
    },

    recruitSoldiers(amount, cost, burgCellId) {
        // Find burg to update its soldier count
        const burg = burgsData.find(b => b.cell_id === burgCellId);

        if (!burg) {
            console.error("Burg not found for recruitment");
            return;
        }

        const availableQuartiers = burg.soldier_quartiers || 0;
        if (availableQuartiers < 1) {
            this.showFeedback("No military quarters available!");
            return;
        }

        const toolsCost = 5;

        if (this.party.gold >= cost && this.party.tools >= toolsCost) {
            this.party.gold -= cost;
            this.party.tools -= toolsCost;
            this.party.soldiers += amount;

            this.updateStats();
            this.showFeedback(`Recruited ${amount} soldiers!`);
        } else {
            if (this.party.gold < cost) {
                this.showFeedback("Not enough gold!");
            } else {
                this.showFeedback("Not enough tools!");
            }
        }
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
        document.getElementById('advTools').textContent = this.party.tools;
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
    },

    drawPath(path) {
        if (!this.pathElement) return;

        if (!path || path.length === 0) {
            this.pathElement.style.display = "none";
            return;
        }

        const points = path.map(id => {
            const cell = graphData[id];
            return cell ? `${cell.p[0]},${cell.p[1]}` : "";
        }).join(" ");

        this.pathElement.setAttribute("points", points);
        this.pathElement.style.display = "block";
    },

    drawPreviewPath(path) {
        if (!this.previewPathElement) return;

        if (!path || path.length === 0) {
            this.previewPathElement.style.display = "none";
            return;
        }

        const points = path.map(id => {
            const cell = graphData[id];
            return cell ? `${cell.p[0]},${cell.p[1]}` : "";
        }).join(" ");

        this.previewPathElement.setAttribute("points", points);
        this.previewPathElement.style.display = "block";
    }
};

window.toggleAdventureMode = () => AdventureManager.toggle();
window.AdventureManager = AdventureManager;
