"""Generate a synthetic dataset for a fictional German online retailer.

The data is NOT real. It is produced with a fixed random seed so that
anyone who runs this script gets exactly the same four CSV files.

Usage:  python data/generate_data.py
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
START, END = date(2024, 1, 1), date(2025, 12, 31)
N_CUSTOMERS = 4000
OUT = Path(__file__).parent

CITIES = ["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt",
          "Stuttgart", "Leipzig", "Düsseldorf"]

# channel: (share of signups, chance of ever ordering, chance of ordering again)
CHANNELS = {
    "Organic":     (0.30, 0.85, 0.45),
    "Paid Search": (0.25, 0.80, 0.30),
    "Social":      (0.20, 0.70, 0.25),
    "Email":       (0.10, 0.90, 0.55),
    "Referral":    (0.15, 0.90, 0.50),
}

# category: (share of items sold, min price, max price, return probability)
CATEGORIES = {
    "Fashion":       (0.28, 20, 120, 0.22),
    "Home & Living": (0.18, 15, 200, 0.06),
    "Beauty":        (0.16, 8, 60, 0.04),
    "Books":         (0.14, 8, 35, 0.02),
    "Electronics":   (0.12, 30, 600, 0.09),
    "Sports":        (0.12, 15, 180, 0.08),
}
PRODUCTS_PER_CATEGORY = 8


def main():
    rng = random.Random(SEED)
    days = (END - START).days

    # products
    products = []
    for cat, (_, lo, hi, _) in CATEGORIES.items():
        for i in range(1, PRODUCTS_PER_CATEGORY + 1):
            price = round(rng.uniform(lo, hi)) - 0.01
            products.append([len(products) + 1, f"{cat} item {i}", cat, price])
    by_cat = {c: [p for p in products if p[2] == c] for c in CATEGORIES}

    # customers (signups grow over time)
    customers = []
    for cid in range(1, N_CUSTOMERS + 1):
        signup = START + timedelta(days=int(days * rng.random() ** 0.75))
        channel = rng.choices(list(CHANNELS), [v[0] for v in CHANNELS.values()])[0]
        customers.append([cid, signup.isoformat(), rng.choice(CITIES), channel])

    # orders and order items
    orders, items = [], []
    for cid, signup, _, channel in customers:
        _, p_first, p_repeat = CHANNELS[channel]
        if rng.random() > p_first:
            continue
        d = date.fromisoformat(signup) + timedelta(days=rng.randint(0, 10))
        while d <= END:
            # quieter months outside the Nov/Dec peak
            if d.month in (11, 12) or rng.random() < 0.75:
                oid = len(orders) + 1
                status = "cancelled" if rng.random() < 0.03 else "completed"
                orders.append([oid, cid, d.isoformat(), status])
                for _ in range(rng.choices([1, 2, 3, 4], [0.5, 0.3, 0.15, 0.05])[0]):
                    cat = rng.choices(list(CATEGORIES),
                                      [v[0] for v in CATEGORIES.values()])[0]
                    pid, _, _, price = rng.choice(by_cat[cat])
                    p_disc = 0.5 if d.month == 11 else 0.15
                    discount = rng.choice([0.10, 0.20]) if rng.random() < p_disc else 0.0
                    returned = int(status == "completed"
                                   and rng.random() < CATEGORIES[cat][3])
                    items.append([oid, pid, rng.choice([1, 1, 1, 2]), price,
                                  discount, returned])
            if rng.random() > p_repeat:
                break
            d += timedelta(days=7 + int(rng.expovariate(1 / 60)))

    def write(name, header, rows):
        with open(OUT / name, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)
        print(f"{name}: {len(rows):,} rows")

    write("customers.csv", ["customer_id", "signup_date", "city", "channel"], customers)
    write("products.csv", ["product_id", "product_name", "category", "list_price"], products)
    write("orders.csv", ["order_id", "customer_id", "order_date", "status"], orders)
    write("order_items.csv", ["order_id", "product_id", "quantity", "unit_price",
                              "discount", "is_returned"], items)


if __name__ == "__main__":
    main()
