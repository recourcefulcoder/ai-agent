"""
Smart element location using various strategies.
Helps find elements by text, role, semantic meaning, etc.
"""

from typing import Any, Dict, Optional, List
from playwright.async_api import Page, Locator
from utils.logger import logger


class ElementLocator:
    """
    Provides intelligent element location strategies.
    """
    
    def __init__(self):
        pass
    
    def find_semantic(self, description: str) -> Optional[Locator]:
        """
        Find an element using semantic/natural language description.
        This is a more intelligent search that tries multiple strategies.
        
        Args:
            description: Natural language description of the element
            
        Returns:
            Best matching locator
        """
        logger.debug(f"Finding element by semantic description: '{description}'")
        
        # TODO: Parse description to extract:
        # - Element type (button, link, input, etc.)
        # - Key text/label
        # - Context (near other elements, etc.)
        # TODO: Try multiple strategies in order of likelihood
        # TODO: Return best match based on visibility and position
        pass
    
    def list_interactive_elements(self, page: Page) -> List[Dict[str, Any]]:
        """
        Get a list of all interactive elements on the page.
        Returns detailed information about each element.
        
        Args:
            page: The Playwright page to analyze
            
        Returns:
            List of dictionaries containing element information:
            {
                "id": unique identifier,
                "contents": text content or value,
                "label": associated label if exists,
                "placeholder": placeholder text if exists,
                "aria_label": aria-label attribute if exists,
                "role": ARIA role if exists,
                "selector": CSS selector to locate the element,
                "is_visible": whether element is currently visible,
                "is_enabled": whether element is enabled/clickable,
                "tag_name": HTML tag name,
                "href": link that specifies element's destination on click,
                "title": element title if exists,
                "input_type": type of input if element is input,
                
            }
        """
        logger.info("Analyzing page for interactive elements...")
        
        interactive_elements = []
        element_id_counter = 0
        
        selectors = {
            'input': 'input:not([type="hidden"])',
            'textarea': 'textarea',
            'select': 'select',
            'button': 'button',
            
            'link': 'a[href]',
            
            'details': 'details',
            'summary': 'summary',
            
            'aria_button': '[role="button"]',
            'aria_link': '[role="link"]',
            'aria_textbox': '[role="textbox"]',
            'aria_searchbox': '[role="searchbox"]',
            'aria_combobox': '[role="combobox"]',
            'aria_listbox': '[role="listbox"]',
            'aria_option': '[role="option"]',
            'aria_checkbox': '[role="checkbox"]',
            'aria_radio': '[role="radio"]',
            'aria_switch': '[role="switch"]',
            'aria_slider': '[role="slider"]',
            'aria_spinbutton': '[role="spinbutton"]',
            'aria_menuitem': '[role="menuitem"]',
            'aria_menuitemcheckbox': '[role="menuitemcheckbox"]',
            'aria_menuitemradio': '[role="menuitemradio"]',
            'aria_tab': '[role="tab"]',
            
            'clickable_div': 'div[onclick]',
            'clickable_span': 'span[onclick]',
            
            'contenteditable': '[contenteditable="true"]',
        }
        
        for _, selector in selectors.items():
            try:
                elements = page.locator(selector).all()
                
                for element in elements:
                    try:
                        if not element.is_visible() and not element.count():
                            continue
                        
                        element_id_counter += 1
                        
                        tag_name = element.evaluate('el => el.tagName.toLowerCase()')
                        is_visible = element.is_visible()
                        is_enabled = element.is_enabled() if tag_name in ['input', 'button', 'select', 'textarea'] else True
                        
                        contents = ""
                        try:
                            if tag_name in ['input', 'textarea']:
                                contents = element.input_value() or ""
                            else:
                                contents = element.inner_text()
                                if len(contents) > 200:
                                    contents = contents[:197] + "..."
                        except:
                            contents = ""
                        
                        attributes = element.evaluate('''el => {
                            return {
                                id: el.id || null,
                                name: el.name || null,
                                type: el.type || null,
                                placeholder: el.placeholder || null,
                                ariaLabel: el.getAttribute('aria-label') || null,
                                role: el.getAttribute('role') || null,
                                value: el.value || null,
                                href: el.href || null,
                                title: el.title || null,
                                alt: el.alt || null,
                                class: el.className || null
                            }
                        }''')
                        
                        label = None
                        try:
                            if attributes.get('id'):
                                label_element = page.locator(f'label[for="{attributes["id"]}"]')
                                if label_element.count() > 0:
                                    label = label_element.first.inner_text()
                            
                            if not label and tag_name in ['input', 'textarea', 'select']:
                                parent_label = element.evaluate('''el => {
                                    const label = el.closest('label');
                                    return label ? label.innerText : null;
                                }''')
                                if parent_label:
                                    label = parent_label
                        except:
                            pass
                        
                        selector_str = self._generate_selector(element, attributes)
                        
                        element_info = {
                            "id": attributes.get('id'),
                            "tag_name": tag_name,
                            "contents": contents.strip(),
                            "label": label.strip() if label else None,
                            "placeholder": attributes.get('placeholder'),
                            "aria_label": attributes.get('ariaLabel'),
                            "role": attributes.get('role'),
                            "selector": selector_str,
                            "is_visible": is_visible,
                            "is_enabled": is_enabled,
                            "name": attributes.get('name'),
                            "href": attributes.get('href'),
                            "title": attributes.get('title'),
                            "input_type": attributes.get('type') if tag_name == 'input' else None,
                        }
                        
                        # I (dev) remove None values to reduce token cost
                        element_info = {k: v for k, v in element_info.items() if v is not None}
                        interactive_elements.append(element_info)
                        
                    except Exception as e:
                        logger.debug(f"Error processing element: {e}")
                        continue
                        
            except Exception as e:
                logger.debug(f"Error with selector '{selector}': {e}")
                continue
        
        logger.info(f"Found {len(interactive_elements)} interactive elements")
        
        # Remove duplicates (same selector appearing multiple times)
        seen_selectors = set()
        unique_elements = []
        for elem in interactive_elements:
            if elem['selector'] not in seen_selectors:
                seen_selectors.add(elem['selector'])
                unique_elements.append(elem)
        
        logger.info(f"After deduplication: {len(unique_elements)} unique interactive elements")
        
        return unique_elements
    
    def _generate_selector(self, element: Locator, attributes: Dict[str, Any]) -> str:
        """
        Generate a stable CSS selector for an element.
        
        Args:
            element: The Playwright locator
            attributes: Dictionary of element attributes
            
        Returns:
            CSS selector string
        """       
        if attributes.get('id'):
            return f"#{attributes['id']}"
        
        if attributes.get('name'):
            tag_name = element.evaluate('el => el.tagName.toLowerCase()')
            return f"{tag_name}[name='{attributes['name']}']"
        
        return "unknown"
