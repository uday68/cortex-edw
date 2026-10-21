"""Enterprise Unstructured Knowledge Base & Standard Operating Procedures (SOPs).

Contains domain documentation, repair benchmarks, business rules, and operational guidelines
used for hybrid retrieval augmentation alongside structured schemas.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class KnowledgeDocument:
    doc_id: str
    title: str
    domain: str
    category: str
    content: str


KNOWLEDGE_DOCUMENTS: List[KnowledgeDocument] = [
    KnowledgeDocument(
        doc_id="SOP-RET-01",
        title="Apple Retail Flagship Store Inventory Reorder Policy",
        domain="Retail",
        category="Inventory Governance",
        content="""Flagship stores (e.g., Regent Street, Fifth Avenue, BKC) must maintain a minimum of 7 to 10 days of supply for tier-1 SKUs (iPhone 16 Pro, MacBook Pro). When days_of_supply falls below 5.0, an automated replenishment batch is dispatched from regional distribution hubs. Genius Bar bay utilization should not exceed 85% to ensure walk-in customer SLA is maintained under 15 minutes."""
    ),
    KnowledgeDocument(
        doc_id="SOP-AC-02",
        title="AppleCare Battery & Display Diagnostic Thresholds",
        domain="AppleCare",
        category="Hardware Diagnostics",
        content="""Under AppleCare+ policy, battery replacement is fully covered at $0 customer cost if verified maximum battery health capacity is below 80% or if catastrophic swelling/thermal throttling is identified. Turnaround time (TAT) targets are: same-day Genius Bar (< 3.5 hours) for battery/display modules, and 48-72 hours for mail-in depot repairs requiring logic board replacement."""
    ),
    KnowledgeDocument(
        doc_id="SOP-SC-03",
        title="Operations Tier-1 Semiconductor Logistics SLA & Carbon Offset",
        domain="SupplyChain",
        category="Procurement & Logistics",
        content="""Inbound shipments of 3nm silicon wafers from TSMC and micro-OLED assemblies from Sony Semiconductor are classified as Mission Critical Priority 1. Air freight transit times must not exceed 5 business days to Elk Grove or Zhengzhou hubs. Any shipment encountering customs hold exceeding 48 hours requires immediate escalation to Global Trade Compliance."""
    ),
    KnowledgeDocument(
        doc_id="SOP-SRV-04",
        title="Apple Services Subscription Grace Period & Churn Mitigation",
        domain="Services",
        category="Billing Operations",
        content="""When a recurring subscription payment fails (status: Payment_Failed), the account enters a 16-day active Grace Period where access to iCloud+ storage and Apple One media is preserved. Intelligent payment retry loops occur on Day 1, Day 3, Day 7, and Day 14. If unrecovered after 16 days, the subscription shifts to Churned."""
    ),
]
