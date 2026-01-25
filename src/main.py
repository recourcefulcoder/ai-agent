import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import AIMessage, ToolMessage, AIMessageChunk

from agent.graph import get_agent
from agent.state import create_initial_state
from browser.manager import BrowserManager
from config.settings import settings
from utils.logger import setup_logger, logger

console = Console()


def execute_task(
    task: str, 
    debug: bool = False,
    agent: Optional[CompiledStateGraph] = None,
) -> None:
    """
    Run a single task with the agent.
    
    Args:
        task: Natural language task description
        debug: Whether to run in debug mode
    """
    log_level = "DEBUG" if debug else settings.log_level
    setup_logger(log_level)
    
    console.print(Panel.fit(
        f"[bold cyan]Task:[/bold cyan] {task}",
        title="Browser AI Agent",
        border_style="cyan"
    ))
    
    try:
        if agent is None:
            agent = get_agent()
        initial_state = create_initial_state(task)
        
        # Invoke the agent graph
        logger.info("Starting agent execution...")
        
        final_state = None
        step_count = 0
        
        for chunk, metadata in agent.stream(
            initial_state, 
            stream_mode="messages",
        ):
            step_count += 1

            if isinstance(chunk, AIMessageChunk):
                if chunk.content:
                    print(chunk.content, end="", flush=True)
            
            # Show progress
            # for node_name, node_output in event.items():
            #     logger.debug(f"Node {node_name} executed")
                
            #     # Show messages from tools
            #     if "messages" in node_output:
            #         messages = node_output["messages"]
            #         if messages:
            #             for msg in messages:
            #                 if hasattr(msg, 'content') and msg.content:
            #                     # Only show tool messages and important AI responses
            #                     if type(msg) == ToolMessage:
            #                         console.print(f"[dim]→ {str(msg.content)[:200]}...[/dim]")
            #                     elif type(msg) == AIMessage:
            #                         #  and not hasattr(msg, 'tool_calls')
            #                         console.print(f"[cyan]AI: {str(msg.content)[:200]}...[/cyan]")
            
            # if event:
            #     final_state = list(event.values())[0]
        
        logger.info(f"Agent execution completed after {step_count} steps")
        
        # Display final result
        if final_state and final_state.get("success"):
            console.print(Panel(
                final_state.get("final_message", "Task completed!"),
                title="[bold green]Success[/bold green]",
                border_style="green"
            ))
        else:
            error_msg = final_state.get("final_message", "Task failed") if final_state else "Task failed"
            console.print(Panel(
                error_msg,
                title="[bold red]Failed[/bold red]",
                border_style="red"
            ))
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Task interrupted by user[/yellow]")
    
    except Exception as e:
        logger.exception("Error running task")
        console.print(f"[red]Error: {str(e)}[/red]")


def interactive_mode(debug: bool = False) -> None:
    console.print(Panel(
        "[bold cyan]Browser AI Agent - Interactive Mode[/bold cyan]\n\n"
        "Enter tasks in natural language. Type 'exit' or 'quit' to stop.",
        border_style="cyan"
    ))
    
    agent = get_agent()
    try:
        while True:
            task = console.input("\n[bold cyan]Enter your task:[/bold cyan] ")
            
            if task.lower() in ("exit", "quit", "q"):
                break
            
            if not task.strip():
                continue
            
            execute_task(
                task, 
                debug,
                agent
            )
    
    finally:
        BrowserManager().stop()


@click.command()
@click.argument('task', required=False)
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.option('--interactive', '-i', is_flag=True, help='Run in interactive mode')
def main(task: str, debug: bool, interactive: bool):
    """
    Browser AI Agent - Automate browser tasks with natural language.
    
    Examples:
    
        $ python main.py "Search for best pizza places near me"
        
        $ python main.py "Check my calendar and find a free slot next week"
        
        $ python main.py --interactive
    """
    if not task and not interactive:
        console.print("[red]Error: Either provide a task or use --interactive mode[/red]")
        sys.exit(1)

    if interactive:
        interactive_mode(debug)
    else:
        execute_task(task, debug)


if __name__ == "__main__":
    main()
