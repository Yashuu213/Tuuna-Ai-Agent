
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
let isProcessing = false; // Prevent overlapping commands

// --- Voice Setup ---
function populateVoices() {
    const allVoices = window.speechSynthesis.getVoices();
    voiceSelect.innerHTML = '';
    voices = [];

    // Prioritize Hindi voices
    const hindiVoices = allVoices.filter(v => v.lang.includes('hi') || v.name.includes('Hindi') || v.name.includes('India'));
    const englishVoices = allVoices.filter(v => (v.lang.includes('en') && !v.lang.includes('hi')) && !hindiVoices.includes(v));

    // Combine: Hindi first, then English
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

    // Auto-select a Hindi voice if available, else a good English one
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

// --- Helper UI Functions ---
function toggleHelp() {
    helpModal.style.display = helpModal.style.display === 'flex' ? 'none' : 'flex';
}

function logMessage(sender, text, isDebug = false) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender === 'Tuuna' ? 'system' : 'user'}`;
    bubble.innerText = text; // Secure text insertion
    chatLog.appendChild(bubble);

    // Auto Scroll
    chatLog.scrollTop = chatLog.scrollHeight;
}

// --- Speech Recognition ---
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (!SpeechRecognition) {
    alert("Speech Recognition not supported. Please use Chrome.");
}

const recognition = new SpeechRecognition();
recognition.continuous = true;
recognition.lang = 'en-IN'; // Works well for Hinglish
recognition.interimResults = true; // KEY CHANGE: Listen to partial speech
recognition.maxAlternatives = 1;

recognition.onstart = () => {
    statusText.innerText = "LISTENING...";
    statusText.style.color = "var(--primary)";
    orb.classList.remove('speaking');
    orb.classList.add('listening');
    isListening = true;
    startBtn.innerText = "STOP LISTENING";
    startBtn.classList.remove('primary'); // Change style to indicate active
};

recognition.onend = () => {
    if (isListening) {
        // If it stopped but we didn't ask it to, restart it (unless speaking)
        if (!isSpeaking) recognition.start();
    } else {
        orb.classList.remove('listening');
        statusText.innerText = "SYSTEM STANDBY";
        statusText.style.color = "#8892b0";
        startBtn.innerText = "START LISTENING";
        startBtn.classList.add('primary');
    }
};

recognition.onerror = (event) => {
    console.error("Speech Error:", event.error);
    statusText.innerText = `ERROR: ${event.error}`;
};

recognition.onresult = (event) => {
    // Clear any existing silence timer
    clearTimeout(silenceTimer);

    const lastResult = event.results[event.results.length - 1];
    const transcript = lastResult[0].transcript.trim().toLowerCase();
    const isFinal = lastResult.isFinal;

    console.log("Heard (Interim):", transcript);

    // Show what is being heard immediately for feedback
    statusText.innerText = `HEARING: "${transcript}"`;
    statusText.style.color = "var(--primary)";

    // Set a timer: If user stops speaking for 1.5 seconds, assume command is done.
    // This is much faster than the default ~5-10s timeout.
    silenceTimer = setTimeout(() => {
        if (transcript.length > 0) {
            console.log("Silence detected. Processing command:", transcript);
            recognition.stop(); // Warning: this triggers onend
            handleCommandLogic(transcript);
        }
    }, 2000); // Increased to 2s to reduce accidental triggers

    if (isFinal) {
        clearTimeout(silenceTimer); // We got a final result natively
        handleCommandLogic(transcript);
    }
};

function handleCommandLogic(transcript) {
    // REMOVED STRICT FILTERS: We now send everything to the AI to decide.
    // This allows conversational Hindi, follow-up questions, and natural speech.

    // Minimum length check to avoid "um", "ah", or background noise triggers
    if (transcript.length > 5 && !isProcessing) {
        logMessage("User", transcript);
        processCommand(transcript);
    }
}

// --- Command Processing ---
async function processCommand(command) {
    if (isProcessing) return;
    isProcessing = true;
    statusText.innerText = "PROCESSING...";
    orb.classList.remove('listening');

    try {
        const response = await fetch('/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command: command })
        });

        const data = await response.json();
        logMessage("Tuuna", data.response);
        speak(data.response);

    } catch (error) {
        console.error("Error:", error);
        logMessage("System", "Error connecting to server.");
        statusText.innerText = "ERROR";
        // Reset state so usage can continue
        orb.classList.remove('listening');
        setTimeout(() => {
            statusText.innerText = "LISTENING...";
            if (!isListening) toggleListening();
        }, 2000);
    } finally {
        isProcessing = false;
    }
}

// --- Speech Synthesis ---
function speak(text) {
    isSpeaking = true;
    recognition.stop(); // Stop listening so it doesn't hear itself

    orb.classList.remove('listening');
    orb.classList.add('speaking');
    statusText.innerText = "VOCALIZING...";

    const utterance = new SpeechSynthesisUtterance(text);

    if (voiceSelect.selectedOptions.length > 0) {
        const selectedName = voiceSelect.selectedOptions[0].getAttribute('data-name');
        const selectedVoice = voices.find(v => v.name === selectedName);
        if (selectedVoice) utterance.voice = selectedVoice;
    }

    utterance.onend = () => {
        isSpeaking = false;
        orb.classList.remove('speaking');
        statusText.innerText = "LISTENING...";

        // Resume listening
        if (isListening) {
            try { recognition.start(); } catch (e) { }
        }
    };

    window.speechSynthesis.speak(utterance);
}

// --- User Interaction ---
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
        processCommand(text);
        manualInput.value = "";
    }
}

const terminalWindow = document.getElementById('terminalWindow');

// --- Log Streaming ---
setInterval(async () => {
    try {
        const res = await fetch('/stream_logs');
        const logs = await res.json();

        if (logs.length > 0) {
            logs.forEach(log => {
                const div = document.createElement('div');
                div.className = `log-entry ${log.type}`;
                // Special formatting for different log types
                let icon = "";
                if (log.type === "thought") icon = "🧠 ";
                if (log.type === "action") icon = "⚡ ";
                if (log.type === "error") icon = "❌ ";

                div.innerHTML = `<span style="opacity:0.5">[${log.ts}]</span> ${icon}${log.msg}`;
                terminalWindow.appendChild(div);
            });
            // Auto Scroll Terminal
            terminalWindow.scrollTop = terminalWindow.scrollHeight;
        }
    } catch (e) {
        // Silent fail for polling
    }
}, 1000); // 1-second poll rate

manualInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") sendManualCommand();
});
