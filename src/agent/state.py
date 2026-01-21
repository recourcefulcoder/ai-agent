from typing import Annotated, List, Optional
from typing_extensions import TypedDict

from langgraph.graph import add_messages
from langchain_core.messages import SystemMessage,AIMessage, HumanMessage
from models.task import TaskPlan, ExecutionResult, BrowserAction
from browser.manager import BrowserManager

from config.settings import settings


class AgentState(TypedDict):
    user_request: str
    # Messages exchanged with the LLM (for reasoning)
    messages: Annotated[List[AIMessage | SystemMessage | HumanMessage], add_messages]
    task_plan: Optional[TaskPlan]
    current_action: Optional[BrowserAction]
    current_action_index: int
    execution_results: List[ExecutionResult]
    browser_manager: BrowserManager
    
    error_count: int
    last_error: Optional[str]
    
    pending_confirmation: Optional[str]
    user_confirmed: bool
    
    final_message: Optional[str]
    success: bool
    
    current_url: Optional[str]


def create_initial_state(user_request: str) -> AgentState:
    sys_prompt = SystemMessage(content=settings.get_prompt("main_agent"), id=1)
    return AgentState(
        user_request=user_request,
        messages=[sys_prompt],
        task_plan=None,
        current_action=None,
        current_action_index=0,
        execution_results=[],
        browser_manager=BrowserManager(),
        error_count=0,
        last_error=None,
        pending_confirmation=None,
        user_confirmed=False,
        final_message=None,
        success=False,
        current_url=None,
        screenshots_taken=[],
    )
