/**
 * TUUNA REALISM AVATAR
 * Handles Image manipulation and CSS class triggers
 */

class RealAvatar {
    constructor() {
        this.frame = document.querySelector('.avatar-frame');
        this.statusRing = document.getElementById('statusRing');
        this.subtitle = document.getElementById('subtitle');
        this.mouthOverlay = document.createElement('div'); // Virtual mouth handler
        this.state = 'IDLE';
    }

    setState(newState) {
        this.state = newState;

        // Reset classes
        this.frame.classList.remove('listening', 'thinking', 'speaking');

        if (newState === 'LISTENING') {
            this.frame.classList.add('listening');
            this.setSubtitle("Listening...");
        } else if (newState === 'THINKING') {
            this.frame.classList.add('thinking');
            this.setSubtitle("Processing...");
        } else if (newState === 'SPEAKING') {
            this.frame.classList.add('speaking');
        } else {
            this.setSubtitle(""); // Clear on idle
        }
    }

    setSubtitle(text) {
        if (text) {
            this.subtitle.innerText = text;
            this.subtitle.classList.add('visible');
        } else {
            this.subtitle.classList.remove('visible');
        }
    }
}

// Global Instance
window.tuunaAvatar = new RealAvatar();
