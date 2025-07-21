"""
Beethoven (Elteoremadebeethoven tutorial) extractor with improved dependency handling.

This extractor creates self-contained scene files that include all necessary dependencies,
fix deprecated functions, and modernize API usage for compatibility with current ManimCE.
"""

import ast
import logging
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any, Iterator
from urllib.parse import urljoin

from ..base import BaseExtractor


class BeethovenExtractor(BaseExtractor):
    """Extract scenes from Elteoremadebeethoven's ManimCE tutorial repository"""
    
    source_id = "beethoven"
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.repo_url = "https://github.com/Elteoremadebeethoven/ManimCE-tutorial"
        self.base_cache_dir = Path(__file__).parent.parent.parent / "cache"
        self.cache_dir = self.base_cache_dir / "elteoremadebeethoven_tutorial"
        
        # Mapping of deprecated functions to modern equivalents
        self.deprecated_functions = {
            'ShowCreationThenDestructionAround': 'Circumscribe',
            'FadeInFromLarge': 'FadeIn',  # scale_factor handled separately
            'FadeToColor': 'Transform',  # needs special handling
        }
        
        # Functions that need modern API updates
        self.api_updates = {
            'Code': self._fix_code_constructor,
        }

    def _validate_config(self) -> None:
        """Validate configuration for this extractor."""
        # No special config validation needed for Beethoven extractor
        pass

    def estimate_sample_count(self) -> Optional[int]:
        """Return estimated number of samples (for progress tracking)."""
        # Estimate based on typical tutorial structure
        return 35  # Approximate number of scenes across all tutorial files

    def extract(self) -> Iterator[Dict[str, Any]]:
        """Extract samples from the Beethoven tutorial cache."""
        scenes = self.extract_scenes()
        for scene in scenes:
            yield self.transform_sample(scene)

    def get_source_info(self) -> Dict[str, Any]:
        return {
            "name": "beethoven",
            "description": "Elteoremadebeethoven's ManimCE tutorial with basic animations and positioning",
            "url": self.repo_url,
            "type": "tutorial",
            "language": "python",
            "framework": "manim_ce"
        }

    def _download_repository(self) -> bool:
        """Download the Beethoven tutorial repository if not present."""
        try:
            self.logger.info(f"Downloading Beethoven tutorial repository to {self.cache_dir}")
            self.base_cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Clone the repository
            cmd = [
                'git', 'clone',
                self.repo_url,
                str(self.cache_dir)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.logger.info("Successfully downloaded Beethoven tutorial repository")
                return True
            else:
                self.logger.error(f"Failed to clone repository: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error downloading repository: {e}")
            return False

    def extract_scenes(self) -> List[Dict[str, Any]]:
        """Extract and process all scenes from the Beethoven tutorial"""
        scenes = []
        
        # Check if cache directory exists, if not, download it
        if not self.cache_dir.exists():
            self.logger.info(f"Cache directory {self.cache_dir} does not exist, downloading...")
            if not self._download_repository():
                self.logger.error("Failed to download Beethoven tutorial repository")
                return scenes
        
        # Verify the directory now exists and has content
        if not self.cache_dir.exists() or not any(self.cache_dir.glob("_*.py")):
            self.logger.error(f"Cache directory {self.cache_dir} is empty or missing tutorial files")
            return scenes
            
        # Process each tutorial file
        tutorial_files = sorted(self.cache_dir.glob("_*.py"))
        self.logger.info(f"Found {len(tutorial_files)} tutorial files to process")
        
        for file_path in tutorial_files:
            self.logger.info(f"Processing {file_path.name}")
            try:
                file_scenes = self._extract_file_scenes(file_path)
                scenes.extend(file_scenes)
            except Exception as e:
                self.logger.error(f"Error processing {file_path.name}: {e}")
                
        return scenes

    def _extract_file_scenes(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract scenes from a single tutorial file"""
        scenes = []
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except Exception as e:
            self.logger.error(f"Failed to read {file_path}: {e}")
            return scenes

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            self.logger.error(f"Syntax error in {file_path}: {e}")
            return scenes

        # Extract tutorial metadata
        tutorial_number = self._extract_tutorial_number(file_path.name)
        tutorial_name = self._extract_tutorial_name(file_path.name)
        
        scene_index = 0
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                # Check if it's a Scene class
                if self._is_scene_class(node):
                    try:
                        scene_data = self._extract_scene_data(
                            node, content, file_path, 
                            tutorial_number, tutorial_name, scene_index
                        )
                        if scene_data:
                            scenes.append(scene_data)
                            scene_index += 1
                    except Exception as e:
                        self.logger.error(f"Error extracting scene {node.name} from {file_path.name}: {e}")
                        
        return scenes

    def _extract_tutorial_number(self, filename: str) -> int:
        """Extract tutorial number from filename like _02_basic_animations.py"""
        match = re.search(r'_(\d+)_', filename)
        return int(match.group(1)) if match else 0

    def _extract_tutorial_name(self, filename: str) -> str:
        """Extract tutorial name from filename"""
        # Remove prefix number and extension
        name = re.sub(r'^_\d+_', '', filename)
        name = re.sub(r'\.py$', '', name)
        return name.replace('_', ' ').title()

    def _is_scene_class(self, node: ast.ClassDef) -> bool:
        """Check if class inherits from Scene"""
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == 'Scene':
                return True
        return False

    def _uses_meaningful_assets(self, class_source: str) -> bool:
        """Check if scene uses meaningful assets that shouldn't be replaced with placeholders"""
        
        # Look for ImageMobject usage - even generic placeholders should be excluded
        # because they represent scenes that were meant to show actual meaningful images
        if 'ImageMobject(' in class_source:
            # Even ImageMobject("image") represents a scene that was designed to show
            # a meaningful image but uses a placeholder. We should exclude these
            # to avoid training the model on scenes that misrepresent the intent.
            return True
        
        # Check for SVGMobject usage
        if 'SVGMobject(' in class_source:
            return True
            
        # Check for external file loading
        asset_indicators = [
            'np.loadtxt(',
            'pd.read_csv(',
            'with open(',
            'Path(__file__)',
            'script_location',
            'assets/',
            '.wav', '.mp3', '.ogg',  # Audio files
        ]
        
        for indicator in asset_indicators:
            if indicator in class_source:
                return True
                
        return False

    def _extract_scene_data(self, class_node: ast.ClassDef, content: str, 
                          file_path: Path, tutorial_number: int, tutorial_name: str, 
                          scene_index: int) -> Optional[Dict[str, Any]]:
        """Extract data for a single scene"""
        
        # Get the source code for the class
        class_source = ast.get_source_segment(content, class_node)
        if not class_source:
            return None

        # Check if scene uses assets that we can't properly replace
        if self._uses_meaningful_assets(class_source):
            self.logger.debug(f"Skipping {class_node.name} - uses meaningful assets")
            return None

        # Build standalone scene code
        standalone_code = self._build_standalone_scene(
            class_source, content, file_path, class_node.name
        )

        # Generate description
        description = self._generate_description(class_node, tutorial_name)

        return {
            'description': description,
            'code': standalone_code,
            'source': 'beethoven',
            'metadata': {
                'scene_index': scene_index,
                'scene_name': class_node.name,
                'topic': tutorial_name.lower().replace(' ', '_'),
                'tutorial_file': file_path.name,
                'tutorial_number': tutorial_number
            }
        }

    def _build_standalone_scene(self, class_source: str, full_content: str, 
                               file_path: Path, scene_name: str) -> str:
        """Build a standalone scene file with all dependencies"""
        
        parts = [
            '# Standard imports',
            'from manim import *',
            'import numpy as np',
            'import itertools as it',
            ''
        ]

        # Add custom classes and functions needed for specific tutorials
        if 'basic_positions' in str(file_path) or 'ScreenGrid' in class_source:
            parts.extend([
                '# Custom Grid classes for positioning tutorial',
                self._get_grid_classes(),
                ''
            ])

        if 'tex_and_texts' in str(file_path) and ('FrenchCursive' in class_source or 'MusicTeX' in class_source):
            parts.extend([
                '# Custom TeX templates',
                self._get_tex_templates(),
                ''
            ])

        if 'tex_and_texts_as_arrays' in str(file_path) and 'get_tex_indexes' in class_source:
            parts.extend([
                '# Helper function for tex indexing',
                self._get_tex_indexes_function(),
                ''
            ])

        # Fix deprecated functions and API issues in the class source
        fixed_class_source = self._fix_scene_code(class_source)

        # Add the scene class
        parts.append('# Scene class')
        parts.append(fixed_class_source)

        return '\n'.join(parts)

    def _fix_scene_code(self, code: str) -> str:
        """Fix deprecated functions and API issues in scene code"""
        fixed_code = code

        # Fix deprecated functions
        for old_func, new_func in self.deprecated_functions.items():
            if old_func in fixed_code:
                if old_func == 'ShowCreationThenDestructionAround':
                    fixed_code = fixed_code.replace(
                        f'{old_func}(', f'{new_func}('
                    )
                elif old_func == 'FadeInFromLarge':
                    # Handle scale_factor parameter
                    pattern = r'FadeInFromLarge\(([^,)]+)(?:,\s*scale_factor=\d+)?\)'
                    fixed_code = re.sub(pattern, r'FadeIn(\1)', fixed_code)
                elif old_func == 'FadeToColor':
                    # Convert FadeToColor(obj, color) to obj.animate.set_color(color)
                    pattern = r'FadeToColor\(([^,)]+),\s*([^)]+)\)'
                    fixed_code = re.sub(pattern, r'\1.animate.set_color(\2)', fixed_code)

        # Fix Code constructor for modern ManimCE
        if 'Code(' in fixed_code:
            fixed_code = self._fix_code_constructor(fixed_code)

        # Note: We no longer replace ImageMobject with placeholders
        # Instead, we filter out scenes that use meaningful assets

        # Fix config access for frame dimensions
        if 'config["frame_width"]' in fixed_code:
            fixed_code = fixed_code.replace('config["frame_width"]', 'config.frame_width')

        return fixed_code

    def _fix_code_constructor(self, code: str) -> str:
        """Fix Code constructor calls for modern ManimCE API"""
        # Find Code constructor calls and fix them
        pattern = r'Code\(\s*code=([^,)]+)(?:,([^)]*))?\)'
        
        def replace_code(match):
            code_param = match.group(1)
            other_params = match.group(2) if match.group(2) else ''
            
            # Ensure language parameter is present
            if 'language=' not in other_params:
                if other_params:
                    other_params = f'language="python", {other_params}'
                else:
                    other_params = 'language="python"'
            
            return f'Code({code_param}, {other_params})'
        
        return re.sub(pattern, replace_code, code)

    def _get_grid_classes(self) -> str:
        """Get the Grid and ScreenGrid classes for positioning tutorial"""
        return '''class Grid(VGroup):
    def __init__(self, rows, columns, height=6, width=6, **kwargs):
        self.height_g = height
        self.width_g = width
        super().__init__(**kwargs)

        x_step = self.width_g / columns
        y_step = self.height_g / rows

        for x in np.arange(0, self.width_g + x_step, x_step):
            self.add(Line(
                [x - self.width_g / 2., -self.height_g / 2., 0],
                [x - self.width_g / 2., self.height_g / 2., 0],
            ))
        for y in np.arange(0, self.height_g + y_step, y_step):
            self.add(Line(
                [-self.width_g / 2., y - self.height_g / 2., 0],
                [self.width_g / 2., y - self.height_g / 2., 0]
            ))


class ScreenGrid(VGroup):
    def __init__(
            self,
            rows=8,
            columns=14,
            height=None,
            width=14,
            grid_stroke=0.5,
            grid_color=WHITE,
            axis_color=RED,
            axis_stroke=2,
            labels_scale=0.25,
            labels_buff=0,
            number_decimals=2,
            **kwargs):
        self.height_g = height if height is not None else config.frame_height
        self.width_g = width
        self.grid_stroke = grid_stroke
        self.grid_color = grid_color
        self.axis_color = axis_color
        self.axis_stroke = axis_stroke
        self.labels_scale = labels_scale
        self.labels_buff = labels_buff
        self.number_decimals = number_decimals
        super().__init__(**kwargs)
        
        grid = Grid(width=self.width_g, height=self.height_g, rows=rows, columns=columns)
        grid.set_stroke(self.grid_color, self.grid_stroke)

        vector_ii = ORIGIN + np.array((- self.width_g / 2, - self.height_g / 2, 0))
        vector_si = ORIGIN + np.array((- self.width_g / 2, self.height_g / 2, 0))
        vector_sd = ORIGIN + np.array((self.width_g / 2, self.height_g / 2, 0))

        axes_x = Line(LEFT * self.width_g / 2, RIGHT * self.width_g / 2)
        axes_y = Line(DOWN * self.height_g / 2, UP * self.height_g / 2)

        axes = VGroup(axes_x, axes_y).set_stroke(self.axis_color, self.axis_stroke)

        divisions_x = self.width_g / columns
        divisions_y = self.height_g / rows

        directions_buff_x = [UP, DOWN]
        directions_buff_y = [RIGHT, LEFT]
        dd_buff = [directions_buff_x, directions_buff_y]
        vectors_init_x = [vector_ii, vector_si]
        vectors_init_y = [vector_si, vector_sd]
        vectors_init = [vectors_init_x, vectors_init_y]
        divisions = [divisions_x, divisions_y]
        orientations = [RIGHT, DOWN]
        labels = VGroup()
        set_changes = zip([columns, rows], divisions, orientations, [0, 1], vectors_init, dd_buff)
        for c_and_r, division, orientation, coord, vi_c, d_buff in set_changes:
            for i in range(1, c_and_r):
                for v_i, directions_buff in zip(vi_c, d_buff):
                    ubication = v_i + orientation * division * i
                    coord_point = round(ubication[coord], self.number_decimals)
                    label = Text(f"{coord_point}", font="Arial", stroke_width=0).scale(self.labels_scale)
                    label.next_to(ubication, directions_buff, buff=self.labels_buff)
                    labels.add(label)

        self.add(grid, axes, labels)'''

    def _get_tex_templates(self) -> str:
        """Get custom TeX templates for French Cursive and MusicTeX"""
        return '''# Custom TeX templates
TemplateForFrenchCursive = TexTemplate(
    preamble=r"""
\\usepackage[english]{babel}
\\usepackage{amsmath}
\\usepackage{amssymb}
\\usepackage[T1]{fontenc}
\\usepackage[default]{frcursive}
\\usepackage[eulergreek,noplusnominus,noequal,nohbar,%
nolessnomore,noasterisk]{mathastext}
"""
)

def FrenchCursive(*tex_strings, **kwargs):
    return Tex(*tex_strings, tex_template=TemplateForFrenchCursive, **kwargs)

TemplateForMusicTeX = TexTemplate(
    preamble=r"""
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage{mtxlatex}
\\usepackage{graphicx}
"""
)

def MusicTeX(*tex_strings, **kwargs):
    return Tex(
        *tex_strings,
        tex_template=TemplateForMusicTeX,
        tex_environment="music",
        **kwargs
    )'''

    def _get_tex_indexes_function(self) -> str:
        """Get the get_tex_indexes helper function"""
        return '''def get_tex_indexes(
        tex,
        number_config={"height": 0.28},
        colors=[RED, TEAL, PURPLE, GREEN, BLUE],
        funcs=[lambda mob, tex: mob.next_to(tex, DOWN, buff=0)]
    ):
    numbers = VGroup()
    colors = it.cycle(colors)
    for i, s in enumerate(tex):
        n = Text(f"{i}", color=next(colors), **number_config)
        for f in funcs:
            f(n, s)
        numbers.add(n)
    return numbers'''

    def _generate_description(self, class_node: ast.ClassDef, tutorial_name: str) -> str:
        """Generate a description for the scene"""
        scene_name = class_node.name
        
        # Extract docstring if available
        docstring = ast.get_docstring(class_node)
        if docstring:
            # Clean up the docstring
            description = ' '.join(docstring.split())
            return f"{tutorial_name}: {description}"
        
        # Generate description based on scene name and tutorial
        scene_words = re.findall(r'[A-Z][a-z]*', scene_name)
        scene_description = ' '.join(scene_words).lower()
        
        return f"{tutorial_name}: {scene_description} tutorial scene"