import pandas as pd

# Read the parquet file
df = pd.read_parquet("data/manimbench/manim_sft_dataset.parquet")

# Look at the first few rows with failing indices
failing_indices = [1, 2, 4, 6, 7, 8, 9]

for idx in failing_indices[:3]:
    row = df.iloc[idx]
    print(f"\n=== Index {idx} ===")
    print(f"Description: {row['Reviewed Description'][:100]}...")
    print(f"\nCode:")
    print(row['Code'])
    print("\n" + "="*80)