# Data Source Evaluation Guide for Manim Dataset

## Critical Context
We are building a dataset to train models to generate ManimCE code. The dataset must contain:
- ManimCE scenes that can be made self-contained through reasonable transformations
- Educational examples that demonstrate diverse Manim features
- Code that renders without errors (after we process it)

**Important**: Raw scenes rarely start self-contained. We're looking for scenes that can be transformed into self-contained examples by:
- Inlining helper functions and classes
- Replacing assets with procedural alternatives
- Adding necessary imports

**Reality Check**: 
- 90% of wild Manim code uses helper functions from other files
- 50% uses some form of assets (images, SVGs, data files)
- 30% has inter-scene dependencies
- Our job is to identify which can be reasonably transformed

## STOP: Before Proposing Any New Data Source

### 1. Mandatory Pre-Checks (NO EXCEPTIONS)

#### A. Version Verification
```python
# Check if it's ManimCE (not ManimGL or old Manim)
# Look for these imports:
# ✅ CORRECT: from manim import *
# ✅ CORRECT: from manimlib.imports import * (if recent)
# ❌ WRONG: from manimlib.imports import * (if from 3b1b/manim)
# ❌ WRONG: from big_ol_pile_of_manim_imports import *
```

#### B. Minimum Requirements Checklist
- [ ] **10+ actual Scene classes** (not files, but actual `class XYZ(Scene):` definitions)
- [ ] **Can be made self-contained** - Dependencies are inlineable, not external libraries
- [ ] **Renders successfully** - Test AT LEAST 5 examples (may need to add imports/helpers)
- [ ] **Meaningful complexity** - More than 5 lines per scene average

### 2. Content Analysis (REQUIRED)

#### A. Download Random Sample
```bash
# For GitHub repositories:
wget https://raw.githubusercontent.com/USER/REPO/main/PATH/TO/FILE.py
# or
curl -O https://raw.githubusercontent.com/USER/REPO/main/PATH/TO/FILE.py
```

#### B. Analyze Code Structure
```python
# Count actual scenes and check quality
import re

with open('downloaded_file.py', 'r') as f:
    content = f.read()
    
# Check 1: Count Scene classes
scenes = re.findall(r'class\s+(\w+)\s*\([^)]*Scene[^)]*\):', content)
print(f"Scene count: {len(scenes)}")

# Check 2: Average lines per scene
if scenes:
    avg_lines = len(content.split('\n')) / len(scenes)
    print(f"Avg lines/scene: {avg_lines:.1f}")
    
# Check 3: Animation diversity
animations = {
    'play': len(re.findall(r'self\.play\(', content)),
    'wait': len(re.findall(r'self\.wait\(', content)),
    'add': len(re.findall(r'self\.add\(', content))
}
print(f"Animation calls: {animations}")

# Check 4: Dependencies analysis
assets = re.findall(r'["\']([^"\'
]+\.(png|jpg|svg|mp3|wav))["\']', content)
helper_imports = re.findall(r'from\s+\.+\s+import|from\s+\w+\s+import', content)
custom_classes = re.findall(r'class\s+(\w+)\s*\([^)]*(?<!Scene)\):', content)

print(f"\nDependency Analysis:")
print(f"Assets found: {len(assets)} - {assets[:3] if assets else 'None'}")
print(f"Local imports: {len(helper_imports)}")
print(f"Custom classes: {len(custom_classes)}")
print(f"\nAssessment: Can these be inlined/replaced? Think about it.")
```

#### C. Render Test (MANDATORY)
```bash
# Test render multiple scenes
manim -ql downloaded_file.py SceneName1
manim -ql downloaded_file.py SceneName2
manim -ql downloaded_file.py SceneName3
```

If ANY scene fails to render, investigate why before proceeding.

### 3. Automatic Disqualifiers (STOP if any are true)

❌ **Wrong Manim Version**
- Uses `manimlib` from 3b1b/manim (ManimGL)
- Uses deprecated imports like `big_ol_pile_of_manim_imports`
- Requires Cairo backend or other non-CE features

❌ **Unfixable Dependencies**
- Complex external libraries: `import custom_physics_engine`
- Large data files: `np.loadtxt("dataset_10GB.csv")`
- Non-Python dependencies: System commands, compiled libraries

⚠️ **Gray Areas (Evaluate Case-by-Case)**
- **Simple assets**: `ImageMobject("logo.png")` - Can potentially replace with shapes
- **Helper functions**: Defined elsewhere in the repo - Can inline if reasonable
- **Custom classes**: Extending Manim objects - Can inline if not too complex
- **Data files**: Small CSV/JSON - Can hardcode data if reasonable

❌ **Code Quality Issues**
- Files under 100 bytes (empty or import-only)
- Average scene length under 10 lines
- Syntax errors when parsing with Python AST
- Render failures on more than 20% of tested scenes

❌ **Content Issues**
- Majority of scenes are trivial (e.g., just `Text("Hello")`)
- Repetitive content (same animation with different text)
- No actual animations (missing `self.play()` calls)
- Copyright violations or inappropriate content

### 4. Quality Indicators (Score each 0-5)

#### Code Quality (Must average 3+)
- **Completeness** [0-5]: Full scenes with proper structure
- **Complexity** [0-5]: Demonstrates multiple Manim features
- **Diversity** [0-5]: Variety of animation types and objects
- **Transformability** [0-5]: Can be made self-contained with reasonable effort
- **Renderability** [0-5]: Scenes render without errors

#### Educational Value (Must average 3+)
- **Concept Coverage** [0-5]: Teaches different Manim concepts
- **Progression** [0-5]: Builds from simple to complex
- **Documentation** [0-5]: Comments or descriptions explain the code
- **Practical Use** [0-5]: Shows real-world applications

#### Source Reliability
- **Maintenance**: Last updated within 2 years
- **Authority**: From recognized Manim community members
- **Testing**: Evidence of code being tested/used
- **License**: Permissive license for dataset inclusion

## Required Validation Steps (DO ALL OF THESE)

### Step 1: Repository Overview
```bash
# Clone/download the repository
git clone <repo-url> temp_inspection

# Count actual Python files with content
find temp_inspection -name "*.py" -exec grep -l "class.*Scene" {} \; | wc -l

# Check file sizes (empty files are usually <100 bytes)
find temp_inspection -name "*.py" -size +100c | wc -l

# View a few random files
find temp_inspection -name "*.py" -size +100c | shuf -n 5 | xargs less
```

### Step 2: Scene Extraction Test
Extract and validate actual content:
```python
# Quick test to see what we'd actually get
import requests
import re

url = "https://raw.githubusercontent.com/USER/REPO/main/example.py"
content = requests.get(url).text
scenes = re.findall(r'class\s+(\w+)\s*\([^)]*Scene[^)]*\)', content)
print(f"Found {len(scenes)} scenes: {scenes}")
print(f"Content length: {len(content)} chars")
print(f"Has animations: {'self.play' in content}")
```

### Step 3: Comprehensive Render Test
```python
# Test multiple scenes systematically
import subprocess
import random

# Extract all scene names
scenes = re.findall(r'class\s+(\w+)\s*\([^)]*Scene[^)]*\):', content)

# Test at least 5 random scenes (or all if fewer)
test_scenes = random.sample(scenes, min(5, len(scenes)))

results = []
for scene in test_scenes:
    cmd = ['manim', '-ql', '--dry_run', 'test_file.py', scene]
    result = subprocess.run(cmd, capture_output=True)
    success = result.returncode == 0
    results.append((scene, success))
    print(f"{scene}: {'✅ PASS' if success else '❌ FAIL'}")

# Calculate success rate
success_rate = sum(1 for _, s in results if s) / len(results)
print(f"\nRender success rate: {success_rate:.1%}")
print(f"DECISION: {'✅ PROCEED' if success_rate >= 0.8 else '❌ STOP'}")
```

### Step 4: Duplicate Check
```python
# Check if content overlaps with existing sources
# Compare against our existing datasets:
# - ManimBench (407 samples)
# - ManimCE Official Docs (~87 samples)

# Look for:
# 1. Identical code snippets
# 2. Very similar examples
# 3. Same conceptual coverage

# If >30% overlap with existing sources, reconsider value
```

## Data Source Priority Matrix

### Tier 1: High Priority (Implement First)
- Official documentation examples
- Established educational channels with code
- Curated benchmark datasets
- Community example galleries

### Tier 2: Medium Priority
- Individual tutorial repositories (if complete)
- Conference/workshop materials
- University course materials

### Tier 3: Low Priority (Carefully Evaluate)
- Personal projects
- Work-in-progress tutorials
- Old/outdated repositories

## Common Pitfalls

1. **Repository Stars ≠ Quality**: A repository with many stars might still be incomplete
2. **"Tutorial" in name ≠ Educational**: Many are unfinished skeletons
3. **File count ≠ Content**: Check actual file contents, not just file count
4. **Recent commits ≠ Complete**: Active development might mean it's unfinished

## Final Evaluation Report Template

```markdown
## Source: [Repository/Source Name]

### Overview
- URL: 
- Type: [GitHub repo / Documentation / Tutorial / etc.]
- Total Scene Classes Found: 
- Successfully Rendered: X/Y (X%)
- Average Lines per Scene: 

### Quality Scores
- Code Quality: X/5
- Educational Value: X/5  
- Uniqueness: X/5

### Sample Analysis
[Paste 2-3 representative examples]

### Dependencies & Transformation Plan
- **Assets**: [List assets and proposed replacements]
  - `logo.png` → Can replace with `Circle().scale(2)` 
  - `data.csv` → Can hardcode as list if <50 values
- **Helper Functions**: [List and feasibility of inlining]
  - `from utils import rotate_around` → Simple 5-line function, easy to inline
- **Custom Classes**: [List and complexity]
  - `class CustomArrow(Arrow)` → 20 lines, reasonable to inline

### Overlap with Existing Data
[Estimate % overlap with current datasets]

### Recommendation
[ ] ✅ HIGH PRIORITY - Implement immediately
[ ] ⚠️ MEDIUM PRIORITY - Implement with modifications
[ ] ❌ DO NOT IMPLEMENT - [Reason]

### Implementation Notes
[Any special handling required]
```

## Real Example: Failed Evaluation

### Source: Elteoremadebeethoven/ManimCE-tutorial
This source FAILED evaluation. Here's why:

```python
# Downloaded _07_transformations.py
from manim import *
# That's it. The ENTIRE file. Empty placeholder.

# Downloaded _01_render_settings.py  
from manim import *

class Scene1(Scene):
    def construct(self):
        t = Text("SCENE 1")
        self.play(Write(t))
        self.wait()
# Trivial 3-line example
```

**Problems Found:**
- 12/18 files were empty (just imports)
- Remaining 6 files had only basic examples
- Average lines per scene: 7 (below 15 threshold)
- No educational progression
- No complex animations demonstrated

**Decision: ❌ DO NOT IMPLEMENT**

## Example Evaluation

### Good Source Example:
```python
# File: projectile_motion.py
class ProjectileMotion(Scene):
    """Demonstrates physics animation of projectile motion with trajectory."""
    def construct(self):
        # Create ground
        ground = Line(LEFT * 7, RIGHT * 7).shift(DOWN * 3)
        
        # Create projectile
        ball = Dot(radius=0.2, color=RED).move_to(LEFT * 6 + DOWN * 2.8)
        
        # Create trajectory path
        path = ParametricFunction(
            lambda t: np.array([
                -6 + 2 * t,
                -2.8 + 4 * t - 0.5 * 9.8 * t**2,
                0
            ]),
            t_range=[0, 1.8],
            color=YELLOW
        )
        
        self.play(Create(ground))
        self.play(Create(ball))
        self.play(
            MoveAlongPath(ball, path),
            Create(path),
            run_time=2,
            rate_func=linear
        )
        self.wait()
```

### Bad Source Example:
```python
# File: scene1.py
from manim import *

class Scene1(Scene):
    def construct(self):
        t = Text("SCENE 1")
        self.play(Write(t))
        self.wait()
```

## Critical Reminders

1. **NO ENGINEERING WORK** until evaluation is complete and approved
2. **Test actual rendering** - Don't trust that code works
3. **Check for ManimCE** specifically - Not ManimGL or old versions
4. **Verify transformable scenes** - Dependencies can be reasonably inlined/replaced
5. **Quality threshold**: If <80% of tested scenes render, STOP
6. **Overlap threshold**: If >30% duplicates existing data, STOP
7. **Complexity threshold**: If average <15 lines per scene, STOP

## Asset Handling Guidelines

### Simple Asset Replacements
```python
# Original: ImageMobject("logo.png")
# Replace with: 
logo = VGroup(
    Circle(radius=1, color=BLUE),
    Text("LOGO", color=WHITE).scale(0.5)
)

# Original: ImageMobject("arrow.png") 
# Replace with:
arrow = Arrow(LEFT, RIGHT, color=GREEN)

# Original: SVGMobject("diagram.svg")
# Replace with procedural drawing or skip if too complex
```

### Helper Function Inlining
```python
# If repo has: from utils import spiral_path
# Look for the function definition and inline it:
def spiral_path(t):
    return np.array([
        np.cos(2 * PI * t) * (1 + 0.5 * t),
        np.sin(2 * PI * t) * (1 + 0.5 * t),
        0
    ])
```

### When to Skip
- Asset is core to the animation (e.g., "explaining this specific image")
- Replacement would fundamentally change the educational value
- Dependencies are too complex to inline (>100 lines)
- External data is essential and large

## Example Sources to Search For

### High-Value Targets
- Official ManimCommunity example galleries
- YouTube educator code repositories (even with assets/helpers)
- University course materials with Manim assignments
- Manim conference/workshop repositories
- Community-curated example collections

### Search Keywords
- "manim community examples"
- "manimce tutorial code"
- "manim workshop materials"
- "manim course assignments"
- NOT "manimgl" or "3b1b manim"