# Manim Code Generation with Fine-tuned Models

This project aims to create a ManimCE fine tuning dataset we can use for code generation models.

## Overview

- **Purpose**: Create a model-agnostic dataset for fine-tuning code generation models on Manim animations

## Output Format

The dataset uses a conversational format with code wrapped in markdown blocks:

```json
{
  "conversations": [
    {"from": "system", "value": "You are a Manim code generator. Create clean, working Manim animations using ManimCE syntax. Always wrap code in Python code blocks."},
    {"from": "user", "value": "<animation description>"},
    {"from": "assistant", "value": "```python\n<manim code>\n```"}
  ],
  "source": "<source_name>"
}
```

All code is normalized to ensure proper imports, Scene class structure, and construct method. This format is standard for LLM training and teaches models to output properly formatted code blocks.

## Quick Start

### Prerequisites
- NVIDIA GPU with 16GB+ VRAM
- Python 3.8+
- Ollama (for deployment)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd manim-post-training-dataset-v2

# Create and activate virtual environment
python -m venv manim-env
source manim-env/bin/activate

# Install dependencies
uv pip install -r requirements.txt
```

### Prepare Dataset

```bash
# Process all available sources
python prepare_data.py

# Process specific sources
python prepare_data.py --source manimbench --source manim_ce_docs

# Skip render validation for faster testing
python prepare_data.py --skip-render

# Process sources in parallel
python prepare_data.py --parallel

# Process single source
python prepare_data.py --source manimbench
```

The script will:
1. Extract examples from each source
2. Deduplicate samples based on normalized code
3. Optionally render videos to validate code
4. Save individual validated datasets to `outputs/sources/`
5. Create final combined dataset at `outputs/manim_dataset_final.parquet`
6. Generate statistics in `outputs/stats.json`

### Enhance with LLM Descriptions (Optional)

```bash
# Generate better descriptions using LLM (with caching)
python prepare_data_with_llm.py generate-descriptions \
    --input data_formatted/train.json \
    --output data_enhanced/train.json \
    --llm gemini

# Check LLM cache statistics
python prepare_data_with_llm.py cache-stats
```

## Key Features

- 🔌 **Modular extractors** - Each data source has its own extractor
- 🔍 **Two-stage deduplication** - Within-source and cross-source deduplication
- ✅ **Render validation** - Optional validation that code actually renders
- 📊 **Individual & merged datasets** - Keep source datasets separate or use combined
- 📈 **Comprehensive statistics** - Track examples, file sizes, and deduplication rates
- 🚀 **Parallel processing** - Process multiple sources concurrently
- 💾 **Efficient storage** - Parquet format with compression
- 🎯 **Source prioritization** - Prefer higher-quality sources when deduplicating

## Project Structure

```
manim-post-training-dataset-v2/
├── prepare_data.py          # Main data preparation script
├── extractors/              # Data source extractors
│   ├── base.py             # Base extractor interface
│   ├── utils.py            # Shared utilities (normalization, etc)
│   └── sources/            # Individual data source extractors
│       ├── manimbench.py   # ManimBench dataset extractor
│       ├── manim_ce_docs.py # Manim CE documentation extractor
│       ├── manim_community.py # Manim Community examples
│       ├── beethoven.py    # Elteoremadebeethoven tutorials
│       └── reducible.py    # Reducible YouTube channel
├── outputs/                 # Output directory (created by script)
│   ├── sources/            # Individual validated datasets
│   │   ├── manimbench.parquet
│   │   ├── manim_ce_docs.parquet
│   │   ├── manim_community.parquet
│   │   ├── beethoven.parquet
│   │   └── reducible.parquet
│   ├── manim_dataset_final.parquet  # Combined dataset
│   ├── dataset.jsonl       # JSONL format output
│   └── stats.json          # Statistics and metrics
├── rendered_videos/        # Rendered validation videos (if enabled)
│   ├── manimbench/
│   ├── manim_ce_docs/
│   └── ...
├── code_samples/           # Python source files for each sample (matches rendered_videos structure)
│   ├── manimbench/
│   ├── manim_ce_docs/
│   └── ...
```

## Adding New Data Sources

Adding a new data source is as simple as creating a new extractor:

```python
# extractors/sources/your_source.py
from ..base import BaseExtractor
from ..registry import register_extractor

@register_extractor
class YourSourceExtractor(BaseExtractor):
    source_id = "your_source"
    source_name = "Your Data Source"
    priority = 3  # 1-5, higher = keep when deduplicating
    
    def extract(self):
        # Your extraction logic here
        yield {"description": "...", "code": "...", "metadata": {...}}
```

### Extractor Output Format

Each extractor must yield dictionaries with this structure:
- **description** (str, required): Description of what the code does (min 5 chars)
- **code** (str, required): Raw Python Manim code (min 20 chars, no markdown)
- **metadata** (dict, optional): Source-specific metadata (URLs, indices, etc.)

The base class automatically adds a `source` field. Code should be valid Manim with Scene classes.

See the [Adding New Data Sources](docs/migration_guide.md) guide for detailed instructions.

## Contributing

See the [Development Roadmap](docs/ROADMAP.md) for priority datasets to add. The plugin-based architecture makes it easy to contribute new data sources.

## Output Files

The pipeline produces several output files:

### Individual Source Files (`outputs/sources/`)
Each source gets its own parquet file containing:
- Samples that passed extraction and validation
- Deduplicated within that source
- Only successful renders (if `--render-videos` was used)

### Combined Dataset (`outputs/manim_dataset_final.parquet`)
- Merges all individual source files
- Cross-source deduplication applied
- Ready for training or fine-tuning

### Statistics (`outputs/stats.json`)
Detailed metrics including:
- Sample counts at each stage
- Deduplication statistics
- Render success rates
- Output format distribution (MP4 vs PNG)

## Deduplication Strategy
The pipeline uses normalized code comparison for deduplication:
- Within each source first
- Then across sources when creating the combined dataset
- Code is normalized to ignore formatting differences
- Original code formatting is preserved in the output
