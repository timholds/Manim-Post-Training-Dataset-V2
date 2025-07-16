#!/usr/bin/env python3
"""
Simple data preparation script for Manim dataset.
Starting with just ManimBench to verify everything works correctly.
"""

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from extractors.manimbench_simple import ManimBenchExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_rendering(sample: Dict[str, Any], timeout: int = 30) -> Tuple[bool, Optional[str]]:
    """
    Validate that a code sample can be rendered by Manim.
    Returns (success, error_message).
    """
    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(sample['code'])
        temp_file = f.name
    
    try:
        # Run manim to render the scene
        cmd = [
            'manim', 
            '-ql',  # Low quality for faster rendering
            '--disable_caching',
            temp_file,
            '--format', 'png',  # Just render last frame for validation
            '--progress_bar', 'none'
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Check if rendering succeeded
        if result.returncode == 0:
            return True, None
        else:
            error_msg = result.stderr or result.stdout
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        return False, f"Rendering timeout after {timeout} seconds"
    except Exception as e:
        return False, str(e)
    finally:
        # Clean up temp file
        Path(temp_file).unlink(missing_ok=True)


def validate_dataset(samples: List[Dict[str, Any]], 
                    sample_size: Optional[int] = None,
                    timeout: int = 30) -> List[Dict[str, Any]]:
    """
    Validate that samples can be rendered.
    If sample_size is provided, only validate a random sample.
    """
    import random
    
    # Determine which samples to validate
    if sample_size and sample_size < len(samples):
        logger.info(f"Validating a random sample of {sample_size} out of {len(samples)} samples")
        samples_to_validate = random.sample(samples, sample_size)
    else:
        logger.info(f"Validating all {len(samples)} samples")
        samples_to_validate = samples
    
    # Validate each sample
    valid_samples = []
    failed_samples = []
    
    for i, sample in enumerate(samples_to_validate):
        logger.info(f"Validating sample {i+1}/{len(samples_to_validate)}...")
        
        success, error = validate_rendering(sample, timeout=timeout)
        
        if success:
            sample['rendering_validated'] = True
            valid_samples.append(sample)
        else:
            logger.warning(f"Sample {sample['original_id']} failed: {error[:200]}...")
            sample['rendering_error'] = error
            failed_samples.append(sample)
    
    # Log summary
    logger.info(f"\nValidation Summary:")
    logger.info(f"  Total validated: {len(samples_to_validate)}")
    logger.info(f"  Successful: {len(valid_samples)} ({len(valid_samples)/len(samples_to_validate)*100:.1f}%)")
    logger.info(f"  Failed: {len(failed_samples)} ({len(failed_samples)/len(samples_to_validate)*100:.1f}%)")
    
    # If we only validated a sample, include all samples but mark which were validated
    if sample_size and sample_size < len(samples):
        # Create a set of validated IDs for quick lookup
        validated_ids = {s['original_id'] for s in samples_to_validate}
        
        # Return all samples, marking which were validated
        all_samples = []
        for sample in samples:
            if sample['original_id'] in validated_ids:
                # Use the validated version
                validated_sample = next(s for s in (valid_samples + failed_samples) 
                                      if s['original_id'] == sample['original_id'])
                all_samples.append(validated_sample)
            else:
                # Not validated
                sample['rendering_validated'] = False
                all_samples.append(sample)
        
        return all_samples
    else:
        # We validated everything, only return valid samples
        return valid_samples


def save_dataset(samples: List[Dict[str, Any]], output_dir: str = "data_formatted"):
    """
    Save the dataset in a simple JSON format.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON lines for easy streaming
    output_file = output_path / "manimbench_validated.jsonl"
    
    with open(output_file, 'w') as f:
        for sample in samples:
            f.write(json.dumps(sample) + '\n')
    
    logger.info(f"Saved {len(samples)} samples to {output_file}")
    
    # Also save statistics
    stats = {
        'total_samples': len(samples),
        'validated_samples': sum(1 for s in samples if s.get('rendering_validated', False)),
        'failed_samples': sum(1 for s in samples if 'rendering_error' in s),
        'source': 'manimbench'
    }
    
    stats_file = output_path / "dataset_stats.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    
    logger.info(f"Saved statistics to {stats_file}")


def main():
    """Main pipeline execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Prepare ManimBench dataset")
    parser.add_argument("--validate-all", action="store_true", 
                       help="Validate all samples (default: validate 10 samples)")
    parser.add_argument("--validate-sample", type=int, default=10,
                       help="Number of samples to validate (default: 10)")
    parser.add_argument("--timeout", type=int, default=30,
                       help="Timeout for rendering validation in seconds (default: 30)")
    parser.add_argument("--output-dir", default="data_formatted",
                       help="Output directory (default: data_formatted)")
    parser.add_argument("--skip-validation", action="store_true",
                       help="Skip rendering validation entirely")
    parser.add_argument("--data-dir", default="data",
                       help="Directory to store raw data (default: data)")
    
    args = parser.parse_args()
    
    # Step 1: Extract data
    logger.info("=== Step 1: Extracting ManimBench data ===")
    extractor = ManimBenchExtractor(data_dir=args.data_dir)
    
    # Download if needed
    if not extractor.download_dataset():
        logger.error("Failed to download dataset. Exiting.")
        return 1
        
    # Extract samples
    samples = extractor.extract_samples()
    
    if not samples:
        logger.error("No samples extracted. Exiting.")
        return 1
    
    # Step 2: Validate rendering (unless skipped)
    logger.info(f"\n=== Step 2: Rendering validation ===")
    if not args.skip_validation:
        sample_size = None if args.validate_all else args.validate_sample
        samples = validate_dataset(samples, sample_size=sample_size, timeout=args.timeout)
    else:
        logger.info("Skipping rendering validation")
    
    # Step 3: Save dataset
    logger.info(f"\n=== Step 3: Saving dataset ===")
    save_dataset(samples, output_dir=args.output_dir)
    
    logger.info("\n✅ Pipeline complete!")
    return 0


if __name__ == "__main__":
    exit(main())