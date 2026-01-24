
const orb = document.getElementById('orb');
const statusText = document.getElementById('status');
const chatLog = document.getElementById('chatLog');
const manualInput = document.getElementById('manualInput');
const helpModal = document.getElementById('helpModal');
const voiceSelect = document.getElementById('voiceSelect');
const startBtn = document.getElementById('startBtn');

let silenceTimer;
let voices = [];
let isListening = false;
let isSpeaking = false;
let isProcessing = false;

// --- Voice Setup ---
function populateVoices() {
    const allVoices = window.speechSynthesis.getVoices();
    voiceSelect.innerHTML = '';
    voices = [];
    const hindiVoices = allVoices.filter(v => v.lang.includes('hi') || v.name.includes('Hindi') || v.name.includes('India'));
    const englishVoices = allVoices.filter(v => (v.lang.includes('en') && !v.lang.includes('hi')) && !hindiVoices.includes(v));
    const sortedVoices = [...hindiVoices, ...englishVoices];

    sortedVoices.forEach((voice) => {
        voices.push(voice);
        const option = document.createElement('option');
        option.textContent = `${voice.name} (${voice.lang})`;
        option.value = voice.name;
        option.setAttribute('data-name', voice.name);
        voiceSelect.appendChild(option);
    });

    if (voices.length === 0) {
        const option = document.createElement('option');
        option.textContent = "Default Voice";
        voiceSelect.appendChild(option);
    }

    const preferredIndex = voices.findIndex(v => v.lang.includes('hi') || v.name.includes('Hindi'));
    if (preferredIndex !== -1) {
        voiceSelect.selectedIndex = preferredIndex;
    } else {
        const fallbackIndex = voices.findIndex(v => v.name.includes('Google US English') || v.name.includes('Zira'));
        if (fallbackIndex !== -1) voiceSelect.selectedIndex = fallbackIndex;
    }
}

populateVoices();
if (speechSynthesis.onvoiceschanged !== undefined) {
    speechSynthesis.onvoiceschanged = populateVoices;
}

function testVoice() {
    console.log("Voice changed to: " + voiceSelect.value);
}

function toggleHelp() {
    const modal = document.getElementById('helpModal');
    if (modal) modal.style.display = modal.style.display === 'flex' ? 'none' : 'flex';
}

function logMessage(sender, text, isDebug = false) {
    const bubble = document.createElement('div');
    bubble.className = `msg ${sender === 'Tuuna' ? 'system' : 'user'}`;
    bubble.innerText = `${sender === 'Tuuna' ? '[AI]' : '[USER]'} ${text}`;

    // Add time stamp
    const ts = document.createElement('span');
    ts.className = 'ts';
    ts.innerText = '[LOG]';
    bubble.prepend(ts);

    chatLog.appendChild(bubble);
    chatLog.scrollTop = chatLog.scrollHeight;
}

// --- Speech Recognition ---
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
    alert("Speech Recognition not supported. Please use Chrome.");
}

const recognition = new SpeechRecognition();
recognition.continuous = true;
recognition.lang = 'en-IN';
recognition.interimResults = true;
recognition.maxAlternatives = 1;

recognition.onstart = () => {
    statusText.innerText = "LISTENING...";
    statusText.style.color = "var(--hud-cyan)";
    if (orb) orb.classList.add('listening');
    // CORE
    if (window.neuralCore) window.neuralCore.setState('LISTENING');
    isListening = true;
};

recognition.onend = () => {
    if (isListening) {
        if (!isSpeaking) recognition.start();
    } else {
        if (orb) orb.classList.remove('listening');
        // CORE
        if (window.neuralCore) window.neuralCore.setState('IDLE');
        statusText.innerText = "STANDBY MODE";
        statusText.style.color = "var(--hud-green)";
    }
};

recognition.onerror = (event) => {
    console.error("Speech Error:", event.error);
    statusText.innerText = `ERROR: ${event.error}`;
};

recognition.onresult = (event) => {
    clearTimeout(silenceTimer);
    const lastResult = event.results[event.results.length - 1];
    const transcript = lastResult[0].transcript.trim().toLowerCase();
    const isFinal = lastResult.isFinal;

    console.log("Heard (Interim):", transcript);
    statusText.innerText = `HEARING: "${transcript}"`;
    statusText.style.color = "var(--hud-cyan)";

    silenceTimer = setTimeout(() => {
        if (transcript.length > 0) {
            console.log("Silence detected. Processing command:", transcript);
            recognition.stop();
            handleCommandLogic(transcript);
        }
    }, 2000);

    if (isFinal) {
        clearTimeout(silenceTimer);
        handleCommandLogic(transcript);
    }
};

function handleCommandLogic(transcript) {
    if (transcript.length > 5 && !isProcessing) {
        logMessage("User", transcript);
        processCommand(transcript);
    }
}

async function processCommand(command) {
    if (isProcessing) return;
    isProcessing = true;
    statusText.innerText = "PROCESSING...";
    // CORE
    if (window.neuralCore) window.neuralCore.setState('THINKING');
    if (orb) orb.classList.remove('listening');

    // VISION CAPTURE
    let clientImage = null;
    const video = document.getElementById('liveFeed');
    if (video && video.srcObject && video.readyState >= 2) {
        try {
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);
            clientImage = canvas.toDataURL('image/jpeg', 0.7);
            console.log("Captured Vision Frame");
        } catch (e) { console.error("Frame Capture Failed", e); }
    }

    try {
        const response = await fetch('/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: command, client_image: clientImage })
        });

        const data = await response.json();
        logMessage("Tuuna", data.response);
        speak(data.response);


    } catch (error) {
        console.error("Error:", error);
        logMessage("System", "Error connecting to server.");
        statusText.innerText = "ERROR";
        if (orb) orb.classList.remove('listening');
        setTimeout(() => {
            statusText.innerText = "LISTENING...";
            if (!isListening) toggleListening();
        }, 2000);
    } finally {
        isProcessing = false;
    }
}

// --- Speech Synthesis Override (with Hex Logic & Core) ---
function speak(text) {
    // Hex Activation
    activateHex('mod_synth', Math.max(2000, text.length * 50));
    // CORE
    if (window.neuralCore) window.neuralCore.setState('SPEAKING');

    isSpeaking = true;
    recognition.stop();

    if (orb) {
        orb.classList.remove('listening');
        orb.classList.add('speaking');
    }
    statusText.innerText = "VOCALIZING...";

    const utterance = new SpeechSynthesisUtterance(text);

    if (voiceSelect.selectedOptions.length > 0) {
        const selectedName = voiceSelect.selectedOptions[0].getAttribute('data-name');
        const selectedVoice = voices.find(v => v.name === selectedName);
        if (selectedVoice) utterance.voice = selectedVoice;
    }

    utterance.onend = () => {
        isSpeaking = false;
        if (orb) orb.classList.remove('speaking');
        statusText.innerText = "LISTENING...";
        // CORE
        if (window.neuralCore) window.neuralCore.setState('IDLE');

        if (isListening) {
            try {
                recognition.start();
                if (window.neuralCore) window.neuralCore.setState('LISTENING');
            } catch (e) { }
        }
        // Deactivate Hex
        const synth = document.getElementById('mod_synth');
        if (synth) synth.classList.remove('active');
    };

    window.speechSynthesis.speak(utterance);
}

function toggleListening() {
    if (isListening) {
        isListening = false;
        recognition.stop();
        statusText.innerText = "PAUSED";
    } else {
        try {
            recognition.start();
        } catch (e) {
            console.log("Already started");
        }
    }
}

function sendManualCommand() {
    const text = manualInput.value;
    if (text) {
        logMessage("User", text);
        console.log("Manual:", text);
        processCommand(text);
        manualInput.value = "";
    }
}

// --- HEX GRID LOGIC ---
const statusOverlay = document.getElementById('statusOverlay');

function activateHex(moduleId, duration = 800) {
    const el = document.getElementById(moduleId);
    if (el) {
        el.classList.add('active');
        setTimeout(() => el.classList.remove('active'), duration);
    }
}

// Polling for Actions/Thoughts
setInterval(async () => {
    try {
        const res = await fetch('/stream_logs');
        const logs = await res.json();

        if (logs.length > 0) {
            logs.forEach(log => {
                // Trigger Hex based on log type
                if (log.type === 'thought') {
                    activateHex('mod_cortex', 1500);
                    if (statusOverlay) statusOverlay.innerText = "CORTEX: " + log.msg;
                    // CORE
                    if (window.neuralCore) window.neuralCore.setState('THINKING');
                }
                if (log.type === 'action') {
                    activateHex('mod_uplink', 1500);
                    activateHex('mod_code', 1500);
                    if (statusOverlay) statusOverlay.innerText = "UPLINK: " + log.msg;
                }
                if (log.type === 'error') {
                    activateHex('mod_secure', 1500);
                    // Hide raw error from UI, just show alert
                    if (statusOverlay) statusOverlay.innerText = "SYSTEM ALERT: CHECK CONSOLE";
                    console.error("BACKEND ERROR:", log.msg);
                }
            });
        }
    } catch (e) { }
}, 800);

manualInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendManualCommand();
});

// INIT
// --- VISION LOGIC ---
async function initVision() {
    const video = document.getElementById('liveFeed');
    const header = document.querySelector('.vision-header');
    const container = document.querySelector('.vision-container');

    if (!video) return;

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        header.innerText = " REC"; // Space for dot
        header.removeAttribute('style'); // Use CSS class styles
        container.classList.add('active');


        // Trigger Hex
        activateHex('mod_vision', 2000);
    } catch (e) {
        console.error("Camera Access Denied", e);
        header.innerText = "SIGNAL LOST";
        header.style.color = "var(--hud-red)";
    }
}

// INIT
window.onload = () => {
    if (window.initLiquidCore) window.initLiquidCore();
    initVision();
}


