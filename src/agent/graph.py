from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from agent.state import AgentState
from agent.nodes import (
    plan_task_node,
    choose_next_action_node,
    reflect_browser_action_node,
    seek_confirmation_node,
    finalize_node,
)
from utils.logger import logger
from tools.interaction import create_interaction_tools
from tools.navigation import create_navigation_tools


def should_continue_execution(state: AgentState) -> Literal["continue", "finalize"]:
    """
    Decide whether to continue executing plan goals or finalize.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name
    """
    if state.get("current_plan_goal") is None:
        return "finalize"
    
    return "continue"

def user_confirmed_action(state: AgentState) -> Literal["confirmed", "rejected"]:
    """Checks whether current browser action was confirmed by user or not"""
    if state.get("user_confirmed"):
        return "confirmed"
    return "rejected"

def reflection_mapping(state: AgentState) -> Literal["proceed_with_next", "continue_current"]:
    """Decides, based on reflect_browser_action_node, whether we should proceed to next plan goal or continue doing this one"""
    return "proceed_with_next" if state.get("current_plan_goal_achieved") else "continue_current"

# def should_seek_confirmation(state: AgentState) -> Literal["confirm", "verify"]:
    """
    Decide whether to seek user confirmation or proceed to verification.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name
    """   
    if state.get("pending_confirmation", None):
        return "confirm"
    return "verify"

# def should_retry_or_abort(state: AgentState) -> Literal["execute", "finalize"]:
    """
    Decide whether to retry after error or abort task.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name
    """
    error_count = state.get("error_count", 0)
    max_retries = 3  # TODO: Get from settings
    
    # TODO: Check if max retries exceeded
    # TODO: Check if error is recoverable
    # TODO: Return "execute" to retry, "finalize" to abort
    
    if error_count < max_retries:
        return "execute"
    return "finalize"

# def should_handle_error(state: AgentState) -> Literal["error", "continue"]:
    """
    Decide whether to handle error or continue to next action.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name
    """
    # Check if we just encountered an error
    if state.get("last_error"):
        return "error"
    
    return "continue"

# Error handling is pending implementation

def create_agent_graph() -> StateGraph:
    """
    Create the LangGraph agent workflow.
    
    The workflow:
    1. plan_task: Create task plan from user request
    2. choose_next_action: Chooses next action for achieving current plan goal
    3. confirm_action: Check whether requires user confirmation and proceed if does
    4. tool: calling tools and returning results
    6. (loop back to choose_next_action until plan_goal achieved)
    7. (loop back to choose_next_action until all plan_goals achieved)
    7. finalize: Wrap up and report results
    
    Returns:
        Compiled StateGraph
    """
    logger.info("Creating agent graph...")
    
    workflow = StateGraph(AgentState)

    tools = create_navigation_tools() + create_interaction_tools()
    
    workflow.add_node("plan", plan_task_node)
    workflow.add_node("choose_action", choose_next_action_node)
    workflow.add_node("confirm", seek_confirmation_node)
    workflow.add_node("reflect", reflect_browser_action_node)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node("finalize", finalize_node)

    # Dummy node for continue_check that just passes through
    workflow.add_node("continue_check", lambda state: state)
    
    workflow.set_entry_point("plan")
    
    workflow.add_edge("plan", "choose_action")
    workflow.add_edge("choose_action", "confirm")
    
    workflow.add_conditional_edges(
        "confirm",
        user_confirmed_action,
        {
            "confirmed": "tools",
            "rejected": "reflect",
        }
    )
    
    workflow.add_edge("tools", "reflect")
    workflow.add_edge("reflect", "choose_action")   
    
    workflow.add_conditional_edges(
        "reflect",
        should_continue_execution,
        {
            "continue": "choose_action",
            "finalize": "finalize",
        }
    )
    
    workflow.add_edge("finalize", END)
    
    graph = workflow.compile()
    
    logger.info("Agent graph created successfully")
    return graph


agent_graph = None


def get_agent() -> StateGraph:
    global agent_graph
    if agent_graph is None:
        agent_graph = create_agent_graph()
    return agent_graph
