#!/usr/bin/env python3
"""Test ALL failing PageRank scenes with our fixes"""

import sys
import json
import tempfile
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extractors.sources.reducible import ReducibleExtractor

# Load the list of failed scenes
with open("temp/reducible_final_failed.json", "r") as f:
    failed_scenes = json.load(f)

# Filter for PageRank scenes
pagerank_scenes = []
for scene in failed_scenes:
    if "PageRank" in scene["description"]:
        # Extract scene name and file from description
        parts = scene["description"].split(" from ")
        scene_name = parts[0].replace("Scene: ", "")
        file_path = parts[1]
        pagerank_scenes.append((scene_name, file_path))

print(f"Testing {len(pagerank_scenes)} PageRank scenes...")

# Create extractor
extractor = ReducibleExtractor({"repo_path": "raw/Reducible"})

results = []
for i, (scene_name, file_path) in enumerate(pagerank_scenes):
    print(f"\n[{i+1}/{len(pagerank_scenes)}] Testing: {scene_name}")
    
    # Extract the scene
    full_path = Path("raw/Reducible") / file_path
    common_imports = ["reducible_colors"]
    if "jesus_animations.py" in file_path:
        common_imports.extend(["markov_chain", "classes"])
    
    scenes = extractor.extract_scenes_from_file(full_path, common_imports, [])
    
    # Find our scene
    scene_code = None
    for scene in scenes:
        if scene['name'] == scene_name:
            scene_code = scene['code']
            break
    
    if not scene_code:
        print(f"  ❌ Not found in extraction")
        results.append((scene_name, "NOT_FOUND", ""))
        continue
    
    # Save to temp file
    temp_file = f"/tmp/test_{scene_name}.py"
    with open(temp_file, "w") as f:
        f.write(scene_code)
    
    # Try to render with short timeout
    cmd = [
        sys.executable, "-m", "manim", 
        "-ql", "--disable_caching", 
        temp_file, scene_name
    ]
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=20,  # Short timeout
            env={**subprocess.os.environ, "PYTHONPATH": str(Path(__file__).parent)}
        )
        
        if result.returncode == 0:
            print(f"  ✅ Success!")
            results.append((scene_name, "SUCCESS", ""))
        else:
            # Extract key error
            error_msg = ""
            if "TypeError: 'weight' is an invalid keyword argument for str()" in result.stderr:
                error_msg = "Text/str type issue"
            elif "AttributeError: 'str' object has no attribute" in result.stderr:
                error_msg = "String attribute issue"
            elif "TypeError: 'scale' is an invalid keyword argument" in result.stderr:
                error_msg = "CustomLabel scale issue"
            elif "NameError: name 'it' is not defined" in result.stderr:
                error_msg = "itertools not imported"
            elif "NameError: name 'CustomCurvedArrow' is not defined" in result.stderr:
                error_msg = "CustomCurvedArrow missing"
            elif "NameError:" in result.stderr:
                # Extract the missing name
                import re
                match = re.search(r"NameError: name '(\w+)' is not defined", result.stderr)
                if match:
                    error_msg = f"Missing: {match.group(1)}"
            elif "AttributeError:" in result.stderr:
                # Extract attribute error
                match = re.search(r"AttributeError: (.+)", result.stderr)
                if match:
                    error_msg = match.group(1)[:50]
            else:
                error_msg = "Other error"
            
            print(f"  ❌ Failed: {error_msg}")
            results.append((scene_name, "FAILED", error_msg))
            
    except subprocess.TimeoutExpired:
        print(f"  ⏱️ Timeout")
        results.append((scene_name, "TIMEOUT", ""))
    except Exception as e:
        print(f"  ❌ Error: {e}")
        results.append((scene_name, "ERROR", str(e)))

# Summary
print(f"\n{'='*60}")
print("SUMMARY:")
print('='*60)
success_count = sum(1 for _, status, _ in results if status == "SUCCESS")
print(f"\nSuccessful: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)\n")

# Group by error type
error_types = {}
for scene, status, error in results:
    if status != "SUCCESS":
        error_key = error if error else status
        if error_key not in error_types:
            error_types[error_key] = []
        error_types[error_key].append(scene)

print("Failures by type:")
for error_type, scenes in sorted(error_types.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n{error_type} ({len(scenes)} scenes):")
    for scene in scenes[:3]:  # Show first 3
        print(f"  - {scene}")
    if len(scenes) > 3:
        print(f"  ... and {len(scenes)-3} more")