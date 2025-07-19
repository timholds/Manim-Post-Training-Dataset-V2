# Reducible Dataset Analysis and Extraction Feasibility Report

## Overview

I've analyzed the Reducible repository (https://github.com/nipunramk/Reducible) to assess the feasibility of extracting self-contained ManimCE scenes for rendering. The repository contains animation code for Reducible YouTube channel videos spanning 2019-2022.

## ManimCE Content Identification

Based on the repository's README and code inspection, the following content uses ManimCE:

1. **2021/MarchingSquares/** - Confirmed ManimCE (imports from `manim import *`)
2. **All 2022 videos**:
   - JPEGImageCompression
   - PNGvsQOI
   - PageRank
   - TSPProblem

All other content (2019-2021 except MarchingSquares) uses the older ManimGL library.

## Dependencies and Complexity Analysis

### 1. Module Dependencies

**Common Pattern**: Most 2022 projects use a shared dependency structure:
```python
sys.path.insert(1, "common/")
from functions import *
from classes import *
from reducible_colors import *
```

**Project-specific imports**:
- TSPProblem: `solver_utils`
- MarchingSquares: `lookup` module with lookup tables
- PageRank: `markov_chain` module

### 2. Asset Dependencies

All projects requiring assets use:
```python
config["assets_dir"] = "assets"
```

**Asset types**:
- **Images**: JPG, PNG files (e.g., `rose.jpg`, `usa-map-satellite-markers.png`)
- **SVG files**: Icons and graphics (e.g., `jpg_file.svg`, `green_ant.svg`)
- **Benchmark data**: Some projects have data files in subdirectories

### 3. External Dependencies

- Standard ManimCE imports
- Common Python libraries: numpy, itertools, math, random, PIL
- Project-specific: cv2 (OpenCV) for image processing scenes

## Extraction Feasibility Assessment

### Successfully Tested

1. **Simple self-contained scenes**: Can be extracted and rendered without modification
2. **Scenes with color dependencies**: Work when proper path setup is included

### Challenges for Extraction

1. **Path Dependencies**: Most scenes require:
   - Access to `common/` directory for shared modules
   - Proper sys.path configuration
   - Asset files in correct relative paths

2. **Inter-scene Dependencies**: Some scenes inherit from utility classes or reference other scenes

3. **Asset Requirements**: Many scenes fail without required image/SVG assets

4. **Font Dependencies**: Some scenes use specific fonts (e.g., "SF Mono", "CMU Serif")

## Extraction Strategy Recommendations

### 1. Scene Classification

Classify scenes into categories:
- **Type A**: Self-contained (no external dependencies)
- **Type B**: Requires color/utility modules only
- **Type C**: Requires assets (images/SVGs)
- **Type D**: Complex dependencies (inherits from other scenes)

### 2. Extraction Pipeline

For each scene:

```python
# 1. Extract scene class definition
# 2. Identify and bundle dependencies:
#    - Import statements
#    - Required modules (functions.py, classes.py, etc.)
#    - Asset files
# 3. Create standalone script with:
#    - Proper imports
#    - Path setup
#    - Inline dependencies where possible
#    - Asset verification
```

### 3. Example Extraction Template

```python
"""
Extracted scene from Reducible/{year}/{project}/scenes.py
Dependencies: [list dependencies]
Assets: [list required assets]
"""

import sys
import os
from manim import *

# Inline color definitions if needed
REDUCIBLE_PURPLE = "#8c4dfb"
# ... other colors

# Inline utility functions if needed

class ExtractedScene(Scene):
    def construct(self):
        # Scene code here
        pass
```

### 4. Automation Opportunities

1. **Dependency Scanner**: Parse imports and identify all requirements
2. **Asset Collector**: Scan for asset references and collect required files
3. **Scene Extractor**: Extract individual scene classes with their methods
4. **Validator**: Test render each extracted scene

## Conclusion

Extracting self-contained scenes from the Reducible dataset is **feasible but requires careful handling** of dependencies. The main challenges are:

1. **Module dependencies** - Can be addressed by inlining or bundling
2. **Asset dependencies** - Require asset collection and path management
3. **Inter-scene dependencies** - May require selective extraction or refactoring

A systematic extraction pipeline that classifies scenes by complexity and handles dependencies appropriately would enable successful extraction of most ManimCE content from the dataset.