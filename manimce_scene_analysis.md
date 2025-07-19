# ManimCE Scene Analysis Report

## Summary

### Total Scene Classes Found: 82

#### 2021/MarchingSquares/scene.py - 19 Scene classes
- MarchingSquaresUtils (Scene)
- MarchingCubesUtils (ThreeDScene)
- TestColorInterpolation (Scene)
- Introduction (Scene)
- CirclesAndEllipses (Scene)
- ProblemSolvingTechniques (Scene)
- ImplicitFunctionCases (Scene)
- FocusOnContour (ZoomedScene)
- IntroMarchingSquaresIdea (ZoomedScene)
- MarchingSquaresCases (Scene)
- LerpImprovement (Scene)
- IntroParallelization (Scene)
- StepBack (Scene)
- MarchingCubesAnimation (ThreeDScene)
- OverlayMarchingCubes (Scene)
- TransitionToConclusion (Scene)
- Conclusion (Scene)
- Patreons (Scene)
- Test (Scene)

#### 2022/JPEGImageCompression/scenes.py - 20 Scene classes
- IntroduceRGBAndJPEG (Scene)
- JPEGDiagramScene (Scene)
- JPEGDiagramMap (MovingCameraScene)
- ShowConfusingImage (Scene)
- MotivateAndExplainRGB (ThreeDScene)
- MotivateAndExplainYCbCr (Scene)
- ImageUtils (Scene)
- DemoJPEGWithDCT2DP2 (ThreeDScene)
- AnimateIntroRect (Scene)
- SponsorRect (Scene)
- SponsorshipMessage (Scene)
- SampleLessColors (ThreeDScene)
- DSPIntro (Scene)
- AudioVideoMention (Scene)
- EnergyCompaction (Scene)
- RemovingHigherFrequencies (Scene)
- FocusOnY (Scene)
- Patreons (Scene)
- VariablesWithValueTracker (Scene) - nested in classes.py
- VariableExample (Scene) - nested in classes.py

#### 2022/PNGvsQOI - 16 Scene classes
- BenchmarkResults (Scene)
- FilteringInsertMSAD (MovingCameraScene)
- IntroPNG (ZoomedScene)
- QOIDemo (Scene)
- SumUpOfPNG (Scene)
- SumUpOfPNGPIP (Scene)
- PNGPerformance (Scene)
- QOISummary (Scene)
- Conclusion (Scene)
- Patreons (Scene)
- SceneUtils (Scene)
- LZSSText (SceneUtils)
- LZSSImageExample (Scene)
- GoBackToTextExample (Scene)
- GradientImageIntro (Scene)
- HuffmanCodeIntro (Scene)

#### 2022/PageRank - 24 Scene classes
- TransitionMatrixCorrected3 (MovingCameraScene)
- EigenvalueMethod (MovingCameraScene)
- PerformanceText (Scene)
- MarkovChainTester (Scene)
- IntroWebGraph (Scene)
- MarkovChainPageRankTitleCard (Scene)
- MarkovChainIntroEdited (Scene)
- IntroImportanceProblem (Scene)
- IntroStationaryDistribution (Scene)
- StationaryDistPreview (Scene)
- ModelingMarkovChainsLastFrame (Scene)
- Uniqueness (Scene)
- ChallengeSeparated (Scene)
- Periodicity (Scene)
- PeriodicityUsersMovement (Scene)
- IntroduceBigTheoremText (Scene)
- PageRankExtraText (Scene)
- PageRankSolution (Scene)
- PageRankAlphaIntro (Scene)
- PageRankRecap (Scene)
- EigenValueMethodFixed2 (Scene)
- EigenvalFinalScene (Scene)
- Patreons (Scene)
- BeforeAfterComparison (Scene)

#### 2022/TSPProblem - 13 Scene classes
- TSPTester (Scene)
- NearestNeighbor2 (Scene)
- GreedApproachExtraText (Scene)
- AntColonyOptimizationSteps (Scene)
- IntroPIP (Scene)
- GeneralPip (Scene)
- BackgroundImage (Scene)
- Conclusion (MovingCameraScene)
- ConclusionFlow (Scene)
- Patreons (Scene)
- CuriosityStream (Scene)
- TSPAssumptions (MovingCameraScene)
- TransitionTemplate (Scene)

## Asset Usage Analysis

### Scenes Using Assets

#### Heavy Asset Users:
1. **2022/JPEGImageCompression/scenes.py** - Extensive use of image assets:
   - `ImageMobject`: rose.jpg, dct.png, quantization.png, lossless.png, confusing_image.png, clear_image.png, r.png, shed.jpg, dog.png
   - `SVGMobject`: jpg_file.svg, empty_file.svg
   - Uses `config["assets_dir"] = "assets"`

2. **2022/PNGvsQOI** - Multiple files use assets:
   - `ImageMobject`: r.png, bw_rose.png, Lempel.png, Ziv.png, r_3_palette.png, sample_jpg, sample_png
   - Various benchmark images: icon_1.png, icon_2.png, plant_1.png, plant_2.png, kodak_1.png, kodak_2.png, game_1.png, game_2.png, texture_1.png, texture_2.png
   - `SVGMobject`: empty_file.svg, zip_side.svg, png_file.svg, trash.svg, encode_ms.svg, decode_ms.svg, comp_rate.svg
   - Uses `config["assets_dir"] = "assets"` in multiple files

3. **2022/TSPProblem** - Background images and icons:
   - `ImageMobject`: bg-75.png (used as BACKGROUND_IMG), usa-map-satellite-markers.png, transition-bg.png, usa-map-clean.png
   - `SVGMobject`: green_ant.svg, yellow_ant.svg, purple_ant.svg, yellow_purple_ant.svg
   - Uses `config["assets_dir"] = "assets"`

4. **2022/PageRank** - Minimal asset usage:
   - `SVGMobject`: check.svg
   - Uses `config["assets_dir"] = "assets"`

### Scenes WITHOUT Assets

#### 2021/MarchingSquares/scene.py
- **All 19 scenes** appear to work without any image/SVG assets
- These scenes focus on geometric shapes, mathematical functions, and procedural graphics
- Good candidates for asset-free rendering

#### 2022/PageRank
- Most scenes (23 out of 24) don't use assets except for one SVGMobject (check.svg)
- These scenes primarily work with graphs, matrices, and mathematical concepts
- Could potentially work without the check.svg asset

## Recommendations

### Best Candidates for Asset-Free Rendering:
1. **All scenes from 2021/MarchingSquares** - 19 scenes total
2. **Most scenes from 2022/PageRank** - 23 scenes (excluding the one using check.svg)

### Scenes Requiring Asset Replacement:
1. **2022/JPEGImageCompression** - Heavily relies on image processing examples
2. **2022/PNGvsQOI** - Demonstrates image compression with real images
3. **2022/TSPProblem** - Uses background maps and ant icons

Total scenes that could potentially work without assets: ~42 out of 82 scenes (approximately 51%)