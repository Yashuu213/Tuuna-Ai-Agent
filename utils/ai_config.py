
import os
import time
import base64
import io
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

def get_all_api_keys():
    keys = []
    if os.getenv("GOOGLE_API_KEY"): keys.append(os.getenv("GOOGLE_API_KEY"))
    for i in range(2, 10): 
        key = os.getenv(f"GOOGLE_API_KEY_{i}")
        if key: keys.append(key)
    return keys

API_KEYS = get_all_api_keys()
AI_AVAILABLE = len(API_KEYS) > 0

MODEL_POOL = [
    'models/gemini-2.0-flash-lite', 
    'models/gemini-1.5-flash',
    'models/gemini-1.5-flash-8b',
    'models/gemini-2.0-flash'
]

def generate_content_with_retry(content_payload):
    if not AI_AVAILABLE:
        return "System Alert: AI Library not available. Please check server logs."

    last_error = ""

    # --- STRICT PAYLOAD NORMALIZATION ---
    formatted_contents = []
    try:
        parts = []
        if isinstance(content_payload, str):
            parts.append(types.Part.from_text(text=content_payload))
        elif isinstance(content_payload, list):
            for item in content_payload:
                if isinstance(item, str):
                    parts.append(types.Part.from_text(text=item))
                elif isinstance(item, dict) and "data" in item:
                    img_bytes = base64.b64decode(item['data'])
                    parts.append(types.Part.from_bytes(data=img_bytes, mime_type=item.get('mime_type', 'image/jpeg')))
                elif hasattr(item, 'save'): 
                    buf = io.BytesIO()
                    item.save(buf, format='JPEG')
                    parts.append(types.Part.from_bytes(data=buf.getvalue(), mime_type='image/jpeg'))

        if not parts: raise Exception("No valid content parts found.")
        formatted_contents = [types.Content(role='user', parts=parts)]

    except Exception as e:
        print(f"❌ Payload Formatting Error: {e}")
        return f"System Alert: Error processing input data. {e}"

    # --- EXECUTION LOOP (Smart Fallback) ---
    # Strategy: Try Primary Key with ALL models first (fastest path if key is good but model is busy)
    # Then switch to backup keys.
    
    for key_index, api_key in enumerate(API_KEYS):
        client = None
        try:
            client = genai.Client(api_key=api_key)
        except: continue

        for model_name in MODEL_POOL:
            try:
                # print(f"Trying Key #{key_index+1} with {model_name}...") # Debug noise reduced
                response = client.models.generate_content(
                    model=model_name,
                    contents=formatted_contents
                )
                
                if response and response.text:
                    return response.text.strip()
                
            except Exception as e:
                error_str = str(e)
                last_error = error_str
                
                if "429" in error_str or "Quota" in error_str:
                    print(f"⚠️ QUOTA HIT: Key #{key_index+1} / {model_name}. Trying next...")
                    time.sleep(1) # Backoff slightly
                    continue 
                else:
                    print(f"⚠️ Error on Key #{key_index+1} / {model_name}: {error_str}")
                    time.sleep(0.5)

    print("❌ CRITICAL: ALL MODELS & KEYS EXHAUSTED.")
    print(f"❌ LAST ERROR: {last_error}")
    return "System Alert: All AI models are currently busy. Please wait 1 minute and try again."
