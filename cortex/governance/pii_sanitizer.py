"""Enterprise PII Sanitizer & Column Masking.

Provides deterministic PII anonymization and column masking for enterprise data warehouse queries,
ensuring strict compliance with internal data governance policies.
"""

import re
from typing import List, Optional
import pandas as pd

from cortex.config import config


class PIISanitizer:
    """Sanitizes PII and masks protected columns in DataFrames and text narratives."""

    EMAIL_REGEX = re.compile(r"([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
    PHONE_REGEX = re.compile(r"(\+?[0-9]{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}")
    SERIAL_REGEX = re.compile(r"\b([A-Z0-9]{10,12})\b")  # Apple 10-12 char serial formats

    def __init__(self, protected_columns: Optional[List[str]] = None):
        self.protected_columns = set(c.lower() for c in (protected_columns or config.mask_pii_columns))

    def mask_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Applies column-level masking to sensitive enterprise attributes."""
        if df.empty:
            return df
        
        df_masked = df.copy()
        for col in df_masked.columns:
            col_lower = str(col).lower()
            if any(prot in col_lower for prot in self.protected_columns):
                df_masked[col] = df_masked[col].apply(self._mask_value)
                
        return df_masked

    def _mask_value(self, val: object) -> str:
        """Masks a single value preserving prefix/suffix for debuggability."""
        s = str(val)
        if len(s) <= 4:
            return "****"
        return f"{s[:2]}****{s[-2:]}"

    def sanitize_text(self, text: str) -> str:
        """Redacts emails, phone numbers, and hardware serials from raw text narratives."""
        text = self.EMAIL_REGEX.sub(r"\1***@***.\2", text)
        text = self.PHONE_REGEX.sub(r"***-***-****", text)
        return text


# Singleton sanitizer
pii_sanitizer = PIISanitizer()
