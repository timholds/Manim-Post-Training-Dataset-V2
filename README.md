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
2. Validate examples (structure and optionally render validation)
3. Deduplicate within each source
4. Save individual datasets to `data/processed/`
5. Create merged dataset in `data/final/`
6. Generate statistics in `data/metadata/`

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
│       └── manim_ce_docs.py # Manim CE documentation extractor
├── data/                    # Output directory (created by script)
│   ├── processed/          # Individual validated datasets
│   │   ├── manimbench.parquet
│   │   └── manim_ce_docs.parquet
│   ├── final/              # Merged dataset
│   │   └── manim_combined.parquet
│   └── metadata/           # Statistics and duplicate info
│       ├── dataset_stats.json
│       └── cross_duplicates.json
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

## Deduplication Strategy
Besides rows that have a placeholder for the description that an LLM will fill in later, all descriptions must be unique. When we find two or more rows with the same description, we keep the one with the highest priority source. 
