from typing import List
from pydantic import BaseModel, Field


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
        ans = f"Current plan for the task '{self.task_description}':"
        for step in self.steps:
            ans += f"\n- {step}"
        ans += "\n"
        return ans


class BrowserActionSuggestion(BaseModel):
    """Represent chose-action node's suggestion on what action on browser should it perform to achieve the goal"""
    description: str = Field(
        default=None,
        description="Detailed description of what do you want to do on the browser page",
    )
    reasoning: str = Field(
        default=None,
        description="Reasoning - why this action is being performed"
    )


class DangerCheck(BaseModel):
    is_sensitive: bool = Field(
        default=False,
        descrpition="Answer to whether suggested action is dangerous (i.e. sensitive); true if it is, false if it isn't"
    )

class PlanGoalAchieved(BaseModel):
    is_achieved: bool = Field(
        default=False,
        description="Answer to question whether curren plan goal achieved at this point"
    )


# class TaskResult(BaseModel):
#     success: bool = Field(
#         description="Whether the overall task succeeded"
#     )
#     message: str = Field(
#         description="Summary message for the user"
#     )
#     execution_results: List[ExecutionResult] = Field(
#         default_factory=list,
#         description="Results of individual actions"
#     )
#     artifacts: List[str] = Field(
#         default_factory=list,
#         description="Paths to screenshots or other generated files"
#     )
