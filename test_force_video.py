from manim import *

class ForceVideoTest(Scene):
    def construct(self):
        # Try setting the config to force video
        config.save_last_frame = False
        text = Text("Test")
        self.add(text)