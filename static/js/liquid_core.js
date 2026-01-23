/**
 * LIQUID CORE v1.0
 * 'Trending' Fluid Gradient Animation
 */

class LiquidCore {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;

        this.ctx = this.canvas.getContext('2d');
        this.resize();

        this.time = 0;
        this.state = 'IDLE';

        // Configuration
        this.blobs = [
            { r: 0, g: 243, b: 255, x: 0, y: 0, vx: 1, vy: 1, s: 100 },
            { r: 188, g: 19, b: 254, x: 0, y: 0, vx: -1, vy: 1, s: 120 },
            { r: 5, g: 255, b: 0, x: 0, y: 0, vx: 1, vy: -1, s: 80 }
        ];

        this.speed = 0.02;
        this.globalScale = 1;

        this.animate = this.animate.bind(this);
        requestAnimationFrame(this.animate);

        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        this.canvas.width = this.canvas.parentElement.offsetWidth;
        this.canvas.height = this.canvas.parentElement.offsetHeight;
        this.centerX = this.canvas.width / 2;
        this.centerY = this.canvas.height / 2;
    }

    setState(newState) {
        this.state = newState;
        if (newState === 'IDLE') {
            this.speed = 0.02;
            this.globalScale = 1;
        } else if (newState === 'LISTENING') {
            this.speed = 0.05;
            this.globalScale = 1.2;
        } else if (newState === 'THINKING') {
            this.speed = 0.1;
            this.globalScale = 0.8; // Tighten
        } else if (newState === 'SPEAKING') {
            this.speed = 0.04;
            this.globalScale = 1.4; // Expand
        }
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.time += this.speed;

        // Composite Operation for "Gooey" effect
        this.ctx.globalCompositeOperation = 'screen';
        // Note: 'screen' or 'lighter' gives that neon look

        this.blobs.forEach((b, i) => {
            // Move in Lissajous curves for organic motion
            const movementX = Math.sin(this.time * b.vx + i) * 50 * this.globalScale;
            const movementY = Math.cos(this.time * b.vy + i) * 50 * this.globalScale;

            const x = this.centerX + movementX;
            const y = this.centerY + movementY;

            const size = b.s * (1 + Math.sin(this.time * 2 + i) * 0.2) * this.globalScale;

            // Gradient
            const grad = this.ctx.createRadialGradient(x, y, 0, x, y, size);
            grad.addColorStop(0, `rgba(${b.r}, ${b.g}, ${b.b}, 0.8)`);
            grad.addColorStop(0.5, `rgba(${b.r}, ${b.g}, ${b.b}, 0.2)`);
            grad.addColorStop(1, `rgba(${b.r}, ${b.g}, ${b.b}, 0)`);

            this.ctx.fillStyle = grad;
            this.ctx.beginPath();
            this.ctx.arc(x, y, size, 0, Math.PI * 2);
            this.ctx.fill();
        });

        requestAnimationFrame(this.animate);
    }
}

window.initLiquidCore = () => {
    window.neuralCore = new LiquidCore('neuralCanvas');
};
