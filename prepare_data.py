#!/usr/bin/env python3
"""
Data preparation pipeline for Manim dataset.
Simple and focused on extraction and rendering validation.
"""

import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from tqdm import tqdm

from extractors import get_registry

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


def prepare_dataset(
    sources: Optional[List[str]] = None,
    output_dir: str = "data_formatted",
    validate_rendering: bool = True,
    validation_sample_size: Optional[int] = None,
    timeout: int = 30
):
    """
    Dataset preparation pipeline.
    
    Args:
        sources: List of source IDs to process (default: all)
        output_dir: Output directory for processed data
        validate_rendering: Whether to validate rendering
        validation_sample_size: Number of samples to validate (None = all)
        timeout: Rendering timeout in seconds
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get registry and discover extractors
    registry = get_registry()
    registry.auto_discover()
    
    available_sources = registry.list_sources()
    logger.info(f"Available sources: {', '.join(available_sources)}")
    
    # Select sources to process
    if sources:
        sources_to_process = [s for s in sources if s in available_sources]
        if len(sources_to_process) < len(sources):
            missing = set(sources) - set(sources_to_process)
            logger.warning(f"Sources not found: {missing}")
    else:
        sources_to_process = available_sources
    
    # Process each source
    all_samples = []
    source_stats = {}
    
    for source_id in sources_to_process:
        logger.info(f"\n=== Processing {source_id} ===")
        
        try:
            # Get extractor (disable quality validation for simplicity)
            config = {
                "enable_quality_validation": False  # We'll do our own validation
            }
            extractor = registry.get_extractor(source_id, config)
            
            # Extract samples
            samples = []
            for sample in extractor:
                sample['source'] = source_id
                samples.append(sample)
            
            logger.info(f"Extracted {len(samples)} samples from {source_id}")
            
            # Store stats
            source_stats[source_id] = {
                'extracted': len(samples),
                'validated': 0,
                'valid': 0,
                'failed': 0
            }
            
            all_samples.extend(samples)
            
        except Exception as e:
            logger.error(f"Failed to process {source_id}: {e}")
            continue
    
    logger.info(f"\nTotal samples extracted: {len(all_samples)}")
    
    # Rendering validation
    if validate_rendering and all_samples:
        logger.info(f"\n=== Rendering Validation ===")
        
        # Determine samples to validate
        import random
        if validation_sample_size and validation_sample_size < len(all_samples):
            logger.info(f"Validating random sample of {validation_sample_size} samples")
            samples_to_validate = random.sample(all_samples, validation_sample_size)
        else:
            logger.info(f"Validating all {len(all_samples)} samples")
            samples_to_validate = all_samples
        
        # Validate with progress bar
        valid_samples = []
        failed_samples = []
        
        for sample in tqdm(samples_to_validate, desc="Validating"):
            success, error = validate_rendering(sample, timeout=timeout)
            
            if success:
                sample['rendering_validated'] = True
                valid_samples.append(sample)
                source_stats[sample['source']]['valid'] += 1
            else:
                sample['rendering_error'] = error
                failed_samples.append(sample)
                source_stats[sample['source']]['failed'] += 1
            
            source_stats[sample['source']]['validated'] += 1
        
        # Log validation summary
        logger.info(f"\nValidation Summary:")
        logger.info(f"  Total validated: {len(samples_to_validate)}")
        logger.info(f"  Successful: {len(valid_samples)} ({len(valid_samples)/len(samples_to_validate)*100:.1f}%)")
        logger.info(f"  Failed: {len(failed_samples)}")
        
        # Per-source breakdown
        logger.info(f"\nPer-source validation results:")
        for source_id, stats in source_stats.items():
            if stats['validated'] > 0:
                success_rate = stats['valid'] / stats['validated'] * 100
                logger.info(f"  {source_id}: {stats['valid']}/{stats['validated']} ({success_rate:.1f}%)")
    
    # Save results
    logger.info(f"\n=== Saving Results ===")
    
    # Save all samples (including validation results)
    output_file = output_path / "dataset.jsonl"
    with open(output_file, 'w') as f:
        for sample in all_samples:
            f.write(json.dumps(sample) + '\n')
    logger.info(f"Saved {len(all_samples)} samples to {output_file}")
    
    # Save statistics
    stats_file = output_path / "stats.json"
    with open(stats_file, 'w') as f:
        json.dump({
            'total_samples': len(all_samples),
            'sources': source_stats,
            'validation_performed': validate_rendering,
            'validation_sample_size': validation_sample_size
        }, f, indent=2)
    logger.info(f"Saved statistics to {stats_file}")
    
    # Save failed samples for debugging
    if validate_rendering and failed_samples:
        failed_file = output_path / "failed_samples.jsonl"
        with open(failed_file, 'w') as f:
            for sample in failed_samples:
                f.write(json.dumps(sample) + '\n')
        logger.info(f"Saved {len(failed_samples)} failed samples to {failed_file}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manim dataset preparation")
    parser.add_argument("--sources", nargs="+", 
                       help="Sources to process (e.g., manimbench, manimbench_v2)")
    parser.add_argument("--output-dir", default="data_formatted", help="Output directory")
    parser.add_argument("--skip-validation", action="store_true", help="Skip rendering validation")
    parser.add_argument("--validate-sample", type=int, help="Number of samples to validate (default: all)")
    parser.add_argument("--timeout", type=int, default=30, help="Rendering timeout in seconds")
    parser.add_argument("--list-sources", action="store_true", help="List available sources and exit")
    
    args = parser.parse_args()
    
    # List sources if requested
    if args.list_sources:
        registry = get_registry()
        registry.auto_discover()
        print("\nAvailable sources:")
        for source_id in sorted(registry.list_sources()):
            try:
                extractor = registry.get_extractor(source_id)
                print(f"  - {source_id}: {extractor.source_name}")
            except Exception as e:
                print(f"  - {source_id}: (error loading)")
        return
    
    # Require sources if not listing
    if not args.sources:
        parser.error("--sources is required when not using --list-sources")
        return
    
    # Run pipeline
    prepare_dataset(
        sources=args.sources,
        output_dir=args.output_dir,
        validate_rendering=not args.skip_validation,
        validation_sample_size=args.validate_sample,
        timeout=args.timeout
    )


if __name__ == "__main__":
    main()