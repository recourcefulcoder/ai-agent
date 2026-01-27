from typing import Any, Dict, Optional, List
from playwright.async_api import Page, Locator
from utils.logger import logger


class ElementLocator:
    """
    Provides intelligent page element location strategies.
    """

    _informative_roles = {
        'article', 'section', 'paragraph', 'listitem', 'blockquote', 
        'heading', 'text', 'list', 'figure', 'img', 'link',
        'code', 'pre', 'table', 'row', 'cell',
        'definition', 'term', 'note', 'complementary',
        'navigation', 'region', 'contentinfo', 'banner', 'text leaf'
    }  # roles of A11y tree elements those may hold valuable textual information

    _interactive_selectors = {
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
    }  # HTML selectors those are pointing on interactive elements (buttons, links, etc.)

    def __init__(self):
        pass

    async def list_informative_elements(self, page: Page) -> List[Dict[str, Any]]:
        logger.info("Extracting informative elements from accessibility tree...")
        
        accessibility_tree = await page.accessibility.snapshot()
        
        if not accessibility_tree:
            logger.warning("No accessibility tree available")
            return []
               
        informative_elements = self._extract_informative_nodes(accessibility_tree, [])
        logger.info(f"Extracted {len(informative_elements)} informative elements")
        return informative_elements
    
    async def list_interactive_elements(self, page: Page) -> List[Dict[str, Any]]:
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
        
        for _, selector in self._interactive_selectors.items():
            try:
                elements = await page.locator(selector).all()
                
                for element in elements:
                    try:
                        if not await element.is_visible() and not await element.count():
                            continue
                        
                        element_id_counter += 1
                        
                        tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                        is_enabled = await element.is_enabled() if tag_name in ['input', 'button', 'select', 'textarea'] else True
                        
                        contents = ""
                        try:
                            if tag_name in ['input', 'textarea']:
                                contents = await element.input_value() or ""
                            else:
                                contents = await element.inner_text()
                                if len(contents) > 200:
                                    contents = contents[:197] + "..."
                        except:
                            contents = ""
                        
                        attributes = await element.evaluate('''el => {
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
                                label_element = await page.locator(f'label[for="{attributes["id"]}"]')
                                if await label_element.count() > 0:
                                    label = await label_element.first.inner_text()
                            
                            if not label and tag_name in ['input', 'textarea', 'select']:
                                parent_label = await element.evaluate('''el => {
                                    const label = el.closest('label');
                                    return label ? label.innerText : null;
                                }''')
                                if parent_label:
                                    label = parent_label
                        except:
                            pass
                        
                        selector_str = await self._generate_selector(element, attributes)
                        
                        element_info = {
                            "id": attributes.get('id'),
                            "tag_name": tag_name,
                            "contents": contents.strip(),
                            "label": label.strip() if label else None,
                            "placeholder": attributes.get('placeholder'),
                            "aria_label": attributes.get('ariaLabel'),
                            "role": attributes.get('role'),
                            "selector": selector_str,
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
        
        return interactive_elements
    
    @staticmethod
    async def _generate_selector(element: Locator, attributes: Dict[str, Any]) -> str:
        """
        Generate a stable CSS selector for an element.
        
        Args:
            element: The Playwright async locator
            attributes: Dictionary of element attributes
            
        Returns:
            CSS selector string
        """       
        if attributes.get('id'):
            return f"#{attributes['id']}"
        
        if attributes.get('name'):
            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
            return f"{tag_name}[name='{attributes['name']}']"
        
        return "unknown"

    @classmethod
    def _extract_informative_nodes(
        cls, 
        node, 
        # informative_elements: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Recursively extract informative elements from the Accessibility tree.
        "leafs" of the tree are closer to the beginning of the returned list 
        """
        role = node.get('role')
        name = node.get('name', '').strip()
        informative_elements = []
        
        if role in cls._informative_roles:
            content = name
            
            if role in {'article', 'section', 'paragraph', 'listitem', 'blockquote'}:
                child_texts = []
                
                def collect_text(n, child_texts):
                    if 'text' in n.get('role') and n.get('name'):
                        child_texts.append(n.get('name'))
                    for child in n.get('children', []):
                        child_texts = collect_text(child, child_texts) + child_texts
                    return child_texts
                        
                child_texts = collect_text(node, [])
                
                if child_texts:
                    content = '\n'.join(child_texts)
            
            if content:
                informative_elements.append({
                    'role': role,
                    'contents': content
                })
        
        children_info = []
        for child in node.get('children', []):
            child_info = cls._extract_informative_nodes(
                child, 
                # informative_elements,
            )
            children_info = child_info + children_info
        informative_elements = children_info + informative_elements
        
        # logger.info(f"NODE: {role}|{name}; \nCONTENTS:{informative_elements}")

        return informative_elements
