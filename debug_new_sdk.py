
import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

def get_all_keys():
    keys = []
    if os.getenv("GOOGLE_API_KEY"): keys.append(os.getenv("GOOGLE_API_KEY"))
    for i in range(2, 10):
        k = os.getenv(f"GOOGLE_API_KEY_{i}")
        if k: keys.append(k)
    return keys

all_keys = get_all_keys()
print(f"Found {len(all_keys)} keys in env.")

for idx, key in enumerate(all_keys):
    print(f"\n--- Testing Key #{idx+1} ({key[:5]}...) ---")
    try:
        client = genai.Client(api_key=key)
        print("✅ SUCCESS! Working Key Found.")
        found_15 = False
        all_mods = []
        for m in client.models.list():
            all_mods.append(m.name)
            if "gemini-1.5-flash" in m.name:
                print(f"🎯 FOUND IT: {m.name}")
                found_15 = True
        
        if not found_15:
            print("⚠️ 1.5-Flash NOT found. Listing all:")
            for n in all_mods[:10]:
                print(f" - {n}")
        break 
    except Exception as e:


        print(f"❌ Key Failed: {e}")

