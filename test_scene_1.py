
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
