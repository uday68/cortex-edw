"""Statistical & Deep Learning Diagnostics Agent.

Performs automated statistical analysis, Z-score outlier detection, Interquartile Range (IQR)
anomaly boundaries, and distributional summaries on executed SQL DataFrames.
"""

import time
from typing import Any, Dict, List
import numpy as np
import pandas as pd
from scipy import stats

from cortex.agents.state import AgentState
from cortex.governance.telemetry import telemetry, QueryAuditTrail


class StatisticalAnalystAgent:
    """Computes rigorous statistical indicators, anomaly boundaries, and KPI summaries."""

    def run(self, state: AgentState, audit_trail: QueryAuditTrail) -> AgentState:
        start_time = time.perf_counter()
        df = state.query_result

        if df.empty:
            state.statistical_summary = {"empty": True}
            state.log_thought("StatisticalAnalystAgent", "Skipped diagnostics on empty result set.", "INFO")
            return state

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        summary: Dict[str, Any] = {
            "total_records": len(df),
            "numeric_columns_analyzed": numeric_cols,
            "metrics": {},
            "anomalies_detected": []
        }

        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) < 2:
                continue

            mean_val = float(series.mean())
            std_val = float(series.std()) if len(series) > 1 else 0.0
            median_val = float(series.median())
            q25 = float(series.quantile(0.25))
            q75 = float(series.quantile(0.75))
            iqr = q75 - q25
            lower_fence = q25 - 1.5 * iqr
            upper_fence = q75 + 1.5 * iqr

            # Z-scores
            z_scores = np.abs(stats.zscore(series)) if std_val > 0 else np.zeros(len(series))
            outlier_indices = np.where(z_scores > 2.0)[0]

            col_stats = {
                "mean": round(mean_val, 2),
                "std": round(std_val, 2),
                "median": round(median_val, 2),
                "iqr_lower_fence": round(lower_fence, 2),
                "iqr_upper_fence": round(upper_fence, 2),
                "outlier_count": int(len(outlier_indices))
            }
            summary["metrics"][col] = col_stats

            # Record any notable outlier records
            if len(outlier_indices) > 0:
                for idx in outlier_indices[:3]:
                    row = df.iloc[idx].to_dict()
                    val = row.get(col)
                    label = row.get("store_name") or row.get("device_category") or row.get("supplier_name") or row.get("service_tier") or f"Row {idx}"
                    summary["anomalies_detected"].append({
                        "metric": col,
                        "entity": str(label),
                        "observed_value": val,
                        "mean": round(mean_val, 2),
                        "z_score": round(float(z_scores[idx]), 2)
                    })

        state.statistical_summary = summary
        anomaly_count = len(summary["anomalies_detected"])
        
        state.log_thought(
            agent="StatisticalAnalystAgent",
            message=f"Analyzed {len(numeric_cols)} numeric series. Detected {anomaly_count} statistical outlier(s) with |z| > 2.0.",
            status="SUCCESS",
            data={"anomalies": summary["anomalies_detected"]}
        )

        elapsed = (time.perf_counter() - start_time) * 1000
        telemetry.record_step(
            audit_trail,
            "StatisticalAnalystAgent",
            "Z-Score & IQR Outlier Diagnostics",
            elapsed,
            status="SUCCESS",
            details={"anomalies_count": anomaly_count}
        )
        return state


stats_agent = StatisticalAnalystAgent()
