"""Dan4Life AOC 2024 dataset extractor - downloads from Kaggle."""

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
class Dan4LifeExtractor(BaseExtractor):
    """Extractor for Dan4Life AOC 2024 dataset from Kaggle."""
    
    source_id = "dan4life"
    source_name = "Dan4Life AOC 2024 Dataset"
    priority = 4  # Medium-high priority
    
    def _validate_config(self) -> None:
        """Validate configuration."""
        self.data_dir = Path(self.config.get("data_dir", "raw"))
        self.dataset_dir = self.data_dir / "dan4life"
        self.dataset_file = self.dataset_dir / "dan4life_aoc2024_cleaned.parquet"
    
    def estimate_sample_count(self) -> Optional[int]:
        """Return estimated number of samples."""
        # We don't know the exact count yet
        return None
    
    def _download_dataset(self) -> bool:
        """Download Dan4Life dataset from Kaggle if needed."""
        # Create data directory if it doesn't exist
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if data already exists
        if self.dataset_file.exists():
            logger.info(f"Dataset already exists at {self.dataset_file}")
            return True
            
        try:
            # Download using Kaggle API
            logger.info("Downloading Dan4Life AOC 2024 dataset from Kaggle...")
            cmd = [
                "kaggle", "datasets", "download",
                "-d", "timholdsworth/manim-bench-cleaned",
                "-f", "dan4life_aoc2024_cleaned.parquet",
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
                logger.error("Expected parquet file not found after download")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error downloading dataset: {e}")
            return False
    
    def extract(self) -> Iterator[Dict[str, Any]]:
        """Extract samples from Dan4Life AOC 2024 dataset."""
        # Download dataset if needed
        if not self._download_dataset():
            logger.error("Failed to download Dan4Life dataset")
            return
            
        try:
            # Read parquet file
            df = pd.read_parquet(self.dataset_file)
            logger.info(f"Loaded {len(df)} samples from Dan4Life AOC 2024 dataset")
            
            # Process each row in the dataframe
            for idx, row in df.iterrows():
                # Extract data from columns - need to check actual column names
                # Based on typical AOC datasets, might have columns like: problem, solution, code, etc.
                
                # First, let's see what columns are available
                if idx == 0:
                    logger.info(f"Available columns: {list(df.columns)}")
                
                # Try to get description/problem statement
                description = None
                if 'description' in df.columns:
                    description = row['description']
                elif 'problem' in df.columns:
                    description = row['problem']
                elif 'prompt' in df.columns:
                    description = row['prompt']
                elif 'task' in df.columns:
                    description = row['task']
                    
                # Try to get code
                code = None
                if 'code' in df.columns:
                    code = row['code']
                elif 'solution' in df.columns:
                    code = row['solution']
                elif 'implementation' in df.columns:
                    code = row['implementation']
                
                # If we couldn't find standard columns, use the first text column as description
                # and second as code
                if description is None or code is None:
                    text_columns = [col for col in df.columns if df[col].dtype == 'object']
                    if len(text_columns) >= 2:
                        if description is None:
                            description = row[text_columns[0]]
                        if code is None:
                            code = row[text_columns[1]]
                
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
                    "source": "dan4life_aoc2024"
                }
                
                # Add any additional columns to metadata
                for col in df.columns:
                    if col not in ['description', 'problem', 'prompt', 'task', 'code', 'solution', 'implementation']:
                        metadata[col] = row.get(col)
                
                yield {
                    "description": str(description).strip(),
                    "code": str(code),  # Keep code exactly as is, no stripping
                    "metadata": metadata
                }
                    
        except Exception as e:
            logger.error(f"Error reading dataset file: {e}")
            return