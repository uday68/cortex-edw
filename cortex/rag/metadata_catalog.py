"""Enterprise Metadata Catalog & Semantic Metric Dictionary.

Contains structured catalog definitions, column descriptions, and business metric formulas
across Apple Retail, AppleCare, Supply Chain, and Internet Services domains.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ColumnMetadata:
    name: str
    data_type: str
    description: str
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_target: Optional[str] = None
    sample_values: List[str] = field(default_factory=list)


@dataclass
class TableMetadata:
    table_name: str
    domain: str  # Retail, AppleCare, SupplyChain, Services
    description: str
    business_owner: str
    refresh_frequency: str
    columns: List[ColumnMetadata]


@dataclass
class MetricDefinition:
    metric_name: str
    domain: str
    formula: str
    description: str
    target_tables: List[str]


# Enterprise Table Catalog
ENTERPRISE_TABLES: List[TableMetadata] = [
    TableMetadata(
        table_name="retail_stores",
        domain="Retail",
        description="Physical Apple Store flagship locations with footprint, regional hierarchy, and Genius Bar bay capacity.",
        business_owner="Retail Real Estate & Global Store Operations",
        refresh_frequency="Daily",
        columns=[
            ColumnMetadata("store_id", "VARCHAR", "Unique store identifier (e.g., R001)", is_primary_key=True, sample_values=["R001", "R002", "R003"]),
            ColumnMetadata("store_name", "VARCHAR", "Official retail store marketing name", sample_values=["Apple Regent Street", "Apple Fifth Avenue", "Apple BKC"]),
            ColumnMetadata("market", "VARCHAR", "Metro city market area", sample_values=["London", "New York", "Mumbai"]),
            ColumnMetadata("country", "VARCHAR", "Country of physical operation", sample_values=["UK", "USA", "India", "Singapore"]),
            ColumnMetadata("region", "VARCHAR", "Global commercial theater", sample_values=["Americas", "EMEIA", "APAC", "Greater China"]),
            ColumnMetadata("square_feet", "INTEGER", "Total retail and back-of-house square footage", sample_values=["25000", "32000"]),
            ColumnMetadata("genius_bar_bays", "INTEGER", "Concurrent technical service customer consultation stations", sample_values=["24", "36", "18"]),
        ]
    ),
    TableMetadata(
        table_name="retail_store_sales",
        domain="Retail",
        description="Granular daily product-line transaction summaries per Apple Store location including gross revenue, discounts, net revenue, and trade-ins.",
        business_owner="Worldwide Retail Finance & Sales Operations",
        refresh_frequency="Near Real-Time / Hourly",
        columns=[
            ColumnMetadata("sale_id", "VARCHAR", "Unique transaction batch key", is_primary_key=True),
            ColumnMetadata("sale_date", "DATE", "Transaction calendar date (YYYY-MM-DD)", sample_values=["2026-09-15", "2026-10-01"]),
            ColumnMetadata("store_id", "VARCHAR", "Foreign key to retail_stores", is_foreign_key=True, foreign_target="retail_stores.store_id"),
            ColumnMetadata("product_id", "VARCHAR", "SKU product identifier", sample_values=["PROD_IPHONE16P", "PROD_MBA_M3"]),
            ColumnMetadata("product_line", "VARCHAR", "Major product family", sample_values=["iPhone", "Mac", "iPad", "Wearables", "Vision"]),
            ColumnMetadata("units_sold", "INTEGER", "Total customer unit sales volume"),
            ColumnMetadata("gross_revenue_usd", "FLOAT", "Total gross transaction amount before promotions"),
            ColumnMetadata("discount_amount", "FLOAT", "Promotional, employee, or educational discounts applied"),
            ColumnMetadata("net_revenue_usd", "FLOAT", "Actual realized revenue (gross minus discount)"),
            ColumnMetadata("trade_in_units", "INTEGER", "Apple Trade In devices accepted toward purchase"),
        ]
    ),
    TableMetadata(
        table_name="retail_inventory",
        domain="Retail",
        description="Daily stock-on-hand inventory snapshots per retail store, safety stock thresholds, and calculated days of supply.",
        business_owner="Retail Fulfillment & Supply Demand Management",
        refresh_frequency="Daily",
        columns=[
            ColumnMetadata("inventory_snapshot_date", "DATE", "Snapshot date"),
            ColumnMetadata("store_id", "VARCHAR", "Foreign key to retail_stores", is_foreign_key=True),
            ColumnMetadata("product_id", "VARCHAR", "Product SKU"),
            ColumnMetadata("stock_on_hand", "INTEGER", "Units physically available in back-of-house inventory"),
            ColumnMetadata("reorder_threshold", "INTEGER", "Automated replenishment trigger unit count"),
            ColumnMetadata("days_of_supply", "FLOAT", "Remaining days of stock based on run-rate velocity"),
        ]
    ),
    TableMetadata(
        table_name="applecare_incidents",
        domain="AppleCare",
        description="Hardware repair telemetry, diagnostic issue classification, warranty status, repair cost, and customer satisfaction (CSAT) scores.",
        business_owner="AppleCare Engineering & Global Service Operations",
        refresh_frequency="Near Real-Time",
        columns=[
            ColumnMetadata("incident_id", "VARCHAR", "Unique service incident case number", is_primary_key=True),
            ColumnMetadata("created_date", "DATE", "Case creation date"),
            ColumnMetadata("device_category", "VARCHAR", "Device family category", sample_values=["iPhone", "Mac", "iPad", "Apple Watch", "Vision Pro"]),
            ColumnMetadata("subsystem", "VARCHAR", "Hardware module affected", sample_values=["OLED Display", "Battery", "Logic Board", "TrueDepth Camera"]),
            ColumnMetadata("issue_diagnostic_code", "VARCHAR", "Technical fault code", sample_values=["Kernel Panic", "Battery Degradation", "Display Artifact"]),
            ColumnMetadata("warranty_status", "VARCHAR", "Coverage tier", sample_values=["AppleCare+", "Standard 1-Year Limited", "Out-of-Warranty"]),
            ColumnMetadata("turnaround_time_hrs", "FLOAT", "Time from intake to customer return in hours"),
            ColumnMetadata("repair_cost_usd", "FLOAT", "Internal absorbed or invoiced repair expense"),
            ColumnMetadata("customer_satisfaction_score", "INTEGER", "Post-repair CSAT survey rating (1 to 5)"),
            ColumnMetadata("channel", "VARCHAR", "Repair channel intake location", sample_values=["Genius Bar Retail", "Mail-in Depot", "Apple Authorized Service Provider"]),
        ]
    ),
    TableMetadata(
        table_name="service_parts_inventory",
        domain="AppleCare",
        description="Service replacement modules and component inventory in central logistics depots.",
        business_owner="AppleCare Global Logistics & Reverse Supply Chain",
        refresh_frequency="Hourly",
        columns=[
            ColumnMetadata("part_sku", "VARCHAR", "Module part number", is_primary_key=True),
            ColumnMetadata("part_name", "VARCHAR", "Official module part name"),
            ColumnMetadata("compatible_device", "VARCHAR", "Associated device family"),
            ColumnMetadata("warehouse_stock", "INTEGER", "Available parts in depot inventory"),
            ColumnMetadata("allocated_stock", "INTEGER", "Parts reserved for in-flight service orders"),
            ColumnMetadata("supplier", "VARCHAR", "OEM component manufacturing partner"),
        ]
    ),
    TableMetadata(
        table_name="supply_chain_shipments",
        domain="SupplyChain",
        description="Global component and assembly freight movements across Tier-1 strategic manufacturing partners and Apple regional hubs.",
        business_owner="Operations & Global Procurement",
        refresh_frequency="Real-Time / Event-Driven",
        columns=[
            ColumnMetadata("shipment_id", "VARCHAR", "Bill of lading shipment tracking number", is_primary_key=True),
            ColumnMetadata("dispatch_date", "DATE", "Date container departed supplier facility"),
            ColumnMetadata("supplier_id", "VARCHAR", "Foreign key to component_suppliers", is_foreign_key=True),
            ColumnMetadata("supplier_name", "VARCHAR", "Strategic manufacturing partner name", sample_values=["TSMC", "Foxconn", "LG Display", "Sony"]),
            ColumnMetadata("component_name", "VARCHAR", "Critical component or wafer type", sample_values=["A18 Pro 3nm Silicon", "M4 Max Silicon", "Tandem OLED Panel"]),
            ColumnMetadata("destination_hub", "VARCHAR", "Regional Apple logistics destination hub", sample_values=["Elk Grove Hub", "Cork Logistics Hub", "Zhengzhou Hub"]),
            ColumnMetadata("quantity_units", "INTEGER", "Total component batch volume"),
            ColumnMetadata("transit_duration_days", "INTEGER", "Elapsed transit days"),
            ColumnMetadata("logistics_status", "VARCHAR", "Real-time shipment status", sample_values=["On-Schedule", "Weather Delay", "Customs Hold", "Port Congestion"]),
            ColumnMetadata("carbon_offset_kg", "FLOAT", "Calculated greenhouse gas emissions for freight transit"),
        ]
    ),
    TableMetadata(
        table_name="services_subscriptions",
        domain="Services",
        description="Apple Services recurring revenue subscriber cohorts (iCloud+, Apple One, Apple TV+, Apple Music).",
        business_owner="Apple Services Finance & Subscription Analytics",
        refresh_frequency="Daily",
        columns=[
            ColumnMetadata("subscription_id", "VARCHAR", "Unique subscriber cohort identifier", is_primary_key=True),
            ColumnMetadata("service_tier", "VARCHAR", "Service offering name", sample_values=["iCloud+ 2TB", "Apple One Premier", "Apple Music Family", "Apple TV+"]),
            ColumnMetadata("service_category", "VARCHAR", "Service category grouping", sample_values=["Cloud Storage", "Bundle", "Streaming Music", "Original Video"]),
            ColumnMetadata("monthly_price_usd", "FLOAT", "Monthly recurring price"),
            ColumnMetadata("subscription_status", "VARCHAR", "Subscription state", sample_values=["Active", "Churned", "Payment_Failed", "Grace_Period"]),
            ColumnMetadata("subscriber_region", "VARCHAR", "Regional geographic billing territory"),
            ColumnMetadata("tenure_months", "INTEGER", "Consecutive months subscribed"),
            ColumnMetadata("autopay_enrolled", "BOOLEAN", "Whether automated card/Apple Pay renewal is enabled"),
        ]
    ),
    TableMetadata(
        table_name="services_daily_metrics",
        domain="Services",
        description="Aggregated platform daily active subscriber counts, daily revenue, and churn rates by service tier.",
        business_owner="Apple Services Executive Planning",
        refresh_frequency="Daily",
        columns=[
            ColumnMetadata("metric_date", "DATE", "Reporting date"),
            ColumnMetadata("service_tier", "VARCHAR", "Service subscription tier"),
            ColumnMetadata("active_subscriber_count", "BIGINT", "Global active recurring subscribers"),
            ColumnMetadata("daily_revenue_usd", "FLOAT", "Total estimated daily revenue"),
            ColumnMetadata("daily_churn_rate", "FLOAT", "Fraction of cohort terminating or lapsing subscription"),
        ]
    ),
]

# Business Metrics Catalog
ENTERPRISE_METRICS: List[MetricDefinition] = [
    MetricDefinition(
        metric_name="Total Net Sales",
        domain="Retail",
        formula="SUM(net_revenue_usd)",
        description="Total realized revenue after all promotional discounts across retail stores.",
        target_tables=["retail_store_sales"]
    ),
    MetricDefinition(
        metric_name="Discount Rate %",
        domain="Retail",
        formula="ROUND(SUM(discount_amount) * 100.0 / NULLIF(SUM(gross_revenue_usd), 0), 2)",
        description="Percentage of gross revenue conceded in educational/promotional discounts.",
        target_tables=["retail_store_sales"]
    ),
    MetricDefinition(
        metric_name="Trade-In Penetration Rate",
        domain="Retail",
        formula="ROUND(SUM(trade_in_units) * 100.0 / NULLIF(SUM(units_sold), 0), 2)",
        description="Ratio of trade-in devices received per 100 new hardware devices sold.",
        target_tables=["retail_store_sales"]
    ),
    MetricDefinition(
        metric_name="Mean Turnaround Time (TAT)",
        domain="AppleCare",
        formula="ROUND(AVG(turnaround_time_hrs), 2)",
        description="Average elapsed hours from incident intake to completion of hardware repair.",
        target_tables=["applecare_incidents"]
    ),
    MetricDefinition(
        metric_name="CSAT Score",
        domain="AppleCare",
        formula="ROUND(AVG(customer_satisfaction_score), 2)",
        description="Average customer satisfaction rating on 1-5 scale post-repair.",
        target_tables=["applecare_incidents"]
    ),
    MetricDefinition(
        metric_name="Logistics On-Time Delivery Rate %",
        domain="SupplyChain",
        formula="ROUND(COUNT(CASE WHEN logistics_status = 'On-Schedule' THEN 1 END) * 100.0 / COUNT(*), 2)",
        description="Percentage of inbound component freight shipments arriving without delay.",
        target_tables=["supply_chain_shipments"]
    ),
    MetricDefinition(
        metric_name="Services Monthly Recurring Revenue (MRR)",
        domain="Services",
        formula="SUM(monthly_price_usd) for Active status or SUM(daily_revenue_usd * 30)",
        description="Predictable subscription revenue generated on an annualized/monthly cadence.",
        target_tables=["services_subscriptions", "services_daily_metrics"]
    ),
]
