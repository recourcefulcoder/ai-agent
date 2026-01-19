"""
Pydantic models for page analysis and element information.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ElementInfo(BaseModel):
    """
    Information about a specific page element.
    """
    selector: str = Field(
        description="CSS selector or other identifier for the element"
    )
    element_type: str = Field(
        description="Type of element (button, input, link, etc.)"
    )
    text_content: Optional[str] = Field(
        default=None,
        description="Visible text in the element"
    )
    attributes: Dict[str, str] = Field(
        default_factory=dict,
        description="HTML attributes of the element"
    )
    is_visible: bool = Field(
        default=True,
        description="Whether the element is currently visible"
    )
    is_interactive: bool = Field(
        default=False,
        description="Whether the element can be clicked/interacted with"
    )


class PageAnalysis(BaseModel):
    """
    Structured analysis of a web page's content and structure.
    """
    url: str = Field(
        description="Current page URL"
    )
    title: str = Field(
        description="Page title"
    )
    main_content: str = Field(
        description="Summary of the main page content"
    )
    interactive_elements: List[ElementInfo] = Field(
        default_factory=list,
        description="Buttons, links, and other interactive elements"
    )
    form_fields: List[ElementInfo] = Field(
        default_factory=list,
        description="Input fields, textareas, etc."
    )
    extracted_text: Optional[str] = Field(
        default=None,
        description="Relevant text extracted from the page"
    )
    suggested_actions: List[str] = Field(
        default_factory=list,
        description="Potential next actions based on page content"
    )
    requires_vision_analysis: bool = Field(
        default=False,
        description="Whether screenshot analysis would be helpful"
    )
