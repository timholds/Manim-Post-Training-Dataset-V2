# Dataset Sources

This document describes the available datasets and any source-specific processing requirements.

## ManimBench
**Link:** https://www.kaggle.com/datasets/ravidussilva/manim-sft  
**Format:** Parquet file with columns: `Generated Description`, `Reviewed Description`, `Code`, `Type`, `Split`  
**Code Format:** Raw Python code (no markdown wrapping)  
**Special Processing:** None required - code is stored as plain text

### Ideosyncrasies
- Many of these examples come from the Manim Community Docs!
- Much of the code (220/407samples) is actually for creating images, not videos. While this behavior can be overwritten with cli flags like -s or `--format=png`, the general rule of thumb is that if the scene is missing `self.wait()` or `self.play()` calls, it is likely an image scene.
- There's a sparesely populated generated description and full reviewed description. We use the latter
- There's three cases where the descriptions are identical but the code is different. We kept the ones with the simpler code and remove the other. 
- There's a few scenes that have incorrect code and don't render. I took these out as well. 

## Reducible
**Link:** https://github.com/nipunramk/Reducible  
**Format:** Python files organized by year and video topic  
**Code Format:** Raw Python code with custom imports and dependencies  
**Special Processing:** Extensive processing required:
- Extract individual Scene classes from larger files
- Filter for ManimCE content only (2022 videos + MarchingSquares from 2021)
- Skip scenes that use external assets (images, SVGs)
- Inline dependencies from common modules (reducible_colors, markov_chain, classes)
- Fix API compatibility issues between older Manim versions and current ManimCE

### Idiosyncrasies
- High-quality educational animations from the Reducible YouTube channel
- ~51% of scenes are asset-free and suitable for extraction (38 out of 74 ManimCE scenes)
- ~42% of extracted scenes render successfully with automatic fixes (16 out of 38)
- Many scenes have inter-dependencies requiring module inlining
- Utility base classes (ending with "Utils") are skipped as they're not meant to be rendered directly
- Contains mix of animated scenes (MP4) and static visualizations (PNG)
- Required fixes for common API changes:
  - Color interpolation (string colors need ManimColor wrapper)
  - Title scale_factor parameter (deprecated, use .scale() method)
  - Text weight parameter (needs string quotes: BOLD → "BOLD")
  - Font parameters in Tex/MathTex (no longer supported, removed entirely)
  - CustomLabel scale parameter (use .scale() method instead)
  - Matrix string elements (wrap with MathTex)
  - Import fixes (scipy.sqrt → numpy.sqrt)
- Remaining rendering issues primarily in PageRank scenes involving complex MarkovChain visualizations



## Notes for Adding New Sources

When adding a new data source, consider:

1. **Markdown Extraction**: Some sources (e.g., GitHub issues, forum posts, documentation) may have code wrapped in markdown blocks (` ```python ... ``` `). For these sources, add extraction logic:
   ```python
   # Example markdown extraction (implement carefully to avoid breaking code with ``` in comments)
   if code.strip().startswith('```'):
       lines = code.strip().split('\n')
       if lines[0] in ['```python', '```'] and lines[-1] == '```':
           code = '\n'.join(lines[1:-1])
   ```

2. **Code Validation**: Each source may have different quality levels. Consider what validation is appropriate.

3. **Metadata**: Preserve source-specific metadata that might be useful for filtering or analysis.
