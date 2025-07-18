import pandas as pd
import json

# Read the parquet file
df = pd.read_parquet("data/manimbench/manim_sft_dataset.parquet")

# Check a failing sample
idx = 1
row = df.iloc[idx]
code = row['Code']

print(f"=== Checking Index {idx} ===")
print(f"Code length: {len(code)}")
print(f"Code repr: {repr(code)}")
print(f"\nCode ends with: {repr(code[-50:])}")

# Also check if the extractor is modifying anything
from extractors.sources.manimbench import ManimBenchExtractor

extractor = ManimBenchExtractor()
samples = list(extractor.extract())
sample = [s for s in samples if s['metadata']['item_index'] == idx][0]

print(f"\nExtracted code length: {len(sample['code'])}")
print(f"Extracted code ends with: {repr(sample['code'][-50:])}")
print(f"\nAre they identical? {code == sample['code']}")