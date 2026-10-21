"""Enterprise Data Warehouse Synthetic Seed Generator.

Populates realistic enterprise OLAP datasets for:
1. Retail Store Operations & Omni-channel Sales
2. AppleCare Hardware Telemetry & Warranty Repairs
3. Global Supply Chain & Component Logistics
4. Internet Services & Subscription MRR
"""

from datetime import datetime, timedelta
import random
from typing import Dict, List, Tuple
import pandas as pd


def generate_retail_data(num_days: int = 90) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generates retail stores, daily store sales, and inventory levels."""
    random.seed(42)
    
    stores = [
        {"store_id": "R001", "store_name": "Apple Regent Street", "market": "London", "country": "UK", "region": "EMEIA", "square_feet": 25000, "genius_bar_bays": 24},
        {"store_id": "R002", "store_name": "Apple Fifth Avenue", "market": "New York", "country": "USA", "region": "Americas", "square_feet": 32000, "genius_bar_bays": 36},
        {"store_id": "R003", "store_name": "Apple BKC", "market": "Mumbai", "country": "India", "region": "APAC", "square_feet": 20000, "genius_bar_bays": 18},
        {"store_id": "R004", "store_name": "Apple Marina Bay Sands", "market": "Singapore", "country": "Singapore", "region": "APAC", "square_feet": 18000, "genius_bar_bays": 16},
        {"store_id": "R005", "store_name": "Apple Shibuya", "market": "Tokyo", "country": "Japan", "region": "APAC", "square_feet": 19000, "genius_bar_bays": 16},
        {"store_id": "R006", "store_name": "Apple Champs-Élysées", "market": "Paris", "country": "France", "region": "EMEIA", "square_feet": 22000, "genius_bar_bays": 20},
        {"store_id": "R007", "store_name": "Apple Union Square", "market": "San Francisco", "country": "USA", "region": "Americas", "square_feet": 26000, "genius_bar_bays": 28},
        {"store_id": "R008", "store_name": "Apple Sanlitun", "market": "Beijing", "country": "China", "region": "Greater China", "square_feet": 28000, "genius_bar_bays": 30},
    ]
    df_stores = pd.DataFrame(stores)
    
    products = [
        {"product_id": "PROD_IPHONE16P", "product_name": "iPhone 16 Pro 256GB", "product_line": "iPhone", "unit_price": 1099.0, "unit_cost": 540.0},
        {"product_id": "PROD_IPHONE16PM", "product_name": "iPhone 16 Pro Max 512GB", "product_line": "iPhone", "unit_price": 1399.0, "unit_cost": 650.0},
        {"product_id": "PROD_MBA_M3", "product_name": "MacBook Air 15-inch M3", "product_line": "Mac", "unit_price": 1299.0, "unit_cost": 720.0},
        {"product_id": "PROD_MBP_M4", "product_name": "MacBook Pro 16-inch M4 Pro", "product_line": "Mac", "unit_price": 2499.0, "unit_cost": 1350.0},
        {"product_id": "PROD_IPAD_M4", "product_name": "iPad Pro 13-inch M4 OLED", "product_line": "iPad", "unit_price": 1299.0, "unit_cost": 690.0},
        {"product_id": "PROD_WATCH_U2", "product_name": "Apple Watch Ultra 2", "product_line": "Wearables", "unit_price": 799.0, "unit_cost": 390.0},
        {"product_id": "PROD_AIRPODS_P2", "product_name": "AirPods Pro (2nd Gen USB-C)", "product_line": "Wearables", "unit_price": 249.0, "unit_cost": 110.0},
        {"product_id": "PROD_VISION_PRO", "product_name": "Apple Vision Pro 512GB", "product_line": "Vision", "unit_price": 3699.0, "unit_cost": 2100.0},
    ]
    
    sales_rows = []
    inventory_rows = []
    start_date = datetime.now() - timedelta(days=num_days)
    
    sale_id = 100000
    for day_offset in range(num_days):
        current_date = (start_date + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        day_of_week = (start_date + timedelta(days=day_offset)).weekday()
        weekend_mult = 1.45 if day_of_week in [4, 5, 6] else 1.0
        
        for store in stores:
            for prod in products:
                base_units = random.randint(4, 30)
                if prod["product_line"] == "iPhone":
                    base_units *= 2
                elif prod["product_line"] == "Vision":
                    base_units = random.randint(0, 3)
                
                units_sold = int(base_units * weekend_mult)
                gross_rev = round(units_sold * prod["unit_price"], 2)
                discount = round(gross_rev * (0.03 if random.random() < 0.2 else 0.0), 2)
                net_rev = gross_rev - discount
                trade_ins = random.randint(0, int(units_sold * 0.4))
                
                sales_rows.append({
                    "sale_id": f"S{sale_id}",
                    "sale_date": current_date,
                    "store_id": store["store_id"],
                    "product_id": prod["product_id"],
                    "product_line": prod["product_line"],
                    "units_sold": units_sold,
                    "gross_revenue_usd": gross_rev,
                    "discount_amount": discount,
                    "net_revenue_usd": net_rev,
                    "trade_in_units": trade_ins
                })
                sale_id += 1
                
                # Snapshot inventory on weekly intervals or final day
                if day_offset % 7 == 0 or day_offset == num_days - 1:
                    stock_level = random.randint(15, 250)
                    inventory_rows.append({
                        "inventory_snapshot_date": current_date,
                        "store_id": store["store_id"],
                        "product_id": prod["product_id"],
                        "stock_on_hand": stock_level,
                        "reorder_threshold": 30,
                        "days_of_supply": round(stock_level / max(1, units_sold), 1)
                    })
                    
    df_sales = pd.DataFrame(sales_rows)
    df_inventory = pd.DataFrame(inventory_rows)
    return df_stores, df_sales, df_inventory


def generate_applecare_data(num_records: int = 1200) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generates AppleCare repair tickets and replacement parts inventory."""
    random.seed(42)
    
    device_categories = ["iPhone", "Mac", "iPad", "Apple Watch", "Vision Pro"]
    subsystems = {
        "iPhone": ["OLED Display", "Battery", "TrueDepth Camera", "Taptic Engine", "Logic Board"],
        "Mac": ["Liquid Retina XDR Display", "Battery", "Logic Board / M-Series SoC", "Keyboard / Top Case", "Thermal Fan"],
        "iPad": ["Liquid Retina Display", "USB-C Port Assembly", "Battery", "Pencil Digitizer"],
        "Apple Watch": ["Ion-X Glass", "Heart Sensor Assembly", "Battery", "Digital Crown"],
        "Vision Pro": ["EyeSight Outer OLED", "Dual 4K Micro-OLED", "Audio Strap", "Battery Pack Cable"]
    }
    
    issues = ["Kernel Panic", "Battery Degradation", "Display Artifact / Vertical Line", "Thermal Throttling", "Port Failure", "Water Ingress"]
    warranty_types = ["AppleCare+", "Standard 1-Year Limited", "Out-of-Warranty"]
    
    start_date = datetime.now() - timedelta(days=120)
    incident_rows = []
    
    for i in range(num_records):
        dev = random.choice(device_categories)
        sub = random.choice(subsystems[dev])
        issue = random.choice(issues)
        warr = random.choices(warranty_types, weights=[0.55, 0.35, 0.10])[0]
        
        # Turnaround time in hours (Genius Bar same-day vs Depot Repair)
        tat = round(random.uniform(1.5, 72.0), 1)
        repair_cost = 0.0 if warr == "AppleCare+" else round(random.uniform(79.0, 699.0), 2)
        csat = random.choices([5, 4, 3, 2, 1], weights=[0.60, 0.25, 0.08, 0.04, 0.03])[0]
        
        inc_date = (start_date + timedelta(days=random.randint(0, 120))).strftime("%Y-%m-%d")
        
        incident_rows.append({
            "incident_id": f"AC-{100000 + i}",
            "created_date": inc_date,
            "device_category": dev,
            "subsystem": sub,
            "issue_diagnostic_code": issue,
            "warranty_status": warr,
            "turnaround_time_hrs": tat,
            "repair_cost_usd": repair_cost,
            "customer_satisfaction_score": csat,
            "channel": random.choice(["Genius Bar Retail", "Mail-in Depot", "Apple Authorized Service Provider"])
        })
        
    df_incidents = pd.DataFrame(incident_rows)
    
    parts_rows = [
        {"part_sku": "PART-IPH-DISP", "part_name": "iPhone 16 Pro OLED Module", "compatible_device": "iPhone", "warehouse_stock": 14200, "allocated_stock": 2100, "supplier": "Samsung Display / LG Display"},
        {"part_sku": "PART-IPH-BATT", "part_name": "iPhone High-Density Battery Cell", "compatible_device": "iPhone", "warehouse_stock": 25800, "allocated_stock": 3400, "supplier": "Sunwoda Electronic"},
        {"part_sku": "PART-MAC-LOGIC", "part_name": "MacBook Pro M4 Logic Board Assm", "compatible_device": "Mac", "warehouse_stock": 3800, "allocated_stock": 450, "supplier": "Foxconn Assembly"},
        {"part_sku": "PART-MAC-DISP", "part_name": "Liquid Retina XDR Display Assm", "compatible_device": "Mac", "warehouse_stock": 5100, "allocated_stock": 620, "supplier": "LG Display"},
        {"part_sku": "PART-VIS-MICRO", "part_name": "Micro-OLED High-DPI Engine Pair", "compatible_device": "Vision Pro", "warehouse_stock": 850, "allocated_stock": 110, "supplier": "Sony Semiconductor"},
    ]
    df_parts = pd.DataFrame(parts_rows)
    return df_incidents, df_parts


def generate_supply_chain_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generates component suppliers and inbound logistics shipments."""
    random.seed(42)
    
    suppliers = [
        {"supplier_id": "SUP-01", "supplier_name": "TSMC", "country": "Taiwan", "tier": "Tier-1 Strategic", "category": "Silicon Wafer / N3E Foundry"},
        {"supplier_id": "SUP-02", "supplier_name": "Foxconn Technology Group", "country": "Taiwan/China/India", "tier": "Tier-1 Assembly", "category": "Final Product Assembly"},
        {"supplier_id": "SUP-03", "supplier_name": "LG Display", "country": "South Korea", "tier": "Tier-1 Strategic", "category": "Tandem OLED Panels"},
        {"supplier_id": "SUP-04", "supplier_name": "Sony Semiconductor", "country": "Japan", "tier": "Tier-1 Strategic", "category": "CMOS Image Sensors & Micro-OLED"},
        {"supplier_id": "SUP-05", "supplier_name": "Murata Manufacturing", "country": "Japan", "tier": "Tier-2 Component", "category": "MLCC Capacitors & RF Filters"},
        {"supplier_id": "SUP-06", "supplier_name": "Corning Incorporated", "country": "USA", "tier": "Tier-1 Strategic", "category": "Ceramic Shield Glass"},
    ]
    df_suppliers = pd.DataFrame(suppliers)
    
    dest_hubs = ["Elk Grove Distribution Hub (USA)", "Cork Logistics Hub (Ireland)", "Zhengzhou Central Hub (China)", "Bengaluru Supply Hub (India)"]
    components = ["A18 Pro 3nm Silicon", "M4 Max Silicon", "Tandem OLED Panel", "48MP Fusion Camera Sensor", "Titanium Enclosure", "Ceramic Shield 2 Glass"]
    
    shipments = []
    start_date = datetime.now() - timedelta(days=60)
    for i in range(400):
        sup = random.choice(suppliers)
        comp = random.choice(components)
        dest = random.choice(dest_hubs)
        qty = random.randint(5000, 150000)
        delay_status = random.choices(["On-Schedule", "Weather Delay", "Customs Hold", "Port Congestion"], weights=[0.82, 0.08, 0.06, 0.04])[0]
        transit_days = random.randint(3, 18)
        ship_date = (start_date + timedelta(days=random.randint(0, 55))).strftime("%Y-%m-%d")
        
        shipments.append({
            "shipment_id": f"SHP-{200000 + i}",
            "dispatch_date": ship_date,
            "supplier_id": sup["supplier_id"],
            "supplier_name": sup["supplier_name"],
            "component_name": comp,
            "destination_hub": dest,
            "quantity_units": qty,
            "transit_duration_days": transit_days,
            "logistics_status": delay_status,
            "carbon_offset_kg": round(qty * 0.015, 2)
        })
    df_shipments = pd.DataFrame(shipments)
    return df_suppliers, df_shipments


def generate_services_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Generates Apple Services subscription cohorts and daily MRR metrics."""
    random.seed(42)
    
    services_tiers = [
        {"service_tier": "iCloud+ 2TB", "monthly_price_usd": 9.99, "category": "Cloud Storage"},
        {"service_tier": "Apple One Premier", "monthly_price_usd": 37.95, "category": "Bundle"},
        {"service_tier": "Apple Music Family", "monthly_price_usd": 16.99, "category": "Streaming Music"},
        {"service_tier": "Apple TV+", "monthly_price_usd": 9.99, "category": "Original Video"},
        {"service_tier": "Apple Arcade", "monthly_price_usd": 6.99, "category": "Gaming"}
    ]
    
    cohort_rows = []
    for i in range(800):
        tier = random.choice(services_tiers)
        status = random.choices(["Active", "Churned", "Payment_Failed", "Grace_Period"], weights=[0.86, 0.08, 0.04, 0.02])[0]
        reg = random.choice(["Americas", "EMEIA", "APAC", "Greater China"])
        cohort_rows.append({
            "subscription_id": f"SUB-{500000 + i}",
            "service_tier": tier["service_tier"],
            "service_category": tier["category"],
            "monthly_price_usd": tier["monthly_price_usd"],
            "subscription_status": status,
            "subscriber_region": reg,
            "tenure_months": random.randint(1, 48),
            "autopay_enrolled": random.random() > 0.10
        })
    df_subs = pd.DataFrame(cohort_rows)
    
    # 60 days of aggregated metrics
    daily_rows = []
    start_date = datetime.now() - timedelta(days=60)
    for day in range(60):
        d_str = (start_date + timedelta(days=day)).strftime("%Y-%m-%d")
        for tier in services_tiers:
            active_users = random.randint(15000000, 45000000)
            daily_rev = round((active_users / 30.0) * tier["monthly_price_usd"], 2)
            churn_rate = round(random.uniform(0.012, 0.024), 4)
            daily_rows.append({
                "metric_date": d_str,
                "service_tier": tier["service_tier"],
                "active_subscriber_count": active_users,
                "daily_revenue_usd": daily_rev,
                "daily_churn_rate": churn_rate
            })
    df_daily = pd.DataFrame(daily_rows)
    return df_subs, df_daily


def seed_all_tables() -> Dict[str, pd.DataFrame]:
    """Returns a dictionary of all enterprise tables ready for warehouse injection."""
    df_stores, df_sales, df_inventory = generate_retail_data()
    df_incidents, df_parts = generate_applecare_data()
    df_suppliers, df_shipments = generate_supply_chain_data()
    df_subs, df_daily = generate_services_data()
    
    return {
        "retail_stores": df_stores,
        "retail_store_sales": df_sales,
        "retail_inventory": df_inventory,
        "applecare_incidents": df_incidents,
        "service_parts_inventory": df_parts,
        "component_suppliers": df_suppliers,
        "supply_chain_shipments": df_shipments,
        "services_subscriptions": df_subs,
        "services_daily_metrics": df_daily,
    }
