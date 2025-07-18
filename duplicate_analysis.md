# Duplicate Code Analysis

## Summary of Findings

I searched for the three specific descriptions you mentioned and found clear evidence of code duplicates in the dataset:

### 1. "Display a green dot at the center of the screen. After a short pause, zooming functionality is..."

**Found 2 instances with identical descriptions but different code:**

- **Item index 150** (train split):
  ```python
  class UseZoomedScene(ZoomedScene):
      def construct(self):
          dot = Dot().set_color(GREEN)
          self.add(dot)
          self.wait(1)
          self.activate_zooming(animate=False)
          self.wait(1)
          self.play(dot.animate.shift(LEFT))
  ```

- **Item index 378** (test split):
  ```python
  class ChangingZoomScale(ZoomedScene):
      def __init__(self, **kwargs):
          ZoomedScene.__init__(self, zoom_factor=0.3, zoomed_display_height=1, ...)
      
      def construct(self):
          dot = Dot().set_color(GREEN)
          sq = Circle(fill_opacity=1, radius=0.2).next_to(dot, RIGHT)
          self.add(dot, sq)
          self.wait(1)
          self.activate_zooming(animate=False)
          self.wait(1)
          self.play(dot.animate.shift(LEFT * 0.3))
          self.play(self.zoomed_camera.frame.animate.scale(4))
          self.play(self.zoomed_camera.frame.animate.shift(0.5 * DOWN))
  ```

### 2. "Display a large circle with two tangent lines..."

**Found 2 instances with identical descriptions but COMPLETELY DIFFERENT code:**

- **Item index 59** (train split) - CORRECT CODE:
  ```python
  class TangentLineExample(Scene):
      def construct(self):
          circle = Circle(radius=2)
          line_1 = TangentLine(circle, alpha=0.0, length=4, color=BLUE_D)
          line_2 = TangentLine(circle, alpha=0.4, length=4, color=GREEN)
          self.add(circle, line_1, line_2)
  ```

- **Item index 131** (train split) - WRONG CODE (creates vectors, not tangent lines):
  ```python
  class VectorExample(Scene):
      def construct(self):
          plane = NumberPlane()
          vector_1 = Vector([1,2])
          vector_2 = Vector([-5,-2])
          self.add(plane, vector_1, vector_2)
  ```

### 3. "Display a red semi-transparent square on the left and a green semi-transparent triangle on the right..."

**Found 2 instances with identical descriptions but different code:**

- **Item index 232** (train split):
  ```python
  class MovingCameraCenter(MovingCameraScene):
      def construct(self):
          s = Square(color=RED, fill_opacity=0.5).move_to(2 * LEFT)
          t = Triangle(color=GREEN, fill_opacity=0.5).move_to(2 * RIGHT)
          self.wait(0.3)
          self.add(s, t)
          self.play(self.camera.frame.animate.move_to(s))
          self.wait(0.3)
          self.play(self.camera.frame.animate.move_to(t))
  ```

- **Item index 239** (train split) - Different colors and additional zooming:
  ```python
  class MovingAndZoomingCamera(MovingCameraScene):
      def construct(self):
          s = Square(color=BLUE, fill_opacity=0.5).move_to(2 * LEFT)
          t = Triangle(color=YELLOW, fill_opacity=0.5).move_to(2 * RIGHT)
          self.add(s, t)
          self.play(self.camera.frame.animate.move_to(s).set(width=s.width*2))
          self.wait(0.3)
          self.play(self.camera.frame.animate.move_to(t).set(width=t.width*2))
          self.play(self.camera.frame.animate.move_to(ORIGIN).set(width=14))
  ```

## Key Issues Identified

1. **Exact Description Duplicates**: Multiple samples share identical descriptions despite having different code implementations.

2. **Incorrect Code-Description Matching**: In the tangent lines example, one instance has code that creates vectors on a number plane, which is completely unrelated to the description about tangent lines to a circle.

3. **Cross-Split Contamination**: Some duplicates appear across train/test splits (items 150 vs 378).

4. **Variations in Implementation**: Even when descriptions are identical, the code implementations vary in complexity and features (e.g., the zooming scene examples).

## Recommendations

1. The deduplication process should check for exact description matches, not just code matches.
2. Quality control is needed to ensure code matches its description.
3. Consider whether having multiple implementations of the same description is intentional for diversity, and if so, the descriptions should be slightly varied to reflect the differences.