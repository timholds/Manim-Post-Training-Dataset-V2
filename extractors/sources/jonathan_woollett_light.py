import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Iterator
import requests
import ast
import logging

from ..base import BaseExtractor


class JonathanWoollettLightExtractor(BaseExtractor):
    """
    Extractor for JonathanWoollett-Light/a-little-more-than-an-introduction-to
    Neural network tutorial series with forward/backpropagation visualizations
    """
    
    source_id = "jonathan_woollett_light"
    source_name = "Neural network tutorials by Jonathan Woollett-Light"
    priority = 2
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.repo_url = "https://raw.githubusercontent.com/JonathanWoollett-Light/a-little-more-than-an-introduction-to/master"
        self.helper_functions = {}
        
    def _fetch_helper_functions(self) -> None:
        """Fetch and store helper functions from scommon.py and ecommon.py"""
        # Fetch scommon.py
        scommon_url = f"{self.repo_url}/nn/scommon.py"
        scommon_content = self._fetch_file(scommon_url)
        if scommon_content:
            self.helper_functions['scommon'] = self._extract_functions(scommon_content)
            
        # Fetch ecommon.py for each episode
        for ep in ['ep1', 'ep2']:
            ecommon_url = f"{self.repo_url}/nn/{ep}/ecommon.py"
            ecommon_content = self._fetch_file(ecommon_url)
            if ecommon_content:
                self.helper_functions[f'ecommon_{ep}'] = self._extract_functions(ecommon_content)
    
    def _fetch_file(self, url: str) -> Optional[str]:
        """Fetch file content from URL"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                print(f"Failed to fetch {url}: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def _extract_functions(self, content: str) -> Dict[str, str]:
        """Extract function definitions from Python code"""
        functions = {}
        try:
            # Use regex to find function definitions
            func_pattern = r'^(def\s+\w+\s*\([^)]*\):.*?)(?=^def\s+|\Z)'
            matches = re.findall(func_pattern, content, re.MULTILINE | re.DOTALL)
            
            for func_code in matches:
                # Extract function name
                name_match = re.match(r'def\s+(\w+)', func_code)
                if name_match:
                    func_name = name_match.group(1)
                    # Remove trailing empty lines
                    func_code = func_code.rstrip()
                    functions[func_name] = func_code
                    
        except Exception as e:
            print(f"Error parsing functions: {e}")
            
        return functions
    
    def _inline_dependencies(self, content: str, episode: str) -> str:
        """Inline helper function dependencies into the scene code"""
        # Remove import statements for helper modules
        content = re.sub(r'from ecommon import \([\s\S]*?\)\n', '', content)
        content = re.sub(r'from scommon import \([\s\S]*?\)\n', '', content)
        content = re.sub(r'import os\nimport sys\n\nsys\.path\.append.*?\n\n', '', content)
        
        # Find which functions are actually used
        used_functions = set()
        for func_name in self.helper_functions.get('scommon', {}):
            if re.search(rf'\b{func_name}\b', content):
                used_functions.add(('scommon', func_name))
                
        ecommon_key = f'ecommon_{episode}'
        for func_name in self.helper_functions.get(ecommon_key, {}):
            if re.search(rf'\b{func_name}\b', content):
                used_functions.add((ecommon_key, func_name))
        
        # Add the used functions after imports
        import_match = re.search(r'(from manim import \*\n)', content)
        if import_match:
            insert_pos = import_match.end()
            
            # Collect all needed functions
            functions_to_add = []
            for source, func_name in used_functions:
                if func_name in self.helper_functions.get(source, {}):
                    functions_to_add.append(self.helper_functions[source][func_name])
            
            if functions_to_add:
                helper_code = "\n# Helper functions inlined from common files\n" + \
                             "\n\n".join(functions_to_add) + "\n\n"
                content = content[:insert_pos] + helper_code + content[insert_pos:]
        
        # System path manipulation already removed above
        
        # Remove or comment out image-related code
        if "play_note_on_3b3b1" in content:
            # Comment out the method that uses the image
            content = re.sub(
                r'def play_note_on_3b3b1\(self\):.*?self\.play\(Unwrite\(text\), FadeOut\(img\)\)',
                '''def play_note_on_3b3b1(self):
        # Skipped: This method originally displayed an image reference to 3Blue1Brown
        pass''',
                content,
                flags=re.DOTALL
            )
            
        return content
    
    def _validate_config(self) -> None:
        """Validate configuration for this extractor."""
        # No special config validation needed
        pass
    
    def estimate_sample_count(self) -> Optional[int]:
        """Return estimated number of samples."""
        return 7  # Based on our evaluation
    
    def extract(self) -> Iterator[Dict[str, Any]]:
        """Extract scenes from the repository"""
        
        # First fetch helper functions
        self._fetch_helper_functions()
        
        # Define files to process (excluding problematic ones)
        files_to_process = [
            ('ep1', '0.py', 'Forepropagation'),
            ('ep1', '1.py', 'Backpropagation'),
            ('ep1', '2.py', 'Neural Network Training'),
            ('ep1', '3.py', 'Neural Network Optimization'),
            ('ep2', '1.py', 'Convolutional Networks Part 1'),
            ('ep2', '2.py', 'Convolutional Networks Part 2'),
            ('ep2', '3.py', 'Convolutional Networks Part 3'),
        ]
        
        for episode, filename, description in files_to_process:
            url = f"{self.repo_url}/nn/{episode}/{filename}"
            content = self._fetch_file(url)
            
            if not content:
                continue
                
            # Check if it's a meaningful file (only skip if it's JUST a placeholder)
            if len(content.strip()) < 100:
                continue
            
            # Skip if it's just a placeholder with only construct method having wait(3)
            if "def construct(self):\n        self.wait(3)" in content and len(content.strip()) < 200:
                continue
                
            # Inline dependencies
            processed_content = self._inline_dependencies(content, episode)
            
            # Extract scene class
            scene_match = re.search(r'class\s+(\w+)\s*\([^)]*Scene[^)]*\):', processed_content)
            if scene_match:
                scene_name = scene_match.group(1)
                
                # Create metadata
                metadata = {
                    'original_source': f'jonathan_woollett_light/{episode}/{filename}',
                    'description': description,
                    'episode': episode
                }
                
                yield {
                    'source_id': self.source_id,
                    'scene_name': scene_name,
                    'code': processed_content,
                    'metadata': metadata
                }