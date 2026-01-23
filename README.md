# Browser AI Agent

An intelligent AI agent that automates complex browser-based tasks through natural language commands.

## Quick Start

### Prerequisites

- Python 3.10+
- OpenRouter API key

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
# Edit .env and add your OPENROUTER_API_KEY
```

### Usage

```bash
# Run chromium browser in debug modefor interactive agent mode
chromium --remote-debugging-port=9222
```

```bash
# Run the agent
python src/main.py "Check my calendar and schedule a meeting with Sara for next weekend"

# With debug mode
python src/main.py "Order pizza from my favorite place" --debug

# Interactive mode
python src/main.py --interactive
```

## Architecture

### Core Components

1. **Agent Layer** (LangGraph): Multi-node workflow for task planning and execution
2. **Browser Layer** (Playwright): Web automation and page interaction
3. **LLM Layer** (OpenRouter): Natural language understanding and decision-making
4. **Tools Layer**: LangChain tools bridging AI and browser

### Workflow

```
User Input → Planning Node → Execution Node → Verification Node → Output
                ↓               ↓                    ↓
           Task Plan    Browser Actions      Success Check
                                                     ↓
                                              [Retry/Error Handler]
```

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

### Running Tests

```bash
pytest tests/
```

### Adding New Tools

1. Define tool function in `src/tools/`
2. Add tool to registry in `src/tools/__init__.py`
3. Update agent graph to include tool

## Safety

- Sensitive actions (payments, deletions) require user confirmation
- Credentials are never logged
- User data stored locally with encryption

## Roadmap

- [ ] Multi-page workflows
- [ ] Browser session persistence
- [ ] Plugin system for domain-specific actions
- [ ] Web UI for monitoring
