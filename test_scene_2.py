
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
