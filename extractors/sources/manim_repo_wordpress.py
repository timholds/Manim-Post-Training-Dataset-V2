"""
ManimRepository WordPress blog extractor.

This extractor scrapes Manim animation examples from The Manim Repository blog
(https://themanimrepository.wordpress.com/), which aggregates ManimCE code examples
from the community.
"""

import logging
import re
from pathlib import Path
from typing import Iterator, Dict, Any, Optional, List, Tuple
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import time

from ..base import BaseExtractor
from ..registry import register_extractor
from ..constants import PLACEHOLDER_DESCRIPTION

logger = logging.getLogger(__name__)


@register_extractor
class ManimRepositoryExtractor(BaseExtractor):
    """Extractor for The Manim Repository WordPress blog."""
    
    source_id = "manim_repo_wordpress"
    source_name = "The Manim Repository Blog"
    priority = 3  # Medium priority - curated examples but limited quantity
    
    def _validate_config(self) -> None:
        """Validate configuration."""
        self.base_url = "https://themanimrepository.wordpress.com/"
        self.posts_per_page = 100  # WordPress default max
        
        # Rate limiting for polite scraping
        self.request_delay = 1.0  # seconds between requests
        
    def estimate_sample_count(self) -> Optional[int]:
        """Return estimated number of samples."""
        # Based on manual inspection, approximately 20-30 posts total
        # But many are ManimGL, so we expect fewer ManimCE samples
        return 10
    
    def _get_blog_posts(self) -> List[Dict[str, str]]:
        """Fetch all blog post URLs and titles."""
        posts = []
        page = 1
        
        while True:
            try:
                # WordPress blog pagination
                url = f"{self.base_url}page/{page}/" if page > 1 else self.base_url
                
                logger.debug(f"Fetching page {page}: {url}")
                response = requests.get(url, timeout=30)
                
                if response.status_code == 404:
                    # No more pages
                    break
                    
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all article links
                articles = soup.find_all('article', class_='post')
                
                if not articles:
                    # Try alternative structure
                    articles = soup.find_all('div', class_='post')
                
                if not articles:
                    logger.warning(f"No articles found on page {page}")
                    break
                
                for article in articles:
                    # Find the title and URL
                    title_elem = article.find('h2', class_='entry-title')
                    if not title_elem:
                        title_elem = article.find('h1', class_='entry-title')
                    
                    if title_elem and title_elem.find('a'):
                        link = title_elem.find('a')
                        post_url = link.get('href')
                        post_title = link.get_text(strip=True)
                        
                        if post_url and post_title:
                            posts.append({
                                'url': post_url,
                                'title': post_title
                            })
                
                # Check if there's a next page
                next_link = soup.find('a', text=re.compile(r'Next|Older posts', re.I))
                if not next_link:
                    break
                    
                page += 1
                
                # Rate limiting
                time.sleep(self.request_delay)
                
            except Exception as e:
                logger.error(f"Error fetching blog page {page}: {e}")
                break
        
        logger.info(f"Found {len(posts)} blog posts")
        return posts
    
    def _extract_code_from_post(self, post_url: str) -> List[Tuple[str, str]]:
        """Extract Manim code blocks from a blog post."""
        code_blocks = []
        seen_codes = set()  # Track unique code blocks
        
        try:
            logger.debug(f"Fetching post: {post_url}")
            response = requests.get(post_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the main content area
            content = soup.find('div', class_='entry-content')
            if not content:
                content = soup.find('article')
            
            if not content:
                logger.warning(f"No content found in {post_url}")
                return code_blocks
            
            # Look for code blocks (various formats)
            # 1. <pre><code> blocks
            pre_blocks = content.find_all('pre')
            for pre in pre_blocks:
                code_elem = pre.find('code')
                if code_elem:
                    code = code_elem.get_text(strip=True)
                else:
                    code = pre.get_text(strip=True)
                
                if self._is_manim_code(code) and code not in seen_codes:
                    seen_codes.add(code)
                    code_blocks.append(("", code))
            
            # 2. Syntax highlighted blocks (e.g., with class="language-python")
            # But skip if already processed as part of a <pre> block
            syntax_blocks = content.find_all(['div', 'pre'], class_=re.compile(r'language-python|highlight|codehilite'))
            for block in syntax_blocks:
                # Skip if this is a <pre> we already processed
                if block.name == 'pre' and block in pre_blocks:
                    continue
                    
                code = block.get_text(strip=True)
                if self._is_manim_code(code) and code not in seen_codes:
                    seen_codes.add(code)
                    code_blocks.append(("", code))
            
            # Rate limiting
            time.sleep(self.request_delay)
            
        except Exception as e:
            logger.error(f"Error extracting code from {post_url}: {e}")
        
        return code_blocks
    
    def _is_manim_code(self, code: str) -> bool:
        """Check if code block is likely Manim code."""
        # Must have imports (either ManimCE or ManimGL)
        has_manim_import = 'from manim import' in code or 'from manimlib import' in code
        if not has_manim_import:
            return False
        
        # Must have a Scene class
        if not re.search(r'class\s+\w+\s*\([^)]*Scene[^)]*\)', code):
            return False
        
        # Must have construct method
        if 'def construct' not in code:
            return False
        
        return True
    
    def _extract_scene_info(self, code: str, post_title: str) -> List[Dict[str, Any]]:
        """Extract individual scenes from a code block."""
        scenes = []
        
        # Find all Scene classes in the code
        scene_pattern = re.compile(r'class\s+(\w+)\s*\([^)]*Scene[^)]*\):')
        matches = list(scene_pattern.finditer(code))
        
        if not matches:
            return scenes
        
        # If single scene, use the whole code
        if len(matches) == 1:
            scene_name = matches[0].group(1)
            scenes.append({
                'name': scene_name,
                'code': code,
                'context': post_title
            })
        else:
            # Multiple scenes - try to split them
            lines = code.split('\n')
            imports = []
            
            # Extract imports
            for line in lines:
                if line.strip().startswith(('import', 'from')):
                    imports.append(line)
                elif line.strip() and not line.strip().startswith('#'):
                    # Stop at first non-import, non-comment line
                    if not any(line.lstrip().startswith(word) for word in ['import', 'from']):
                        break
            
            import_block = '\n'.join(imports)
            
            # Extract each scene
            for i, match in enumerate(matches):
                scene_name = match.group(1)
                start_line = None
                end_line = None
                
                # Find the line number of this class
                for j, line in enumerate(lines):
                    if match.group(0) in line:
                        start_line = j
                        break
                
                if start_line is None:
                    continue
                
                # Find the end of this class (next class or end of file)
                if i + 1 < len(matches):
                    next_match = matches[i + 1]
                    for j, line in enumerate(lines[start_line + 1:], start=start_line + 1):
                        if next_match.group(0) in line:
                            end_line = j
                            break
                else:
                    end_line = len(lines)
                
                # Extract the scene code
                scene_lines = lines[start_line:end_line]
                scene_code = '\n'.join(scene_lines)
                
                # Combine with imports
                full_scene_code = f"{import_block}\n\n{scene_code}"
                
                scenes.append({
                    'name': scene_name,
                    'code': full_scene_code,
                    'context': post_title
                })
        
        return scenes
    
    def _clean_code(self, code: str) -> str:
        """Clean and normalize extracted code."""
        # Remove any HTML entities that might have slipped through
        code = code.replace('&gt;', '>')
        code = code.replace('&lt;', '<')
        code = code.replace('&amp;', '&')
        code = code.replace('&nbsp;', ' ')
        code = code.replace('&quot;', '"')
        code = code.replace('&#39;', "'")
        
        # Fix common formatting issues
        # Remove excessive blank lines
        code = re.sub(r'\n\n\n+', '\n\n', code)
        
        # Ensure consistent indentation (convert tabs to spaces)
        code = code.replace('\t', '    ')
        
        # Fix version compatibility issues
        if 'ParametricSurface' in code:
            # In newer ManimCE, ParametricSurface is now just Surface
            code = code.replace('ParametricSurface', 'Surface')
            
        # Fix incomplete imports - if code uses 3D objects but doesn't import them
        if 'from manim import *' in code:
            # Already has wildcard import, should be fine
            pass
        elif 'from manim import' in code and 'ThreeDScene' in code:
            # Has specific imports but might be missing 3D imports
            # Check for 3D objects that might not be imported
            threed_objects = ['Surface', 'ThreeDScene']
            for obj in threed_objects:
                if obj in code and f'import {obj}' not in code:
                    # Add to imports
                    code = code.replace('from manim import', f'from manim import {obj},', 1)
        
        return code.strip()
    
    def _is_manimce_code(self, code: str) -> bool:
        """Check if code is ManimCE (not ManimGL) and has no external dependencies."""
        # Must have ManimCE import
        if 'from manim import' not in code:
            return False
            
        lines = code.split('\n')
        for line in lines:
            # Skip commented lines
            if line.strip().startswith('#'):
                continue
                
            # Reject if we find an active manimlib import
            if 'from manimlib import' in line:
                return False
                
            # Reject if it has external module dependencies
            # (other than standard library and manim)
            if line.strip().startswith('from ') or line.strip().startswith('import '):
                # Extract module name
                import_line = line.strip()
                
                # Skip standard imports
                if any(std in import_line for std in [
                    'from manim import', 'import manim',
                    'import numpy', 'from numpy', 
                    'import math', 'from math',
                    'import random', 'from random',
                    'import itertools', 'from itertools',
                    'import functools', 'from functools',
                    'import collections', 'from collections',
                    '__future__'
                ]):
                    continue
                    
                # Reject custom module imports
                if ('from functions import' in import_line or
                    'from mobjects import' in import_line or
                    'from utils import' in import_line or
                    'from helpers import' in import_line):
                    return False
                
        return True
    
    def extract(self) -> Iterator[Dict[str, Any]]:
        """Extract samples from The Manim Repository blog."""
        # Get all blog posts
        posts = self._get_blog_posts()
        
        if not posts:
            logger.error("No blog posts found")
            return
        
        extracted_count = 0
        
        for post in posts:
            post_url = post['url']
            post_title = post['title']
            
            logger.debug(f"Processing post: {post_title}")
            
            # Extract code blocks from the post
            code_blocks = self._extract_code_from_post(post_url)
            
            for _, code in code_blocks:
                # Clean the code
                cleaned_code = self._clean_code(code)
                
                # Skip if it's ManimGL code
                if not self._is_manimce_code(cleaned_code):
                    logger.debug(f"Skipping ManimGL code in post: {post_title}")
                    continue
                
                # Extract individual scenes
                scenes = self._extract_scene_info(cleaned_code, post_title)
                
                for scene_info in scenes:
                    # Create description with placeholder and context
                    description = f"{PLACEHOLDER_DESCRIPTION} - Source: {self.source_id} - Post: {post_title} - Scene: {scene_info['name']}"
                    
                    metadata = {
                        "post_title": post_title,
                        "post_url": post_url,
                        "scene_name": scene_info['name'],
                        "source": self.source_id
                    }
                    
                    yield {
                        "description": description,
                        "code": scene_info['code'],
                        "metadata": metadata
                    }
                    extracted_count += 1
        
        logger.info(f"Extracted {extracted_count} samples from {self.source_id}")
    
    def validate_sample(self, sample: Dict[str, Any]) -> bool:
        """Validate that a sample meets quality requirements."""
        # Allow placeholder descriptions
        if sample.get("description", "").startswith(PLACEHOLDER_DESCRIPTION):
            code = sample.get("code", "")
            
            # Basic validation
            if not code or len(code) < 50:
                return False
            
            # Must have class definition and construct method
            if "class" not in code or "def construct" not in code:
                return False
            
            # Must have some Manim-specific content
            manim_indicators = ["self.play", "self.wait", "self.add", "Scene", "ThreeDScene"]
            if not any(indicator in code for indicator in manim_indicators):
                return False
            
            # We now transform ManimGL to ManimCE, so don't reject based on imports
            
            # Check for minimum complexity
            lines = [line.strip() for line in code.split('\n') if line.strip() and not line.strip().startswith('#')]
            if len(lines) < 10:
                return False
            
            return True
        
        # For non-placeholder descriptions, use parent validation
        return super().validate_sample(sample)