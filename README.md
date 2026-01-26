# Browser AI Agent

An intelligent AI agent that automates complex browser-based tasks through natural language commands.

## Quick Start

### Prerequisites

- Python 3.10+
- DeepSeek API key

Commentary - Deepseek was chosen as main LLM due to its incredible price/quality ratio


### Installation

```bash
# Clone the repository
git clone git@github.com:recourcefulcoder/ai-agent.git
cd ai-agent

# Create virtual environment and switch to it
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env and add your DEEPSEEK_API_KEY
```

### Usage

```bash
# Run chromium browser in debug modefor interactive agent mode
chromium --remote-debugging-port=9222
```

```bash
# Run the agent
python src/main.py "Check my calendar and schedule a meeting with Sara for next weekend"

# Interactive mode
python src/main.py --interactive
```

## Architecture

### Core Components

1. **Agent Layer** (LangGraph): Multi-node workflow for task planning and execution
2. **Browser Layer** (Playwright): Web automation and page interaction
3. **LLM Layer** (OpenRouter): Natural language understanding and decision-making
4. **Tools Layer**: LangChain tools bridging AI and browser

### Architecture/workflow

Generally provided agent is a ReAct agent, following given workflow:

- `Planning node` - plans out task in general
- `Choosing action node` - decides what should it do next, without calling tools yet
- `Confirmation node` - decides whether action agent is about to do dangerous and requires user confirmation; if it does, requests one
- `Execution node` - decides what tools to call and performs that tool calls
- `Reflection node` - keeps track of plan achievement, if achieved prompts agent to proceed with next plan step (returns to `Choosing action node`)
- `Finalizing node` - returns generalization on work done

## Configuration

See `.env.example` for all configuration options.

Key settings:
- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `DEFAULT_LLM_MODEL`: Model to use (default: anthropic/claude-sonnet-4)
- `BROWSER_HEADLESS`: Run browser in headless mode (true/false)

## Project Structure

```
src/
├── agent/          # LangGraph agent implementation
├── browser/        # Playwright browser management
├── tools/          # LangChain tools
├── models/         # Pydantic models
└── services/       # External service integrations
```

## Development

### Adding New Tools

1. Define tool function in `src/tools/`
2. Add tool to registry in `src/tools/__init__.py`
3. Update agent graph to include tool

## Safety

- Sensitive actions (payments, deletions) require user confirmation
- Credentials are never logged
