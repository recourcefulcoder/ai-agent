"""
LangGraph agent definition.
Defines the workflow graph with nodes and conditional edges.
"""

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
    task_plan = state.get("task_plan")
    current_index = state.get("current_action_index", 0)
    
    # TODO: Check if there are more actions to execute
    # TODO: Check if max errors exceeded
    # TODO: Return "execute" if more actions, "finalize" if done
    
    if task_plan and current_index < len(task_plan.steps):
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
    execution_results = state.get("execution_results", [])
    
    if not execution_results:
        return "continue"
    
    last_result = execution_results[-1]
    
    # TODO: Check if last action failed
    # TODO: Return "error" if failed, "continue" if succeeded
    
    if not last_result.success:
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
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("plan", plan_task_node)
    workflow.add_node("execute", execute_action_node)
    workflow.add_node("verify", verify_action_node)
    workflow.add_node("error", handle_error_node)
    workflow.add_node("confirm", seek_confirmation_node)
    workflow.add_node("finalize", finalize_node)
    
    # Define edges
    workflow.set_entry_point("plan")
    
    # After planning, start executing
    workflow.add_edge("plan", "execute")
    
    # After execution, check if confirmation needed
    workflow.add_conditional_edges(
        "execute",
        should_seek_confirmation,
        {
            "confirm": "confirm",
            "verify": "verify",
        }
    )
    
    # After confirmation, proceed to verify
    workflow.add_edge("confirm", "verify")
    
    # After verification, check if error occurred
    workflow.add_conditional_edges(
        "verify",
        should_handle_error,
        {
            "error": "error",
            "continue": "check_done",  # We'll add this virtual node
        }
    )
    
    # After error handling, decide retry or abort
    workflow.add_conditional_edges(
        "error",
        should_retry_or_abort,
        {
            "execute": "execute",
            "finalize": "finalize",
        }
    )
    
    # Virtual decision point: are we done with all actions?
    # (In practice, we'll use should_continue_execution after verify)
    # Simplified: After verify, check if more actions
    workflow.add_conditional_edges(
        "verify",
        should_continue_execution,
        {
            "execute": "execute",
            "finalize": "finalize",
        }
    )
    
    # Finalize leads to END
    workflow.add_edge("finalize", END)
    
    # Compile the graph
    graph = workflow.compile()
    
    logger.info("Agent graph created successfully")
    return graph


# Global graph instance
agent_graph = None


def get_agent_graph() -> StateGraph:
    """
    Get or create the agent graph singleton.
    
    Returns:
        Compiled agent graph
    """
    global agent_graph
    if agent_graph is None:
        agent_graph = create_agent_graph()
    return agent_graph
