from manim import *

class StaticScene(Scene):
    def construct(self):
        # This only uses self.add() - no animation
        text = Text("Static Scene Test")
        self.add(text)