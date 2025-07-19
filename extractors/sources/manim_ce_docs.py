"""ManimCE official documentation examples extractor."""

import json
import logging
import re
from pathlib import Path
from typing import Iterator, Dict, Any, Optional, List
import requests
from bs4 import BeautifulSoup

from ..base import BaseExtractor
from ..registry import register_extractor
from ..constants import PLACEHOLDER_DESCRIPTION

logger = logging.getLogger(__name__)


@register_extractor
class ManimCEDocsExtractor(BaseExtractor):
    """Extractor for examples from ManimCE official documentation."""
    
    source_id = "manim_ce_docs"
    source_name = "ManimCE Official Documentation"
    priority = 5  # Highest priority as these are official examples
    
    def _validate_config(self) -> None:
        """Validate configuration."""
        self.base_url = self.config.get("base_url", "https://docs.manim.community/en/stable/")
        self.cache_dir = Path(self.config.get("cache_dir", "cache/manim_ce_docs"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Pages to extract examples from
        self.pages = [
            "examples.html",
            "reference/manim.animation.animation.html",
            "reference/manim.animation.composition.html",
            "reference/manim.animation.creation.html",
            "reference/manim.animation.fading.html",
            "reference/manim.animation.growing.html",
            "reference/manim.animation.indication.html",
            "reference/manim.animation.movement.html",
            "reference/manim.animation.numbers.html",
            "reference/manim.animation.rotation.html",
            "reference/manim.animation.transform.html",
            "reference/manim.animation.updater.html",
            "reference/manim.mobject.geometry.arc.html",
            "reference/manim.mobject.geometry.boolean_ops.html",
            "reference/manim.mobject.geometry.line.html",
            "reference/manim.mobject.geometry.polygram.html",
            "reference/manim.mobject.geometry.shape_matchers.html",
            "reference/manim.mobject.geometry.tips.html",
            "reference/manim.mobject.graph.html",
            "reference/manim.mobject.graphing.coordinate_systems.html",
            "reference/manim.mobject.graphing.functions.html",
            "reference/manim.mobject.graphing.number_line.html",
            "reference/manim.mobject.graphing.probability.html",
            "reference/manim.mobject.graphing.scale.html",
            "reference/manim.mobject.matrix.html",
            "reference/manim.mobject.svg.brace.html",
            "reference/manim.mobject.svg.svg_mobject.html",
            "reference/manim.mobject.table.html",
            "reference/manim.mobject.text.code_mobject.html",
            "reference/manim.mobject.text.numbers.html",
            "reference/manim.mobject.text.tex_mobject.html",
            "reference/manim.mobject.text.text_mobject.html",
            "reference/manim.mobject.three_d.polyhedra.html",
            "reference/manim.mobject.three_d.three_d_utils.html",
            "reference/manim.mobject.three_d.three_dimensions.html",
            "reference/manim.mobject.types.image_mobject.html",
            "reference/manim.mobject.types.point_cloud_mobject.html",
            "reference/manim.mobject.types.vectorized_mobject.html",
            "reference/manim.mobject.value_tracker.html",
            "reference/manim.mobject.vector_field.html",
            "reference/manim.scene.moving_camera_scene.html",
            "reference/manim.scene.scene.html",
            "reference/manim.scene.three_d_scene.html",
            "reference/manim.scene.vector_space_scene.html",
            "reference/manim.scene.zoomed_scene.html",
            # Tutorial pages
            "tutorials/quickstart.html",
            "tutorials/building_blocks.html",
            # Guide pages with examples
            "guides/deep_dive.html",
            "guides/using_text.html",
            "guides/add_voiceovers.html"
        ]
    
    def estimate_sample_count(self) -> Optional[int]:
        """Estimate based on typical number of examples per page."""
        # Updated estimate based on investigation: ~87 total examples expected
        return 87
    
    def _fetch_page(self, page: str) -> Optional[str]:
        """Fetch a documentation page with caching."""
        cache_file = self.cache_dir / page.replace('/', '_')
        
        # Check cache first
        if cache_file.exists():
            logger.debug(f"Using cached page: {page}")
            return cache_file.read_text(encoding='utf-8')
        
        # Fetch from web
        try:
            url = self.base_url + page
            logger.info(f"Fetching: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Cache the response
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(response.text, encoding='utf-8')
            
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch {page}: {e}")
            return None
    
    def _extract_code_blocks(self, html: str) -> List[Dict[str, Any]]:
        """Extract code examples from HTML documentation."""
        soup = BeautifulSoup(html, 'html.parser')
        examples = []
        
        # Find all code blocks that look like complete Manim examples
        # In Sphinx docs, these are usually in <div class="highlight">
        for highlight_div in soup.find_all('div', class_='highlight'):
            pre_tag = highlight_div.find('pre')
            if not pre_tag:
                continue
            
            code = pre_tag.get_text().strip()
            
            # Basic validation - must have class and Scene
            if 'class' not in code or 'Scene' not in code:
                continue
            
            # Look for context around the code block
            # Try to find a description in nearby elements
            description = None
            
            # Check for a preceding paragraph or heading
            prev_elem = highlight_div.find_previous_sibling()
            if prev_elem and prev_elem.name in ['p', 'h1', 'h2', 'h3', 'h4']:
                description = prev_elem.get_text().strip()
            
            # Check for docstring-style description in dl/dt/dd elements
            if not description:
                parent_section = highlight_div.find_parent(['section', 'div'], class_=['class', 'method', 'function'])
                if parent_section:
                    # Look for class/function name
                    sig_elem = parent_section.find('dt', class_='sig')
                    if sig_elem:
                        class_name = sig_elem.get('id', '').split('.')[-1]
                        if class_name:
                            # Get the description from dd element
                            dd_elem = parent_section.find('dd')
                            if dd_elem:
                                desc_p = dd_elem.find('p')
                                if desc_p:
                                    description = f"{class_name}: {desc_p.get_text().strip()}"
            
            # Extract scene name from code for metadata
            scene_match = re.search(r'class\s+(\w+)\s*\([^)]*Scene[^)]*\)', code)
            scene_name = scene_match.group(1) if scene_match else "UnknownScene"
            
            # Determine if this is likely an animation or static scene
            has_animation = any(pattern in code for pattern in ['self.play(', 'self.wait(', '.animate.', '.play(', '.wait('])
            
            examples.append({
                'code': code,
                'description': description or f"{PLACEHOLDER_DESCRIPTION} - Create a Manim animation using {scene_name}",
                'metadata': {
                    'scene_name': scene_name,
                    'has_animation': has_animation,
                    'needs_description': description is None
                }
            })
        
        return examples
    
    def _extract_from_examples_page(self, html: str) -> List[Dict[str, Any]]:
        """Special handling for the main examples page which has a different structure."""
        soup = BeautifulSoup(html, 'html.parser')
        examples = []
        
        # The examples page has sections with headings followed by code
        current_section = None
        
        for elem in soup.find_all(['h2', 'h3', 'div']):
            if elem.name in ['h2', 'h3']:
                # Update current section
                current_section = elem.get_text().strip()
            elif elem.name == 'div' and 'highlight' in elem.get('class', []):
                pre_tag = elem.find('pre')
                if not pre_tag:
                    continue
                
                code = pre_tag.get_text().strip()
                
                # Validate
                if 'class' not in code or 'Scene' not in code:
                    continue
                
                # Extract scene name
                scene_match = re.search(r'class\s+(\w+)\s*\([^)]*Scene[^)]*\)', code)
                scene_name = scene_match.group(1) if scene_match else "UnknownScene"
                
                # Build description
                description = None
                if current_section:
                    description = f"Example from {current_section}: {scene_name}"
                
                # Sometimes there's a caption or description right before the code
                prev_p = elem.find_previous_sibling('p')
                if prev_p and prev_p.get_text().strip():
                    desc_text = prev_p.get_text().strip()
                    if len(desc_text) > 10 and len(desc_text) < 200:  # Reasonable description length
                        description = desc_text
                
                examples.append({
                    'code': code,
                    'description': description or f"{PLACEHOLDER_DESCRIPTION} - Example demonstrating {scene_name}",
                    'metadata': {
                        'scene_name': scene_name,
                        'section': current_section,
                        'needs_description': description is None or PLACEHOLDER_DESCRIPTION in description
                    }
                })
        
        return examples
    
    def extract(self) -> Iterator[Dict[str, Any]]:
        """Extract examples from ManimCE documentation."""
        total_extracted = 0
        
        for page in self.pages:
            logger.info(f"Processing page: {page}")
            
            # Fetch the page
            html = self._fetch_page(page)
            if not html:
                logger.warning(f"Skipping {page} - failed to fetch")
                continue
            
            # Extract examples based on page type
            if page == "examples.html":
                examples = self._extract_from_examples_page(html)
            else:
                examples = self._extract_code_blocks(html)
            
            logger.info(f"Found {len(examples)} examples in {page}")
            
            # Yield each example
            for example in examples:
                # Add source page to metadata
                example['metadata']['source_page'] = page
                example['metadata']['url'] = self.base_url + page
                
                total_extracted += 1
                yield example
        
        logger.info(f"Total examples extracted from ManimCE docs: {total_extracted}")