from typing import Dict, Any
    
from rich.console import Console
from rich.panel import Panel
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage

from agent.state import AgentState
from models.task import TaskPlan, BrowserAction, ExecutionResult
from utils.logger import logger
from services.llm import get_llm_service
from tools.interaction import create_interaction_tools
from tools.navigation import create_navigation_tools


def plan_task_node(state: AgentState) -> Dict[str, Any]:
    """
    Planning node: Analyzes user request and creates a task plan.
    
    This node:
    1. Takes the user's request
    2. Uses LLM to break it down into actionable steps
    3. Creates a structured TaskPlan
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with task_plan
    """
    logger.info("Planning task...")
    
    user_request = state.get("user_request")
    
    # Get LLM with tool binding
    llm = (
        get_llm_service()
        .get_main_llm()
        .with_structured_output(TaskPlan)
    )
    
    messages = state["messages"] + [HumanMessage(content=user_request)]
    
    response = llm.invoke(messages)
    
    logger.info(f"Planning response received")
    
    return {
        "task_plan": response,
        "messages": messages + [response],
    }


def choose_next_action_node(state: AgentState) -> Dict[str, Any]:
    """
    Execution node: Decides what BrowserAction should be taken next o achieve current plan goal
    
    This node uses the LLM with tools to decide and what BrowserAction to perform, updates 
    state with "current browser action" 
    IMPORTANT: This node decides whether action is sensitive or not! It sets 'pending_confirmation'!
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with execution result
    """
    logger.info("Executing action...")
    
    messages = state["messages"]
    
    # if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
    #     result = tool_node(state)
    #     return result
    # else:
    #     llm = (
    #         get_llm_service()
    #         .get_main_llm()
    #         .with_structured_output(ExecutionResult)
    #     )
    #     tools = create_interaction_tools() + create_navigation_tools()
    #     llm_with_tools = llm.bind_tools(tools)
        
    #     response = llm_with_tools.invoke(messages)
        
    #     return {
    #         "messages": [response],
    #     }
    return dict()


def reflect_browser_action_node(state: AgentState):
    """Validates current state of current plan goal - is succeded? 
    updates "current_goal_achieved" with True or False 
    and sets 'current_plan_goal' with relevant for now; if task completed, sets current_plan_goal to None"""
    pass


def seek_confirmation_node(state: AgentState) -> Dict[str, Any]:
    """
    Confirmation node: Requests user confirmation for sensitive actions.
    
    This node displays a confirmation request and waits for user input.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with user_confirmed flag
    """
    logger.info("Seeking user confirmation...")
    
    console = Console()
    pending = state.get("pending_confirmation", "")
    
    if pending:
        console.print(Panel(
            f"[bold yellow]Confirmation Required[/bold yellow]\n\n{pending}",
            border_style="yellow"
        ))
        
        response = console.input("[bold yellow]Proceed? (yes/no):[/bold yellow] ").strip().lower()
        confirmed = response in ['yes', 'y']

        # TODO: If user rejected action, SystemMessage of representing it should be added to state messages queue!
        
        logger.info(f"User {'confirmed' if confirmed else 'declined'} action")
        
        return {
            "user_confirmed": confirmed,
            "pending_confirmation": None,
        }
    
    return {
        "user_confirmed": True,
        "pending_confirmation": None,
    }


def finalize_node(state: AgentState) -> Dict[str, Any]:
    """
    Finalization node: Wraps up task execution and reports results.
    
    This node summarizes the conversation and task completion.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with final_message
    """
    logger.info("Finalizing task...")
    
    messages = state["messages"]
    error_count = state.get("error_count", 0)
    
    # Check if there were too many errors
    if error_count >= 3:
        return {
            "success": False,
            "final_message": f"Task failed after {error_count} errors. Please try again or rephrase your request.",
        }
    
    # Summarize based on messages
    if messages:
        last_msg = messages[-1]
        if hasattr(last_msg, 'content'):
            content = str(last_msg.content)
            
            # Check if task seems complete
            completion_indicators = ["completed", "done", "finished", "success"]
            if any(indicator in content.lower() for indicator in completion_indicators):
                return {
                    "success": True,
                    "final_message": "Task completed successfully!",
                }
    
    return {
        "success": True,
        "final_message": "Task execution finished.",
    }
