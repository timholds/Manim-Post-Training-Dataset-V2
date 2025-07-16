"""ManimBench dataset extractor - downloads from Kaggle."""

import json
import logging
import subprocess
from pathlib import Path
from typing import Iterator, Dict, Any, Optional

from ..base import BaseExtractor
from ..registry import register_extractor

logger = logging.getLogger(__name__)


@register_extractor
class ManimBenchV2Extractor(BaseExtractor):
    """Extractor for ManimBench benchmark dataset from Kaggle."""
    
    source_id = "manimbench_v2"
    source_name = "ManimBench Dataset (Kaggle)"
    priority = 5  # High priority as it's a curated benchmark dataset
    
    def _validate_config(self) -> None:
        """Validate configuration."""
        self.data_dir = Path(self.config.get("data_dir", "data"))
        self.dataset_dir = self.data_dir / "manimbench"
        self.dataset_file = self.dataset_dir / "data.json"
    
    def estimate_sample_count(self) -> Optional[int]:
        """Return estimated number of samples."""
        # ManimBench v1 has around 100 samples
        return 100
    
    def _download_dataset(self) -> bool:
        """Download ManimBench dataset from Kaggle if needed."""
        # Create data directory if it doesn't exist
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if data already exists
        if self.dataset_file.exists():
            logger.info(f"Dataset already exists at {self.dataset_file}")
            return True
            
        try:
            # Download using Kaggle API
            logger.info("Downloading ManimBench dataset from Kaggle...")
            cmd = [
                "kaggle", "datasets", "download",
                "-d", "ravidussilva/manim-sft",
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
            
            # Find the extracted JSON file
            json_files = list(self.dataset_dir.glob("*.json"))
            if not json_files:
                logger.error("No JSON file found in downloaded data")
                return False
                
            # Rename to consistent name
            json_files[0].rename(self.dataset_file)
            
            return True
            
        except Exception as e:
            logger.error(f"Error downloading dataset: {e}")
            return False
    
    def extract(self) -> Iterator[Dict[str, Any]]:
        """Extract samples from ManimBench dataset."""
        # Download dataset if needed
        if not self._download_dataset():
            logger.error("Failed to download ManimBench dataset")
            return
            
        try:
            with open(self.dataset_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Process each item in the dataset
            for idx, item in enumerate(data):
                # Extract description and code
                description = None
                code = None
                
                # Try different possible field names
                if 'description' in item and 'code' in item:
                    description = item['description']
                    code = item['code']
                elif 'prompt' in item and 'completion' in item:
                    description = item['prompt']
                    code = item['completion']
                elif 'question' in item and 'answer' in item:
                    description = item['question']
                    code = item['answer']
                elif 'instruction' in item and 'output' in item:
                    description = item['instruction']
                    code = item['output']
                else:
                    logger.warning(f"Item {idx}: Unknown format, keys: {list(item.keys())}")
                    continue
                
                # Clean up code if it's wrapped in markdown
                if code and '```' in code:
                    # Extract code from markdown code blocks
                    if '```python' in code:
                        code = code.split('```python')[1].split('```')[0].strip()
                    else:
                        code = code.split('```')[1].split('```')[0].strip()
                
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
                    "item_index": idx
                }
                
                # Add any additional metadata if available
                if 'difficulty' in item:
                    metadata['difficulty'] = item['difficulty']
                if 'category' in item:
                    metadata['category'] = item['category']
                
                yield {
                    "description": description.strip(),
                    "code": code.strip(),
                    "metadata": metadata
                }
                    
        except Exception as e:
            logger.error(f"Error reading dataset file: {e}")
            return