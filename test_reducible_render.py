"""
Test script to render a simple scene from Reducible dataset
"""

import sys
import os

# Add the Reducible directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Reducible/2021/MarchingSquares'))

# Import the required modules
from manim import *
from math import floor
import random
from lookup import LookupTable
import itertools
import numpy as np

np.random.seed(0)

# Define the missing color constants
INSIDE_COLOR = PURE_GREEN
OUTSIDE_COLOR = BLUE
CONTOUR_COLOR = YELLOW

# Import only the MarchingSquare class
from scene import MarchingSquare

# Create a minimal test scene
class TestMarchingSquareScene(Scene):
    def construct(self):
        # Create a simple text to verify rendering works
        title = Text("Marching Squares Test", font_size=48)
        self.play(FadeIn(title))
        self.wait(1)
        
        # Test creating a simple square
        square = Square(side_length=2, color=CONTOUR_COLOR)
        self.play(Transform(title, square))
        self.wait(1)
        
        self.play(FadeOut(square))