/**
 * NEURAL NEXUS CORE v2.0
 * Generative Particle System for AI Visualization
 */

class NeuralCore {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;

        this.ctx = this.canvas.getContext('2d');
        this.resize();

        this.particles = [];
        this.numParticles = 80;
        this.connectionDistance = 100;
        this.state = 'IDLE'; // IDLE, LISTENING, THINKING, SPEAKING

        this.color = { r: 0, g: 243, b: 255 }; // Cyan default
        this.speedMod = 1;
        this.pulse = 0;

        this.initParticles();
        this.animate();

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
            this.targetColor = { r: 0, g: 243, b: 255 }; // Cyan
            this.speedMod = 0.5;
            this.numParticles = 60;
        } else if (newState === 'LISTENING') {
            this.targetColor = { r: 5, g: 255, b: 0 }; // Green
            this.speedMod = 0.2; // Slow, focused
            this.numParticles = 80;
        } else if (newState === 'THINKING') {
            this.targetColor = { r: 188, g: 19, b: 254 }; // Purple
            this.speedMod = 3.0; // Fast processing
            this.numParticles = 100;
        } else if (newState === 'SPEAKING') {
            this.targetColor = { r: 0, g: 243, b: 255 };
            this.speedMod = 1.0;
        }
    }

    initParticles() {
        this.particles = [];
        for (let i = 0; i < this.numParticles; i++) {
            this.particles.push({
                x: Math.random() * this.canvas.width,
                y: Math.random() * this.canvas.height,
                vx: (Math.random() - 0.5) * 2,
                vy: (Math.random() - 0.5) * 2,
                size: Math.random() * 2 + 1
            });
        }
    }

    lerpColor() {
        if (!this.targetColor) return;
        this.color.r += (this.targetColor.r - this.color.r) * 0.05;
        this.color.g += (this.targetColor.g - this.color.g) * 0.05;
        this.color.b += (this.targetColor.b - this.color.b) * 0.05;
    }

    animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.lerpColor();
        this.pulse += 0.05;

        const rgb = `rgb(${Math.floor(this.color.r)},${Math.floor(this.color.g)},${Math.floor(this.color.b)})`;
        const rgba = (a) => `rgba(${Math.floor(this.color.r)},${Math.floor(this.color.g)},${Math.floor(this.color.b)}, ${a})`;

        // Audio Pulse Effect (Simulated)
        let radiusMod = 0;
        if (this.state === 'SPEAKING') {
            radiusMod = Math.sin(this.pulse * 4) * 5;
        }

        // Update Particles
        this.particles.forEach((p, index) => {
            // Movement
            p.x += p.vx * this.speedMod;
            p.y += p.vy * this.speedMod;

            // Bounce off walls
            if (p.x < 0 || p.x > this.canvas.width) p.vx *= -1;
            if (p.y < 0 || p.y > this.canvas.height) p.vy *= -1;

            // Draw Point
            this.ctx.beginPath();
            this.ctx.arc(p.x, p.y, p.size + radiusMod / 4, 0, Math.PI * 2);
            this.ctx.fillStyle = rgb;
            this.ctx.fill();

            // Connections
            for (let j = index + 1; j < this.particles.length; j++) {
                const p2 = this.particles[j];
                const dx = p.x - p2.x;
                const dy = p.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < this.connectionDistance) {
                    this.ctx.beginPath();
                    this.ctx.strokeStyle = rgba(1 - dist / this.connectionDistance);
                    this.ctx.lineWidth = 1;
                    this.ctx.moveTo(p.x, p.y);
                    this.ctx.lineTo(p2.x, p2.y);
                    this.ctx.stroke();
                }
            }
        });

        // Center Interaction: Pull to center if Listening
        if (this.state === 'LISTENING') {
            this.particles.forEach(p => {
                const dx = this.centerX - p.x;
                const dy = this.centerY - p.y;
                p.x += dx * 0.01;
                p.y += dy * 0.01;
            });
        }

        requestAnimationFrame(() => this.animate());
    }
}

// Global hook
window.initNeuralCore = () => {
    window.neuralCore = new NeuralCore('neuralCanvas');
};
