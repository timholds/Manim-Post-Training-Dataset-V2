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
                        
                        scenes.append((node.name, full_code))
            
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")
        
        return scenes
    
    def _extract_imports(self, content: str) -> str:
        """Extract import statements from Python code."""
        lines = content.splitlines()
        imports = []
        
        for line in lines:
            # Stop at first non-import statement (excluding comments and docstrings)
            stripped = line.strip()
            if stripped and not stripped.startswith(('#', 'import', 'from', '"""', "'''")):
                if not any(line.lstrip().startswith(imp) for imp in ['import', 'from']):
                    break
            
            if line.strip().startswith(('import', 'from')):
                imports.append(line)
        
        # Always include basic manim import if not present
        import_text = '\n'.join(imports)
        if 'from manim import' not in import_text and 'import manim' not in import_text:
            import_text = "from manim import *\n" + import_text
        
        return import_text.strip()
    
    def _extract_test_functions(self, file_path: Path) -> List[Tuple[str, str]]:
        """Extract test functions that create scenes from test files."""
        scenes = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find test functions with scene parameter, including decorated ones
            # This pattern matches functions with or without decorators
            pattern = r'(?:@\w+(?:\([^)]*\))?\s*\n)?def\s+(test_\w+)\s*\([^)]*scene[^)]*\):\s*\n((?:(?!\n(?:@|def)\s).*\n)*)'
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            
            for func_name, func_body in matches:
                # Skip if it's just a pass or too short
                if 'pass' in func_body and len(func_body.strip()) < 20:
                    continue
                
                # Convert test function to Scene class
                class_name = self._test_name_to_class_name(func_name)
                
                # Extract the function body and convert to construct method
                indented_body = '\n'.join(f"        {line}" if line.strip() else ''
                                        for line in func_body.splitlines())
                
                # Build Scene class
                class_code = f"""class {class_name}(Scene):
    def construct(self):
{indented_body}"""
                
                # Include imports
                import_code = self._extract_imports(content)
                full_code = f"{import_code}\n\n{class_code}"
                
                # Clean up scene references
                full_code = full_code.replace('scene.play(', 'self.play(')
                full_code = full_code.replace('scene.wait(', 'self.wait(')
                full_code = full_code.replace('scene.add(', 'self.add(')
                full_code = full_code.replace('scene.remove(', 'self.remove(')
                
                scenes.append((class_name, full_code))
        
        except Exception as e:
            logger.warning(f"Error extracting test functions from {file_path}: {e}")
        
        return scenes
    
    def _test_name_to_class_name(self, test_name: str) -> str:
        """Convert test_function_name to TestFunctionName."""
        parts = test_name.split('_')
        return ''.join(part.capitalize() for part in parts)
    
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
            
            return True
        
        # For non-placeholder descriptions, use parent validation
        return super().validate_sample(sample)