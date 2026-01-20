import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from langgraph.graph.state import CompiledStateGraph

from agent.graph import get_agent
from agent.state import AgentState, create_initial_state
from browser.manager import BrowserManager
from config.settings import settings
from utils.logger import setup_logger, logger

console = Console()


def run_task(
    task: str, 
    browser_manager: BrowserManager, 
    debug: bool = False,
    agent: Optional[CompiledStateGraph] = None,
    initial_state: Optional[AgentState] = None,
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
        
        # TODO: Stream or invoke the graph with initial state
        # TODO: Handle intermediate outputs (show progress)
        # TODO: Get final state
        
        final_state = None  
        
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


def interactive_mode(browser_manager: BrowserManager, debug: bool = False) -> None:
    console.print(Panel(
        "[bold cyan]Browser AI Agent - Interactive Mode[/bold cyan]\n\n"
        "Enter tasks in natural language. Type 'exit' or 'quit' to stop.",
        border_style="cyan"
    ))
    
    agent = get_agent()
    initial_state = create_initial_state(task)
    try:
        while True:
            task = console.input("\n[bold cyan]Enter your task:[/bold cyan] ")
            
            if task.lower() in ("exit", "quit", "q"):
                break
            
            if not task.strip():
                continue
            
            run_task(
                task, 
                browser_manager, 
                debug,
                agent,
                initial_state
            )
    
    finally:
        browser_manager.stop()


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
    
    browser_manager = BrowserManager()
    browser_manager.start()

    if interactive:
        interactive_mode(browser_manager, debug)
    else:
        run_task(task, browser_manager, debug)


if __name__ == "__main__":
    main()
