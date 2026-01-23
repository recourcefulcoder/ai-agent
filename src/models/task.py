from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    """Types of browser actions that can be performed."""
    NAVIGATE = "navigate"
    SEARCH = "search"
    CLICK = "click"
    TYPE = "type"
    # EXTRACT = "extract"
    WAIT = "wait"
    # ANALYZE_PAGE = "analyze_page"
    REQUEST_CONFIRMATION = "request_confirmation"


class BrowserActionSuggestion(BaseModel):
    """Represent chose-action node's suggestion on what action on browser should it perform to achieve the goal"""
    description: str = Field(
        default=None,
        description="What do you want to do on the browser page",
    )
    reasoning: str = Field(
        default=None,
        description="Reasoning - why this action is being performed"
    )


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
        description="Value to type in, if needed"
    )
    reason: str = Field(
        description="Why this action is being performed"
    )
    is_sensitive: bool = Field(
        default=False,
        description="Whether this action requires user confirmation"
    )
    

    def __str__(self):
        response = f"I should perform \"{self.action_type}\" action on target \"{self.target}\", because {self.reason}"
        return response


    class Config:
        use_enum_values = True


class TaskPlan(BaseModel):
    """
    Structured plan for accomplishing a user's task.
    """
    task_description: str = Field(
        description="Natural language description of what needs to be done"
    )
    steps: List[str] = Field(
        description="Ordered list of subtasks to accomplish the task"
    )  # TODO: Edit description for AI to better understand planning
    
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
