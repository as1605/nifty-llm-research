# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Removed
- Removed visualization and email functionality
  - Removed `src/visualization/plotter.py` module
  - Removed `src/utils/email.py` module
  - Removed email-related models and collections
  - Removed AWS SES integration
  - Removed plotting dependencies
  - Updated documentation and configuration

### Changed
- Migrated from Perplexity to Google Gemini API
  - Updated base agent to use Google's Gemini AI
  - Added Google Search integration for real-time market data
  - Updated prompt configurations for Gemini model
  - Enhanced metadata handling for search results
  - Major changes in:
    - `src/agents/base.py`
    - `scripts/seed_prompts.py`
    - `config/settings.py`
    - `requirements.txt`

### Added
- Improved prompt system using ChatGPT
  - Enhanced prompt templates in `prompts/6-chatgpt-prompt.md`
  - Updated seed prompts script with better prompt management
  - Minor optimizations in portfolio and stock research agents

### Changed
- Refactored and optimized Stock Research flow
  - Major improvements in `src/agents/stock_research.py` (188 changes)
  - Enhanced visualization system in `src/visualization/plotter.py`
  - Added new base agent functionality in `src/agents/base.py`
  - Improved stock analysis script with better error handling

### Added
- Enhanced PromptConfig system
  - New configuration in `prompts/4-cursor-promptconfig.md`
  - Improved prompt seeding system
  - Better parameter management in base agent
  - Streamlined agent configurations

### Fixed
- Various error fixes and improvements
  - Updated database models in `src/db/models.py`
  - Fixed configuration settings
  - Improved base agent stability

### Changed
- Migrated to Perplexity Deep Research
  - Major overhaul of stock research agent
  - Updated portfolio agent for better integration
  - Enhanced test coverage
  - Updated documentation and environment settings

### Changed
- Code quality improvements with Ruff
  - Applied Ruff formatting to all Python files
  - Improved code style and consistency
  - Enhanced type hints and documentation
  - Major files affected:
    - `src/agents/portfolio.py`
    - `src/agents/stock_research.py`
    - `src/db/database.py`
    - `src/utils/email.py`

### Changed
- Migrated from uv to venv
  - Updated package management system
  - Consolidated requirements files
  - Improved development setup
  - Updated Makefile for new environment

### Changed
- Migrated to MongoDB with detailed schema
  - New schema design in `prompts/2-cursor-schema.md`
  - Updated database models and operations
  - Enhanced portfolio and stock research agents
  - Improved data persistence layer
  - Major changes in:
    - `src/db/models.py`
    - `src/db/database.py`
    - `scripts/setup_db.py`

### Added
- Initial Cursor setup
  - Project structure and configuration
  - Base agent implementations
  - Database and visualization systems
  - Test framework
  - Documentation
  - Key files:
    - `src/agents/base.py`
    - `src/agents/portfolio.py`
    - `src/agents/stock_research.py`
    - `src/visualization/plotter.py`
    - `tests/test_stock_research.py`

### Added
- Initial ChatGPT README
  - Basic project documentation
  - Setup instructions
  - Project structure

### Added
- Initial project setup
  - Basic README
  - Git configuration
  - Project structure

## [0.1.0] - 2024-03-20
- Initial release 