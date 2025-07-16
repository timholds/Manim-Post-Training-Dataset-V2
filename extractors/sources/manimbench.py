"""ManimBench dataset extractor."""

import json
import logging
from pathlib import Path
from typing import Iterator, Dict, Any, Optional

from ..base import BaseExtractor
from ..registry import register_extractor

logger = logging.getLogger(__name__)


@register_extractor
class ManimBenchExtractor(BaseExtractor):
    """Extractor for ManimBench benchmark dataset."""
    
    source_id = "manimbench"
    source_name = "ManimBench Dataset"
    priority = 5  # High priority as it's a curated benchmark dataset
    
    def _validate_config(self) -> None:
        """Validate configuration."""
        # Support multiple possible file locations
        possible_paths = [
            Path(self.config.get("file", "data/manimbench/manimbench.jsonl")),
            Path(self.config.get("file", "data/manimbench.jsonl")),
            Path(self.config.get("file", "data/data_manimbench/manimbench.jsonl"))
        ]
        
        self.file_path = None
        for path in possible_paths:
            if path.exists():
                self.file_path = path
                break
        
        if self.file_path is None:
            logger.warning(f"ManimBench data file not found. Tried: {[str(p) for p in possible_paths]}")
    
    def estimate_sample_count(self) -> Optional[int]:
        """Return estimated number of samples."""
        # ManimBench is typically a smaller, high-quality benchmark dataset
        return 100  # Adjust based on actual dataset size
    
    def extract(self) -> Iterator[Dict[str, Any]]:
        """Extract samples from ManimBench dataset."""
        if self.file_path is None or not self.file_path.exists():
            logger.error(f"ManimBench data file not found")
            return
        
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    if not line.strip():
                        continue
                        
                    try:
                        item = json.loads(line.strip())
                        
                        # Handle different possible formats
                        # Format 1: Direct description and code fields
                        if "description" in item and "code" in item:
                            description = item["description"]
                            code = item["code"]
                        
                        # Format 2: Conversation format (like other datasets)
                        elif "conversations" in item:
                            conversations = item.get("conversations", [])
                            if len(conversations) >= 3:
                                description = conversations[1].get("value", "")
                                code = conversations[2].get("value", "")
                            else:
                                logger.warning(f"Line {line_num}: Invalid conversation format")
                                continue
                        
                        # Format 3: Question/answer format
                        elif "question" in item and "answer" in item:
                            description = item["question"]
                            code = item["answer"]
                        
                        # Format 4: Prompt/completion format
                        elif "prompt" in item and "completion" in item:
                            description = item["prompt"]
                            code = item["completion"]
                        
                        else:
                            logger.warning(f"Line {line_num}: Unknown format, skipping")
                            continue
                        
                        # Clean code from markdown if needed
                        if code.startswith("```python"):
                            code = code.split("```python")[1].split("```")[0].strip()
                        elif code.startswith("```"):
                            code = code.split("```")[1].split("```")[0].strip()
                        
                        # Skip empty or invalid samples
                        if not description or not code:
                            logger.warning(f"Line {line_num}: Empty description or code")
                            continue
                        
                        # Extract additional metadata if available
                        metadata = {
                            "source_file": str(self.file_path),
                            "line_number": line_num
                        }
                        
                        # Add any benchmark-specific metadata
                        if "difficulty" in item:
                            metadata["difficulty"] = item["difficulty"]
                        if "category" in item:
                            metadata["category"] = item["category"]
                        if "tags" in item:
                            metadata["tags"] = item["tags"]
                        if "benchmark_id" in item:
                            metadata["benchmark_id"] = item["benchmark_id"]
                        
                        yield {
                            "description": description,
                            "code": code,
                            "metadata": metadata
                        }
                    
                    except json.JSONDecodeError as e:
                        logger.warning(f"Line {line_num}: JSON decode error: {e}")
                        continue
                    except Exception as e:
                        logger.warning(f"Line {line_num}: Error processing item: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error reading file {self.file_path}: {e}")
            return
    
    def validate_sample(self, sample: Dict[str, Any]) -> bool:
        """
        Validate that a sample meets quality requirements.
        ManimBench samples should have higher quality standards.
        """
        # First apply base validation
        if not super().validate_sample(sample):
            return False
        
        # Additional validation for benchmark data
        code = sample.get("code", "")
        description = sample.get("description", "")
        
        # Ensure code has proper structure
        if "class" not in code or "Scene)" not in code:
            logger.debug(f"ManimBench sample missing Scene class definition")
            return False
        
        if "def construct" not in code:
            logger.debug(f"ManimBench sample missing construct method")
            return False
        
        # Ensure description is meaningful (not just a placeholder)
        if len(description) < 20:
            logger.debug(f"ManimBench sample has too short description")
            return False
        
        # Check for common quality issues
        if description.lower().startswith("create a"):
            # Ensure it's not just "Create a scene" but has more detail
            if len(description) < 30:
                logger.debug(f"ManimBench sample has generic description")
                return False
        
        return True