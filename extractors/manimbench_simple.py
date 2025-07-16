#!/usr/bin/env python3
"""
Simple ManimBench dataset extractor.
Downloads and processes the ManimBench v1 dataset from Kaggle.
"""

import json
import logging
import os
import subprocess
import zipfile
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ManimBenchExtractor:
    """Simple extractor for ManimBench dataset."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.dataset_dir = self.data_dir / "manimbench"
        self.dataset_file = self.dataset_dir / "data.json"
        
    def download_dataset(self) -> bool:
        """
        Download ManimBench dataset from Kaggle.
        Requires Kaggle API credentials to be set up.
        """
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
    
    def extract_samples(self) -> List[Dict[str, Any]]:
        """
        Extract samples from the ManimBench dataset.
        Returns a list of samples with 'description' and 'code' fields.
        """
        if not self.dataset_file.exists():
            logger.error(f"Dataset file not found at {self.dataset_file}")
            return []
            
        try:
            with open(self.dataset_file, 'r') as f:
                data = json.load(f)
                
            samples = []
            
            # Process each item in the dataset
            for idx, item in enumerate(data):
                # Extract description and code
                # The exact field names depend on the dataset format
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
                    logger.warning(f"Unknown format for item {idx}, keys: {list(item.keys())}")
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
                    logger.warning(f"Skipping item {idx}: missing description or code")
                    continue
                    
                # Basic validation that it's Manim code
                if 'class' not in code or 'Scene' not in code:
                    logger.warning(f"Skipping item {idx}: doesn't look like Manim code")
                    continue
                    
                sample = {
                    'description': description.strip(),
                    'code': code.strip(),
                    'source': 'manimbench',
                    'original_id': idx
                }
                
                # Add any additional metadata if available
                if 'difficulty' in item:
                    sample['difficulty'] = item['difficulty']
                if 'category' in item:
                    sample['category'] = item['category']
                    
                samples.append(sample)
                
            logger.info(f"Extracted {len(samples)} valid samples from ManimBench")
            return samples
            
        except Exception as e:
            logger.error(f"Error reading dataset file: {e}")
            return []


def main():
    """Test the extractor independently."""
    logging.basicConfig(level=logging.INFO)
    
    extractor = ManimBenchExtractor()
    
    # Download dataset
    if not extractor.download_dataset():
        logger.error("Failed to download dataset")
        return
        
    # Extract samples
    samples = extractor.extract_samples()
    
    if samples:
        logger.info(f"\nFirst sample:")
        logger.info(f"Description: {samples[0]['description'][:100]}...")
        logger.info(f"Code preview: {samples[0]['code'][:200]}...")


if __name__ == "__main__":
    main()