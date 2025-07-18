# Dataset Sources

This document describes the available datasets and any source-specific processing requirements.

## ManimBench
**Link:** https://www.kaggle.com/datasets/ravidussilva/manim-sft  
**Format:** Parquet file with columns: `Generated Description`, `Reviewed Description`, `Code`, `Type`, `Split`  
**Code Format:** Raw Python code (no markdown wrapping)  
**Special Processing:** None required - code is stored as plain text

### Ideosyncrasies
There's a sparesely populated generated description and full reviewed description. We use the latter

There's three cases where the descriptions are identical but the code is different. We remove the duplicates and kept the ones with the simpler code.



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
