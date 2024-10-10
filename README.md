# CodeMason AI

CodeMason AI is an AI Engineer Co-Pilot powered by LLM models, specialized in full cycle software development. This project is built using Python and Poetry for dependency management.

## Requirements

- Python 3.10 or higher

## Setup

Follow these steps to set up the CodeMason AI project:

1. Clone the repository:
   ```
   git clone https://gitlab.com/llm-engineer
   cd llm-engineer
   ```

3. Install project dependencies:
   ```
   python -m venv .venv
   source .venv/bin/activate
   pip install poetry
   poetry install
   ```

## Configuration

1. Copy the example environment file:
   ```
   cp .env.example .env
   ```
   note: you need to get an anthropic API key [here](https://console.anthropic.com/settings/keys) and get a tavily KEY [here](https://app.tavily.com/home)
   (I'm thinking of switching to the PS LLM APIs now that it supports function calling)

2. Edit the `.env` file and set your configuration variables, including any necessary API keys.

## Usage

To start using CodeMason AI, run the following command:

```
poetry run start
```

For more detailed usage instructions, please refer to the documentation in the `docs/` directory.

## Development

To add new dependencies to the project:

```
poetry add package_name
```

To update dependencies:

```
poetry update
```

To run tests:

```
poetry run pytest
```

## Support

If you encounter any problems or have any questions, please open an issue in the repository.
