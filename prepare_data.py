#!/usr/bin/env python3
"""
Data preparation pipeline for Manim dataset.
Simple and focused on extraction and video rendering.
"""

import json
import logging
import re
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


def deduplicate_samples(samples: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Remove duplicate samples based on identical code.
    Returns (deduplicated_samples, duplicate_counts_by_source).
    """
    seen_codes = {}
    deduplicated = []
    duplicate_counts = {}
    
    for sample in samples:
        code = sample['code']
        source = sample['source']
        
        if code not in seen_codes:
            seen_codes[code] = sample
            deduplicated.append(sample)
        else:
            # Track which source had the duplicate
            if source not in duplicate_counts:
                duplicate_counts[source] = 0
            duplicate_counts[source] += 1
    
    return deduplicated, duplicate_counts


def render_video(sample: Dict[str, Any], output_path: Path, timeout: int = 120) -> Tuple[bool, Optional[str]]:
    """
    Render a code sample as a video.
    Returns (success, error_message).
    """
    # Create a temporary file for the code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(sample['code'])
        temp_file = f.name
    
    # Create a temporary directory for manim output
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Extract scene class name from code
        scene_match = re.search(r'class\s+(\w+)\s*\([^)]*Scene[^)]*\)', sample['code'])
        if not scene_match:
            return False, "Could not find Scene class in code"
        
        scene_name = scene_match.group(1)
        
        # Run manim to render the video
        cmd = [
            'manim', 
            '-ql',  # Low quality for faster rendering
            '--disable_caching',
            '--media_dir', temp_dir,
            '--format', 'mp4',  # Force MP4 output
            temp_file,
            scene_name
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Check if rendering succeeded
        if result.returncode == 0:
            # Find the rendered video or image
            video_files = list(Path(temp_dir).glob("videos/**/*.mp4"))
            image_files = list(Path(temp_dir).glob("images/**/*.png"))
            
            if video_files:
                # Move the video to the output path
                output_path.parent.mkdir(parents=True, exist_ok=True)
                video_files[0].rename(output_path)
                return True, None
            else:
                return False, "No video file produced"
        else:
            error_msg = result.stderr or result.stdout
            return False, error_msg
            
    except subprocess.TimeoutExpired:
        return False, f"Rendering timeout after {timeout} seconds"
    except Exception as e:
        return False, str(e)
    finally:
        # Clean up temp files
        Path(temp_file).unlink(missing_ok=True)
        # Clean up temp directory
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def prepare_dataset(
    sources: Optional[List[str]] = None,
    output_dir: str = "data_formatted",
    timeout: int = 30,
    render_videos: bool = False,
    no_cached_videos: bool = False,
    no_deduplication: bool = False
):
    """
    Dataset preparation pipeline.
    
    Args:
        sources: List of source IDs to process (default: all)
        output_dir: Output directory for processed data
        timeout: Rendering timeout in seconds
        render_videos: Whether to render all samples as videos
        no_cached_videos: Force re-render existing videos
        no_deduplication: Disable deduplication of samples
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
            # Get extractor
            extractor = registry.get_extractor(source_id)
            
            # Extract samples
            samples = []
            for sample in extractor:
                sample['source'] = source_id
                samples.append(sample)
            
            logger.info(f"Extracted {len(samples)} samples from {source_id}")
            
            # Store stats
            source_stats[source_id] = {
                'extracted': len(samples)
            }
            
            all_samples.extend(samples)
            
        except Exception as e:
            logger.error(f"Failed to process {source_id}: {e}")
            continue
    
    logger.info(f"\nTotal samples extracted: {len(all_samples)}")
    
    # Deduplication
    if no_deduplication:
        logger.info(f"\n=== Deduplication Disabled ===")
        deduplicated_samples = all_samples
        duplicate_counts = {}
    else:
        logger.info(f"\n=== Deduplicating Samples ===")
        deduplicated_samples, duplicate_counts = deduplicate_samples(all_samples)
        
        # Update stats with deduplication info
        for source_id in source_stats:
            source_stats[source_id]['duplicates_removed'] = duplicate_counts.get(source_id, 0)
        
        total_duplicates = sum(duplicate_counts.values())
        logger.info(f"Removed {total_duplicates} duplicates, {len(deduplicated_samples)} unique samples remain")
        
        if duplicate_counts:
            for source_id, count in duplicate_counts.items():
                logger.info(f"  {source_id}: {count} duplicates removed")
    
    # Video rendering and filtering
    valid_samples = []
    
    if render_videos:
        logger.info(f"\n=== Rendering Videos ===")
        
        # Track rendering statistics
        for source_id in source_stats:
            source_stats[source_id]['videos_rendered'] = 0
            source_stats[source_id]['videos_failed'] = 0
        
        # Process each source separately
        for source_id in sources_to_process:
            source_samples = [s for s in deduplicated_samples if s['source'] == source_id]
            if not source_samples:
                continue
                
            # Create output directory for this source
            video_dir = Path("rendered_videos") / source_id
            video_dir.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"\nRendering {len(source_samples)} videos for {source_id}...")
            
            # Track failed renders
            failed_renders = []
            
            # Render each sample
            for idx, sample in enumerate(tqdm(source_samples, desc=f"Rendering {source_id}")):
                video_path = video_dir / f"{idx:04d}.mp4"
                
                # Skip if video exists and caching is enabled
                if video_path.exists() and not no_cached_videos:
                    source_stats[source_id]['videos_rendered'] += 1
                    valid_samples.append(sample)
                    continue
                
                # Render the video
                success, error = render_video(sample, video_path, timeout=timeout * 4)  # 4x timeout for videos
                
                if success:
                    source_stats[source_id]['videos_rendered'] += 1
                    valid_samples.append(sample)
                else:
                    source_stats[source_id]['videos_failed'] += 1
                    failed_renders.append({
                        'index': idx,
                        'description': sample.get('description', 'No description'),
                        'error': error
                    })
            
            # Log results for this source
            total = source_stats[source_id]['videos_rendered'] + source_stats[source_id]['videos_failed']
            if total > 0:
                success_rate = source_stats[source_id]['videos_rendered'] / total * 100
                logger.info(f"{source_id}: {source_stats[source_id]['videos_rendered']}/{total} videos rendered ({success_rate:.1f}%)")
            
            # Save failed renders log
            if failed_renders:
                failed_log = video_dir / "render_errors.json"
                with open(failed_log, 'w') as f:
                    json.dump(failed_renders, f, indent=2)
                logger.info(f"Saved {len(failed_renders)} render errors to {failed_log}")
    else:
        # If not rendering videos, use deduplicated samples
        valid_samples = deduplicated_samples
    
    # Save results
    logger.info(f"\n=== Saving Results ===")
    
    # Save valid samples only
    output_file = output_path / "dataset.jsonl"
    with open(output_file, 'w') as f:
        for sample in valid_samples:
            f.write(json.dumps(sample) + '\n')
    logger.info(f"Saved {len(valid_samples)} valid samples to {output_file} (filtered from {len(all_samples)} total)")
    
    # Save statistics
    stats_file = output_path / "stats.json"
    with open(stats_file, 'w') as f:
        json.dump({
            'total_samples': len(all_samples),
            'deduplicated_samples': len(deduplicated_samples),
            'valid_samples': len(valid_samples),
            'sources': source_stats
        }, f, indent=2)
    logger.info(f"Saved statistics to {stats_file}")
    
    # Display summary table
    print("\n" + "="*80)
    print("DATASET PREPARATION SUMMARY")
    print("="*80)
    
    # Calculate per-source data for table
    source_data = {}
    for source_id in sources_to_process:
        stats = source_stats.get(source_id, {})
        
        # Initial count
        initial = stats.get('extracted', 0)
        
        # After deduplication
        duplicates = stats.get('duplicates_removed', 0)
        after_dedup = initial - duplicates
        
        # After rendering validation
        if render_videos:
            rendered = stats.get('videos_rendered', 0)
            final = rendered
        else:
            # If not rendering, count samples that made it through dedup
            source_samples = [s for s in deduplicated_samples if s['source'] == source_id]
            final = len(source_samples)
        
        source_data[source_id] = {
            'initial': initial,
            'after_dedup': after_dedup,
            'final': final
        }
    
    # Print table header
    print(f"{'Dataset':<20} {'Initial':>15} {'Deduplication':>15} {'Rendering':>15}")
    print("-"*80)
    
    # Print per-source rows
    for source_id in sources_to_process:
        data = source_data[source_id]
        print(f"{source_id:<20} {data['initial']:>15,} {data['after_dedup']:>15,} {data['final']:>15,}")
    
    # Print total row
    print("-"*80)
    print(f"{'TOTAL':<20} {len(all_samples):>15,} {len(deduplicated_samples):>15,} {len(valid_samples):>15,}")
    
    # Print summary statistics
    print("\nSummary:")
    total_filtered = len(all_samples) - len(valid_samples)
    retention_rate = (len(valid_samples) / len(all_samples) * 100) if all_samples else 0
    print(f"  Total datapoints filtered: {total_filtered:,}")
    print(f"  Overall retention rate: {retention_rate:.1f}%")
    
    if not no_deduplication:
        total_duplicates = len(all_samples) - len(deduplicated_samples)
        print(f"  Duplicates removed: {total_duplicates:,}")
    
    if render_videos:
        total_invalid = len(deduplicated_samples) - len(valid_samples)
        print(f"  Invalid (failed rendering): {total_invalid:,}")
    
    print("="*80)
    


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manim dataset preparation")
    parser.add_argument("--sources", nargs="+", 
                       help="Sources to process (e.g., manimbench, manimbench_v2)")
    parser.add_argument("--output-dir", default="data_formatted", help="Output directory")
    parser.add_argument("--timeout", type=int, default=30, help="Rendering timeout in seconds")
    parser.add_argument("--list-sources", action="store_true", help="List available sources and exit")
    parser.add_argument("--render-videos", action="store_true", help="Render all samples as videos")
    parser.add_argument("--no-cached-videos", action="store_true", help="Force re-render existing videos")
    parser.add_argument("--no-deduplication", action="store_true", help="Disable deduplication of samples with identical code")
    
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
        timeout=args.timeout,
        render_videos=args.render_videos,
        no_cached_videos=args.no_cached_videos,
        no_deduplication=args.no_deduplication
    )


if __name__ == "__main__":
    main()