CATEGORIES = ["Burgers", "Sides", "Drinks", "Desserts", "Deals"]

MENU = [
    {"id": "mcaloo", "name": "McAloo Tikki Burger", "price": 65, "cat": "Burgers", "veg": True},
    {"id": "mcveggie", "name": "McVeggie Burger", "price": 149, "cat": "Burgers", "veg": True},
    {"id": "spicy_paneer", "name": "McSpicy Paneer Burger", "price": 199, "cat": "Burgers", "veg": True},
    {"id": "mcchicken", "name": "McChicken Burger", "price": 139, "cat": "Burgers", "veg": False},
    {"id": "spicy_chicken", "name": "McSpicy Chicken Burger", "price": 209, "cat": "Burgers", "veg": False},
    {"id": "maharaja", "name": "Chicken Maharaja Mac", "price": 269, "cat": "Burgers", "veg": False},
    {"id": "fries_m", "name": "Fries (Medium)", "price": 109, "cat": "Sides", "veg": True},
    {"id": "fries_l", "name": "Fries (Large)", "price": 139, "cat": "Sides", "veg": True},
    {"id": "peri_fries", "name": "Peri Peri Fries", "price": 129, "cat": "Sides", "veg": True},
    {"id": "mcpuff", "name": "Veg Pizza McPuff", "price": 59, "cat": "Sides", "veg": True},
    {"id": "nuggets", "name": "Chicken McNuggets (6 pc)", "price": 179, "cat": "Sides", "veg": False},
    {"id": "coke_m", "name": "Coke (Medium)", "price": 89, "cat": "Drinks", "veg": True},
    {"id": "coke_l", "name": "Coke (Large)", "price": 109, "cat": "Drinks", "veg": True},
    {"id": "iced_tea", "name": "Lemon Iced Tea", "price": 119, "cat": "Drinks", "veg": True},
    {"id": "cold_coffee", "name": "McCafe Cold Coffee", "price": 159, "cat": "Drinks", "veg": True},
    {"id": "soft_serve", "name": "Soft Serve Cone", "price": 49, "cat": "Desserts", "veg": True},
    {"id": "mcflurry", "name": "McFlurry Oreo", "price": 119, "cat": "Desserts", "veg": True},
    {"id": "hot_fudge", "name": "Hot Fudge Sundae", "price": 89, "cat": "Desserts", "veg": True},
    {"id": "meal_upgrade", "name": "Make it a Meal", "price": 129, "cat": "Deals", "desc": "Medium fries + medium Coke with any burger"},
    {"id": "tikki_duo", "name": "McAloo Tikki Duo", "price": 99, "cat": "Deals", "desc": "Two McAloo Tikki burgers"},
    {"id": "share_box", "name": "Big Share Box", "price": 549, "cat": "Deals", "desc": "2 McChicken, 2 medium fries, 2 medium Coke"},
    {"id": "sweet_pair", "name": "Sweet Pair", "price": 139, "cat": "Deals", "desc": "McFlurry Oreo + Soft Serve Cone"},
]

BY_ID = {m["id"]: m for m in MENU}

DEALS = [
    "Make any burger a meal for just ₹129 and save ₹69",
    "McAloo Tikki Duo: two burgers for ₹99",
    "Spend ₹499 or more and get 10% off your order",
    "Big Share Box: feeds two for ₹549",
]


class Cart:
    def __init__(self):
        self.items = {}

    def add(self, item_id, qty=1):
        if item_id not in BY_ID or qty < 1:
            return False
        self.items[item_id] = self.items.get(item_id, 0) + qty
        return True

    def remove(self, item_id, qty=None):
        if item_id not in self.items:
            return False
        if qty is None or qty >= self.items[item_id]:
            del self.items[item_id]
        else:
            self.items[item_id] -= qty
        return True

    def clear(self):
        self.items = {}

    def subtotal(self):
        return sum(BY_ID[i]["price"] * q for i, q in self.items.items())

    def discount(self):
        sub = self.subtotal()
        return round(sub * 0.1) if sub >= 499 else 0

    def total(self):
        return self.subtotal() - self.discount()

    def snapshot(self):
        lines = [(i, BY_ID[i]["name"], q, BY_ID[i]["price"] * q) for i, q in self.items.items()]
        return lines, self.subtotal(), self.discount(), self.total()

    def describe(self):
        if not self.items:
            return "empty"
        rows = [f"{q} x {BY_ID[i]['name']} ({i}) = {BY_ID[i]['price'] * q} rupees" for i, q in self.items.items()]
        rows.append(f"subtotal {self.subtotal()}, discount {self.discount()}, total {self.total()} rupees")
        return "\n".join(rows)
