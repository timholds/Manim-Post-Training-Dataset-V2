# Reducible Dataset Scene Breakdown

## Total ManimCE Scenes: 82

### Quality Assessment

**GOOD NEWS**: The asset-free scenes are NOT trivial! They are high-quality, complex educational animations from a popular YouTube channel.

## Asset-Free Scenes (~42 scenes, 51%)

### 1. MarchingSquares (2021) - 19 scenes
**Content**: Complex algorithm visualizations
- **Introduction**: Professional title cards and question framing
- **MarchingSquaresCases**: Visualizes all 16 marching squares cases with interpolation
- **CirclesAndEllipses**: Mathematical equations with geometric demonstrations
- **ImplicitFunctionCases**: Root finding and contour generation
- **LerpImprovement**: Linear interpolation optimization
- **MarchingCubesAnimation**: 3D extension of the algorithm
- **FocusOnContour**: Zoomed scenes showing contour details
- Other utility and transition scenes

**Quality**: These are sophisticated computer graphics algorithm tutorials

### 2. PageRank (2022) - 23 scenes
**Content**: Google PageRank algorithm and Markov chains
- **MarkovChain animations**: Complex graph visualizations with probability flows
- **TransitionMatrix**: Matrix operations animated in real-time
- **EigenvalueMethod**: Mathematical eigenvalue/eigenvector visualizations
- **Stationary distributions**: Animated probability convergence
- **User simulations**: Agents moving through graphs
- **Mathematical proofs**: Step-by-step theorem demonstrations

**Quality**: Advanced CS/Math concepts with custom graph rendering

## Asset-Dependent Scenes (~40 scenes, 49%)

### 1. JPEGImageCompression (2022) - 20 scenes
**Requires**: rose.jpg, dog.png, dct.png, quantization.png, etc.
**Content**: JPEG compression algorithm demonstration
**Note**: Core algorithm could potentially work with generated test patterns

### 2. PNGvsQOI (2022) - 16 scenes  
**Requires**: Various PNG images, benchmark results, file icons
**Content**: PNG vs QOI compression comparison
**Note**: Some scenes might work with procedurally generated gradients

### 3. TSPProblem (2022) - 13 scenes
**Requires**: USA map backgrounds, ant SVG icons
**Content**: Traveling Salesman Problem algorithms
**Note**: Could potentially work with generated graphs instead of maps

### 4. PageRank - 1 scene
**Requires**: check.svg icon
**Note**: Trivial to replace or remove

## Extraction Feasibility

### Definitely Extractable (High Value)
- **All 19 MarchingSquares scenes**: Pure algorithmic visualizations
- **23 PageRank scenes**: Graph theory and linear algebra animations

### Potentially Extractable with Modifications
- Some JPEG/PNG scenes that demonstrate algorithms (not image-specific)
- TSP scenes if we replace map backgrounds with generated graphs

### Challenging to Extract
- Image compression demos that specifically show compression artifacts
- Benchmark comparison scenes
- Scenes requiring specific visual assets for context

## Recommendation

The Reducible dataset contains **42 high-quality, non-trivial scenes** that can be extracted without assets. These are professional educational animations covering:
- Computer graphics algorithms (marching squares/cubes)
- Graph theory and PageRank
- Mathematical visualizations
- Algorithm step-by-step demonstrations

These scenes would provide excellent training data for:
- Algorithm visualization
- Mathematical concept explanation
- Graph and network animations
- 3D graphics concepts
- Educational content creation

The complexity and quality far exceed typical example animations.