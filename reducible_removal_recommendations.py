#!/usr/bin/env python3
"""Final recommendations for reducible scenes to remove."""

import pandas as pd
import json
from pathlib import Path

# Load the dataset
df = pd.read_parquet('data_formatted/sources/reducible_updated.parquet')

# Load analysis results
with open('reducible_scenes_analysis.json', 'r') as f:
    quality_issues = json.load(f)

# Failed to render scenes
failed_to_render = [7, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 28, 29, 30, 31, 32, 33, 34]

# Successfully rendered scenes
successfully_rendered = [0, 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 26, 27, 35, 36, 37]

print("REDUCIBLE DATASET SCENE REMOVAL RECOMMENDATIONS")
print("=" * 80)
print(f"Total scenes in dataset: {len(df)}")
print(f"Successfully rendered: {len(successfully_rendered)}")
print(f"Failed to render: {len(failed_to_render)}")
print()

# Collect all removal recommendations
scenes_to_remove = {}

# 1. Failed to render scenes
for idx in failed_to_render:
    if idx < len(df):
        scenes_to_remove[idx] = {
            'reason': 'Failed to render',
            'scene_name': df.iloc[idx].get('scene_name', f'scene_{idx}'),
            'description': df.iloc[idx].get('description', '')[:100] + '...'
        }

# 2. Quality issues from analysis
quality_issue_indices = [scene['index'] for scene in quality_issues]
for scene in quality_issues:
    idx = scene['index']
    if idx in successfully_rendered:  # Only flag if it rendered but has issues
        if idx not in scenes_to_remove:
            scenes_to_remove[idx] = {
                'reason': ', '.join(scene['issues']),
                'scene_name': scene['scene_name'],
                'description': df.iloc[idx].get('description', '')[:100] + '...'
            }

# 3. Scenes with no educational value based on description
for idx, row in df.iterrows():
    if idx in successfully_rendered and idx not in scenes_to_remove:
        desc = str(row.get('description', '')).lower()
        # Check for acknowledgment/credit scenes
        if any(word in desc for word in ['acknowledgment', 'patreon', 'thanks', 'credit']):
            scenes_to_remove[idx] = {
                'reason': 'Non-educational content (acknowledgments)',
                'scene_name': row.get('scene_name', f'scene_{idx}'),
                'description': row.get('description', '')[:100] + '...'
            }

# Print recommendations
print("\nSCENES RECOMMENDED FOR REMOVAL:")
print("-" * 80)

# Group by reason
removal_by_reason = {}
for idx, info in scenes_to_remove.items():
    reason = info['reason']
    if reason not in removal_by_reason:
        removal_by_reason[reason] = []
    removal_by_reason[reason].append((idx, info))

for reason, scenes in removal_by_reason.items():
    print(f"\n{reason} ({len(scenes)} scenes):")
    for idx, info in sorted(scenes)[:5]:  # Show first 5 of each type
        print(f"  [{idx}] {info['scene_name']}: {info['description']}")
    if len(scenes) > 5:
        print(f"  ... and {len(scenes) - 5} more")

# Calculate final statistics
scenes_to_keep = [i for i in range(len(df)) if i not in scenes_to_remove]
print("\n" + "=" * 80)
print(f"\nFINAL RECOMMENDATION:")
print(f"Remove {len(scenes_to_remove)} scenes")
print(f"Keep {len(scenes_to_keep)} scenes")
print(f"\nScenes to remove: {sorted(scenes_to_remove.keys())}")
print(f"\nScenes to keep: {sorted(scenes_to_keep)}")

# Save recommendations
recommendations = {
    'total_scenes': len(df),
    'scenes_to_remove': sorted(scenes_to_remove.keys()),
    'scenes_to_keep': sorted(scenes_to_keep),
    'removal_details': scenes_to_remove
}

with open('reducible_removal_recommendations.json', 'w') as f:
    json.dump(recommendations, f, indent=2)

print("\nRecommendations saved to reducible_removal_recommendations.json")