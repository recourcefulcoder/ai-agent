"""
Pydantic models for task planning and execution.
"""

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Types of browser actions that can be performed."""
    NAVIGATE = "navigate"
    SEARCH = "search"
    CLICK = "click"
    TYPE = "type"
    EXTRACT = "extract"
    SCREENSHOT = "screenshot"
    WAIT = "wait"
    ANALYZE_PAGE = "analyze_page"
    REQUEST_CONFIRMATION = "request_confirmation"


class BrowserAction(BaseModel):
    """
    Represents a single browser action to be performed.
    """
    action_type: ActionType = Field(
        description="The type of action to perform"
    )
    target: Optional[str] = Field(
        default=None,
        description="Target element description or URL"
    )
    value: Optional[str] = Field(
        default=None,
        description="Value to type or search for"
    )
    reason: str = Field(
        description="Why this action is being performed"
    )
    is_sensitive: bool = Field(
        default=False,
        description="Whether this action requires user confirmation"
    )
    
    class Config:
        use_enum_values = True


class TaskPlan(BaseModel):
    """
    Structured plan for accomplishing a user's task.
    """
    task_description: str = Field(
        description="Natural language description of what needs to be done"
    )
    steps: List[BrowserAction] = Field(
        description="Ordered list of actions to accomplish the task"
    )
    estimated_duration: Optional[str] = Field(
        default=None,
        description="Rough estimate of how long this will take"
    )
    requires_user_data: bool = Field(
        default=False,
        description="Whether this task needs user preferences/data"
    )
    
    def __str__(self) -> str:
        """Human-readable representation of the plan."""
        # TODO: Implement pretty-printing of the plan
        pass


class ExecutionResult(BaseModel):
    """
    Result of executing a browser action.
    """
    action: BrowserAction = Field(
        description="The action that was executed"
    )
    success: bool = Field(
        description="Whether the action succeeded"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if action failed"
    )
    extracted_data: Optional[str] = Field(
        default=None,
        description="Any data extracted during the action"
    )
    screenshot_path: Optional[str] = Field(
        default=None,
        description="Path to screenshot if one was taken"
    )
    
    class Config:
        arbitrary_types_allowed = True


class TaskResult(BaseModel):
    """
    Final result of task execution.
    """
    success: bool = Field(
        description="Whether the overall task succeeded"
    )
    message: str = Field(
        description="Summary message for the user"
    )
    execution_results: List[ExecutionResult] = Field(
        default_factory=list,
        description="Results of individual actions"
    )
    artifacts: List[str] = Field(
        default_factory=list,
        description="Paths to screenshots or other generated files"
    )
