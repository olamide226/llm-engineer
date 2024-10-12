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

2. Edit the `.env` file and set your configuration variables, including any necessary API keys.

3. In the `src/global_state.py` file, you can configure the LLM provider by setting the `LLM_PROVIDER` variable. The supported options are:
   - "anthropic" (default)
   - "litellm"
   - "custom"

   For example, to use LiteLLM, set:
   ```python
   LLM_PROVIDER = "litellm"
   ```

   note: You need to obtain the appropriate API key for your chosen LLM provider:
   - For Anthropic, get an API key [here](https://console.anthropic.com/settings/keys)
   - For custom providers, ensure you have the required authentication credentials
   You'll also need to get a Tavily API key [here](https://app.tavily.com/home)

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

## Testing

This project uses pytest for unit and integration testing. To run the tests, follow these steps:

1. Ensure you have installed the project dependencies, including dev dependencies:
   ```
   poetry install --with dev
   ```

2. Run the tests using pytest:
   ```
   poetry run pytest
   ```

This will run all the tests in the `tests/` directory, including both unit and integration tests.

To run only unit tests:
```
poetry run pytest tests/unit
```

To run only integration tests:
```
poetry run pytest tests/integration
```

If you add new functionality to the project, make sure to write corresponding tests in the appropriate test files.

## Extending LLM Provider Support

To add support for a new LLM provider:

1. In `src/models/llm_providers.py`, create a new class that inherits from `LLMProvider`.
2. Implement the `create_message` method for the new provider.
3. Update the `get_llm_provider` function to include the new provider.
4. Add any necessary configuration options to `src/global_state.py`.

For example, to add support for a new provider called "NewLLM":

```python
class NewLLMProvider(LLMProvider):
    def create_message(self, model: str, max_tokens: int, system: str, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None, tool_choice: Optional[Dict[str, str]] = None) -> Any:
        # Implement the method according to NewLLM's API
        pass

# In the get_llm_provider function
elif provider_name == "newllm":
    return NewLLMProvider()
```

## Support

If you encounter any problems or have any questions, please open an issue in the repository.