
import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Updated Pool
MODEL_POOL = [
    'models/gemini-2.0-flash-lite', 
    'models/gemini-1.5-flash',
    'models/gemini-1.5-flash-8b',
    'models/gemini-2.0-flash'
]

def test_key(key, index):
    if not key: return
    masked = key[:6] + "..." + key[-4:]
    print(f"\n🔍 Testing Key #{index}: {masked} against ALL models...")
    
    client = genai.Client(api_key=key)
    
    for model in MODEL_POOL:
        try:
            print(f"   👉 Testing {model}...", end="\r")
            response = client.models.generate_content(
                model=model,
                contents='Hello'
            )
            print(f"   ✅ {model}: WORKING!             ")
            return # Stop after first success per key if you just want to know if key allows ANY access
        except Exception as e:
            if "429" in str(e):
                print(f"   ⚠️ {model}: QUOTA HIT          ")
            else:
                print(f"   ❌ {model}: FAILED ({e})")

# Test Primary
test_key(os.getenv("GOOGLE_API_KEY"), 1)

# Test Others
for i in range(2, 10):
    k = os.getenv(f"GOOGLE_API_KEY_{i}")
    if k: test_key(k, i)
