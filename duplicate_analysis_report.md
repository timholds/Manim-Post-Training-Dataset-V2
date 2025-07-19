# Duplicate Analysis Report: manim_ce_docs vs manimbench

## Executive Summary

Your concerns were absolutely justified! The newly added tutorial pages have an extremely high duplicate rate:

- **Overall duplicate rate**: 87.4% (76 out of 87 examples)
- **Tutorial pages duplicate rate**: 88.4% (38 out of 43 examples)
- **Only 11 unique examples** in the entire manim_ce_docs source

## Detailed Breakdown

### Overall Statistics
```
Total manim_ce_docs samples: 87
├── Duplicates with manimbench: 76 (87.4%)
└── Unique to manim_ce_docs: 11 (12.6%)
```

### Tutorial Pages Analysis

| Page | Total | Duplicates | Unique | Unique Examples |
|------|-------|------------|--------|-----------------|
| tutorials/quickstart.html | 2 | 1 (50%) | 1 (50%) | TransformCycle |
| tutorials/building_blocks.html | 12 | 11 (92%) | 1 (8%) | Shapes |
| guides/deep_dive.html | 3 | 2 (67%) | 1 (33%) | ToyExample |
| guides/using_text.html | 25 | 24 (96%) | 1 (4%) | t2gExample |
| guides/add_voiceovers.html | 1 | 0 (0%) | 1 (100%) | RecorderExample |
| **TOTAL** | **43** | **38 (88.4%)** | **5 (11.6%)** | |

### Most Problematic Pages

1. **guides/using_text.html**: 96% duplicate rate (24/25 duplicates)
   - Only unique example: `t2gExample`
   
2. **tutorials/building_blocks.html**: 92% duplicate rate (11/12 duplicates)
   - Only unique example: `Shapes`

3. **examples.html**: 93% duplicate rate (25/27 duplicates)
   - Only unique examples: `GradientImageFromArray`, `PointWithTrace`

### Complete List of Unique Examples

Only **11 unique examples** from manim_ce_docs:

1. `GradientImageFromArray` (examples.html)
2. `PointWithTrace` (examples.html)
3. `MovingAndZoomingCamera` (reference/manim.scene.moving_camera_scene.html)
4. `MovingCameraOnGraph` (reference/manim.scene.moving_camera_scene.html)
5. `HelloWorld` (reference/manim.mobject.text.text_mobject.html)
6. `ChangingZoomScale` (reference/manim.scene.zoomed_scene.html)
7. `TransformCycle` (tutorials/quickstart.html)
8. `Shapes` (tutorials/building_blocks.html)
9. `ToyExample` (guides/deep_dive.html)
10. `t2gExample` (guides/using_text.html)
11. `RecorderExample` (guides/add_voiceovers.html)

### Why So Many Duplicates?

The ManimbBench dataset appears to have been curated from multiple sources including:
- Official documentation examples
- Tutorial examples
- Community contributions

This explains why 76 out of 87 manim_ce_docs examples are already in ManimbBench.

### Reverse Analysis

Interestingly, ManimbBench has **331 examples (81.3%)** that are NOT in the official docs, suggesting it contains many community-contributed or custom examples beyond the official documentation.

## Recommendations

1. **Keep only the 11 unique examples** from manim_ce_docs to avoid redundancy
2. **Prioritize ManimbBench** as it already contains most official examples plus additional community content
3. **Consider finding other sources** like GitHub repositories, Stack Overflow, or Manim Discord to get truly unique examples
4. The effective gain from manim_ce_docs is minimal - only 11 unique examples out of 87 extracted