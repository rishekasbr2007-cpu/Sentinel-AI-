document.addEventListener('DOMContentLoaded', () => {
    const menu = document.getElementById('radial-menu');
    const centerBtn = document.getElementById('radial-center-btn');
    const items = document.querySelectorAll('.radial-item');
    const RADIUS = 120; // Distance of items from center

    // Pre-calculate positions for expanded state
    items.forEach((item, index) => {
        // Subtract 90 degrees (PI/2) so the first item starts at the top
        const angle = (index / items.length) * (2 * Math.PI) - (Math.PI / 2); 
        const x = Math.round(RADIUS * Math.cos(angle));
        const y = Math.round(RADIUS * Math.sin(angle));
        
        item.style.setProperty('--target-x', `${x}px`);
        item.style.setProperty('--target-y', `${y}px`);
    });

    let isDragging = false;
    let startX, startY, initialLeft, initialTop;
    let dragThreshold = 5; // Pixels to move before registering as a drag
    let hasMoved = false;

    // Initial position (bottom left corner-ish, similar to a FAB)
    let menuX = 80;
    let menuY = window.innerHeight - 80;

    function constrainBounds() {
        // Ensure the menu can't be dragged too close to the edge
        // so that the expanded radial items stay on screen
        const buffer = RADIUS + 40; // RADIUS + item radius + some padding
        menuX = Math.max(buffer, Math.min(window.innerWidth - buffer, menuX));
        menuY = Math.max(buffer, Math.min(window.innerHeight - buffer, menuY));
    }

    function updateMenuPosition() {
        // Position the menu using transform for better performance, centered on coords
        menu.style.transform = `translate(calc(${menuX}px - 50%), calc(${menuY}px - 50%))`;
    }

    // Initialize position
    constrainBounds();
    updateMenuPosition();

    // Pointer events for drag and drop
    centerBtn.addEventListener('pointerdown', (e) => {
        // Ignore right clicks
        if (e.button !== 0) return;
        
        isDragging = true;
        hasMoved = false;
        startX = e.clientX;
        startY = e.clientY;
        
        initialLeft = menuX;
        initialTop = menuY;

        centerBtn.setPointerCapture(e.pointerId);
        menu.classList.add('dragging');
    });

    centerBtn.addEventListener('pointermove', (e) => {
        if (!isDragging) return;
        
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;

        if (!hasMoved && (Math.abs(dx) > dragThreshold || Math.abs(dy) > dragThreshold)) {
            hasMoved = true;
            // Optionally collapse if dragging while open
            menu.classList.remove('open'); 
        }

        if (hasMoved) {
            menuX = initialLeft + dx;
            menuY = initialTop + dy;
            constrainBounds();
            updateMenuPosition();
        }
    });

    centerBtn.addEventListener('pointerup', (e) => {
        if (!isDragging) return;
        isDragging = false;
        centerBtn.releasePointerCapture(e.pointerId);
        menu.classList.remove('dragging');

        if (!hasMoved) {
            // It was a simple click
            menu.classList.toggle('open');
        }
    });

    // Close on click outside
    document.addEventListener('click', (e) => {
        if (menu.classList.contains('open') && !menu.contains(e.target)) {
            menu.classList.remove('open');
        }
    });

    // Handle window resize
    window.addEventListener('resize', () => {
        constrainBounds();
        updateMenuPosition();
    });
});
