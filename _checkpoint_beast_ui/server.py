import os
import time
import json
import pyautogui
import pywhatkit
import sys
import threading
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

# --- REAL-TIME LOGGING SYSTEM ---
LOG_BUFFER = []
LOG_LOCK = threading.Lock()

class LogStream(object):
    """Captures print() statements and stores them for the frontend."""
    def __init__(self, original_stdout):
        self.original_stdout = original_stdout

    def write(self, message):
        self.original_stdout.write(message) # Keep printing to console
        if message.strip():
            with LOG_LOCK:
                # Add timestamp and categorize
                ts = time.strftime("%H:%M:%S")
                category = "system"
                if "Error" in message: category = "error"
                elif "Thinking" in message or "Thought" in message or "🧠" in message: category = "thought"
                elif "Action" in message or "🛠️" in message: category = "action"
                
                LOG_BUFFER.append({"ts": ts, "msg": message.strip(), "type": category})
                # Keep buffer small
                if len(LOG_BUFFER) > 100: LOG_BUFFER.pop(0)

    def flush(self):
        self.original_stdout.flush()

# Redirect stdout
sys.stdout = LogStream(sys.stdout)

# --- IMPORT MODULES ---
from utils.ai_config import generate_content_with_retry, AI_AVAILABLE
from utils.system_tools import (
    APP_PATHS, get_system_status, find_and_open_file, write_file, read_file, 
    get_clipboard_text, run_terminal_command, perform_web_search, 
    set_alarm, save_memory, get_memory_string, learn_lesson
)
from utils.organizer import organize_files
from utils.vision import (
    get_screenshot, take_user_screenshot, omni_vision_action, 
    start_auto_apply, stop_auto_apply
)
from utils.beast_mode import (
    execute_architect, execute_protocol, execute_job_hunter, execute_python_code,
    execute_cognitive_chain
)


app = Flask(__name__)
CORS(app)

# --- AI ROUTER ---
def execute_ai_action(action_data):
    """Executes the JSON action(s) returned by Gemini."""
    
    if isinstance(action_data, list):
        results = []
        for action_item in action_data:
            result = execute_ai_action(action_item)
            results.append(result)
        return " | ".join(results)

    action = action_data.get("action")
    target = action_data.get("target", "")
    
    print(f"Executing AI Action: {action} -> {target}")

    if action == "delay":
        try:
            seconds = float(target)
            time.sleep(seconds)
            return f"Waited {seconds}s"
        except:
            time.sleep(1)
            return "Waited 1s"

    if action == "open_app":
        if target in APP_PATHS:
            os.system(APP_PATHS[target])
            return f"Opening {target}"
        else:
            pyautogui.press('win')
            time.sleep(0.5)
            pyautogui.write(target)
            time.sleep(0.5)
            pyautogui.press('enter')
            return f"Opening {target}"

    elif action == "open_web":
        if not target.startswith('http'): target = 'https://' + target
        webbrowser.open(target)
        return f"Opening {target}"

    elif action == "play_music":
        pywhatkit.playonyt(target)
        return f"Playing {target} on YouTube"

    elif action == "system":
        if "shutdown" in target: os.system("shutdown /s /t 10"); return "Shutting down in 10s"
        if "restart" in target: os.system("shutdown /r /t 10"); return "Restarting in 10s"
        if "sleep" in target: os.system("rundll32.dll powrprof.dll,SetSuspendState 0,1,0"); return "Going to sleep"
        if "battery" in target: return get_system_status()
        if "alarm" in target: return set_alarm(action_data.get("seconds", 5))
        if "recycle" in target: 
             try: winshell.recycle_bin().empty(confirm=False, show_progress=False, sound=False); return "Recycle bin emptied"
             except: return "Recycle bin already empty"

    elif action == "mouse":
        sub = action_data.get("sub")
        if sub == "move":
            direction = target
            amount = 100
            if "up" in direction: pyautogui.moveRel(0, -amount)
            if "down" in direction: pyautogui.moveRel(0, amount)
            if "left" in direction: pyautogui.moveRel(-amount, 0)
            if "right" in direction: pyautogui.moveRel(amount, 0)
            return "Moved mouse"
        if sub == "click": pyautogui.click(); return "Clicked"
        if sub == "right_click": pyautogui.click(button='right'); return "Right clicked"
        if sub == "scroll": 
            if "up" in target: pyautogui.scroll(500)
            else: pyautogui.scroll(-500)
            return "Scrolled"

    elif action == "media":
        sub = action_data.get("sub")
        if sub == "screenshot": return take_user_screenshot()
        if sub == "screen_record":
            duration = int(action_data.get("duration", 10))
            code = f"""
            import cv2
            import numpy as np
            import pyautogui
            import time
            import os
            
            SCREEN_SIZE = tuple(pyautogui.size())
            fourcc = cv2.VideoWriter_fourcc(*"XVID")
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            filename = os.path.join(desktop, f"ScreenRec_{{int(time.time())}}.avi")
            out = cv2.VideoWriter(filename, fourcc, 20.0, (SCREEN_SIZE))
            
            print(f"Recording for {duration} seconds...")
            start_time = time.time()
            while int(time.time() - start_time) < {duration}:
                img = pyautogui.screenshot()
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                out.write(frame)
                
            out.release()
            print(f"Saved: {{filename}}")
            os.startfile(filename)
            """
            return execute_python_code(code)

        if sub == "voice_record":
            duration = int(action_data.get("duration", 10))
            code = f"""
            import sounddevice as sd
            from scipy.io.wavfile import write
            import os
            import time
            
            fs = 44100
            seconds = {duration}
            print(f"Recording Voice for {duration}s...")
            myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
            sd.wait()
            
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            filename = os.path.join(desktop, f"VoiceRec_{{int(time.time())}}.wav")
            write(filename, fs, myrecording)
            print(f"Saved: {{filename}}")
            os.startfile(filename)
            """
            return execute_python_code(code)

    elif action == "keyboard":
        sub = action_data.get("sub")
        if sub == "type": 
            # FIX: Use Clipboard Paste
            pyperclip.copy(target)
            pyautogui.hotkey('ctrl', 'v')
            return f"Pasted {len(target)} chars"
        if sub == "press": pyautogui.press(target); return f"Pressed {target}"
        if sub == "copy": pyautogui.hotkey('ctrl', 'c'); return "Copied"
        if sub == "paste": pyautogui.hotkey('ctrl', 'v'); return "Pasted"
        if sub == "hotkey": 
            keys = target.split(",")
            pyautogui.hotkey(*[k.strip() for k in keys])
            return f"Pressed Hotkey: {target}"

    elif action == "file":
        sub = action_data.get("sub")
        if sub == "open": return find_and_open_file(target)
        if sub == "write": return write_file(target, action_data.get("content", ""))
        if sub == "read": return read_file(target)

    elif action == "memory":
        sub = action_data.get("sub")
        target_val = target
        if sub == "save": save_memory(target_val, "user_facts")
        elif sub == "preference": save_memory(target_val, "preferences")
        else: save_memory(target_val, "user_facts")
        return f"Memory Saved: {target_val}"

    elif action == "learn":
        learn_lesson(target)
        return f"Lesson Learned: {target}"
    
    elif action == "clipboard":
        return get_clipboard_text()
    
    elif action == "terminal":
        return run_terminal_command(target)
    
    elif action == "search":
        return perform_web_search(target)
        
    elif action == "organize":
        return organize_files(target)

    elif action == "architect":
        return execute_architect(target, action_data.get("sub", ""))

    elif action == "protocol":
        return execute_protocol(target)

    elif action == "job_hunter":
        return execute_job_hunter(target)
        
    elif action == "auto_apply":
        sub = action_data.get("sub")
        if sub == "start": return start_auto_apply()
        if sub == "stop": return stop_auto_apply()

    elif action == "executor":
        return execute_python_code(action_data.get("code", ""))

    elif action == "reasoning":
        return execute_cognitive_chain(target)

    elif action == "vision_agent":
        return omni_vision_action(target)

    return "Action completed."

# --- SYSTEM PROMPT ---
def ask_gemini_brain(user_command):
    """Sends command to Gemini with Auto-Model-Rotation for fallback."""
    if not AI_AVAILABLE:
        return None, "AI Library not installed."

    system_prompt = """
    You are Tuuna, a friendly and helpful AI personal assistant. You speak in a casual, warm, and engaging tone, like a close friend. You are always ready to help with PC tasks or just chat.
    
    LANGUAGE SUPPORT: You understand both English and Hindi (and Hinglish).
    - If the user speaks Hindi, reply in **Hindi (using Devanagari script)** so the TTS engine speaks it correctly.
    - Translate Hindi commands to actions (e.g. "Google kholo" -> open_web google).

    CODE GENERATION RULES:
    - If the user asks to write code or a file, you MUST follow these strict rules:
    1. **ghost_writer_mode**: If the user asks to "write code", "type this", or is looking at a code editor, do NOT create a file. Instead, **TYPE/PASTE** the code directly into the active window using the `keyboard` -> `type` action.
    2. **file_mode**: Only use `file` -> `write` if the user explicitly says "create a file named..." or "save to...".
    3. **NO COMMENTS**: Do not write comments in the code.
    4. **NO EXAMPLES**: Do not add "Example usage" blocks.
    5. **CLEAN CODE**: Write only the necessary functional code.

    Analyze the user's command and decide if it requires a PC action or just a chat response.

    If it is a PC ACTION, output ONLY a JSON LIST of objects with this format:
    [
        {"action": "open_app", "target": "notepad"},
        {"action": "delay", "target": "2"},
        {"action": "keyboard", "sub": "type", "target": "Hello World"}
    ]

    Available Actions:
    - Open App: {"action": "open_app", "target": "app_name"} (e.g. calculator, notepad, vscode)
    - Open Website: {"action": "open_web", "target": "url_or_name"}
    - Play Media: {"action": "play_music", "target": "song_name"}
    - Media:
        - Screenshot: {"action": "media", "sub": "screenshot"}
        - Screen Record: {"action": "media", "sub": "screen_record", "duration": 10}
        - Voice Record: {"action": "media", "sub": "voice_record", "duration": 10}
    - System Control: 
        - General: {"action": "system", "target": "shutdown/restart/sleep/battery/recycle_bin"}
        - Alarm: {"action": "system", "target": "alarm", "seconds": 60}
    - Mouse: {"action": "mouse", "sub": "move/click/right_click/scroll", "target": "up/down/left/right"}
    - Keyboard: 
        - Type: {"action": "keyboard", "sub": "type", "target": "text"}
        - Press: {"action": "keyboard", "sub": "press", "target": "key_name"}
        - Hotkey: {"action": "keyboard", "sub": "hotkey", "target": "ctrl,c"}
    - Files: 
        - Open: {"action": "file", "sub": "open", "target": "filename"}
        - Write: {"action": "file", "sub": "write", "target": "filename.ext", "content": "file_content"}
        - Read: {"action": "file", "sub": "read", "target": "filename.ext"}
        * Note: Files are written to the CURRENT PROJECT FOLDER where Tuuna is running.
    - Delay: {"action": "delay", "target": "seconds_to_wait"}
    - Memory: 
        - {"action": "memory", "sub": "save", "target": "User is a dev"}
        - {"action": "memory", "sub": "preference", "target": "Always use chrome"}
    - Learn: {"action": "learn", "target": "Lesson or correction"} (Use this when the user corrects you or an action fails. e.g. "Do not use 'start' for spotify")
    - Clipboard: {"action": "clipboard", "sub": "read"}
    - Terminal: {"action": "terminal", "target": "command_to_run"} (Use for system commands, git, pip, etc.)
    - Search: {"action": "search", "target": "search_query"} (Use when you need information from the internet)
    - Organize: {"action": "organize", "target": "downloads/desktop/path"} (Use when user says "organize my desktop" or "clean up this folder")
    - Architect: {"action": "architect", "target": "Project Name", "sub": "Description of the app"} (Use for "Build a website...", "Create a project...")
    - Protocol: {"action": "protocol", "target": "gaming/focus"} (Use for "Initiate Gaming Protocol", "Focus Mode")
    - Job Hunter: {"action": "job_hunter", "target": "Role Name"} (Use for "Apply for Python jobs", "Find me a react job")
    - Auto Apply: {"action": "auto_apply", "sub": "start/stop"} (Use for "Start auto apply", "The Closer", "Stop applying")
    - GOD MODE / Executor: {"action": "executor", "code": "python_script_here"} (Use ONLY when no other tool fits. Generates a Python script to solve the user's problem. PREFER this for 'convert files', 'scrape', 'complex math', 'data processing'.)
    - Omni-Vision: {"action": "vision_agent", "target": "instruction"} (Use for UI tasks like "Click the settings icon", "Select the second option" when specific tools don't exist.)
    - Cross-App Reasoning: {"action": "reasoning", "target": "Goal"} (Use for COMPLEX MULTI-STEP flows like "Read my email and schedule the meeting" or "Find the error in this log and fix it". This triggers a self-correcting agent loop.)

    VISION CAPABILITY:
    - You can SEE the user's screen. If the user asks "What's on my screen" or "Look at this", I will provide an image.
    - If an image is provided, analyze it and answer the user's question.

    CURRENT LONG-TERM MEMORY:
    {memory_context}

    If it is a CHAT/QUESTION (e.g. "Who is...", "Tell me a joke", "Help me write"), output a normal plain text response. Do NOT output JSON for chat.
    
    User Command: 
    """
    
    memory_context = get_memory_string()
    final_prompt = system_prompt.replace("{memory_context}", memory_context)

    # --- VISION CHECK ---
    vision_keywords = ["look", "see", "screen", "vision", "watch", "display", "monitor"]
    clipboard_keywords = ["clipboard", "copied", "paste"]
    
    content_payload = final_prompt + user_command
    
    if any(k in user_command.lower() for k in vision_keywords):
        print("👀 Vision Request Detected...")
        screenshot = get_screenshot()
        if screenshot:
            content_payload = [final_prompt + user_command, screenshot]
    elif any(k in user_command.lower() for k in clipboard_keywords):
        clip_text = get_clipboard_text()
        content_payload = final_prompt + f"\n[Clipboard Content: {clip_text}]\nUser Command: " + user_command

    # --- GENERATE & PARSE ---
    try:
        text = generate_content_with_retry(content_payload)
        
        # Try to find JSON in the response
        if "[" in text and "]" in text:
            try:
                start = text.find("[")
                end = text.rfind("]") + 1
                json_str = text[start:end]
                action_data = json.loads(json_str)
                return action_data, None # Action found
            except:
                pass 
        
        if "{" in text and "}" in text:
            try:
                start = text.find("{")
                end = text.rfind("}") + 1
                json_str = text[start:end]
                action_data = json.loads(json_str)
                return [action_data], None
            except:
                pass

        return None, text # Treat as chat
        
    except Exception as e:
        return None, f"I'm experiencing heavy traffic (Quota Exceeded) or API Error: {e}"


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/command', methods=['POST'])
def handle_command():
    data = request.json
    command = data.get('command', '').lower()
    
    print(f"🎤 Received: {command}")
    
    if not command:
        return jsonify({"response": "I didn't hear anything."})

    # ASK BRAIN
    actions, response_text = ask_gemini_brain(command)
    
    if actions:
        execution_result = execute_ai_action(actions)
        return jsonify({"response": execution_result})
    else:
        return jsonify({"response": response_text})

@app.route('/stream_logs')
def stream_logs():
    """Returns new logs since last check."""
    global LOG_BUFFER
    with LOG_LOCK:
        logs = list(LOG_BUFFER)
        LOG_BUFFER.clear() # Clear after sending to avoid duplicates
    return jsonify(logs)

if __name__ == '__main__':
    print("Tuuna Ultimate AI Server Running (Beast Mode)...")
    app.run(port=5000, debug=True, use_reloader=False)
