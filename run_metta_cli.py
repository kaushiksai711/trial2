#!/usr/bin/env python3
"""
Run MeTTa CLI Interface
This script provides a simple way to run the MeTTa knowledge graph CLI interface.
"""

import os
import sys
import platform
import subprocess

def main():
    """Main entry point for running the MeTTa CLI."""
    # Check if running in Linux (required for MeTTa)
    if platform.system() != 'Linux':
        print("Warning: MeTTa (hyperon) only works in Linux subsystem.")
        print("Please run this script in WSL (Windows Subsystem for Linux).")
        
        # Try to open WSL if on Windows
        if platform.system() == 'Windows':
            try:
                print("Attempting to open WSL...")
                subprocess.run(['wsl'], check=True)
            except subprocess.CalledProcessError:
                print("Failed to open WSL. Please install WSL and try again.")
            except FileNotFoundError:
                print("WSL not found. Please install WSL and try again.")
        sys.exit(1)
    
    # Set up the Python path to include the project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.environ['PYTHONPATH'] = project_root
    
    # Run the CLI
    try:
        from cli.metta_cli import main as cli_main
        cli_main()
    except ImportError as e:
        print(f"Error importing MeTTa CLI: {e}")
        print("Make sure you have installed all required dependencies:")
        print("  pip install rich hyperon")
        sys.exit(1)
    except Exception as e:
        print(f"Error running MeTTa CLI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 