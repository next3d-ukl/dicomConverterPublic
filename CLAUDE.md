# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Run the application: `python src/main.py`
- Install dependencies: `pip install -r requirements.txt`

## Code Style Guidelines

- **Architecture**: Follow MVVM pattern with clear separation between models, views, viewmodels, and services
- **Imports**: Group standard library imports first, then third-party packages, then local modules
- **Formatting**: Use 4 spaces for indentation
- **Function Naming**: Use snake_case for functions and methods
- **Class Naming**: Use PascalCase for class names
- **Error Handling**: Use try/except blocks with specific exception types
- **Docstrings**: Add docstrings to public functions and classes
- **Type Hints**: Add type hints for all function parameters and return values
- **Threading**: Use Python's threading module for background operations
- **PyQt Conventions**: Follow Qt naming conventions for Qt-specific code (e.g., camelCase for slots)
- **File Structure**: Keep models in models/, views in views/, viewmodels in viewmodels/, and business logic in services/