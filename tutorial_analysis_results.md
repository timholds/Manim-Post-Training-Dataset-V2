# Comprehensive Analysis: Manim CE Docs Tutorial Pages

## Executive Summary

By adding tutorial and guide pages to the `manim_ce_docs` extractor, we can gain **43 additional unique Scene examples**, bringing the total from 44 to approximately **87 examples**.

## Detailed Findings

### Current Status
- **Current extraction**: 44 examples (27 from examples.html + 17 from reference pages)
- **Missing pages**: All tutorial and guide pages

### Tutorial Pages Analysis

#### 1. tutorials/quickstart.html
- **Scene examples found**: 7
- **Classes**: CreateCircle, SquareToCircle, SquareAndCircle, AnimatedSquareToCircle, DifferentRotations, TwoTransforms, TransformCycle

#### 2. tutorials/output_and_config.html
- **Scene examples found**: 0
- **Note**: Configuration-focused page with no Scene examples

#### 3. tutorials/building_blocks.html
- **Scene examples found**: 12
- **Classes**: CreatingMobjects, Shapes, MobjectPlacement, MobjectStyling, MobjectZOrder, SomeAnimations, AnimateExample, RunTime, CountingScene, MobjectExample, ExampleTransform, ExampleRotation

### Guide Pages Analysis

#### 4. guides/configuration.html
- **Scene examples found**: 0
- **Note**: Configuration guide with no Scene examples

#### 5. guides/deep_dive.html
- **Scene examples found**: 2
- **Classes**: ToyExample, VMobjectDemo

#### 6. guides/using_text.html
- **Scene examples found**: 21
- **Classes**: HelloWorld, SingleLineColor, FontsExample, SlantsExample, DifferentWeight, SimpleColor, Textt2cExample, GradientExample, t2gExample, LineSpacing, DisableLigature, IterateColor, HelloLaTeX, MathTeXDemo, AMSLaTeX, LaTeXAttributes, AddPackageLatex, LaTeXSubstrings, IncorrectLaTeXSubstringColoring, CorrectLaTeXSubstringColoring, IndexLabelsMathTex

#### 7. guides/add_voiceovers.html
- **Scene examples found**: 1
- **Classes**: RecorderExample (inherits from VoiceoverScene)

### HTML Structure Analysis

Tutorial examples follow the same structure as examples.html:
- Contained in `div.highlight` elements with class `highlight-python`
- Code is in `<pre>` tags within these divs
- The existing extractor should work without modification

## Summary Table

| Page Type | Page | Scene Examples |
|-----------|------|----------------|
| Tutorial | quickstart.html | 7 |
| Tutorial | output_and_config.html | 0 |
| Tutorial | building_blocks.html | 12 |
| Guide | configuration.html | 0 |
| Guide | deep_dive.html | 2 |
| Guide | using_text.html | 21 |
| Guide | add_voiceovers.html | 1 |
| **Total** | | **43** |

## Recommendations

### 1. Update the extractor's pages list

Add these pages to the `self.pages` list in `manim_ce_docs.py`:
```python
# Tutorial pages
"tutorials/quickstart.html",
"tutorials/building_blocks.html", 
"guides/deep_dive.html",
"guides/using_text.html",
"guides/add_voiceovers.html"
```

### 2. No code changes needed

The existing extraction logic will work perfectly since tutorial pages use the same HTML structure.

### 3. Expected final count

- Current: 44 examples
- Additional from tutorials: 43 examples
- **New total: ~87 examples**

### 4. Note on expectations

While 87 is significantly better than 44, it's still far from the expected 200. The discrepancy might be due to:
- Different documentation versions
- Confusion with the total number of classes/methods documented (not all have examples)
- Possibly missing other sources like GitHub examples, community contributions, etc.