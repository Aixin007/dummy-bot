import os
import time

from dotenv import load_dotenv

load_dotenv()

import speech_recognition as sr
from google import genai

from brain import MODELS

key = os.getenv("GEMINI_API_KEY", "").strip()
print("key loaded:", bool(key) and "paste" not in key, f"({key[:6]}...)" if key else "")

client = genai.Client(api_key=key)
for model in [os.getenv("GEMINI_MODEL")] + MODELS:
    if not model:
        continue
    start = time.time()
    try:
        res = client.models.generate_content(model=model, contents="say hi in three words")
        print(f"ok   {model} ({time.time() - start:.1f}s): {res.text.strip()}")
    except Exception as e:
        print(f"fail {model}: {str(e)[:200]}")

print("\nmics:")
for i, name in enumerate(sr.Microphone.list_microphone_names()):
    print(f"  {i}: {name}")

rec = sr.Recognizer()
with sr.Microphone() as src:
    rec.adjust_for_ambient_noise(src, duration=1.5)
    print("\nroom noise level:", int(rec.energy_threshold))
    print("say something...")
    try:
        audio = rec.listen(src, timeout=6, phrase_time_limit=6)
        print("heard:", rec.recognize_google(audio, language="en-IN"))
    except Exception as e:
        print("didn't get it:", type(e).__name__, e)
