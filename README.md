# Codi - Your AI Senior Developer Assistant

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Codi is an AI-powered development assistant that acts as a senior software engineer, providing code analysis, generation, and review capabilities. It integrates with Slack and GitHub to seamlessly fit into your development workflow.

## 🚀 Features

- **Code Analysis**: Deep understanding of code structure, patterns, and potential improvements
- **Code Generation**: Creates production-ready code based on requirements
- **Code Review**: Thorough code reviews with actionable feedback
- **Slack Integration**: Real-time interaction through Slack
- **GitHub Integration**: PR creation and management
- **REST API**: FastAPI-based endpoints for service integration
- **CLI Interface**: Command-line tools for local development

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/codi.git
cd codi
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

## ⚙️ Configuration

Create a `.env` file in the project root with the following variables:

```env
OPENAI_API_KEY=your_openai_api_key
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_APP_TOKEN=your_slack_app_token
GITHUB_TOKEN=your_github_token
GITHUB_REPO=your_github_token
```

### Slack App Configuration

1. Create a new Slack App at https://api.slack.com/apps
2. Enable Socket Mode
3. Add the following Bot Token Scopes:
   - app_mentions:read
   - chat:write
   - channels:history
4. Install the app to your workspace
5. Copy the Bot User OAuth Token and App-Level Token to your `.env` file

## 🎯 Usage

### Interactive Chat

Start an interactive chat session with Codi:
```bash
# Start chat in current directory
codi chat

# Start chat with a specific workspace
codi chat -w /path/to/workspace
```

Special chat commands:
- `exit` or `quit`: End the chat session
- `clear`: Start a new conversation
- `context`: View current conversation context
- `save`: Save the current conversation

Chat features:
- Natural language interaction
- Conversation memory and context awareness
- Automatic task detection and handling
- Code analysis and generation
- Workspace awareness for better context

### Slack Commands

Mention @codi in your Slack channel with one of these commands:

```
@codi analyze this code
@codi generate in python a sorting algorithm
@codi review my pull request
```

### API Usage

Start the API server:
```bash
uvicorn api.main:app --reload
```

Example API request:
```python
import requests

task = {
    "task_type": "analyze",
    "description": "Check this code for improvements",
    "context": {
        "files": {"main.py": "your_code_here"},
        "language": "python"
    }
}

response = requests.post("http://localhost:8000/task", json=task)
print(response.json())
```

### CLI Usage

```bash
# Get help
codi --help

# Analyze a repository
codi analyze /path/to/repo

# Generate code
codi generate "Create a FastAPI endpoint"

# Review code
codi review /path/to/file
```

## 🧪 Testing

Run the test suite:
```bash
pytest
```

## 📦 Project Structure

```
codi/
├── api/                # FastAPI endpoints
├── src/
│   ├── core/          # Core AI agent functionality
│   ├── integrations/  # Slack and GitHub integrations
│   ├── cli.py         # Command-line interface
│   └── main.py        # Main application entry point
├── tests/             # Test suite
├── requirements.txt   # Project dependencies
└── setup.py          # Package configuration
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for providing the GPT-4 model
- Slack for their excellent bot integration capabilities
- The FastAPI team for the amazing web framework

## 📫 Support

For support, please open an issue in the GitHub repository or contact the maintainers.