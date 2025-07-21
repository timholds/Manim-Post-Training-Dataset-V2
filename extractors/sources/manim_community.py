"""ManimCommunity/manim repository extractor - extracts examples and test scenes."""

import ast
import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Iterator, Dict, Any, Optional, List, Tuple

from ..base import BaseExtractor
from ..registry import register_extractor
from ..constants import PLACEHOLDER_DESCRIPTION

logger = logging.getLogger(__name__)


@register_extractor
class ManimCommunityExtractor(BaseExtractor):
    """Extractor for ManimCommunity/manim GitHub repository examples and tests."""
    
    source_id = "manim_community"
    source_name = "ManimCommunity Repository"
    priority = 4  # Medium-high priority as it's the official community repository
    
    def _validate_config(self) -> None:
        """Validate configuration."""
        self.data_dir = Path(self.config.get("data_dir", "data"))
        self.repo_dir = self.data_dir / "manim_community_repo"
        self.repo_url = "https://github.com/ManimCommunity/manim.git"
        
        # Configuration for which directories to extract
        self.extract_examples = self.config.get("extract_examples", True)
        self.extract_tests = self.config.get("extract_tests", True)
        
        # Specific test files to prioritize (high-value 3D and specialized tests)
        self.priority_test_files = [
            "test_threed.py",
            "test_probability.py", 
            "test_vector_scene.py",
            "test_axes.py",
            "test_coordinate_systems.py",
            "test_functions.py",
            "test_geometry.py",
            "test_polyhedra.py",
            "test_tables.py",
            "test_tex_mobject.py",
            "test_text.py",
            "test_transform.py"
        ]
    
    def estimate_sample_count(self) -> Optional[int]:
        """Return estimated number of samples."""
        # Based on analysis:
        # - Example scenes: ~25
        # - Test scenes: ~300-450 (we'll extract high-value ones)
        # Conservatively estimate 150 high-quality extractable scenes
        return 150
    
    def _clone_or_update_repo(self) -> bool:
        """Clone the repository if needed, or update if it exists."""
        try:
            if self.repo_dir.exists():
                # Update existing repo
                logger.info(f"Updating existing repository at {self.repo_dir}")
                result = subprocess.run(
                    ["git", "pull"],
                    cwd=self.repo_dir,
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    logger.warning(f"Failed to update repo: {result.stderr}")
            else:
                # Clone new repo
                logger.info(f"Cloning ManimCommunity repository to {self.repo_dir}")
                self.repo_dir.parent.mkdir(parents=True, exist_ok=True)
                result = subprocess.run(
                    ["git", "clone", self.repo_url, str(self.repo_dir)],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    logger.error(f"Failed to clone repo: {result.stderr}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error cloning/updating repository: {e}")
            return False
    
    def _extract_scene_classes(self, file_path: Path) -> List[Tuple[str, str]]:
        """Extract Scene classes and their code from a Python file."""
        scenes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST
            tree = ast.parse(content)
            
            # Find all Scene classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it inherits from Scene or any Scene subclass
                    base_names = []
                    for base in node.bases:
                        if isinstance(base, ast.Name):
                            base_names.append(base.id)
                        elif isinstance(base, ast.Attribute):
                            base_names.append(base.attr)
                    
                    # Check if this is a Scene class
                    scene_bases = ["Scene", "ThreeDScene", "VectorScene", "LinearTransformationScene"]
                    if any(base in scene_bases for base in base_names):
                        # Extract the class code
                        class_lines = content.splitlines()[node.lineno - 1:node.end_lineno]
                        class_code = '\n'.join(class_lines)
                        
                        # Include necessary imports
                        import_code = self._extract_imports(content)
                        full_code = f"{import_code}\n\n{class_code}"
                        
                        # Apply LaTeX transformations to make code more portable
                        full_code = self._transform_latex_code(full_code)
                        
                        scenes.append((node.name, full_code))
            
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")
        
        return scenes
    
    def _extract_imports(self, content: str) -> str:
        """Extract import statements from Python code."""
        lines = content.splitlines()
        imports = []
        future_imports = []
        
        for line in lines:
            # Stop at first non-import statement (excluding comments and docstrings)
            stripped = line.strip()
            if stripped and not stripped.startswith(('#', 'import', 'from', '"""', "'''")):
                if not any(line.lstrip().startswith(imp) for imp in ['import', 'from']):
                    break
            
            if line.strip().startswith('from __future__'):
                future_imports.append(line)
            elif line.strip().startswith(('import', 'from')):
                # Skip testing framework imports and relative imports
                if ('frames_comparison' not in line and 
                    'pytest' not in line and 
                    not line.strip().startswith('from ..')):
                    imports.append(line)
        
        # Build imports with proper order: __future__ first, then manim, then others
        all_imports = []
        
        # Add __future__ imports first
        all_imports.extend(future_imports)
        
        # Always include basic manim import if not present
        has_manim = any('from manim import' in imp for imp in imports)
        if not has_manim:
            all_imports.append("from manim import *")
        
        # Add other imports
        all_imports.extend(imports)
        
        return '\n'.join(all_imports)
    
    def _transform_latex_code(self, code: str) -> str:
        """Transform LaTeX code to use standard packages and commands."""
        
        # Transform custom vector notation to standard LaTeX
        code = re.sub(r'\\vv\{([^}]+)\}', r'\\vec{\1}', code)
        
        # Replace FrenchCursive with standard MathTex/Tex
        code = re.sub(
            r'FrenchCursive\(([^)]+)\)',
            r'MathTex(\1)',
            code
        )
        
        # Remove custom TeX template assignments and simplify
        # Remove lines that create custom templates
        lines = code.split('\n')
        filtered_lines = []
        skip_template_block = False
        
        for line in lines:
            # Skip custom template definitions
            if 'TexTemplate(' in line or 'myTemplate =' in line:
                skip_template_block = True
                continue
            elif skip_template_block and line.strip().startswith('myTemplate.'):
                continue
            elif skip_template_block and (line.strip() == '' or not line.startswith(' ')):
                skip_template_block = False
            
            # Remove tex_template parameter from MathTex/Tex calls
            if 'tex_template=' in line:
                line = re.sub(r',\s*tex_template=[^,)]+', '', line)
                line = re.sub(r'tex_template=[^,)]+,?\s*', '', line)
            
            if not skip_template_block:
                filtered_lines.append(line)
        
        code = '\n'.join(filtered_lines)
        
        # Clean up any double empty lines
        code = re.sub(r'\n\n\n+', '\n\n', code)
        
        return code
    
    def _extract_test_functions(self, file_path: Path) -> List[Tuple[str, str]]:
        """Extract test functions that create scenes from test files."""
        scenes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST to properly extract individual test functions
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if (isinstance(node, ast.FunctionDef) and 
                    node.name.startswith('test_') and 
                    len(node.args.args) > 0 and 
                    any(arg.arg == 'scene' for arg in node.args.args)):
                    
                    # Detect Scene base class from decorator
                    base_scene = self._detect_scene_base_class(content, node)
                    
                    # Extract function parameters for default values
                    test_params = self._extract_test_parameters(content, node)
                    
                    # Extract just this function's body
                    lines = content.splitlines()
                    func_start = node.lineno - 1
                    func_end = node.end_lineno if hasattr(node, 'end_lineno') else len(lines)
                    
                    # Get the function definition and body (skip decorators)
                    func_lines = []
                    in_function = False
                    
                    for i in range(func_start, min(func_end, len(lines))):
                        line = lines[i]
                        
                        # Start collecting when we hit the def line (skip decorators)
                        if line.strip().startswith('def '):
                            in_function = True
                            continue  # Skip the def line itself
                        
                        if in_function:
                            # Stop if we hit another function or decorator
                            if (line.strip().startswith(('@', 'def ')) and 
                                not line.strip().startswith('        ')):
                                break
                            func_lines.append(line)
                    
                    if not func_lines:
                        continue
                    
                    # Clean and dedent the function body
                    func_body = '\n'.join(func_lines)
                    
                    # Remove leading whitespace consistently
                    import textwrap
                    func_body = textwrap.dedent(func_body).strip()
                    
                    # Skip if too short or just pass
                    if len(func_body) < 20 or func_body.strip() == 'pass':
                        continue
                    
                    # Convert to Scene class
                    class_name = self._test_name_to_class_name(node.name)
                    
                    # Add test parameter defaults at the beginning
                    param_defaults = '\n'.join(f"        {param} = {default}" 
                                              for param, default in test_params.items())
                    if param_defaults:
                        param_defaults = f"\n{param_defaults}\n"
                    
                    # Indent for construct method
                    indented_body = '\n'.join(f"        {line}" if line.strip() else line
                                            for line in func_body.splitlines())
                    
                    # Build Scene class with correct base class
                    class_code = f"""class {class_name}({base_scene}):
    def construct(self):{param_defaults}
{indented_body}"""
                    
                    # Include imports (excluding test framework imports)
                    import_code = self._extract_imports(content)
                    full_code = f"{import_code}\n\n{class_code}"
                    
                    # Clean up scene references using AST-aware replacement
                    full_code = self._replace_scene_references(full_code)
                    
                    # Apply LaTeX transformations
                    full_code = self._transform_latex_code(full_code)
                    
                    scenes.append((class_name, full_code))
        
        except Exception as e:
            logger.warning(f"Error extracting test functions from {file_path}: {e}")
        
        return scenes
    
    def _test_name_to_class_name(self, test_name: str) -> str:
        """Convert test_function_name to TestFunctionName."""
        parts = test_name.split('_')
        return ''.join(part.capitalize() for part in parts)
    
    def _detect_scene_base_class(self, content: str, func_node: ast.FunctionDef) -> str:
        """Detect the Scene base class from @frames_comparison decorator."""
        lines = content.splitlines()
        
        # Look for decorator above the function
        for i in range(max(0, func_node.lineno - 5), func_node.lineno - 1):
            if i < len(lines):
                line = lines[i].strip()
                if '@frames_comparison' in line:
                    # Extract base_scene parameter
                    if 'base_scene=ThreeDScene' in line:
                        return 'ThreeDScene'
                    elif 'base_scene=VectorScene' in line:
                        return 'VectorScene'
                    elif 'base_scene=LinearTransformationScene' in line:
                        return 'LinearTransformationScene'
        
        # Default to Scene if no specific base class found
        return 'Scene'
    
    def _extract_test_parameters(self, content: str, func_node: ast.FunctionDef) -> dict:
        """Extract test parameters and provide sensible defaults."""
        params = {}
        lines = content.splitlines()
        
        # Look for @pytest.mark.parametrize decorators
        for i in range(max(0, func_node.lineno - 10), func_node.lineno - 1):
            if i < len(lines):
                line = lines[i].strip()
                if '@pytest.mark.parametrize' in line and 'use_vectorized' in line:
                    params['use_vectorized'] = 'True'
        
        # Check function body for undefined variables and provide defaults
        func_source = ast.get_source_segment(content, func_node)
        if func_source and 'use_vectorized' in func_source and 'use_vectorized' not in params:
            params['use_vectorized'] = 'True'
        
        return params
    
    def _replace_scene_references(self, code: str) -> str:
        """Replace scene. references with self. while preserving imports."""
        lines = code.splitlines()
        result_lines = []
        
        for line in lines:
            # Don't replace 'scene' in import statements
            if line.strip().startswith(('import', 'from')):
                result_lines.append(line)
            else:
                # Replace scene. with self. in non-import lines
                # Use word boundary to avoid replacing scene in other contexts
                import re
                modified_line = re.sub(r'\bscene\.', 'self.', line)
                result_lines.append(modified_line)
        
        return '\n'.join(result_lines)
    
    def _create_description_with_context(self, class_name: str, file_path: Path, is_test: bool) -> str:
        """Create a placeholder description with context information."""
        context_parts = [PLACEHOLDER_DESCRIPTION]
        
        # Add source information
        context_parts.append(f"Source: {self.source_id}")
        
        # Add file information
        rel_path = file_path.relative_to(self.repo_dir)
        context_parts.append(f"File: {rel_path}")
        
        # Add class name
        context_parts.append(f"Class: {class_name}")
        
        # Add type information
        if is_test:
            context_parts.append("Type: test")
        else:
            context_parts.append("Type: example")
        
        # Try to infer category from filename
        if is_test:
            category = file_path.stem.replace('test_', '').replace('_', ' ').title()
            context_parts.append(f"Category: {category}")
        
        return " - ".join(context_parts)
    
    def extract(self) -> Iterator[Dict[str, Any]]:
        """Extract samples from ManimCommunity repository."""
        # Clone or update repository
        if not self._clone_or_update_repo():
            logger.error("Failed to access ManimCommunity repository")
            return
        
        extracted_count = 0
        
        # Extract from example_scenes directory
        if self.extract_examples:
            examples_dir = self.repo_dir / "example_scenes"
            if examples_dir.exists():
                logger.info(f"Extracting examples from {examples_dir}")
                
                for py_file in examples_dir.glob("*.py"):
                    # Skip __init__.py and config files
                    if py_file.name.startswith('_'):
                        continue
                    
                    logger.debug(f"Processing example file: {py_file.name}")
                    scenes = self._extract_scene_classes(py_file)
                    
                    for class_name, code in scenes:
                        description = self._create_description_with_context(
                            class_name, py_file, is_test=False
                        )
                        
                        metadata = {
                            "file_path": str(py_file.relative_to(self.repo_dir)),
                            "class_name": class_name,
                            "type": "example"
                        }
                        
                        yield {
                            "description": description,
                            "code": code,
                            "metadata": metadata
                        }
                        extracted_count += 1
        
        # Extract from test_graphical_units directory
        if self.extract_tests:
            tests_dir = self.repo_dir / "tests" / "test_graphical_units"
            if tests_dir.exists():
                logger.info(f"Extracting tests from {tests_dir}")
                
                # Process priority test files first
                test_files = []
                for priority_file in self.priority_test_files:
                    file_path = tests_dir / priority_file
                    if file_path.exists():
                        test_files.append(file_path)
                
                # Add remaining test files
                for py_file in tests_dir.glob("test_*.py"):
                    if py_file not in test_files:
                        test_files.append(py_file)
                
                for py_file in test_files:
                    logger.debug(f"Processing test file: {py_file.name}")
                    
                    # Extract test functions
                    scenes = self._extract_test_functions(py_file)
                    
                    for class_name, code in scenes:
                        # Skip very simple tests
                        if len(code) < 100:
                            continue
                        
                        description = self._create_description_with_context(
                            class_name, py_file, is_test=True
                        )
                        
                        metadata = {
                            "file_path": str(py_file.relative_to(self.repo_dir)),
                            "class_name": class_name,
                            "type": "test",
                            "original_file": py_file.name
                        }
                        
                        yield {
                            "description": description,
                            "code": code,
                            "metadata": metadata
                        }
                        extracted_count += 1
        
        logger.info(f"Extracted {extracted_count} scenes from ManimCommunity repository")
    
    def validate_sample(self, sample: Dict[str, Any]) -> bool:
        """Validate that a sample meets quality requirements."""
        # Allow placeholder descriptions
        if sample.get("description", "").startswith(PLACEHOLDER_DESCRIPTION):
            # Just validate code
            code = sample.get("code", "")
            if not code or len(code) < 50:
                return False
            
            # Must have class definition and construct method
            if "class" not in code or "def construct" not in code:
                return False
            
            # Must have some Manim-specific content
            manim_indicators = ["self.play", "self.wait", "self.add", "Scene", "ThreeDScene"]
            if not any(indicator in code for indicator in manim_indicators):
                return False
            
            # Filter out problematic content that won't render in standard Manim
            
            # Skip OpenGL-specific scenes (require OpenGL renderer)
            opengl_indicators = [
                "get_plane_mesh", "self.renderer.context", "opengl.py",
                "interactive_embed", "FullScreenQuad", "Shader(", "Mesh(",
                "self.widgets", "dpg.get_value"
            ]
            if any(indicator in code for indicator in opengl_indicators):
                logger.debug(f"Skipping OpenGL scene: {sample.get('metadata', {}).get('class_name', 'Unknown')}")
                return False
            
            # Skip scenes with complex custom LaTeX that can't be easily transformed
            # Note: We now transform most LaTeX issues, so this is only for extreme cases
            complex_latex_indicators = [
                "TexFontTemplateLibrary",  # The scene that tries many fonts
                "TexFontTemplateManual",   # Uses complex custom font definitions
            ]
            if any(indicator in code for indicator in complex_latex_indicators):
                logger.debug(f"Skipping complex LaTeX scene: {sample.get('metadata', {}).get('class_name', 'Unknown')}")
                return False
            
            # Skip test scenes with testing framework dependencies that can't be transformed
            # These should be cleaned out by extraction, but catch any that slip through
            test_framework_indicators = [
                "__module_test__"  # Only skip if this module-level marker is still present
            ]
            if any(indicator in code for indicator in test_framework_indicators):
                logger.debug(f"Skipping test framework scene: {sample.get('metadata', {}).get('class_name', 'Unknown')}")
                return False
            
            # Skip scenes with external file dependencies that won't exist
            file_dependency_indicators = [
                'script_location / "assets"', 'Path(__file__)', "day_texture", "night_texture"
            ]
            if any(indicator in code for indicator in file_dependency_indicators):
                logger.debug(f"Skipping file dependency scene: {sample.get('metadata', {}).get('class_name', 'Unknown')}")
                return False
            
            return True
        
        # For non-placeholder descriptions, use parent validation
        return super().validate_sample(sample)