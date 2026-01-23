
import os
import json
import subprocess
import webbrowser
import time
import pyperclip
from duckduckgo_search import DDGS
from .ai_config import generate_content_with_retry
from .vision import get_screenshot
from .system_tools import APP_PATHS, run_terminal_command, perform_web_search, find_and_open_file
import pyautogui


def execute_python_code(code_str):
    """Writes and executes a dynamic Python script in a Docker Sandbox."""
    try:
        print("⚡ GOD MODE: Preparing Sandboxed Execution...")
        
        # Clean code (remove markdown fences)
        code_str = code_str.replace("```python", "").replace("```", "").strip()
        
        filename = "god_mode_task.py"
        cwd = os.getcwd()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code_str)

        # Check for Docker
        has_docker = False
        try:
            subprocess.run(["docker", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            has_docker = True
        except:
            has_docker = False

        if has_docker:
            print("📦 CONTAINER: Running in secure Docker sandbox...")
            # Sandbox Config
            TIMEOUT = 30 # seconds
            CPU_LIMIT = "0.5" # 50% of 1 CPU
            RAM_LIMIT = "512m" # 512MB RAM
            IMAGE = "python:3.9-slim"
            
            # Base Command
            docker_cmd = [
                "docker", "run", "--rm",
                "-v", f"{cwd}:/app",
                "-w", "/app",
                f"--cpus={CPU_LIMIT}",
                f"--memory={RAM_LIMIT}",
                IMAGE,
                "python", filename
            ]

            try:
                result = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=TIMEOUT)
                output = result.stdout + result.stderr
                
                # Auto-Heal (Docker Version)
                if "ModuleNotFoundError" in output:
                    try:
                        mod_name = output.split("No module named '")[1].split("'")[0]
                        print(f"💊 Auto-Healing (Sandbox): Installing '{mod_name}'...")
                        
                        # Re-run with install
                        heal_cmd = [
                            "docker", "run", "--rm",
                            "-v", f"{cwd}:/app",
                            "-w", "/app",
                            f"--cpus={CPU_LIMIT}",
                            f"--memory={RAM_LIMIT}",
                            IMAGE,
                            "/bin/bash", "-c", f"pip install {mod_name} && python {filename}"
                        ]
                        result = subprocess.run(heal_cmd, capture_output=True, text=True, timeout=TIMEOUT + 30)
                        output = result.stdout + result.stderr
                    except Exception as he:
                        output += f"\n[Auto-Heal Failed: {he}]"

                return f"Sandbox Result:\n{output[:2000]}"

            except subprocess.TimeoutExpired:
                return f"Sandbox Error: Execution timed out ({TIMEOUT}s)."
            except Exception as e:
                return f"Sandbox Error: {e}"

        else:
            # Fallback to Host Execution
            print("⚠️ DOCKER NOT FOUND: Running on HOST (Unsafe)...")
            result = subprocess.run(f"python {filename}", shell=True, capture_output=True, text=True)
            output = result.stdout + result.stderr
            
            # Auto-Heal (Host Version)
            if "ModuleNotFoundError" in output:
                try:
                    mod_name = output.split("No module named '")[1].split("'")[0]
                    print(f"💊 Auto-Healing: Installing missing module '{mod_name}'...")
                    subprocess.run(f"pip install {mod_name}", shell=True)
                    result = subprocess.run(f"python {filename}", shell=True, capture_output=True, text=True)
                    output = result.stdout + result.stderr
                except:
                    pass
                    
            return f"Execution Result:\n{output[:2000]}" 

    except Exception as e:
        return f"Execution Failed: {e}"

def execute_architect(project_name, description):
    """Builds a complete web project instantly."""
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        project_dir = os.path.join(desktop, project_name.replace(" ", "_"))
        
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
            
        print(f"🏗️ Architect: Building '{project_name}'...")
        
        prompt = f"""
        You are an expert Full Stack Developer.
        Create a Modern, Premium, Responsive web project for: "{description}".
        
        Return a JSON object with the code for these 3 files:
        - index.html (Modern HTML5, Tailwind or Custom CSS classes)
        - style.css (Beautiful, Glassmorphism, Dark Mode, Animations)
        - script.js (Interactive logic)
        
        OUTPUT FORMAT (JSON ONLY):
        {{
            "index.html": "<!DOCTYPE html>...",
            "style.css": "body {{ ... }}",
            "script.js": "console.log(...)"
        }}
        """
        
        text = generate_content_with_retry(prompt)
        
        start = text.find("{")
        end = text.rfind("}") + 1
        code_data = json.loads(text[start:end])
        
        for filename, content in code_data.items():
            with open(os.path.join(project_dir, filename), "w", encoding="utf-8") as f:
                f.write(content)
                
        index_path = os.path.join(project_dir, "index.html")
        webbrowser.open(f"file:///{index_path}")
        subprocess.run(f"code \"{project_dir}\"", shell=True)
        
        return f"Architect Built '{project_name}'. Opened in Browser & VS Code."
        
    except Exception as e:
        return f"Architect Failed: {e}"

def execute_protocol(protocol_type):
    """System-wide macro for Gaming or Focus."""
    try:
        protocol_type = protocol_type.lower()
        commands = []
        msg = ""

        if "gaming" in protocol_type:
            commands = [
                "taskkill /f /im code.exe",
                "taskkill /f /im teams.exe",
                "taskkill /f /im slack.exe",
                "taskkill /f /im chrome.exe",
                "start steam",
                "start discord"
            ]
            msg = "Gaming Protocol Initiated 🎮. Work apps killed."
            
        elif "focus" in protocol_type:
            commands = [
                "taskkill /f /im steam.exe", 
                "taskkill /f /im discord.exe",
                "taskkill /f /im whatsapp.exe",
                "code" 
            ]
            webbrowser.open("https://www.youtube.com/watch?v=jfKfPfyJRdk") 
            msg = "Focus Protocol Initiated 🧠. Distractions eliminated."
            
        else:
            return "Unknown Protocol. Available: 'gaming', 'focus'."

        for cmd in commands:
            try:
                subprocess.run(cmd, shell=True)
            except: pass
            
        return msg

    except Exception as e:
        return f"Protocol Failed: {e}"

def execute_job_hunter(role):
    """Automates Job Search and Cover Letter prep."""
    try:
        print(f"🏹 Job Hunter: Hunting for '{role}' roles...")
        role_lower = role.lower()
        
        only_linkedin = False
        search_keyword = role
        
        if "linkedin" in role_lower:
            only_linkedin = True
            search_keyword = role_lower.replace("on linkedin", "").replace("linkedin", "").strip()
            print(f"🎯 Specific Platform Detected: LinkedIn Only (Keyword: {search_keyword})")
        
        linkedin_url = f"https://www.linkedin.com/jobs/search/?keywords={search_keyword}&f_AL=true"
        webbrowser.open(linkedin_url)
        opened_count = 1
        
        if not only_linkedin:
            query = f"{role} jobs hiring now"
            try:
                results = DDGS().text(query, max_results=4)
                if results:
                    for r in results:
                        webbrowser.open(r['href'])
                        opened_count += 1
                        time.sleep(0.5)
            except:
                print("DuckDuckGo Search failed but LinkedIn is open.")
            
        prompt = f"""
        Write a professional, enthusiastic Cover Letter for a "{search_keyword}" position.
        The candidate is skilled, passionate, and ready to start.
        Keep it generic enough to paste into any application, but specific to the role.
        Do not include placeholders like [Your Name] in the middle, sign it as "A Passionate Developer".
        """
        
        cover_letter = generate_content_with_retry(prompt)
        pyperclip.copy(cover_letter)
        
        return f"Job Hunter: Opened {opened_count} jobs. Copied Cover Letter to Clipboard. Go apply! 🚀"
        
    except Exception as e:
        return f"Job Hunter Failed: {e}"

def execute_cognitive_chain(goal):
    """
    Experimental: Multi-Step Reasoning Loop (ReAct).
    Allows the agent to Look -> Think -> Act -> Loop.
    """
    try:
        print(f"🧠 Cognitive Chain: Starting task '{goal}'...")
        history = []
        max_steps = 10
        
        for step in range(max_steps):
            print(f"🧠 Step {step+1}/{max_steps}...")
            
            # 1. Capture State (Screen + History)
            screenshot = get_screenshot()
            
            # 2. Ask Brain
            prompt = f"""
            You are in a Cognitive Reasoning Loop.
            GOAL: {goal}
            
            HISTORY:
            {json.dumps(history, indent=2)}
            
            Analyze the screen and the history. Decide the NEXT single step.
            
            AVAILABLE TOOLS:
            - LOOK: Describe what you see on the screen (useful to read emails, errors).
            - OPEN: Open an app or website. Target: "notepad", "google.com".
            - CLICK: Click on a text/icon. Target: "Send Button", "File menu".
            - TYPE: Type text. Target: "Hello world".
            - SCROLL: Scroll down.
            - SEARCH: Google search. Target: "Query".
            - FINISH: Task is done. Target: "Summary of what you did".
            
            OUTPUT JSON ONLY:
            {{
                "thought": "I need to open the email app to find the meeting time.",
                "tool": "OPEN",
                "target": "outlook"
            }}
            """
            
            try:
                response = generate_content_with_retry([prompt, screenshot])
                start = response.find("{")
                end = response.rfind("}") + 1
                action_data = json.loads(response[start:end])
                
                thought = action_data.get("thought", "")
                tool = action_data.get("tool", "").upper()
                target = action_data.get("target", "")
                
                print(f"🤔 Thought: {thought}")
                print(f"🛠️ Tool: {tool} -> {target}")
                
                result = "Executed."
                
                # 3. Execute Tool
                if tool == "FINISH":
                    return f"Reference Chain Completed: {target}"
                    
                elif tool == "LOOK":
                    # The prompt already sees the screen, but this specific step 
                    # implies we want to record the observation into history.
                    result = f"Visual Observation: {thought}" # The LLM's thought usually contains the observation
                    
                elif tool == "OPEN":
                    if target.startswith("http"):
                        webbrowser.open(target)
                        result = f"Opened Website: {target}"
                    elif target in APP_PATHS:
                         subprocess.Popen(APP_PATHS[target], shell=True)
                         result = f"Opened App: {target}"
                    else:
                        pyautogui.press('win')
                        time.sleep(0.5)
                        pyautogui.write(target)
                        time.sleep(0.5)
                        pyautogui.press('enter')
                        result = f"Opened: {target}"
                    time.sleep(2) # Wait for load
                    
                elif tool == "CLICK":
                    # Mini Vision-Click logic
                    width, height = pyautogui.size()
                    click_prompt = f"""
                    Find the center coordinates [x, y] of the UI element described as: "{target}".
                    Image Size: {width}x{height}
                    OUTPUT JSON: {{"x": 123, "y": 456}}
                    """
                    coords_json = generate_content_with_retry([click_prompt, screenshot])
                    try:
                        c_start = coords_json.find("{")
                        c_end = coords_json.rfind("}") + 1
                        coords = json.loads(coords_json[c_start:c_end])
                        x, y = int(coords['x']), int(coords['y'])
                        pyautogui.moveTo(x, y, duration=0.5)
                        pyautogui.click()
                        result = f"Clicked '{target}' at ({x}, {y})"
                    except:
                        result = f"Could not find '{target}' on screen."

                elif tool == "TYPE":
                    pyperclip.copy(target)
                    pyautogui.hotkey('ctrl', 'v')
                    result = f"Typed: {target}"
                    
                elif tool == "SCROLL":
                    pyautogui.scroll(-500)
                    result = "Scrolled Down"
                    
                elif tool == "SEARCH":
                    result = perform_web_search(target)
                    
                else:
                    result = "Unknown Tool"

                history.append({"step": step+1, "thought": thought, "tool": tool, "result": result})
                time.sleep(1)
                
            except Exception as e:
                print(f"Chain Error: {e}")
                history.append({"step": step+1, "error": str(e)})
        
        return "Cognitive Chain timed out (Max Steps Reached)."
        
    except Exception as e:
        return f"Cognitive Chain Failed: {e}"
