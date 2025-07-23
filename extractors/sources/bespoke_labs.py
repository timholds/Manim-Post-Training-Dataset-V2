"""
Extractor for Bespoke Labs Manim Dataset from HuggingFace
https://huggingface.co/datasets/bespokelabs/bespoke-manim

This dataset contains 1000 high-quality, self-contained ManimCE scenes
focusing on advanced mathematical topics.
"""

import logging
import re
from typing import Dict, List, Optional, Any, Iterator
from pathlib import Path

from ..base import BaseExtractor

logger = logging.getLogger(__name__)


class BespokeLabsExtractor(BaseExtractor):
    """Extracts Manim scenes from Bespoke Labs HuggingFace dataset."""
    
    source_id = "bespoke_labs"
    source_name = "Bespoke Labs Manim Dataset - Advanced Mathematics Visualizations"
    priority = 3  # High quality, curated dataset
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self._dataset = None
        self._df = None
    
    def _validate_config(self) -> None:
        """Validate configuration for this extractor."""
        # No special config validation needed
        pass
    
    def estimate_sample_count(self) -> Optional[int]:
        """Return estimated number of samples."""
        return 1000  # Known size of the dataset
    
    def _load_dataset(self):
        """Lazy load the dataset from HuggingFace."""
        if self._dataset is None:
            try:
                from datasets import load_dataset
                import pandas as pd
                
                self.logger.info("Loading Bespoke Labs dataset from HuggingFace...")
                self._dataset = load_dataset("bespokelabs/bespoke-manim", split="train")
                self._df = pd.DataFrame(self._dataset)
                self.logger.info(f"Loaded {len(self._df)} samples from dataset")
            except Exception as e:
                self.logger.error(f"Failed to load dataset: {e}")
                raise
    
    def extract(self) -> Iterator[Dict[str, Any]]:
        """Extract all scenes from the Bespoke Labs dataset."""
        self.logger.info("Starting extraction from Bespoke Labs Manim dataset")
        
        # Load dataset if not already loaded
        self._load_dataset()
        
        if self._df is None:
            self.logger.error("Dataset not loaded")
            return
        
        import pandas as pd
        
        for idx, row in self._df.iterrows():
            try:
                # Skip if no code or scene name
                if pd.isna(row.get('python_code')) or pd.isna(row.get('scene_class_name')):
                    self.logger.debug(f"Skipping sample {idx}: missing code or scene name")
                    continue
                
                code = row['python_code']
                scene_name = row['scene_class_name']
                
                # Apply API compatibility fixes
                code = self._fix_api_compatibility(code)
                
                # Build description from metadata
                description_parts = []
                
                # Add subject and topic
                if pd.notna(row.get('subject')):
                    description_parts.append(f"Subject: {row['subject']}")
                if pd.notna(row.get('topic')):
                    description_parts.append(f"Topic: {row['topic']}")
                
                # Add title if available
                if pd.notna(row.get('title')):
                    description_parts.append(f"{row['title']}")
                
                # Add question if available
                if pd.notna(row.get('question')):
                    # Truncate very long questions
                    question = row['question']
                    if len(question) > 200:
                        question = question[:197] + "..."
                    description_parts.append(f"Question: {question}")
                
                # Fallback description
                if not description_parts:
                    description_parts = [f"Advanced mathematics visualization: {scene_name}"]
                
                description = "\n".join(description_parts)
                
                # Prepare metadata
                metadata = {
                    "source": self.source_id,
                    "scene_name": scene_name,
                    "subject": row.get('subject', ''),
                    "topic": row.get('topic', ''),
                    "index": idx,
                }
                
                # Optional metadata
                if pd.notna(row.get('visual_style')):
                    metadata['visual_style'] = row['visual_style']
                if pd.notna(row.get('video')):
                    metadata['has_video'] = True
                
                yield {
                    "description": description,
                    "code": code,
                    "metadata": metadata
                }
                
            except Exception as e:
                self.logger.warning(f"Error processing sample {idx}: {e}")
                continue
    
    def _fix_api_compatibility(self, code: str) -> str:
        """Fix known API compatibility issues in the code."""
        # Fix to_center() -> move_to(ORIGIN)
        code = re.sub(r'\.to_center\(\)', '.move_to(ORIGIN)', code)
        
        # Fix get_point_from_proportion -> point_from_proportion
        code = re.sub(r'\.get_point_from_proportion\(', '.point_from_proportion(', code)
        
        # Fix other potential issues
        # Add more fixes here as we discover them during testing
        
        return code


# For testing
if __name__ == "__main__":
    import sys
    sys.path.append("../..")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    extractor = BespokeLabsExtractor()
    
    # Test extraction of first few samples
    count = 0
    for sample in extractor:
        count += 1
        if count <= 3:
            print(f"\n--- Sample {count} ---")
            print(f"Description: {sample['description'][:200]}...")
            print(f"Code length: {len(sample['code'])} chars")
            print(f"Scene: {sample['metadata'].get('scene_name', 'Unknown')}")
            print(f"Subject: {sample['metadata'].get('subject', 'Unknown')}")
            print(f"Topic: {sample['metadata'].get('topic', 'Unknown')}")
        
        if count >= 5:  # Just test first 5 for now
            break
    
    print(f"\n\nTotal samples extracted: {count}")
    print(f"Extraction stats: {extractor.extraction_stats}")