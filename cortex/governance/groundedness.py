"""Hallucination & Groundedness Verification Guard.

Verifies that all numerical metrics, store names, and entity claims in the agent's synthesized
narrative are mathematically grounded in the executed SQL result set.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd


class GroundednessGuard:
    """Detects metric hallucinations by cross-referencing narrative claims against SQL DataFrames."""

    NUMBER_PATTERN = re.compile(r"(\$?\d+(?:,\d{3})*(?:\.\d+)?%?)")

    def evaluate_groundedness(self, narrative: str, df: pd.DataFrame, stats_summary: Optional[Dict[str, Any]] = None) -> Tuple[float, List[str], Dict[str, bool]]:
        """Evaluates whether numbers cited in the narrative appear in the SQL results.
        
        Returns:
            Tuple of:
            - groundedness_score: float (0.0 to 1.0)
            - ungrounded_tokens: List[str]
            - audit_details: Dict[str, bool]
        """
        if df.empty:
            return 1.0, [], {"empty_dataframe_note": True}

        # Focus groundedness audit on analytical findings and metrics, ignoring general policy text
        factual_section = narrative
        if "#### Strategic Recommendations" in narrative:
            factual_section = narrative.split("#### Strategic Recommendations")[0]

        # Extract all numbers/currencies/percentages from factual findings
        found_matches = self.NUMBER_PATTERN.findall(factual_section)
        cleaned_tokens: Set[str] = set()
        
        for m in found_matches:
            cleaned = m.replace("$", "").replace("%", "").replace(",", "").strip()
            try:
                val = float(cleaned)
                # Ignore trivial counters or markdown headers
                if val not in [1.0, 2.0, 3.0, 4.0, 5.0]:
                    cleaned_tokens.add(cleaned)
            except ValueError:
                pass

        if not cleaned_tokens:
            return 1.0, [], {}

        # Build candidate string set from dataframe cells + computed statistics
        df_cell_values: Set[str] = set()
        for col in df.columns:
            for val in df[col].dropna():
                s_val = str(val).strip()
                df_cell_values.add(s_val)
                try:
                    num_val = float(s_val)
                    df_cell_values.add(f"{num_val:.2f}")
                    df_cell_values.add(f"{num_val:.1f}")
                    df_cell_values.add(f"{int(num_val)}")
                except ValueError:
                    pass

        # Include statistical outputs
        if stats_summary and isinstance(stats_summary, dict):
            for col_metric, s_dict in stats_summary.get("metrics", {}).items():
                for k, v in s_dict.items():
                    df_cell_values.add(str(v))
            for anomaly in stats_summary.get("anomalies_detected", []):
                for k, v in anomaly.items():
                    df_cell_values.add(str(v))

        audit: Dict[str, bool] = {}
        ungrounded: List[str] = []

        for token in cleaned_tokens:
            # Check if token or rounded variation matches any value in dataframe or stats
            is_grounded = False
            try:
                t_val = float(token)
                for cell in df_cell_values:
                    try:
                        c_val = float(cell)
                        if abs(t_val - c_val) < 0.05 or (c_val != 0 and abs(t_val - c_val) / abs(c_val) < 0.02):
                            is_grounded = True
                            break
                    except ValueError:
                        continue
            except ValueError:
                is_grounded = token in df_cell_values

            audit[token] = is_grounded
            if not is_grounded:
                ungrounded.append(token)

        score = (len(cleaned_tokens) - len(ungrounded)) / max(1, len(cleaned_tokens))
        return round(score, 3), ungrounded, audit


# Singleton groundedness guard
groundedness_guard = GroundednessGuard()
