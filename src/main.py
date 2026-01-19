"""
Main entry point for the Browser AI Agent CLI.
"""

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from agent.graph import get_agent_graph
from agent.state import create_initial_state
from browser.manager import BrowserManager
from config.settings import settings
from utils.logger import setup_logger, logger

console = Console()


async def run_task(task: str, debug: bool = False) -> None:
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
    
    browser_manager = BrowserManager()
    
    try:
        await browser_manager.start()
        console.print("[green]✓[/green] Browser started")
        
        graph = get_agent_graph()
        
        initial_state = create_initial_state(task)
        
        # Run the agent
        console.print("[yellow]→[/yellow] Planning and executing task...")
        
        # TODO: Stream or invoke the graph with initial state
        # TODO: Handle intermediate outputs (show progress)
        # TODO: Get final state
        
        final_state = None  # TODO: Replace with actual final state
        
        # Display results
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
    
    finally:
        # Clean up
        await browser_manager.stop()
        console.print("[green]✓[/green] Browser closed")


async def interactive_mode() -> None:
    """
    Run the agent in interactive mode.
    """
    console.print(Panel(
        "[bold cyan]Browser AI Agent - Interactive Mode[/bold cyan]\n\n"
        "Enter tasks in natural language. Type 'exit' or 'quit' to stop.",
        border_style="cyan"
    ))
    
    browser_manager = BrowserManager()
    await browser_manager.start()
    
    try:
        while True:
            # Get user input
            task = console.input("\n[bold cyan]Task:[/bold cyan] ")
            
            if task.lower() in ("exit", "quit", "q"):
                break
            
            if not task.strip():
                continue
            
            # TODO: Run task with the agent
            # TODO: Display results
            
            console.print("[yellow]Interactive mode not fully implemented yet[/yellow]")
    
    finally:
        await browser_manager.stop()


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
        asyncio.run(interactive_mode())
    else:
        asyncio.run(run_task(task, debug))


if __name__ == "__main__":
    main()
