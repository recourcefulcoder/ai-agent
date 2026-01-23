from typing import Literal
from langgraph.graph import StateGraph, END
from agent.state import AgentState
from agent.nodes import (
    plan_task_node,
    execute_action_node,
    verify_action_node,
    handle_error_node,
    seek_confirmation_node,
    finalize_node,
)
from utils.logger import logger


def should_continue_execution(state: AgentState) -> Literal["execute", "finalize"]:
    """
    Decide whether to continue executing actions or finalize.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name
    """
    messages = state.get("messages", [])
    
    # Check if we've exceeded max errors
    if state.get("error_count", 0) >= 3:
        return "finalize"
    
    # Check if last message has tool calls (more work to do)
    if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
        return "execute"
    
    # Check if last message indicates completion
    if messages and hasattr(messages[-1], 'content'):
        content = str(messages[-1].content).lower()
        completion_phrases = [
            "task completed", "task is complete", "finished", 
            "done", "successfully completed", "all set"
        ]
        if any(phrase in content for phrase in completion_phrases):
            return "finalize"
    
    # Continue if we haven't done much yet
    if len(messages) < 10:
        return "execute"
    
    return "finalize"


def should_seek_confirmation(state: AgentState) -> Literal["confirm", "verify"]:
    """
    Decide whether to seek user confirmation or proceed to verification.
    
    Args:
        state: Current agent state
        
    Returns:
        Next node name
    """
    pending = state.get("pending_confirmation")
    
    # TODO: Check if confirmation is pending
    # TODO: Return "confirm" if confirmation needed, "verify" otherwise
    
    if pending:
        return "confirm"
    return "verify"


def should_retry_or_abort(state: AgentState) -> Literal["execute", "finalize"]:
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


def should_handle_error(state: AgentState) -> Literal["error", "continue"]:
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


def create_agent_graph() -> StateGraph:
    """
    Create the LangGraph agent workflow.
    
    The workflow:
    1. plan_task: Create task plan from user request
    2. execute_action: Execute current action
    3. verify_action: Verify action succeeded
    4. (conditional) handle_error: If action failed, handle error
    5. (conditional) seek_confirmation: If sensitive action, get user approval
    6. (loop back to execute_action until all actions done)
    7. finalize: Wrap up and report results
    
    Returns:
        Compiled StateGraph
    """
    logger.info("Creating agent graph...")
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("plan", plan_task_node)
    workflow.add_node("execute", execute_action_node)
    workflow.add_node("verify", verify_action_node)
    workflow.add_node("error", handle_error_node)
    workflow.add_node("confirm", seek_confirmation_node)
    workflow.add_node("finalize", finalize_node)
    
    workflow.set_entry_point("plan")
    
    workflow.add_edge("plan", "execute")
    
    workflow.add_conditional_edges(
        "execute",
        should_seek_confirmation,
        {
            "confirm": "confirm",
            "verify": "verify",
        }
    )
    
    workflow.add_edge("confirm", "verify")
    
    workflow.add_conditional_edges(
        "verify",
        should_handle_error,
        {
            "error": "error",
            "continue": "continue_check",
        }
    )
    
    workflow.add_conditional_edges(
        "error",
        should_retry_or_abort,
        {
            "execute": "execute",
            "finalize": "finalize",
        }
    )
    
    # Add a dummy node for continue_check that just passes through
    workflow.add_node("continue_check", lambda state: state)
    
    workflow.add_conditional_edges(
        "continue_check",
        should_continue_execution,
        {
            "execute": "execute",
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
