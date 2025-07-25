"""
Simple CLI interface for the MeTTa knowledge graph.
"""

import os
import sys
import asyncio
from typing import Optional, Dict, Any
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Initialize rich console
console = Console()

class SimpleCLI:
    """
    Simple Command Line Interface for interacting with the MeTTa knowledge graph.
    """
    
    def __init__(self):
        """Initialize the CLI interface."""
        # Import MeTTa here to ensure it's only imported in Linux
        try:
            from hyperon import MeTTa
            self.metta = MeTTa()
            # Create a space and bind it
            self.metta.run('!(bind! &kb (new-space))')
            self.meetta_available = True
        except ImportError:
            console.print("[bold red]Error: MeTTa (hyperon) is not available. Please run this in WSL.[/bold red]")
            self.meetta_available = False
            return
            
        # Load knowledge base if available
        try:
            kb_path = os.path.join('src', 'knowledge', 'knowledge_base.metta')
            if os.path.exists(kb_path):
                with open(kb_path, 'r') as f:
                    kb_content = f.read()
                    # Add content to the knowledge base
                    self.metta.run(f'!(add-atom &kb {kb_content})')
                    console.print("[bold green]Knowledge base loaded successfully![/bold green]")
            else:
                console.print(f"[bold yellow]Warning: Knowledge base file not found at {kb_path}[/bold yellow]")
                console.print("[bold yellow]Creating a new knowledge base with some example facts.[/bold yellow]")
                self._add_example_facts()
        except Exception as e:
            console.print(f"[bold red]Error loading knowledge base: {str(e)}[/bold red]")
            self._add_example_facts()
    
    def _add_example_facts(self):
        """Add some example facts to the knowledge base."""
        facts = [
            '!(add-atom &kb (is_a diabetes medical_condition))',
            '!(add-atom &kb (treats insulin diabetes))',
            '!(add-atom &kb (symptom_of increased_thirst diabetes))',
            '!(add-atom &kb (is_a type_2_diabetes diabetes))',
            '!(add-atom &kb (treats metformin type_2_diabetes))',
            '!(add-atom &kb (symptom_of frequent_urination diabetes))',
            '!(add-atom &kb (risk_factor obesity type_2_diabetes))'
        ]
        
        for f in facts:
            self.metta.run(f)
        console.print("[bold green]Added example facts to the knowledge base.[/bold green]")
    
    def process_query(self, query: str) -> Optional[str]:
        """
        Process a user query and return the response.
        
        Args:
            query: The user's query string
            
        Returns:
            The system's response or None if there was an error
        """
        if not self.meetta_available:
            return "MeTTa is not available. Please run this in WSL."
            
        try:
            # Simple query processing
            if "what is" in query.lower():
                # Extract the concept
                concept = query.lower().split("what is")[1].strip().split()[0]
                result = self.metta.run(f'!(match &kb (is_a {concept} $X))')
                if result:
                    return f"{concept} is a {result}"
                return f"I don't know what {concept} is."
                
            elif "treat" in query.lower() or "treatment" in query.lower():
                # Extract the condition
                condition = query.lower().split("treat")[1].strip().split()[0]
                result = self.metta.run(f'!(match &kb (treats $X {condition}))')
                if result:
                    return f"Treatments for {condition} include: {result}"
                return f"I don't know the treatments for {condition}."
                
            elif "symptom" in query.lower():
                # Extract the condition
                condition = query.lower().split("symptom")[1].strip().split()[0]
                result = self.metta.run(f'!(match &kb (symptom_of $X {condition}))')
                if result:
                    return f"Symptoms of {condition} include: {result}"
                return f"I don't know the symptoms of {condition}."
                
            elif "risk" in query.lower() or "factor" in query.lower():
                # Extract the condition
                condition = query.lower().split("risk")[1].strip().split()[0]
                result = self.metta.run(f'!(match &kb (risk_factor $X {condition}))')
                if result:
                    return f"Risk factors for {condition} include: {result}"
                return f"I don't know the risk factors for {condition}."
                
            else:
                # Try a general query
                result = self.metta.run(f'!(match &kb ($P $S $O))')
                if result:
                    return f"Here's what I know: {result}"
                return "I don't understand your query. Try asking about what something is, treatments, symptoms, or risk factors."
                
        except Exception as e:
            console.print(f"[bold red]Error processing query: {str(e)}[/bold red]")
            return None
    
    def display_help(self):
        """Display help information."""
        help_text = """
        Simple MeTTa Knowledge Graph CLI
        
        Commands:
        /help     - Show this help message
        /exit     - Exit the program
        /clear    - Clear the screen
        /facts    - Show all facts in the knowledge base
        
        Example questions:
        - What is diabetes?
        - What treats diabetes?
        - What are the symptoms of diabetes?
        - What are the risk factors for type_2_diabetes?
        """
        console.print(Panel(help_text, title="Help", border_style="blue"))
    
    def display_welcome(self):
        """Display welcome message."""
        welcome_text = """
        Welcome to the Simple MeTTa Knowledge Graph CLI!
        
        This CLI allows you to query the knowledge graph about medical conditions.
        Type /help for available commands.
        """
        console.print(Panel(welcome_text, title="MeTTa Knowledge Graph", border_style="green"))
    
    def run(self):
        """Run the CLI interface."""
        self.display_welcome()
        
        while True:
            try:
                # Get user input
                query = Prompt.ask("\n[bold blue]You[/bold blue]")
                
                # Handle commands
                if query.lower() == "/exit":
                    console.print("[bold green]Goodbye![/bold green]")
                    break
                elif query.lower() == "/help":
                    self.display_help()
                    continue
                elif query.lower() == "/clear":
                    console.clear()
                    continue
                elif query.lower() == "/facts":
                    result = self.metta.run('!(match &kb ($P $S $O))')
                    console.print("\n[bold green]All facts:[/bold green]")
                    console.print(result)
                    continue
                
                # Process the query
                response = self.process_query(query)
                
                if response:
                    # Display the response
                    console.print("\n[bold green]Chatbot[/bold green]")
                    console.print(Markdown(response))
                else:
                    console.print("[bold red]Sorry, I couldn't process your query. Please try again.[/bold red]")
                    
            except KeyboardInterrupt:
                console.print("\n[bold yellow]Use /exit to quit the program[/bold yellow]")
            except Exception as e:
                console.print(f"[bold red]An error occurred: {str(e)}[/bold red]")

def main():
    """Main entry point for the CLI."""
    cli = SimpleCLI()
    cli.run()

if __name__ == "__main__":
    main() 