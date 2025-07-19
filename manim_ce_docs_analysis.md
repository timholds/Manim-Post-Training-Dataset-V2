# Analysis of manim_ce_docs Extractor

## Current Status
- **Extracted**: 44 examples
- **Expected**: ~200 examples (based on user's expectation)

## Investigation Findings

### 1. Examples Page Structure
The `examples.html` page contains 27 unique Scene examples, but each appears twice in the HTML:
- Once inside `div.highlight` tags (with full imports)
- Once as standalone `<pre>` tags with `data-manim-binder` attributes

The extractor correctly identifies and extracts the 27 unique examples from this page.

### 2. Reference Pages
The extractor searches through 45 reference pages and finds:
- Most reference pages contain no examples
- 11 pages contain 1-5 examples each
- Total from reference pages: 17 examples

### 3. Missing Sources
The extractor is **NOT** visiting these pages that contain additional examples:
- `/tutorials/quickstart.html` - Contains 5 Scene examples
- `/tutorials/building_blocks.html` - Contains 7 Scene examples
- Potentially other tutorial pages

### 4. Actual vs Expected Count
- Current extraction: 44 examples (27 from examples.html + 17 from reference pages)
- Missing: ~12 examples from tutorial pages
- Even with tutorials, total would be ~56 examples, not 200

## Evidence from Codebase

From the extractor configuration (lines 33-79 in `manim_ce_docs.py`):
```python
self.pages = [
    "examples.html",
    "reference/manim.animation.animation.html",
    # ... 44 reference pages total
]
```

The extractor only visits the main examples page and reference pages, but skips tutorial pages entirely.

## Recommendations

1. **Add Tutorial Pages**: Update the `pages` list to include:
   ```python
   "tutorials/quickstart.html",
   "tutorials/building_blocks.html",
   # Check for other tutorial pages
   ```

2. **Improve Example Detection**: The current code only looks for examples in `div.highlight`. Consider also extracting from:
   - `<pre>` tags with `data-manim-binder` attribute
   - Code blocks in tutorial pages which might have different HTML structure

3. **Remove Duplicate Detection**: The extractor might be missing valid examples if the same Scene name appears in different contexts (e.g., basic vs advanced usage).

4. **Verify Expectation**: The expectation of 200 examples might be based on:
   - A different version of the docs
   - Including non-Scene examples (functions, snippets)
   - Counting duplicates or variations

## Summary
The extractor is working correctly for the pages it visits, but it's missing entire sections of the documentation (tutorials). Even with these additions, the total would be around 56 examples, not 200. The user's expectation of 200 examples may need to be verified against the actual documentation content.