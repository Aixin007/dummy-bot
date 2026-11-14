import math
import queue
import threading
import time
import tkinter as tk

from menu import MENU, DEALS, CATEGORIES, BY_ID

BG = "#07070d"
PANEL = "#0f0f1a"
CREAM = "#f6f3ee"
RED = "#da291c"
YELLOW = "#ffc72c"
INK = "#27251f"
FONT = "Segoe UI"

COLORS = {
    "boot": "#2b3f6b",
    "sleep": "#3a6fd8",
    "listen": "#36c5ff",
    "think": "#8b7bff",
    "speak": "#4fe3c1",
}

STATUS = {
    "boot": "warming up...",
    "sleep": 'say "Hey Dummy" or press space',
    "listen": "listening...",
    "think": "thinking...",
    "speak": "",
}


def mix(a, b, f):
    a = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    f = max(0, min(1, f))
    return "#" + "".join(f"{int(x + (y - x) * f):02x}" for x, y in zip(a, b))


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Dummy")
        self.root.geometry("1380x800")
        self.root.minsize(1200, 720)
        self.root.configure(bg=BG)
        self.root.bind("<Escape>", lambda e: self.root.destroy())
        self.q = queue.Queue()
        self.wake = threading.Event()
        self.root.bind("<space>", lambda e: self.wake.set() if self.state == "sleep" else None)
        self.state = "boot"
        self.start = time.time()
        self.cat = None
        self.cards = {}
        self.last = {}
        self.deal_i = 0
        self.overlay = None
        self.build()
        self.show(CATEGORIES[0])
        self.set_cart(([], 0, 0, 0))
        self.rotate_deal()
        self.clock_tick()
        self.tick()
        self.poll()

    def post(self, *msg):
        self.q.put(msg)

    def build(self):
        left = tk.Frame(self.root, bg=BG, width=440)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        self.orb = tk.Canvas(left, width=440, height=400, bg=BG, highlightthickness=0)
        self.orb.pack(pady=(10, 0))

        self.status = tk.Label(left, text=STATUS["boot"], fg="#8fb8ff", bg=BG, font=(FONT, 15))
        self.status.pack()

        self.log = tk.Text(left, bg=PANEL, fg="#d6d6e0", font=(FONT, 11), wrap="word", bd=0,
                           padx=16, pady=12, highlightthickness=0, cursor="arrow")
        self.log.pack(fill="both", expand=True, padx=22, pady=22)
        self.log.tag_config("you", foreground=YELLOW, font=(FONT, 10, "bold"))
        self.log.tag_config("bot", foreground="#7fd4ff", font=(FONT, 10, "bold"))
        self.log.tag_config("line", foreground="#3a3a50")
        self.log.config(state="disabled")

        self.kiosk = tk.Frame(self.root, bg=CREAM)
        self.kiosk.pack(side="left", fill="both", expand=True, padx=(0, 22), pady=22)

        head = tk.Frame(self.kiosk, bg=RED, height=72)
        head.pack(fill="x")
        head.pack_propagate(False)
        tk.Label(head, text="McDonald's", fg="white", bg=RED, font=(FONT, 22, "bold")).pack(side="left", padx=(22, 8))
        tk.Label(head, text="self order", fg=YELLOW, bg=RED, font=(FONT, 13)).pack(side="left", pady=(8, 0))
        self.clock = tk.Label(head, text="", fg="white", bg=RED, font=(FONT, 13))
        self.clock.pack(side="right", padx=22)

        self.deal_bar = tk.Label(self.kiosk, text="", bg=YELLOW, fg=INK, font=(FONT, 12, "bold"), pady=9)
        self.deal_bar.pack(fill="x", side="bottom")

        tabs = tk.Frame(self.kiosk, bg=CREAM)
        tabs.pack(fill="x", padx=18, pady=(16, 4))
        self.tabs = {}
        for c in CATEGORIES:
            lbl = tk.Label(tabs, text=c, font=(FONT, 12, "bold"), padx=18, pady=8, cursor="hand2")
            lbl.pack(side="left", padx=4)
            lbl.bind("<Button-1>", lambda e, c=c: self.show(c))
            self.tabs[c] = lbl

        body = tk.Frame(self.kiosk, bg=CREAM)
        body.pack(fill="both", expand=True, padx=18, pady=12)

        self.grid = tk.Frame(body, bg=CREAM)
        self.grid.pack(side="left", fill="both", expand=True)

        cartbox = tk.Frame(body, bg="white", width=290)
        cartbox.pack(side="right", fill="y", padx=(14, 0))
        cartbox.pack_propagate(False)
        tk.Label(cartbox, text="Your order", bg="white", fg=INK, font=(FONT, 15, "bold")).pack(anchor="w", padx=18, pady=(16, 8))
        self.cart_list = tk.Frame(cartbox, bg="white")
        self.cart_list.pack(fill="both", expand=True, padx=18)
        tk.Frame(cartbox, bg="#ece6dc", height=1).pack(fill="x", padx=18, pady=8)
        self.totals = tk.Label(cartbox, text="", bg="white", fg="#6b655b", font=(FONT, 11), justify="right", anchor="e")
        self.totals.pack(fill="x", padx=18)
        self.total_big = tk.Label(cartbox, text="", bg="white", fg=RED, font=(FONT, 26, "bold"), anchor="e")
        self.total_big.pack(fill="x", padx=18, pady=(2, 18))

    def show(self, cat):
        if cat not in self.tabs:
            return
        self.cat = cat
        for c, lbl in self.tabs.items():
            on = c == cat
            lbl.config(bg=RED if on else "#e8e2d8", fg="white" if on else INK)
        for w in self.grid.winfo_children():
            w.destroy()
        self.cards = {}
        items = [m for m in MENU if m["cat"] == cat]
        for n, m in enumerate(items):
            card = tk.Frame(self.grid, bg="white", padx=16, pady=14, highlightthickness=3,
                            highlightbackground="white", highlightcolor="white")
            card.grid(row=n // 3, column=n % 3, sticky="nsew", padx=6, pady=6)
            tk.Label(card, text=m["name"], bg="white", fg=INK, font=(FONT, 12, "bold"),
                     wraplength=170, justify="left").pack(anchor="w")
            if m.get("desc"):
                tk.Label(card, text=m["desc"], bg="white", fg="#8a8378", font=(FONT, 10),
                         wraplength=170, justify="left").pack(anchor="w", pady=(4, 0))
            elif "veg" in m:
                tk.Label(card, text="veg" if m["veg"] else "non-veg", bg="white",
                         fg="#2e8b3e" if m["veg"] else "#b3261e", font=(FONT, 9, "bold")).pack(anchor="w", pady=(4, 0))
            tk.Label(card, text=f"₹{m['price']}", bg="white", fg=RED, font=(FONT, 14, "bold")).pack(anchor="w", pady=(10, 0))
            self.cards[m["id"]] = card
        for c in range(3):
            self.grid.columnconfigure(c, weight=1, uniform="col")

    def highlight(self, item_id):
        cat = BY_ID[item_id]["cat"]
        if cat != self.cat:
            self.show(cat)
        card = self.cards.get(item_id)
        if not card:
            return
        card.config(highlightbackground=YELLOW, highlightcolor=YELLOW)
        self.root.after(1600, lambda: card.winfo_exists() and card.config(highlightbackground="white", highlightcolor="white"))

    def set_cart(self, snap):
        lines, sub, disc, total = snap
        now = {i: q for i, _, q, _ in lines}
        added = [i for i, q in now.items() if q > self.last.get(i, 0)]
        self.last = now
        for w in self.cart_list.winfo_children():
            w.destroy()
        if not lines:
            tk.Label(self.cart_list, text="Nothing here yet", bg="white", fg="#a39d92", font=(FONT, 11)).pack(anchor="w", pady=6)
        for i, name, q, amt in lines:
            row = tk.Frame(self.cart_list, bg="white")
            row.pack(fill="x", pady=4)
            tk.Label(row, text=f"₹{amt}", bg="white", fg=INK, font=(FONT, 11, "bold")).pack(side="right")
            tk.Label(row, text=f"{q} × {name}", bg="white", fg=INK, font=(FONT, 11),
                     wraplength=180, justify="left", anchor="w").pack(side="left")
        text = f"Subtotal  ₹{sub}"
        if disc:
            text += f"\n10% off  −₹{disc}"
        elif sub:
            text += f"\n₹{499 - sub} more for 10% off"
        self.totals.config(text=text)
        self.total_big.config(text=f"₹{total}")
        if added:
            self.highlight(added[-1])

    def write(self, who, text):
        self.log.config(state="normal")
        if who == "line":
            self.log.insert("end", "─" * 34 + "\n\n", "line")
        else:
            self.log.insert("end", ("YOU" if who == "you" else "DUMMY") + "\n", who)
            self.log.insert("end", text + "\n\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def checkout(self, info):
        self.clear_overlay()
        box = tk.Frame(self.kiosk, bg=RED)
        box.place(relx=0, rely=0, relwidth=1, relheight=1)
        tk.Label(box, text="Order placed!", fg="white", bg=RED, font=(FONT, 30, "bold")).pack(pady=(170, 6))
        tk.Label(box, text=f"#{info['number']}", fg=YELLOW, bg=RED, font=(FONT, 72, "bold")).pack()
        tk.Label(box, text=f"₹{info['total']}  ·  {info['payment']}", fg="white", bg=RED, font=(FONT, 16)).pack(pady=8)
        tk.Label(box, text="grab a seat, we'll call your number", fg="#ffd9d4", bg=RED, font=(FONT, 13)).pack()
        self.overlay = box
        self.root.after(10000, self.clear_overlay)

    def clear_overlay(self):
        if self.overlay and self.overlay.winfo_exists():
            self.overlay.destroy()
        self.overlay = None

    def rotate_deal(self):
        self.deal_bar.config(text="★  " + DEALS[self.deal_i % len(DEALS)] + "  ★")
        self.deal_i += 1
        self.root.after(5000, self.rotate_deal)

    def clock_tick(self):
        self.clock.config(text=time.strftime("%I:%M %p").lstrip("0"))
        self.root.after(1000, self.clock_tick)

    def poll(self):
        try:
            while True:
                kind, *rest = self.q.get_nowait()
                if kind == "state":
                    self.state = rest[0]
                    self.status.config(text=STATUS.get(self.state, ""), fg=mix(COLORS.get(self.state, "#8fb8ff"), "#ffffff", 0.35))
                elif kind == "error":
                    self.status.config(text=rest[0], fg="#ff6b6b")
                elif kind in ("you", "bot"):
                    self.write(kind, rest[0])
                elif kind == "cart":
                    self.set_cart(rest[0])
                elif kind == "category":
                    self.show(rest[0])
                elif kind == "checkout":
                    self.checkout(rest[0])
                elif kind == "reset":
                    self.clear_overlay()
                    self.write("line", "")
                    self.show(CATEGORIES[0])
        except queue.Empty:
            pass
        self.root.after(40, self.poll)

    def glow(self, cx, cy, r, color, w):
        c = self.orb
        for i in range(9, 0, -1):
            col = mix(color, BG, 0.45 + i * 0.06)
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=col, width=w + i * 5)
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=mix(color, "#ffffff", 0.25), width=w)
        c.create_oval(cx - r + w, cy - r + w, cx + r - w, cy + r - w, outline=mix(color, BG, 0.75), width=2)

    def ripples(self, cx, cy, r, color, speed, spread):
        t = time.time() - self.start
        for i in range(3):
            p = (t * speed + i / 3) % 1
            rr = r + p * spread
            self.orb.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline=mix(color, BG, 0.3 + p * 0.7), width=2)

    def tick(self):
        t = time.time() - self.start
        c = self.orb
        c.delete("all")
        cx, cy = 220, 200
        s = self.state
        color = COLORS.get(s, COLORS["sleep"])
        if s in ("sleep", "boot"):
            k = 0.5 + 0.5 * math.sin(t * 1.3)
            self.glow(cx, cy, 92 + 5 * k, mix(color, BG, 0.45 - k * 0.3), 8)
        elif s == "listen":
            k = 0.5 + 0.5 * math.sin(t * 5)
            r = 100 + 7 * k
            self.ripples(cx, cy, r, color, 0.7, 85)
            self.glow(cx, cy, r, color, 12)
        elif s == "think":
            self.glow(cx, cy, 98, color, 10)
            for i in range(3):
                start = (t * 260 + i * 120) % 360
                c.create_arc(cx - 128, cy - 128, cx + 128, cy + 128, start=start, extent=65,
                             style="arc", outline=mix(color, "#ffffff", 0.3), width=4)
        elif s == "speak":
            amp = abs(math.sin(t * 9)) * 0.6 + abs(math.sin(t * 13.7)) * 0.4
            r = 100 + 15 * amp
            self.ripples(cx, cy, r, color, 1.2, 70)
            self.glow(cx, cy, r, color, 12 + int(amp * 6))
        self.root.after(16, self.tick)
