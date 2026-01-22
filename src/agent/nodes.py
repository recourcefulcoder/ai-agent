from typing import Dict, Any
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from agent.state import AgentState
from models.task import TaskPlan, BrowserAction, ExecutionResult
from utils.logger import logger


def plan_task_node(state: AgentState) -> Dict[str, Any]:
    """
    Planning node: Analyzes user request and creates a task plan.
    
    This node:
    1. Takes the user's request
    2. Uses LLM to break it down into actionable steps
    3. Creates a structured TaskPlan
    4. Identifies any user data needed
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with task_plan
    """
    logger.info("Planning task...")
    
    user_request = state["user_request"]
    
    from services.llm import get_llm_service
    from tools import get_all_tools
    
    # Get LLM with tool binding
    llm = get_llm_service().get_main_llm()
    tools = get_all_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    # Add user request to messages
    messages = state["messages"] + [HumanMessage(content=user_request)]
    
    # Invoke LLM to get planning response
    response = llm_with_tools.invoke(messages)
    
    logger.info(f"Planning response received")
    
    # For now, we'll use a simple plan structure
    # In a more advanced implementation, you could use structured output
    plan = TaskPlan(
        task_description=user_request,
        steps=[],  # Will be populated by execute node dynamically
        requires_user_data=False,
    )
    
    return {
        "task_plan": plan,
        "messages": messages + [response],
    }


def execute_action_node(state: AgentState) -> Dict[str, Any]:
    """
    Execution node: Executes the current browser action.
    
    This node uses the LLM with tools to decide and execute actions.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with execution result
    """
    logger.info("Executing action...")
    
    from services.llm import get_llm_service
    from tools import get_all_tools
    
    messages = state["messages"]
    
    # Check if last message has tool calls
    if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
        # Execute the tool calls
        result = tool_node(state)
        return result
    else:
        # LLM needs to decide next action
        llm = get_llm_service().get_main_llm()
        tools = get_all_tools()
        llm_with_tools = llm.bind_tools(tools)
        
        response = llm_with_tools.invoke(messages)
        
        return {
            "messages": [response],
        }


def verify_action_node(state: AgentState) -> Dict[str, Any]:
    """
    Verification node: Checks if the last action succeeded.
    
    This node:
    1. Checks the last execution result
    2. If failed, increments error count
    3. Optionally takes screenshot for analysis
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with verification info
    """
    logger.info("Verifying action...")
    
    messages = state["messages"]
    
    # Check if last message indicates an error
    if messages and hasattr(messages[-1], 'content'):
        content = str(messages[-1].content)
        if content.startswith("Error:"):
            logger.warning(f"Action failed: {content}")
            return {
                "error_count": state.get("error_count", 0) + 1,
                "last_error": content,
            }
    
    # Action succeeded
    return {}


def handle_error_node(state: AgentState) -> Dict[str, Any]:
    """
    Error handling node: Attempts to recover from failures.
    
    This node logs the error and lets the LLM decide how to recover.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with recovery plan
    """
    logger.warning("Handling error...")
    
    last_error = state.get("last_error", "Unknown error")
    error_count = state.get("error_count", 0)
    
    logger.error(f"Error #{error_count}: {last_error}")
    
    # Add error context to messages
    error_msg = HumanMessage(
        content=f"The last action failed with error: {last_error}. Please try a different approach or continue with the task."
    )
    
    return {
        "messages": [error_msg],
    }


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
    
    from rich.console import Console
    from rich.panel import Panel
    
    console = Console()
    pending = state.get("pending_confirmation", "")
    
    if pending:
        console.print(Panel(
            f"[bold yellow]Confirmation Required[/bold yellow]\n\n{pending}",
            border_style="yellow"
        ))
        
        response = console.input("[bold yellow]Proceed? (yes/no):[/bold yellow] ").strip().lower()
        confirmed = response in ['yes', 'y']
        
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


def tool_node(state: AgentState):
    """
    Tool node performs tool calls and returns results.
    """
    from tools import get_all_tools
    
    result = []
    tools = get_all_tools()
    tools_by_name = {tool.name: tool for tool in tools}
    
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}

