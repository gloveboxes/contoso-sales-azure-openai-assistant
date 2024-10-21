import random

main_categories = {
    "APPAREL": {
        "JACKETS & VESTS": [50, 250],
        "OTHER": [10, 100],
        "PANTS & SHORTS": [30, 120],
        "SHIRTS": [20, 80],
        "TOPS": [15, 60],
        "UNDERWEAR & BASE LAYERS": [10, 50],
        "FOOTWEAR ACCESSORIES": [5, 50],  # Added
        "OUTERWEAR": [60, 300],  # Added
        "GLOVES & HATS": [10, 50],  # Added
    },
    "CAMPING & HIKING": {
        "BACKPACKING TENTS": [100, 500],
        "BIVYS": [50, 200],
        "COOKWARE": [20, 150],
        "DAYPACKS": [30, 150],
        "EXTENDED TRIP PACKS": [150, 400],
        "FAMILY CAMPING TENTS": [200, 800],
        "FOOD & NUTRITION": [5, 50],
        "HAMMOCKS": [30, 150],
        "HYDRATION PACKS": [40, 120],
        "LINERS": [10, 60],
        "OTHER": [5, 100],
        "OVERNIGHT PACKS": [80, 250],
        "SHELTERS & TARPS": [40, 200],
        "SLEEPING BAGS": [60, 300],
        "SLEEPING PADS": [30, 150],
        "STOVES": [20, 150],
        "UTENSILS & ACCESSORIES": [5, 50],
        "WATER FILTRATION & PURIFICATION": [10, 100],  # Added
        "NAVIGATION TOOLS": [20, 150],  # Added
        "FIRST AID KITS": [10, 60],  # Added
    },
    "CLIMBING": {
        "AVALANCHE SAFETY": [100, 500],
        "CARABINERS & QUICKDRAWS": [5, 50],
        "CHALK & CHALK BAGS": [5, 30],
        "CLIMBING SHOES": [60, 200],
        "CRAMPONS": [100, 300],
        "HARNESSES": [50, 200],
        "HELMETS": [40, 150],
        "ICE AXES": [50, 300],
        "MOUNTAINEERING BOOTS": [150, 500],
        "OTHER": [10, 100],
        "ROPES & SLINGS": [30, 300],
        "TRAINING EQUIPMENT": [20, 150],
        "SLACKLINES": [30, 150],  # Added
        "BOULDERING PADS": [100, 400],  # Added
    },
    "FOOTWEAR": {
        "HIKING BOOTS": [60, 250],
        "OTHER": [20, 100],
        "SANDALS": [20, 80],
        "TRAIL SHOES": [50, 150],
        "WINTER BOOTS": [60, 200],
        "INSULATED FOOTWEAR": [80, 250],  # Added
        "FOOTWEAR CARE PRODUCTS": [5, 30],  # Added
    },
    "TRAVEL": {
        "CARRY-ONS": [50, 200],
        "DUFFEL BAGS": [30, 150],
        "EYE MASKS": [5, 20],
        "OTHER": [5, 50],
        "PACKING ORGANIZERS": [10, 50],
        "SECURITY": [10, 100],
        "TRAVEL ACCESSORIES": [5, 80],
        "TRAVEL BACKPACKS": [30, 200],
        "TRAVEL PILLOWS": [10, 40],
        "TECH ORGANIZERS": [15, 60],  # Added
        "LUGGAGE LOCKS": [5, 20],  # Added
    },
    "WATER GEAR": {
        "ACCESSORIES": [10, 50],
        "CANOES": [300, 1200],
        "KAYAKS": [200, 1000],
        "PADDLES": [20, 150],
        "RASH GUARDS": [20, 80],
        "SAFETY GEAR": [20, 100],
        "SURF ACCESSORIES": [10, 100],
        "SURFBOARDS": [500, 800],
        "WETSUITS": [250, 500],
        "DRY BAGS": [20, 100],
        "SNORKELING & DIVING GEAR": [30, 800],
        "SWIMWEAR": [20, 80],
    },
    "FISHING GEAR": {
        "RODS & REELS": [30, 200],
        "TACKLE": [5, 50],
        "WADERS": [150, 250],
        "SAFETY GEAR": [20, 100],
        "ACCESSORIES": [10, 100],
        "FISHING LINE": [10, 50],
        "FISHING HOOKS": [5, 30],
        "FISHING BAIT": [5, 50],
    },
    "WINTER SPORTS": {
        "ACCESSORIES": [10, 100],
        "BINDINGS": [250, 600],
        "HELMETS": [200, 450],
        "OTHER": [10, 100],
        "POLES": [20, 100],
        "SKI BINDINGS": [100, 500],
        "SKI BOOTS": [500, 800],
        "SKI POLES": [100, 200],
        "SKIS": [600, 1200],
        "SNOWBOARD BOOTS": [100, 300],
        "SNOWBOARDS": [700, 1100],
        "SNOWSHOES": [50, 200],
        "GOGGLES": [150, 250],  # Added
        "THERMAL UNDERWEAR": [30, 100],  # Added
        "GLOVES & MITTENS": [50, 150],  # Added
    },
}

regions = [
    "AFRICA",
    "ASIA-PACIFIC",
    "EUROPE",
    "EUROPE",
    "MIDDLE EAST",
    "NORTH AMERICA",
    "NORTH AMERICA",
    "NORTH AMERICA",
    "LATIN AMERICA",
    "CHINA",
    "CHINA",
]
# years = [2020, 2021, 2022, 2023, 2024]
# growth_factors = [1.0, 1.05, 1.1, 1.15, 1.2]


years_growth = [(2022, .98), (2023, 1.01), (2024, 1.05)]


def generate_sql_insert():
    insert_statements = []

    for _ in range(40000):
        yg = random.choice(years_growth)
        growth_factor = yg[1]
        year = yg[0]
        month = random.randint(1, 12)
        region = random.choice(regions)

        main_category = random.choice(list(main_categories.keys()))
        product_category = main_categories[main_category]
        product_type = random.choice(list(product_category.keys()))
        price_range = product_category[product_type]

        number_of_orders = int(random.randint(1, 20) * growth_factor)
        revenue = random.randint(price_range[0], price_range[1]) * number_of_orders

        shipping_cost_percentage = random.randint(10, 20) / 100.0
        shipping_cost = shipping_cost_percentage * revenue

        discount_percentage = random.randint(0, 15)
        discount_decimal = discount_percentage / 100.0
        discount = discount_decimal * revenue

        month_date = f"{year}-{str(month).zfill(2)}"

        insert_statements.append(
            f"INSERT INTO sales_data (main_category, product_type, revenue, shipping_cost, number_of_orders, year, month, discount, region, month_date) "
            f"VALUES ('{main_category}', '{product_type}', {revenue}, {shipping_cost}, {number_of_orders}, {year}, {month}, {discount}, '{region}', '{month_date}');"
        )

    return "\n".join(insert_statements)


sql_script = f"""
-- Create the table
CREATE TABLE IF NOT EXISTS sales_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    main_category TEXT,
    product_type TEXT,
    revenue REAL,
    shipping_cost REAL,
    number_of_orders INTEGER,
    year INTEGER,
    month INTEGER,
    discount INTEGER,
    region TEXT,
    month_date TEXT
);

CREATE INDEX idx_main_category ON sales_data(main_category);
CREATE INDEX idx_product_type ON sales_data(product_type);
CREATE INDEX idx_region ON sales_data(region);
CREATE INDEX idx_year ON sales_data(year);
CREATE INDEX idx_month_date ON sales_data(month_date);

-- Insert random records into the table
{generate_sql_insert()}
"""

# Write the SQL script to a file
with open("populate_sales_data.sql", "w") as file:
    file.write(sql_script)

print("SQL script has been written to 'populate_sales_data.sql'")
