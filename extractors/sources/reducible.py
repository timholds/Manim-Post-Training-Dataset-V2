"""
Extractor for Reducible dataset - extracts asset-free ManimCE scenes
"""

import ast
import os
import re
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Iterator
import json
import logging

from ..base import BaseExtractor
from ..registry import register_extractor

logger = logging.getLogger(__name__)


@register_extractor
class ReducibleExtractor(BaseExtractor):
    """Extracts asset-free scenes from the Reducible dataset"""
    
    source_id = "reducible"
    source_name = "Reducible - Advanced Algorithm Visualizations (Marching Squares, PageRank, Markov Chains)"
    priority = 8  # High priority for quality educational content
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # Configure quality validation to allow static scenes (no animation commands)
        if config is None:
            config = {}
        
        # Set up config to allow scenes without animation methods
        if "_quality_config" not in config:
            config["_quality_config"] = {
                "allow_through": {
                    "no_animation_methods": {
                        "enabled": True
                    }
                }
            }
        
        super().__init__(config)
        
        # Asset-free scenes to extract
        self.target_files = {
            "2021/MarchingSquares/scene.py": {
                "common_imports": [],
                "skip_scenes": []  # All scenes are asset-free
            },
            "2022/PageRank/jesus_animations.py": {
                "common_imports": ["reducible_colors", "markov_chain", "classes"],
                "skip_scenes": []  # We'll identify which use assets during extraction
            },
            "2022/PageRank/markov_chain.py": {
                "common_imports": ["reducible_colors", "functions"],
                "skip_scenes": []
            }
        }
        
    def _validate_config(self) -> None:
        """Validate configuration for this extractor."""
        self.repo_path = Path(self.config.get("repo_path", "raw/Reducible"))
        self.repo_url = "https://github.com/nipunramk/Reducible.git"
        
        # Download repository if it doesn't exist
        if not self.repo_path.exists():
            logger.info(f"Reducible repository not found at {self.repo_path}, downloading...")
            if not self._download_repository():
                raise ValueError(f"Failed to download Reducible repository to {self.repo_path}")
    
    def _download_repository(self) -> bool:
        """Download the Reducible repository if not present."""
        try:
            logger.info(f"Downloading Reducible repository to {self.repo_path}")
            # Create parent directory if needed
            self.repo_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Clone the repository
            cmd = [
                'git', 'clone',
                self.repo_url,
                str(self.repo_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("Successfully downloaded Reducible repository")
                return True
            else:
                logger.error(f"Failed to clone repository: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error downloading repository: {e}")
            return False
    
    def estimate_sample_count(self) -> Optional[int]:
        """Return estimated number of samples."""
        # Based on our analysis: 19 + 24 = 43 asset-free scenes
        return 43
    
    def extract(self) -> Iterator[Dict[str, Any]]:
        """Extract samples from the Reducible repository."""
        
        for file_path, config in self.target_files.items():
            full_path = self.repo_path / file_path
            if not full_path.exists():
                logger.warning(f"{file_path} not found")
                continue
                
            logger.info(f"Processing {file_path}...")
            scenes = self.extract_scenes_from_file(
                full_path, 
                config["common_imports"],
                config["skip_scenes"]
            )
            
            for scene in scenes:
                yield {
                    "description": f"Scene: {scene['name']} from {scene['file']}",
                    "code": scene['code'],
                    "metadata": {
                        "scene_name": scene['name'],
                        "original_file": scene['file'],
                        "common_imports": scene['common_imports']
                    }
                }
    
    def extract_scenes_from_file(self, 
                                file_path: Path, 
                                common_imports: List[str],
                                skip_scenes: List[str]) -> List[Dict]:
        """Extract all Scene classes from a single file"""
        
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Parse the AST
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return []
            
        # Extract imports
        imports = self._extract_imports(tree)
        
        # Extract all Scene classes
        scenes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if it inherits from Scene
                if self._inherits_from_scene(node):
                    scene_name = node.name
                    
                    if scene_name in skip_scenes:
                        continue
                    
                    # Skip utility base classes (they're meant to be inherited, not rendered)
                    if scene_name.endswith('Utils'):
                        logger.debug(f"Skipping {scene_name} - utility base class")
                        continue
                        
                    # Check if scene uses assets
                    if self._uses_assets(node):
                        logger.debug(f"Skipping {scene_name} - uses assets")
                        continue
                        
                    # Extract the scene
                    scene_data = self._extract_scene(
                        node, 
                        content, 
                        imports, 
                        common_imports,
                        file_path
                    )
                    
                    if scene_data:
                        scenes.append(scene_data)
                        
        return scenes
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract only module-level import statements from AST"""
        imports = []
        
        # Skip problematic imports (we handle these specially)
        skip_modules = ['lookup', 'markov_chain', 'classes', 'functions', 'reducible_colors']
        
        # Only look at module-level nodes, not inside functions/classes
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if not any(skip in alias.name for skip in skip_modules):
                        if alias.asname:
                            imports.append(f"import {alias.name} as {alias.asname}")
                        else:
                            imports.append(f"import {alias.name}")
                    
            elif isinstance(node, ast.ImportFrom):
                if node.module and not any(skip in node.module for skip in skip_modules):
                    names = [alias.name for alias in node.names]
                    # Fix known incorrect imports
                    if node.module == 'scipy' and 'sqrt' in names:
                        # Replace with correct import
                        imports.append("from numpy import sqrt")
                    elif names == ['*']:
                        imports.append(f"from {node.module} import *")
                    else:
                        imports.append(f"from {node.module} import {', '.join(names)}")
                        
        return imports
    
    def _inherits_from_scene(self, class_node: ast.ClassDef) -> bool:
        """Check if class inherits from Scene or its variants"""
        scene_types = ['Scene', 'MovingCameraScene', 'ThreeDScene', 'ZoomedScene']
        
        for base in class_node.bases:
            if isinstance(base, ast.Name) and base.id in scene_types:
                return True
            # Handle inheritance from classes with modules
            elif isinstance(base, ast.Attribute) and base.attr in scene_types:
                return True
                
        return False
    
    def _uses_assets(self, class_node: ast.ClassDef) -> bool:
        """Check if scene uses image or SVG assets"""
        asset_indicators = [
            'ImageMobject',
            'SVGMobject', 
            'config["assets_dir"]',
            'config[\'assets_dir\']',
            '.png',
            '.jpg', 
            '.jpeg',
            '.svg',
            'BACKGROUND_IMG'
        ]
        
        # Convert AST to string for simple checking
        class_str = ast.unparse(class_node)
        
        for indicator in asset_indicators:
            if indicator in class_str:
                return True
                
        return False
    
    def _extract_scene(self, 
                      class_node: ast.ClassDef,
                      full_content: str,
                      imports: List[str],
                      common_imports: List[str],
                      file_path: Path) -> Optional[Dict]:
        """Extract a single scene with its dependencies"""
        
        # Get the source code for this class
        class_source = ast.get_source_segment(full_content, class_node)
        
        if not class_source:
            return None
            
        # Collect any helper functions defined outside the class
        helper_functions = self._extract_helper_functions(class_node, full_content)
        
        # Build the standalone scene code
        scene_code = self._build_standalone_scene(
            class_node,
            class_source,
            imports,
            common_imports,
            helper_functions,
            file_path,
            full_content
        )
        
        return {
            "name": class_node.name,
            "file": str(file_path.relative_to(self.repo_path)),
            "code": scene_code,
            "imports": imports,
            "common_imports": common_imports
        }
    
    def _extract_helper_functions(self, 
                                 class_node: ast.ClassDef, 
                                 content: str) -> List[str]:
        """Extract helper functions that the scene might use"""
        helper_funcs = []
        
        # Parse the full file
        tree = ast.parse(content)
        
        # Get all function names used in the class
        used_names = set()
        for node in ast.walk(class_node):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
                
        # Find function definitions that match used names
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name in used_names:
                func_source = ast.get_source_segment(content, node)
                if func_source:
                    # Fix incorrect scipy sqrt imports in function bodies
                    func_source = func_source.replace("from scipy import sqrt", "from numpy import sqrt")
                    # Don't fix scale_factor here - it's more complex
                    helper_funcs.append(func_source)
                    
        return helper_funcs
    
    def _extract_base_classes(self, class_node: ast.ClassDef, content: str) -> List[str]:
        """Extract base classes that the scene inherits from"""
        base_classes = []
        
        # Get base class names
        base_names = []
        for base in class_node.bases:
            if isinstance(base, ast.Name):
                base_names.append(base.id)
        
        # Skip standard Manim scene types
        scene_types = ['Scene', 'MovingCameraScene', 'ThreeDScene', 'ZoomedScene']
        custom_bases = [b for b in base_names if b not in scene_types]
        
        if custom_bases:
            # Parse the full file to find base class definitions
            tree = ast.parse(content)
            for node in tree.body:
                if isinstance(node, ast.ClassDef) and node.name in custom_bases:
                    base_source = ast.get_source_segment(content, node)
                    if base_source:
                        # Don't fix scale_factor - it's more complex
                        base_classes.append(base_source)
                        # Recursively get bases of bases
                        sub_bases = self._extract_base_classes(node, content)
                        base_classes.extend(sub_bases)
        
        return base_classes
    
    def _fix_common_issues(self, code: str) -> str:
        """Fix common API compatibility issues in the code"""
        import re
        
        # Fix 1: CustomLabel scale parameter (but not in class definitions)
        # Change: CustomLabel(str(k), scale=0.6) -> CustomLabel(str(k)).scale(0.6)
        # More precise: only skip the specific class definition line
        lines = code.split('\n')
        new_lines = []
        in_custom_label_init = False
        
        for line in lines:
            if 'class CustomLabel' in line:
                in_custom_label_init = True
            elif in_custom_label_init and 'def ' in line and 'def __init__' not in line:
                in_custom_label_init = False
            
            if not in_custom_label_init:
                line = re.sub(
                    r'CustomLabel\((.*?),\s*scale\s*=\s*([\d.]+)\)',
                    r'CustomLabel(\1).scale(\2)',
                    line
                )
            new_lines.append(line)
        
        code = '\n'.join(new_lines)
        
        # Fix 2: Text weight parameter
        # Change: Text("...", weight=BOLD) -> Text("...", weight="BOLD")
        code = re.sub(
            r'Text\((.*?),\s*weight\s*=\s*BOLD\)',
            r'Text(\1, weight="BOLD")',
            code
        )
        
        # Fix 3: Text font parameter (remove it entirely as it's not supported)
        # Change: Text("...", font=REDUCIBLE_FONT) -> Text("...")
        code = re.sub(
            r'(Text\([^)]*?),\s*font\s*=\s*[^,)]+([,)])',
            r'\1\2',
            code
        )
        
        # Fix 4: Matrix with string elements
        # Actually, don't fix this - the original code uses strings with Text
        # The Matrix class handles this correctly when element_to_mobject=Text
        
        # Fix 5: Title scale_factor parameter
        # Change: Title("...", scale_factor=1.2) -> Title("...").scale(1.2)
        code = re.sub(
            r'Title\((.*?),\s*scale_factor\s*=\s*([\d.]+)\)',
            r'Title(\1).scale(\2)',
            code
        )
        
        # Fix 6: interpolate_color with string colors
        # Wrap string color arguments with ManimColor
        # This regex looks for interpolate_color calls where colors might be strings
        code = re.sub(
            r'interpolate_color\(([^,\)]+),\s*([^,\)]+),\s*([^)]+)\)',
            lambda m: f'interpolate_color(ManimColor({m.group(1)}), ManimColor({m.group(2)}), {m.group(3)})',
            code
        )
        
        return code

    def _build_standalone_scene(self,
                               class_node: ast.ClassDef,
                               class_source: str,
                               imports: List[str],
                               common_imports: List[str],
                               helper_functions: List[str],
                               file_path: Path,
                               full_content: str) -> str:
        """Build a standalone scene file with all dependencies"""
        
        parts = [
            '# Standard imports',
            'from manim import *',
            'import numpy as np',
            'import random',
            'from math import *',
            'from typing import Hashable, Iterable, Optional, List, Dict, Tuple, Any',  # Import only what's needed
            ''
        ]
        
        # Add MarchingSquares-specific color constants
        if 'MarchingSquares' in str(file_path):
            parts.extend([
                '# MarchingSquares color constants',
                'INSIDE_COLOR = PURE_GREEN',
                'OUTSIDE_COLOR = BLUE', 
                'CONTOUR_COLOR = YELLOW',
                ''
            ])
        
        # Add other imports (skip manim and common)
        for imp in imports:
            if 'from manim' not in imp and not any(c in imp for c in common_imports):
                parts.append(imp)
                
        if any(imp for imp in imports if 'from manim' not in imp):
            parts.append('')
            
        # Add common dependencies inline first (before MarkovChain classes)
        if common_imports:
            parts.append('# Dependencies from common modules')
            for common in common_imports:
                inline_code = self._get_common_module_code(common)
                if inline_code:
                    parts.append(f'# From {common}.py:')
                    parts.append(inline_code)
                    parts.append('')
        
        # Special handling for markov_chain.py - extract MarkovChain classes AFTER dependencies
        if "markov_chain.py" in str(file_path):
            # Check if the scene uses MarkovChain classes
            scene_uses_markov = any(name in class_source for name in ['MarkovChain', 'MarkovChainGraph', 'MarkovChainSimulator'])
            if scene_uses_markov:
                parts.append('# MarkovChain classes from same file')
                tree = ast.parse(full_content)
                # Also need to extract CustomLabel and CustomCurvedArrow which are defined in markov_chain.py
                classes_to_extract = ['MarkovChain', 'MarkovChainGraph', 'MarkovChainSimulator', 'CustomLabel', 'CustomCurvedArrow']
                for node in tree.body:
                    if isinstance(node, ast.ClassDef) and node.name in classes_to_extract:
                        class_code = ast.get_source_segment(full_content, node)
                        if class_code:
                            parts.append(f'# {node.name} class')
                            # Apply fixes to CustomLabel
                            if node.name == 'CustomLabel':
                                class_code = self._fix_common_issues(class_code)
                            parts.append(class_code)
                            parts.append('')
                    
        # Handle LookupTable dependency for MarchingSquares
        if 'MarchingSquares' in str(file_path):
            # Check if LookupTable is used in the scene
            if 'LookupTable' in class_source or any('LookupTable' in func for func in helper_functions):
                parts.append('# LookupTable dependency')
                parts.append(self._get_lookup_table_code())
                parts.append('')
            
        # Add base classes if needed (for MarchingSquares)
        if 'MarchingSquares' in str(file_path):
            base_classes = self._extract_base_classes(class_node, full_content)
            if base_classes:
                parts.append('# Base classes')
                for base_class in base_classes:
                    parts.append(base_class)
                    parts.append('')
        
        # Add helper functions
        if helper_functions:
            parts.append('# Helper functions')
            for func in helper_functions:
                # Apply fixes to helper functions
                fixed_func = self._fix_common_issues(func)
                parts.append(fixed_func)
                parts.append('')
                
        # Add the scene class
        parts.append('# Scene class')
        # Apply fixes to the class source
        fixed_class_source = self._fix_common_issues(class_source)
        parts.append(fixed_class_source)
        
        # Apply fixes to the complete code
        complete_code = '\n'.join(parts)
        return self._fix_common_issues(complete_code)
    
    def _get_common_module_code(self, module_name: str) -> Optional[str]:
        """Get the code from a common module to inline"""
        
        # Map module names to their content
        if module_name == "reducible_colors":
            return '''# Color definitions
REDUCIBLE_PURPLE_DARK_FILL = "#331B5D"
REDUCIBLE_PURPLE_DARKER = "#3B0893"
REDUCIBLE_PURPLE = "#8c4dfb"
REDUCIBLE_VIOLET = "#d7b5fe"
REDUCIBLE_BLUE = "#650FFA"
REDUCIBLE_BLUE_DARKER = "#02034E"
REDUCIBLE_YELLOW = "#ffff5c"
REDUCIBLE_YELLOW_DARKER = "#7F7F2D"
REDUCIBLE_GREEN_LIGHTER = "#00cc70"
REDUCIBLE_GREEN = "#008f4f"
REDUCIBLE_GREEN_DARKER = "#004F2C"
REDUCIBLE_WARM_BLUE = "#08B6CE"
REDUCIBLE_WARM_BLUE_DARKER = "#044263"
REDUCIBLE_ORANGE = "#FFB413"
REDUCIBLE_ORANGE_DARKER = "#714400"
REDUCIBLE_CHARM = "#FF5752"
REDUCIBLE_CHARM_DARKER = "#6F001F"
REDUCIBLE_FONT = "CMU Serif"
REDUCIBLE_MONO = "SF Mono"'''
        
        elif module_name == "markov_chain":
            # Extract MarkovChain classes from the file
            markov_path = self.repo_path / "2022/PageRank/markov_chain.py"
            if markov_path.exists():
                with open(markov_path, 'r') as f:
                    content = f.read()
                # Extract just the class definitions we need
                tree = ast.parse(content)
                classes_to_extract = ['MarkovChain', 'MarkovChainGraph', 'MarkovChainSimulator', 'CustomLabel', 'CustomCurvedArrow']
                extracted_code = []
                
                # First add necessary imports for MarkovChain classes
                extracted_code.append("import itertools as it")
                extracted_code.append("from typing import Hashable, Iterable")
                extracted_code.append("")
                
                for node in tree.body:
                    if isinstance(node, ast.ClassDef) and node.name in classes_to_extract:
                        class_code = ast.get_source_segment(content, node)
                        if class_code:
                            # Apply fixes to extracted classes
                            class_code = self._fix_common_issues(class_code)
                            extracted_code.append(class_code)
                
                if extracted_code:
                    return '\n'.join(extracted_code)
        
        elif module_name == "classes":
            # Extract RVariable, RDecimalNumber, and CustomLabel from common/classes.py
            classes_path = self.repo_path / "2022/common/classes.py"
            if classes_path.exists():
                with open(classes_path, 'r') as f:
                    content = f.read()
                # Extract specific classes
                tree = ast.parse(content)
                classes_to_extract = ['RVariable', 'RDecimalNumber', 'CustomLabel']
                extracted_code = []
                
                for node in tree.body:
                    if isinstance(node, ast.ClassDef) and node.name in classes_to_extract:
                        class_code = ast.get_source_segment(content, node)
                        if class_code:
                            # Always apply fixes to extracted classes
                            class_code = self._fix_common_issues(class_code)
                            extracted_code.append(class_code)
                
                if extracted_code:
                    return '\n\n'.join(extracted_code)
        
        elif module_name == "functions":
            # Extract specific functions from common/functions.py
            functions_path = self.repo_path / "2022/common/functions.py"
            if functions_path.exists():
                with open(functions_path, 'r') as f:
                    content = f.read()
                # Extract specific functions that are commonly used
                tree = ast.parse(content)
                functions_to_extract = [
                    'get_glowing_surround_circle',
                    'get_glowing_surround_rect',
                    'align_text_vertically',
                    'matrix_to_mob'
                ]
                extracted_code = []
                
                # First check if we need any imports from the file
                needed_imports = []
                for node in tree.body:
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        import_str = ast.get_source_segment(content, node)
                        # Skip manim and reducible_colors imports (already handled)
                        if import_str and 'manim' not in import_str and 'reducible_colors' not in import_str:
                            needed_imports.append(import_str)
                
                if needed_imports:
                    extracted_code.extend(needed_imports)
                    extracted_code.append("")
                
                for node in tree.body:
                    if isinstance(node, ast.FunctionDef) and node.name in functions_to_extract:
                        func_code = ast.get_source_segment(content, node)
                        if func_code:
                            extracted_code.append(func_code)
                
                if extracted_code:
                    return '\n'.join(extracted_code)
                    
        return None
    
    def _get_lookup_table_code(self) -> str:
        """Get the LookupTable code from the Reducible repo"""
        lookup_path = self.repo_path / "2021/MarchingSquares/lookup.py"
        if lookup_path.exists():
            with open(lookup_path, 'r') as f:
                return f.read()
        else:
            # Fallback minimal implementation
            return """class LookupTable:
    TABLE = [[-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]]"""