#!/usr/bin/env python3
"""Debug script to understand why manim_ce_docs only extracts 44 examples."""

import re
from pathlib import Path
from bs4 import BeautifulSoup

# Load the cached examples.html
cache_file = Path("cache/manim_ce_docs/examples.html")
html = cache_file.read_text(encoding='utf-8')
soup = BeautifulSoup(html, 'html.parser')

print("=== Debugging manim_ce_docs extraction ===\n")

# Method 1: Current extractor approach - looking for div.highlight
highlight_divs = soup.find_all('div', class_='highlight')
print(f"1. Found {len(highlight_divs)} div.highlight elements")

valid_examples = 0
for div in highlight_divs:
    pre_tag = div.find('pre')
    if pre_tag:
        code = pre_tag.get_text().strip()
        if 'class' in code and 'Scene' in code:
            valid_examples += 1

print(f"   - {valid_examples} contain 'class' and 'Scene'\n")

# Method 2: Look for pre tags with data-manim attributes
pre_with_manim = soup.find_all('pre', attrs={'data-manim-binder': True})
print(f"2. Found {len(pre_with_manim)} <pre> tags with data-manim-binder attribute")

# Method 3: Look for all pre tags
all_pre = soup.find_all('pre')
print(f"3. Found {len(all_pre)} total <pre> tags")

pre_with_scene = 0
for pre in all_pre:
    code = pre.get_text().strip()
    if 'class' in code and 'Scene' in code:
        pre_with_scene += 1
        # Check if it has a parent div.highlight
        parent_highlight = pre.find_parent('div', class_='highlight')
        if not parent_highlight:
            print(f"   - Found Scene example NOT in div.highlight: {code[:50]}...")

print(f"   - {pre_with_scene} contain 'class' and 'Scene'\n")

# Method 4: Raw regex search
scene_classes = re.findall(r'class\s+(\w+)\s*\([^)]*Scene[^)]*\)', html)
print(f"4. Regex found {len(scene_classes)} Scene class definitions")
print(f"   First 10: {scene_classes[:10]}\n")

# Method 5: Check structure of a few examples
print("5. Examining structure of first few Scene examples:")
scene_count = 0
for pre in all_pre:
    code = pre.get_text().strip()
    if 'class' in code and 'Scene' in code:
        scene_count += 1
        if scene_count <= 3:
            # Check parent structure
            parent = pre.parent
            grandparent = parent.parent if parent else None
            print(f"\n   Example {scene_count}:")
            print(f"   - Pre tag attrs: {pre.attrs}")
            print(f"   - Parent: {parent.name if parent else 'None'} {parent.get('class', []) if parent else ''}")
            print(f"   - Grandparent: {grandparent.name if grandparent else 'None'} {grandparent.get('class', []) if grandparent else ''}")
            print(f"   - Code preview: {code[:60]}...")