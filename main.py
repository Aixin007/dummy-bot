import os
import random
import threading

from dotenv import load_dotenv

load_dotenv()

from brain import Brain
from menu import Cart
from ui import App
from voice import Voice

WAKE = ["dummy", "dummie", "dumy", "dumi", "dommy", "dami", "demi", "tummy", "dumb me", "dum"]


def woke(options):
    for text in options:
        t = text.lower()
        for w in WAKE:
            if w in t:
                rest = t.split(w, 1)[1].strip(" ,.!?")
                return rest.split(" ", 1)[1] if rest.startswith(("my ", "me ")) else rest
    return None


class Bot:
    def __init__(self, app):
        self.app = app
        self.cart = Cart()
        self.brain = None
        self.voice = None

    def ui(self, *msg):
        self.app.post(*msg)

    def run(self):
        key = os.getenv("GEMINI_API_KEY", "")
        if not key or "paste" in key:
            self.ui("error", "put your GEMINI_API_KEY in .env")
            return
        self.brain = Brain(self.cart)
        try:
            self.voice = Voice(os.getenv("VOICE") or "en-US-AndrewNeural")
        except Exception as e:
            print("mic error:", e)
            self.ui("error", "couldn't open the mic")
            return
        self.ui("state", "sleep")
        while True:
            if self.app.wake.is_set():
                self.app.wake.clear()
                self.session("")
                self.ui("state", "sleep")
                continue
            heard = self.voice.listen(timeout=2, limit=5, alts=True)
            if not heard:
                continue
            print("heard:", heard)
            rest = woke(heard)
            if rest is not None:
                self.session(rest)
                self.ui("state", "sleep")

    def talk(self, text):
        self.ui("bot", text)
        self.ui("state", "speak")
        self.voice.speak(text)

    def session(self, opener):
        self.brain.reset()
        self.cart.clear()
        self.ui("reset")
        self.ui("cart", self.cart.snapshot())
        text = opener or "(customer just walked up and said hey dummy)"
        quiet = 0
        while True:
            if text:
                if not text.startswith("("):
                    self.ui("you", text)
                self.ui("state", "think")
                data = self.brain.reply(text)
                self.apply(data.get("actions") or [])
                if data.get("say"):
                    self.talk(data["say"])
                if data.get("end"):
                    return
            self.ui("state", "listen")
            heard = self.voice.listen(timeout=8, limit=15)
            print("you:", heard)
            if heard is None:
                quiet += 1
                if quiet >= 3:
                    self.talk("Alright, I'll be right here. Just say hey dummy when you're hungry.")
                    return
                text = "(customer has gone quiet)" if quiet == 2 else None
            elif heard == "":
                self.talk(random.choice(["Sorry, didn't catch that.", "Come again?", "One more time?"]))
                text = None
            else:
                quiet = 0
                text = heard

    def apply(self, actions):
        for a in actions:
            if not isinstance(a, dict):
                continue
            kind = a.get("type")
            qty = a.get("qty")
            try:
                qty = int(qty) if qty is not None else None
            except (TypeError, ValueError):
                qty = None
            if kind == "add":
                self.cart.add(a.get("id"), qty or 1)
            elif kind == "remove":
                self.cart.remove(a.get("id"), qty)
            elif kind == "clear":
                self.cart.clear()
            elif kind == "show":
                self.ui("category", a.get("category"))
            elif kind == "checkout" and self.cart.items:
                pay = {"upi": "UPI", "card": "card", "cash": "pay at counter"}.get(str(a.get("payment", "")).lower(), "pay at counter")
                self.ui("checkout", {"number": random.randint(100, 999), "total": self.cart.total(), "payment": pay})
        self.ui("cart", self.cart.snapshot())


def main():
    app = App()
    bot = Bot(app)
    threading.Thread(target=bot.run, daemon=True).start()
    app.root.mainloop()


if __name__ == "__main__":
    main()
