"""
Test extracting and rendering a self-contained scene from Reducible
"""

import sys
import os

# Test 1: Extract the simple Test scene from MarchingSquares
test_scene_1 = '''
from manim import *
import numpy as np

class Test(Scene):
    def construct(self):
        triangle = Polygon(LEFT, RIGHT, UP * 2)
        triangle.set_stroke(width=0)
        triangle.set_fill(color=[RED, YELLOW, BLUE], opacity=1)
        triangle.set_sheen_direction([-1, 0, 0])
        # triangle.set_sheen_direction([0, 1, 0]).rotate_sheen_direction(PI / 2)
        self.add(triangle)
        self.wait()
'''

# Test 2: Extract a scene that needs color constants
test_scene_2 = '''
from manim import *
import sys
import os

# Add common directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Reducible/2022/common'))
from reducible_colors import *

class IntroduceRGBAndJPEG(Scene):
    def construct(self):
        r_t = Text("R", font="SF Mono", weight=MEDIUM).scale(3).set_color(PURE_RED)
        g_t = Text("G", font="SF Mono", weight=MEDIUM).scale(3).set_color(PURE_GREEN)
        b_t = Text("B", font="SF Mono", weight=MEDIUM).scale(3).set_color(PURE_BLUE)

        rgb_vg_h = VGroup(r_t, g_t, b_t).arrange(RIGHT, buff=2)
        
        self.play(LaggedStartMap(FadeIn, rgb_vg_h, lag_ratio=0.5))
        self.wait(2)
'''

# Write test files
with open("test_scene_1.py", "w") as f:
    f.write(test_scene_1)

with open("test_scene_2.py", "w") as f:
    f.write(test_scene_2)

print("Test scene files created:")
print("- test_scene_1.py: Simple self-contained scene")
print("- test_scene_2.py: Scene with color dependencies")