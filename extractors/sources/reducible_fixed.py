"""
Extractor for manually fixed Reducible dataset
"""

from pathlib import Path
from typing import Iterator, Dict, Any, Optional
import pandas as pd
import logging

from ..base import BaseExtractor
from ..registry import register_extractor

logger = logging.getLogger(__name__)


@register_extractor
class ReducibleFixedExtractor(BaseExtractor):
    """Extracts pre-fixed Reducible samples from parquet file"""
    
    source_id = "reducible_fixed"
    source_name = "Reducible YouTube Channel (Fixed)"
    priority = 9  # Higher priority than original
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
    def _validate_config(self) -> None:
        """Validate configuration for this extractor."""
        self.parquet_path = Path(self.config.get("parquet_path", "data_formatted/reducible_final.parquet"))
        
        # This is an optional extractor - log a warning instead of failing
        if not self.parquet_path.exists():
            logger.warning(
                f"Fixed Reducible parquet not found at {self.parquet_path}. "
                f"This file contains manually corrected Reducible samples. "
                f"To use this extractor, first run the regular 'reducible' extractor, "
                f"then manually fix any issues and save the corrected samples to {self.parquet_path}"
            )
            self._skip_extraction = True
        else:
            self._skip_extraction = False
    
    def estimate_sample_count(self) -> Optional[int]:
        """Return estimated number of samples."""
        if hasattr(self, '_skip_extraction') and self._skip_extraction:
            return 0
        try:
            df = pd.read_parquet(self.parquet_path)
            return len(df)
        except:
            return 0
    
    def extract(self) -> Iterator[Dict[str, Any]]:
        """Extract samples from the fixed parquet file."""
        
        # Skip extraction if file doesn't exist
        if self._skip_extraction:
            logger.info("Skipping reducible_fixed extraction - parquet file not found")
            return
        
        df = pd.read_parquet(self.parquet_path)
        logger.info(f"Loaded {len(df)} fixed samples from {self.parquet_path}")
        
        for _, row in df.iterrows():
            # Convert to dict and handle any numpy types
            sample = row.to_dict()
            # Ensure all values are JSON serializable
            def make_json_serializable(obj):
                if hasattr(obj, 'tolist'):  # numpy array
                    return obj.tolist()
                elif pd.isna(obj):  # NaN values
                    return None
                elif isinstance(obj, dict):
                    return {k: make_json_serializable(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [make_json_serializable(item) for item in obj]
                else:
                    return obj
            
            sample = make_json_serializable(sample)
            yield sample