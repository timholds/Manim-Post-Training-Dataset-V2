"""ManimBench dataset extractor - downloads cleaned version from Kaggle."""

import json
import logging
import subprocess
from pathlib import Path
from typing import Iterator, Dict, Any, Optional

import pandas as pd

from ..base import BaseExtractor
from ..registry import register_extractor

logger = logging.getLogger(__name__)


@register_extractor
class ManimBenchExtractor(BaseExtractor):
    """Extractor for ManimBench benchmark dataset from Kaggle (cleaned version)."""
    
    source_id = "manimbench"
    source_name = "ManimBench Dataset (Cleaned)"
    priority = 5  # High priority as it's a curated benchmark dataset
    
    def _validate_config(self) -> None:
        """Validate configuration."""
        self.data_dir = Path(self.config.get("data_dir", "data"))
        self.dataset_dir = self.data_dir / "manimbench"
        self.dataset_file = self.dataset_dir / "manim_sft_dataset_cleaned.parquet"
    
    def estimate_sample_count(self) -> Optional[int]:
        """Return estimated number of samples."""
        # Cleaned dataset v5 has 407 samples (10 removed: 5 mismatches + 2 duplicates + 1 sound + 1 config + 1 import)
        return 407
    
    def _download_dataset(self) -> bool:
        """Download cleaned ManimBench dataset from Kaggle if needed."""
        # Create data directory if it doesn't exist
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if data already exists
        if self.dataset_file.exists():
            logger.info(f"Dataset already exists at {self.dataset_file}")
            return True
            
        try:
            # Download using Kaggle API
            logger.info("Downloading cleaned ManimBench dataset from Kaggle...")
            cmd = [
                "kaggle", "datasets", "download",
                "-d", "timholdsworth/manim-bench-cleaned",
                "-p", str(self.dataset_dir),
                "--unzip"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to download dataset: {result.stderr}")
                logger.info("Make sure you have Kaggle API credentials set up.")
                logger.info("See: https://github.com/Kaggle/kaggle-api#api-credentials")
                return False
                
            logger.info("Dataset downloaded successfully")
            
            # Check if the expected file exists after download
            if not self.dataset_file.exists():
                # Try to find any parquet file in the directory
                parquet_files = list(self.dataset_dir.glob("*.parquet"))
                if parquet_files and parquet_files[0] != self.dataset_file:
                    parquet_files[0].rename(self.dataset_file)
            
            # Check if parquet file exists
            if not self.dataset_file.exists():
                logger.error("Expected parquet file not found after download")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error downloading dataset: {e}")
            return False
    
    def extract(self) -> Iterator[Dict[str, Any]]:
        """Extract samples from cleaned ManimBench dataset."""
        # Download dataset if needed
        if not self._download_dataset():
            logger.error("Failed to download ManimBench dataset")
            return
            
        try:
            # Read parquet file
            df = pd.read_parquet(self.dataset_file)
            logger.info(f"Loaded {len(df)} samples from cleaned ManimBench dataset")
            
            # Process each row in the dataframe
            for idx, row in df.iterrows():
                # ManimBench dataset has columns: Generated Description, Reviewed Description, Code, Type, Split
                description = row['Reviewed Description'] or row['Generated Description']
                code = row['Code']  # Keep code exactly as is from the dataset
                
                # Validate we have both description and code
                if not description or not code:
                    logger.warning(f"Item {idx}: Missing description or code")
                    continue
                    
                # Basic validation that it's Manim code
                if 'class' not in code or 'Scene' not in code:
                    logger.warning(f"Item {idx}: Doesn't look like Manim code")
                    continue
                
                # Build metadata
                metadata = {
                    "dataset_file": str(self.dataset_file),
                    "item_index": idx,
                    "type": row.get('Type'),
                    "split": row.get('Split')
                }
                
                yield {
                    "description": description.strip(),
                    "code": code,  # Keep code exactly as is, no stripping
                    "metadata": metadata
                }
                    
        except Exception as e:
            logger.error(f"Error reading dataset file: {e}")
            return