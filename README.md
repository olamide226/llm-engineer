# CodeMason AI

CodeMason AI is an AI Engineer Co-Pilot powered by LLM models, specialized in full cycle software development. This project is built using Python and Poetry for dependency management.

## Requirements

- Python 3.10 or higher
- Poetry (Python package manager)

## Setup

Follow these steps to set up the CodeMason AI project:

1. Clone the repository:
   ```
   git clone https://gitlab.com/llm-engineer
   cd llm-engineer
   ```

2. Install Poetry (if not already installed):
   ```
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Install project dependencies:
   ```
   poetry install
   ```

4. Activate the virtual environment:
   ```
   poetry shell
   ```

## Configuration

1. Copy the example environment file:
   ```
   cp .env.example .env
   ```

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

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any problems or have any questions, please open an issue in the GitHub repository.
