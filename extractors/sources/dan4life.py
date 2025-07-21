"""Dan4Life Advent of Code 2024 dataset extractor - downloads from Kaggle."""

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
    """Extractor for Dan4Life's Advent of Code 2024 Manim solutions from Kaggle."""
    
    source_id = "dan4life"
    source_name = "Dan4Life AOC 2024"
    priority = 4  # Medium-high priority as it's AoC solutions
    
    def _validate_config(self) -> None:
        """Validate configuration."""
        self.data_dir = Path(self.config.get("data_dir", "raw"))
        self.dataset_dir = self.data_dir / "dan4life"
        self.dataset_file = self.dataset_dir / "dan4life_aoc2024.parquet"
    
    def estimate_sample_count(self) -> Optional[int]:
        """Return estimated number of samples."""
        # We'll return None until we know the actual count
        return None
    
    def _download_dataset(self) -> bool:
        """Download dan4life dataset from Kaggle if needed."""
        # Create data directory if it doesn't exist
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if data already exists
        if self.dataset_file.exists():
            logger.info(f"Dataset already exists at {self.dataset_file}")
            return True
            
        try:
            # Download using Kaggle API
            logger.info("Downloading dan4life AOC 2024 dataset from Kaggle...")
            cmd = [
                "kaggle", "datasets", "download",
                "-d", "timholdsworth/manim-bench-cleaned",
                "-f", "dan4life_aoc2024.parquet",
                "-p", str(self.dataset_dir)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Failed to download dataset: {result.stderr}")
                logger.info("Make sure you have Kaggle API credentials set up.")
                logger.info("See: https://github.com/Kaggle/kaggle-api#api-credentials")
                return False
                
            logger.info("Dataset downloaded successfully")
            
            # The file might be in a zip, let's check
            zip_file = self.dataset_dir / "dan4life_aoc2024.parquet.zip"
            if zip_file.exists():
                import zipfile
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(self.dataset_dir)
                zip_file.unlink()  # Remove the zip file
            
            # Check if parquet file exists
            if not self.dataset_file.exists():
                logger.error("Expected parquet file not found after download")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error downloading dataset: {e}")
            return False
    
    def extract(self) -> Iterator[Dict[str, Any]]:
        """Extract samples from dan4life AOC 2024 dataset."""
        # Download dataset if needed
        if not self._download_dataset():
            logger.error("Failed to download dan4life dataset")
            return
            
        try:
            # Read parquet file
            df = pd.read_parquet(self.dataset_file)
            logger.info(f"Loaded {len(df)} samples from dan4life AOC 2024 dataset")
            
            # Process each row in the dataframe
            for idx, row in df.iterrows():
                # We need to check what columns are available in the parquet file
                # Common patterns might be: description, code, prompt, solution, etc.
                # For now, let's assume it has similar structure to ManimBench
                
                # Try different column names for description
                description = None
                for desc_col in ['description', 'Description', 'prompt', 'Prompt', 'problem', 'Problem']:
                    if desc_col in row:
                        description = row[desc_col]
                        break
                
                # Try different column names for code
                code = None
                for code_col in ['code', 'Code', 'solution', 'Solution', 'manim_code', 'Manim Code']:
                    if code_col in row:
                        code = row[code_col]
                        break
                
                # If we still don't have description/code, log available columns and skip
                if description is None or code is None:
                    if idx == 0:  # Only log once
                        logger.warning(f"Available columns: {list(row.index)}")
                    logger.warning(f"Item {idx}: Missing description or code")
                    continue
                
                # Validate we have both description and code
                if not description or not code:
                    logger.warning(f"Item {idx}: Empty description or code")
                    continue
                    
                # Basic validation that it's Manim code
                if 'class' not in code or 'Scene' not in code:
                    logger.warning(f"Item {idx}: Doesn't look like Manim code")
                    continue
                
                # Build metadata
                metadata = {
                    "dataset_file": str(self.dataset_file),
                    "item_index": idx,
                    "source": "Advent of Code 2024"
                }
                
                # Add any additional columns as metadata
                for col in row.index:
                    if col not in ['description', 'Description', 'code', 'Code', 'prompt', 'Prompt', 'solution', 'Solution']:
                        metadata[col] = row[col]
                
                yield {
                    "description": description.strip(),
                    "code": code,  # Keep code exactly as is, no stripping
                    "metadata": metadata
                }
                    
        except Exception as e:
            logger.error(f"Error reading dataset file: {e}")
            return