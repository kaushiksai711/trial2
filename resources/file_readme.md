# Project File Documentation

## Core Application Files

### `run_metta_cli.py`
- **Purpose**: Main entry point for the MeTTa Knowledge Graph CLI
- **Dependencies**: `cli.metta_cli`, `os`, `sys`, `platform`, `subprocess`
- **Description**: 
  - Validates the operating system (requires Linux/WSL)
  - Sets up Python path and environment variables
  - Initializes and runs the MeTTa CLI interface
  - Handles errors and provides user-friendly messages

### `cli/metta_cli.py`
- **Purpose**: Implements the command-line interface for MeTTa knowledge graph
- **Key Features**:
  - Interactive command prompt with syntax highlighting
  - Commands for knowledge base management (add, query, list, save, load)
  - Medical-specific commands (treatments, symptoms, risk_factors)
  - Rich text formatting and tables for better readability
- **Dependencies**: `src.knowledge.metta_kg`, `rich`, `hyperon`

### `src/knowledge/metta_kg.py`
- **Purpose**: Implements the MeTTa knowledge graph backend
- **Features**:
  - Knowledge graph construction and querying
  - Fact storage and retrieval
  - Relationship management between medical concepts
  - Integration with MeTTa reasoning engine

## Configuration Files

### `.env`
- **Purpose**: Environment configuration
- **Typical Contents**:
  - Database connection strings
  - API keys
  - Environment-specific settings
  - Path configurations

### `requirements.txt`
- **Purpose**: Lists all Python package dependencies
- **Key Dependencies**:
  - `hyperon`: MeTTa knowledge representation and reasoning
  - `fastapi`: Web framework for API endpoints
  - `uvicorn`: ASGI server
  - `rich`: Terminal formatting
  - `pydantic`: Data validation

## Documentation

### `README.md`
- **Purpose**: Main project documentation
- **Sections**:
  - Project overview and features
  - Installation instructions
  - Usage examples
  - Architecture details
  - Configuration guide

### `README_BACKEND.md`
- **Purpose**: Technical documentation for backend components
- **Contents**:
  - API specifications
  - Database schema
  - Service architecture
  - Development setup instructions

## Development & Testing

### `run_tests.py`
- **Purpose**: Test runner for the project
- **Features**:
  - Discovers and runs all test cases
  - Generates coverage reports
  - Supports different test configurations

### `tests/`
- **Purpose**: Contains all test files
- **Key Test Files**:
  - `test_system.py`: Integration tests
  - `test_metta.py`: MeTTa-specific tests
  - `test_connections.py`: Database connection tests
  - `test_load_save.py`: Data persistence tests

## Utility Scripts

### `download_nltk_data.py`
- **Purpose**: Downloads required NLTK data
- **Usage**: Run once during setup
- **Dependencies**: `nltk`

### `simple_cli.py`
- **Purpose**: Alternative, simpler CLI implementation
- **Status**: Deprecated in favor of `metta_cli.py`
- **Features**:
  - Basic MeTTa interaction
  - File-based knowledge base loading

## Project Structure
```
.
├── cli/                    # Command-line interface components
│   ├── metta_cli.py       # Main CLI implementation
│   └── cli_interface.py   # Alternative CLI (deprecated)
├── src/                   # Source code
│   └── knowledge/        # Knowledge graph implementation
│       └── metta_kg.py   # MeTTa knowledge graph
├── tests/                 # Test files
├── .env                  # Environment configuration
├── requirements.txt      # Dependencies
└── README.md            # Project documentation
```

## Important Notes

1. **Platform Requirements**:
   - Requires Linux or WSL (Windows Subsystem for Linux)
   - Python 3.8+ recommended

2. **Setup**:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Download NLTK data
   python download_nltk_data.py
   
   # Run the CLI
   python run_metta_cli.py
   ```

3. **Troubleshooting**:
   - Ensure WSL is properly configured if on Windows
   - Verify all dependencies are installed
   - Check `.env` for correct configuration