#!/bin/bash

# Script to update descriptions in parquet files using Claude CLI
# Usage: ./update_descriptions_cli.sh <source_name> [--test N] [--resume]

set -e

# Check arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <source_name> [--test N] [--resume]"
    echo "Example: $0 reducible"
    echo "Example: $0 dan4life --test 5"
    echo "Example: $0 reducible --resume"
    exit 1
fi

SOURCE_NAME=$1
PARQUET_FILE="data_formatted/sources/${SOURCE_NAME}.parquet"
OUTPUT_FILE="data_formatted/sources/${SOURCE_NAME}_updated.parquet"
PROGRESS_FILE="data_formatted/sources/.${SOURCE_NAME}_progress.json"
TEST_MODE=false
TEST_ROWS=5
RESUME_MODE=false

# Parse arguments
shift
while [ $# -gt 0 ]; do
    case $1 in
        --test)
            TEST_MODE=true
            TEST_ROWS=$2
            shift 2
            ;;
        --resume)
            RESUME_MODE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Activate manim environment
source manim-env/bin/activate

# Create prompt templates
case "$SOURCE_NAME" in
    "reducible")
        PROMPT_TEMPLATE='You are an expert at analyzing Manim animation code and writing clear, educational descriptions.

I have a Manim scene that needs a proper description for a fine-tuning dataset. The current description is just metadata and needs to be completely rewritten.

Current inadequate description: "{{DESCRIPTION}}"

Here is the Manim code:

```python
{{CODE}}
```

Please analyze this code and write a 1-5 sentence description that:
1. Starts with "Show how to..." or "Create an animation that..." or "Visualize..."
2. Clearly explains what mathematical/algorithmic concept is being demonstrated
3. Describes the key visual elements and animation approach
4. Is written as a request for creating this specific visualization
5. Focuses on the educational content, not implementation details

Examples of good descriptions:
- "Show how to visualize the PageRank algorithm step by step. Demonstrate how link importance propagates through a network graph with animated transitions and color-coded node values."
- "Create an animation that explains Markov chains using a simple state diagram. Show probability transitions between states with animated arrows and update state probabilities in real-time."
- "Visualize the marching squares algorithm for generating contour lines. Show how the algorithm examines grid cells and connects points to form smooth curves representing level sets."

Write only the description, nothing else.'
        ;;
    "dan4life")
        PROMPT_TEMPLATE='You are an expert at improving descriptions for Manim animations, specifically for Advent of Code visualizations.

Current description: "{{DESCRIPTION}}"

Here is the Manim code:

```python
{{CODE}}
```

Please improve this description following these guidelines:

1. Start with "Show how to..." focusing on the algorithmic task
2. Remove any story elements (elves, Christmas, historians, etc.)
3. Use clear, simple language like a LeetCode problem
4. Include specific algorithmic details and constraints
5. Describe both Part 1 and Part 2 if applicable
6. End with what the visualization shows
7. Keep it to 2-4 sentences

Good example:
"Show how to parse and execute multiplication instructions from corrupted text. Part 1 finds valid mul(X,Y) patterns in a string and calculates their sum. Part 2 adds do() and don'"'"'t() instructions that enable/disable subsequent multiplications. Visualizes scanning through text character by character to find valid patterns."

If the current description is already good, you may keep it. Otherwise, rewrite it completely.

Write only the improved description, nothing else.'
        ;;
    *)
        PROMPT_TEMPLATE='You are an expert at writing descriptions for Manim animations.

Current description: "{{DESCRIPTION}}"

Here is the Manim code:

```python
{{CODE}}
```

Please write or improve the description to:
1. Be a clear request for creating this visualization (1-5 sentences)
2. Explain what concept or problem is being visualized
3. Mention key visual elements if relevant
4. Be suitable for a fine-tuning dataset

Write only the description, nothing else.'
        ;;
esac

# Save prompt template to file
echo "$PROMPT_TEMPLATE" > /tmp/description_prompt_template.txt

# Create Python script to process parquet and call Claude CLI
cat > process_descriptions_cli.py << 'EOF'
import pandas as pd
import sys
import subprocess
import json
import time
import os
import tempfile
import re
import shutil

# Load arguments
source_name = sys.argv[1]
parquet_file = sys.argv[2]
output_file = sys.argv[3]
test_mode = sys.argv[4] == "true"
test_rows = int(sys.argv[5])
resume_mode = sys.argv[6] == "true"
progress_file = sys.argv[7]

# Find claude command
claude_cmd = shutil.which('claude')
if not claude_cmd:
    # Try common locations
    possible_paths = [
        '/usr/local/bin/claude',
        '/opt/homebrew/bin/claude',
        os.path.expanduser('~/.local/bin/claude'),
        os.path.expanduser('~/bin/claude'),
    ]
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            claude_cmd = path
            break
    
    if not claude_cmd:
        print("Error: 'claude' command not found. Please ensure Claude CLI is installed and in your PATH.")
        print("You can install it with: npm install -g @anthropic-ai/claude-cli")
        sys.exit(1)

print(f"Using claude command at: {claude_cmd}")

# Read the parquet file
df = pd.read_parquet(parquet_file)

# Read prompt template
with open('/tmp/description_prompt_template.txt', 'r') as f:
    prompt_template = f.read()

# Load progress if resuming
start_idx = 0
processed_indices = set()
if resume_mode and os.path.exists(progress_file):
    try:
        with open(progress_file, 'r') as f:
            progress_data = json.load(f)
            processed_indices = set(progress_data.get('processed_indices', []))
            print(f"Resuming from previous run. Already processed {len(processed_indices)} rows.")
    except Exception as e:
        print(f"Warning: Could not load progress file: {e}")

# Process rows
if test_mode:
    df_to_process = df.head(test_rows)
    print(f"TEST MODE: Processing first {test_rows} rows")
else:
    df_to_process = df
    print(f"Processing all {len(df)} rows")

# Initialize descriptions list - load existing if resuming
if resume_mode and os.path.exists(output_file):
    df_existing = pd.read_parquet(output_file)
    updated_descriptions = df_existing['description'].tolist()
else:
    updated_descriptions = df['description'].tolist()

# Save progress function
def save_progress(processed_indices):
    progress_data = {
        'processed_indices': list(processed_indices),
        'timestamp': time.time()
    }
    with open(progress_file, 'w') as f:
        json.dump(progress_data, f)

for idx, row in df_to_process.iterrows():
    # Skip if already processed
    if idx in processed_indices:
        continue
        
    print(f"\nProcessing row {idx + 1}/{len(df_to_process)}...")
    
    # Prepare the prompt
    prompt = prompt_template
    prompt = prompt.replace("{{DESCRIPTION}}", str(row['description']))
    prompt = prompt.replace("{{CODE}}", str(row['code']))
    
    try:
        # Call Claude CLI with prompt via stdin
        result = subprocess.run(
            [claude_cmd, '--model', 'sonnet'],
            input=prompt,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Extract the description from output
        new_description = result.stdout.strip()
        
        # Clean up any potential formatting
        new_description = new_description.strip('"\'')
        
        updated_descriptions[idx] = new_description
        
        # Print the full updated description
        print(f"  OLD: {row['description']}")
        print(f"  NEW: {new_description}")
        print()
        
        # Mark as processed and save progress
        processed_indices.add(idx)
        save_progress(processed_indices)
        
        # Rate limiting
        time.sleep(1)
        
    except subprocess.CalledProcessError as e:
        print(f"  Error calling Claude CLI: {e}")
        print(f"  Stderr: {e.stderr}")
        # Keep original on error but continue
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Progress saved.")
        save_progress(processed_indices)
        sys.exit(0)
    except Exception as e:
        print(f"  Error: {str(e)}")
        # Keep original on error but continue

# Update dataframe with all descriptions
df['description'] = updated_descriptions

# Save to new file
df.to_parquet(output_file)
print(f"\nSaved updated descriptions to: {output_file}")

# Show comparison for test mode
if test_mode:
    print("\n--- COMPARISON ---")
    for i in range(min(3, len(df_to_process))):
        print(f"\nRow {i+1}:")
        print(f"OLD: {df_to_process.iloc[i]['description']}")
        print(f"NEW: {updated_descriptions[i]}")

# Clean up
if os.path.exists('/tmp/description_prompt_template.txt'):
    try:
        os.unlink('/tmp/description_prompt_template.txt')
    except Exception as e:
        pass  # Ignore cleanup errors
EOF

# Run the Python script
echo "Processing $SOURCE_NAME descriptions using Claude CLI..."
if [ "$RESUME_MODE" == "true" ]; then
    echo "Resume mode enabled. Will continue from last saved progress."
fi
python process_descriptions_cli.py "$SOURCE_NAME" "$PARQUET_FILE" "$OUTPUT_FILE" "$TEST_MODE" "$TEST_ROWS" "$RESUME_MODE" "$PROGRESS_FILE"

# Clean up
rm process_descriptions_cli.py

echo "Done! Check $OUTPUT_FILE for results."