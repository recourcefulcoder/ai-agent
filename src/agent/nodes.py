from typing import Dict, Any
    
from rich.console import Console
from rich.panel import Panel
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage

from agent.state import AgentState
from models.task import TaskPlan, BrowserActionSuggestion, DangerCheck, PlanGoalAchieved
from utils.logger import logger
from services.llm import get_llm_service
from tools.interaction import create_interaction_tools
from tools.navigation import create_navigation_tools
from config.settings import settings


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

    llm = (
        get_llm_service()
        .get_main_llm()
        .with_structured_output(TaskPlan)
    )
    
    messages = state.get("messages") + [HumanMessage(content=user_request)]
    
    response = llm.invoke(messages)
    response_msg = AIMessage(content=str(response))
    
    logger.info(f"Planning response received; steps are:")
    for step in response.steps:
        logger.info(f"{step}")
    
    return {
        "task_plan": response,
        "current_plan_step_ind": 0,
        "messages": [response_msg],
        "current_plan_step_messages": [response_msg],
    }

def choose_next_action_node(state: AgentState) -> Dict[str, Any]:
    """
    Execution node: Decides what browser action should be taken next to achieve current plan goal
    
    This node uses the LLM with tools to decide and what browser action to perform, updates 
    state with "current browser action" 
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with execution result
    """
    logger.info("Executing action...")

    llm = (
        get_llm_service()
        .get_main_llm()
        .with_structured_output(BrowserActionSuggestion)        
    )

    logger.info(f"{state.get('messages')}")

    response = llm.invoke(state.get("messages"))
    
    return {
        "current_action": response,
    }

def reflect_browser_action_node(state: AgentState):
    """Validates current state of current plan goal - is succeded? 
    updates "current_goal_achieved" with True or False 
    and sets 'current_plan_step_ind' with relevant for now; if task completed, sets current_plan_step_ind to None"""
    llm = (
        get_llm_service()
        .get_main_llm()
        .with_structured_output(PlanGoalAchieved)
    )

    step_ind = state.get("current_plan_step_ind")
    goal = state.get("task_plan").steps[step_ind]
    goal = f"current goal is: {goal}"
    context = state.get("current_plan_step_messages") + [SystemMessage(content=goal)]

    decision = llm.invoke(context)
    if decision.is_achieved:
        return {
            "messages": [SystemMessage(
                content="goal for current plan step is achieved, proceeding with next step of the plan"
            )],
            "current_plan_step_messages": [],
            "current_plan_step_ind": step_ind + 1,
        }
    return {}

def seek_confirmation_node(state: AgentState) -> Dict[str, Any]:
    """
    Confirmation node: Decides whether action is sensitive or not and requests user confirmation for sensitive ones.
    
    This node displays a confirmation request and waits for user input.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with user_confirmed flag
    """
    logger.info("Seeking user confirmation...")
    
    console = Console()
    action_to_check = state.get("current_action")
    is_sensitive = False
    
    llm = (
        get_llm_service()
        .get_main_llm()
        .with_structured_output(DangerCheck)
    )

    messages = [
        SystemMessage(content=settings.get_prompt("safety_check")),
        AIMessage(content=state.get("current_action").description)
    ]

    is_sensitive = llm.invoke(messages)

    if is_sensitive:
        console.print(Panel(
            f"[bold yellow]Confirmation Required[/bold yellow]\n\n{action_to_check.description}",
            border_style="yellow"
        ))
        
        response = console.input("[bold yellow]Proceed? (yes/no):[/bold yellow] ").strip().lower()
        confirmed = response in ['yes', 'y']

        # TODO: If user rejected action, SystemMessage of representing it should be added to state messages queue!
        
        logger.info(f"User {'confirmed' if confirmed else 'declined'} action")
        
        return {
            "user_confirmed": confirmed,
        }
    
    return {
        "user_confirmed": True,
    }

async def perform_action_node(state: AgentState) -> Dict[str, Any]:

    tools = create_interaction_tools() + create_navigation_tools()
    tools_by_name = {tool.name: tool for tool in tools}
    llm = (
        get_llm_service()
        .get_main_llm()
        .bind_tools(tools, tool_choice="auto")
    )

    goal = f"execute this task step: {state.get('current_action').description}"
    sys_msg = SystemMessage(content=goal)
    context = state.get("current_plan_step_messages") + [sys_msg]

    answer = llm.invoke(context)
    result = [answer]
    for tool_call in answer.tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = await tool.ainvoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    
    return {
        "messages": result,
        "current_plan_step_messages": context + result
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
    
    messages = state.get("messages")
    error_count = state.get("error_count", 0)
    
    # Check if there were too many errors
    if error_count >= 3:
        return {
            "success": False,
            "final_message": f"Task failed after {error_count} errors. Please try again or rephrase your request.",
        }
    
    # # Summarize based on messages
    # if messages:
    #     last_msg = messages[-1]
    #     if hasattr(last_msg, 'content'):
    #         content = str(last_msg.content)
            
    #         completion_indicators = ["completed", "done", "finished", "success"]
    #         if any(indicator in content.lower() for indicator in completion_indicators):
    #             return {
    #                 "success": True,
    #                 "final_message": "Task completed successfully!",
    #             }
    
    return {
        "success": True,
        "final_message": "Task execution finished.",
    }
