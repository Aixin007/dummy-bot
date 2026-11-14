import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout

from google import genai
from google.genai import types

from menu import MENU, DEALS

PROMPT = """You are Dummy, the voice assistant on a McDonald's self-order kiosk in India. Everything you say is spoken out loud, so talk like a friendly, quick, slightly cheeky crew member. Use contractions and casual language. Keep replies short: one to three sentences, under 45 words. No emojis, lists, markdown or symbols. Say prices like "199 rupees".

Be a good salesperson, not a pushy one. Suggest making a burger a meal, offer a drink or dessert if they don't have one, bring up a deal when it actually saves them money, and tell them when they're close to the 499 rupee discount. Upsell once or twice per order, not every turn.

If they ask random or silly questions, answer briefly with a bit of humour and steer back to the order. Only sell what's on the menu. If they want something that isn't there, say so and offer the closest thing.

When they're done, read back the order and total and ask how they'd like to pay: card, UPI, or cash at the counter. Once they pick, do the checkout action and wrap up warmly. Set end to true after your goodbye, or if they cancel or say bye.

Messages in brackets like (customer has gone quiet) are notes from the system, not the customer.

MENU (id | name | price | category | notes)
{menu}

DEALS
{deals}

CURRENT CART
{cart}

Reply with JSON only, in this shape:
{{"say": "what you speak", "actions": [], "end": false}}

Actions:
{{"type": "add", "id": "menu_id", "qty": 1}}
{{"type": "remove", "id": "menu_id", "qty": 1}}  leave out qty to remove all of it
{{"type": "clear"}}
{{"type": "show", "category": "Burgers|Sides|Drinks|Desserts|Deals"}}
{{"type": "checkout", "payment": "card|upi|cash"}}

Only add things the customer clearly asked for or agreed to. "Make it a meal" means one meal_upgrade per burger. Use exact ids. Use show when you're talking about a category so the screen follows along."""


def menu_text():
    rows = []
    for m in MENU:
        note = m.get("desc") or ("veg" if m.get("veg") else "non-veg")
        rows.append(f"{m['id']} | {m['name']} | {m['price']} | {m['cat']} | {note}")
    return "\n".join(rows)


def parse(raw):
    match = re.search(r"\{.*\}", raw, re.S)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return {"say": raw.strip(), "actions": []}


MODELS = ["gemini-flash-lite-latest", "gemini-2.5-flash-lite", "gemini-flash-latest", "gemini-2.5-flash"]


class Brain:
    def __init__(self, cart):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        picked = (os.getenv("GEMINI_MODEL") or "").strip()
        self.models = [picked] + [m for m in MODELS if m != picked] if picked else list(MODELS)
        self.json = True
        self.pool = ThreadPoolExecutor(max_workers=4)
        self.cart = cart
        self.history = []
        self.menu = menu_text()

    def reset(self):
        self.history = []

    def call(self, model, system):
        cfg = types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.7,
            response_mime_type="application/json" if self.json else None,
        )
        return self.client.models.generate_content(model=model, contents=self.history[-20:], config=cfg)

    def ask(self, system):
        deadline = time.time() + 25
        for model in list(self.models):
            while time.time() < deadline:
                try:
                    res = self.pool.submit(self.call, model, system).result(timeout=min(12, deadline - time.time()))
                    if self.models[0] != model:
                        self.models.remove(model)
                        self.models.insert(0, model)
                        print("switched to", model)
                    return res
                except FutureTimeout:
                    print(model, "took too long")
                    break
                except Exception as e:
                    msg = str(e)
                    print(model, "failed:", msg[:300])
                    if "API key" in msg or "API_KEY" in msg or "PERMISSION_DENIED" in msg:
                        raise
                    if "400" in msg and self.json:
                        self.json = False
                        continue
                    break
        raise RuntimeError("no model answered")

    def reply(self, text):
        self.history.append(types.Content(role="user", parts=[types.Part(text=text)]))
        system = PROMPT.format(menu=self.menu, deals="\n".join(DEALS).replace("₹", ""), cart=self.cart.describe())
        try:
            start = time.time()
            res = self.ask(system)
            raw = res.text or ""
            print(f"dummy ({time.time() - start:.1f}s):", raw)
        except Exception as e:
            print("gemini error:", e)
            self.history.pop()
            if "API key" in str(e) or "API_KEY" in str(e):
                return {"say": "My API key isn't working. Check the key in the env file.", "actions": [], "end": True}
            return {"say": "Ugh, my brain lagged for a sec. Say that again?", "actions": []}
        data = parse(raw)
        if isinstance(data, list):
            data = data[0] if data and isinstance(data[0], dict) else {"say": "", "actions": []}
        self.history.append(types.Content(role="model", parts=[types.Part(text=raw)]))
        return data
