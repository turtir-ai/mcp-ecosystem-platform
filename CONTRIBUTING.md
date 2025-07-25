# Contributing to MCP Ecosystem Platform

We love your input! We want to make contributing to MCP Ecosystem Platform as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### Pull Requests

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

### Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/mcp-ecosystem-platform.git
cd mcp-ecosystem-platform

# Install dependencies
cd backend && pip install -r requirements.txt
cd ../frontend && npm install

# Start development environment
docker-compose up -d
```

### Code Style

#### Python (Backend)
- Follow PEP 8
- Use Black for formatting: `black .`
- Use isort for imports: `isort .`
- Use mypy for type checking: `mypy .`

#### TypeScript (Frontend)
- Use ESLint configuration provided
- Use Prettier for formatting
- Follow React best practices

### Testing

#### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app
```

#### Frontend Tests
```bash
cd frontend
npm test
```

### Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation changes
- `style:` formatting changes
- `refactor:` code refactoring
- `test:` adding tests
- `chore:` maintenance tasks

Example: `feat: add real-time workflow monitoring`

## Any contributions you make will be under the MIT Software License

When you submit code changes, your submissions are understood to be under the same [MIT License](LICENSE) that covers the project.

## Report bugs using GitHub's [issue tracker](https://github.com/your-username/mcp-ecosystem-platform/issues)

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/your-username/mcp-ecosystem-platform/issues/new).

### Bug Report Template

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Feature Requests

We welcome feature requests! Please use the [feature request template](https://github.com/your-username/mcp-ecosystem-platform/issues/new?template=feature_request.md).

## License

By contributing, you agree that your contributions will be licensed under its MIT License.