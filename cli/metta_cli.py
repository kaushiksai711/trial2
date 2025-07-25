#!/usr/bin/env python3
"""
MeTTa Knowledge Graph CLI Interface
This module provides a command-line interface for interacting with the MeTTa knowledge graph.
"""

import os
import sys
import platform
import argparse
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

# Check if running in Linux (required for MeTTa)
if platform.system() != 'Linux':
    print("Warning: MeTTa (hyperon) only works in Linux subsystem. Please run this code in WSL.")
    sys.exit(1)

from hyperon import MeTTa
from src.knowledge.metta_kg import MeTTaKnowledgeGraph

# Initialize Rich console
console = Console()

class MeTTaCLI:
    """Command-line interface for MeTTa knowledge graph."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.kg = MeTTaKnowledgeGraph()
        self.console = Console()
        self.commands = {
            'help': self.show_help,
            'add': self.add_fact,
            'query': self.query_facts,
            'list': self.list_facts,
            'exit': self.exit_cli,
            'quit': self.exit_cli,
            'clear': self.clear_screen,
            'load': self.load_knowledge_base,
            'save': self.save_knowledge_base,
            'treatments': self.show_treatments,
            'symptoms': self.show_symptoms,
            'risk_factors': self.show_risk_factors
        }
        
    def run(self):
        """Run the CLI interface."""
        self.clear_screen()
        self.console.print("[bold green]MeTTa Knowledge Graph CLI[/bold green]")
        self.console.print("Type 'help' for available commands or 'exit' to quit.\n")
        
        # Add some sample data if the knowledge base is empty
        self._add_sample_data_if_empty()
        
        while True:
            try:
                command = Prompt.ask("metta>")
                if not command:
                    continue
                    
                parts = command.split()
                cmd = parts[0].lower()
                
                if cmd in self.commands:
                    self.commands[cmd](parts[1:])
                else:
                    self.console.print(f"[red]Unknown command: {cmd}[/red]")
                    self.console.print("Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'exit' to quit the application.[/yellow]")
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")
    
    def _add_sample_data_if_empty(self):
        """Add sample medical facts if the knowledge base is empty."""
        # Check if we have any facts
        results = self.kg.query()
        if not results:
            self.console.print("[yellow]Adding sample medical facts to the knowledge graph...[/yellow]")
            
            # Add medical conditions
            self.kg.add_fact("diabetes", "is_a", "medical_condition")
            self.kg.add_fact("type_1_diabetes", "is_a", "diabetes")
            self.kg.add_fact("type_2_diabetes", "is_a", "diabetes")
            self.kg.add_fact("hypertension", "is_a", "medical_condition")
            self.kg.add_fact("asthma", "is_a", "medical_condition")
            
            # Add treatments
            self.kg.add_fact("insulin", "treats", "type_1_diabetes")
            self.kg.add_fact("metformin", "treats", "type_2_diabetes")
            self.kg.add_fact("ace_inhibitors", "treats", "hypertension")
            self.kg.add_fact("beta_blockers", "treats", "hypertension")
            self.kg.add_fact("inhalers", "treats", "asthma")
            
            # Add symptoms
            self.kg.add_fact("increased_thirst", "symptom_of", "diabetes")
            self.kg.add_fact("frequent_urination", "symptom_of", "diabetes")
            self.kg.add_fact("fatigue", "symptom_of", "diabetes")
            self.kg.add_fact("headache", "symptom_of", "hypertension")
            self.kg.add_fact("dizziness", "symptom_of", "hypertension")
            self.kg.add_fact("wheezing", "symptom_of", "asthma")
            self.kg.add_fact("shortness_of_breath", "symptom_of", "asthma")
            
            # Add risk factors
            self.kg.add_fact("obesity", "risk_factor", "type_2_diabetes")
            self.kg.add_fact("family_history", "risk_factor", "type_2_diabetes")
            self.kg.add_fact("age", "risk_factor", "type_2_diabetes")
            self.kg.add_fact("high_sodium_diet", "risk_factor", "hypertension")
            self.kg.add_fact("stress", "risk_factor", "hypertension")
            self.kg.add_fact("smoking", "risk_factor", "asthma")
            self.kg.add_fact("allergies", "risk_factor", "asthma")
            
            self.console.print("[green]Sample data added successfully![/green]")
    
    def show_help(self, args=None):
        """Show help information."""
        help_table = Table(title="Available Commands")
        help_table.add_column("Command", style="cyan")
        help_table.add_column("Description", style="green")
        
        help_table.add_row("help", "Show this help message")
        help_table.add_row("add <subject> <predicate> <object>", "Add a fact to the knowledge graph")
        help_table.add_row("query <subject> <predicate> <object>", "Query facts (use * for wildcards)")
        help_table.add_row("list", "List all facts in the knowledge graph")
        help_table.add_row("treatments <condition>", "Show treatments for a medical condition")
        help_table.add_row("symptoms <condition>", "Show symptoms of a medical condition")
        help_table.add_row("risk_factors <condition>", "Show risk factors for a medical condition")
        help_table.add_row("load <filename>", "Load knowledge base from file")
        help_table.add_row("save <filename>", "Save knowledge base to file")
        help_table.add_row("clear", "Clear the screen")
        help_table.add_row("exit/quit", "Exit the application")
        
        self.console.print(help_table)
    
    def add_fact(self, args):
        """Add a fact to the knowledge graph."""
        if len(args) < 3:
            self.console.print("[red]Error: add command requires subject, predicate, and object[/red]")
            self.console.print("Usage: add <subject> <predicate> <object>")
            return
            
        subject = args[0]
        predicate = args[1]
        object_value = args[2]
        
        try:
            self.kg.add_fact(subject, predicate, object_value)
            self.console.print(f"[green]Added fact: {predicate}({subject}, {object_value})[/green]")
        except Exception as e:
            self.console.print(f"[red]Error adding fact: {str(e)}[/red]")
    
    def query_facts(self, args):
        """Query facts from the knowledge graph."""
        if len(args) < 3:
            self.console.print("[red]Error: query command requires subject, predicate, and object[/red]")
            self.console.print("Usage: query <subject> <predicate> <object>")
            self.console.print("Use * for wildcards, e.g., query * treats diabetes")
            return
            
        subject = args[0] if args[0] != '*' else None
        predicate = args[1] if args[1] != '*' else None
        object_value = args[2] if args[2] != '*' else None
        
        try:
            # Use the updated query method
            results = self.kg.query(subject, predicate, object_value)
            
            if not results:
                self.console.print("[yellow]No facts found matching the query.[/yellow]")
                return
                
            result_table = Table(title="Query Results")
            result_table.add_column("Subject", style="cyan")
            result_table.add_column("Predicate", style="magenta")
            result_table.add_column("Object", style="green")
            
            for result in results:
                result_table.add_row(
                    result['subject'],
                    result['predicate'],
                    result['object']
                )
                
            self.console.print(result_table)
            
        except Exception as e:
            self.console.print(f"[red]Error querying facts: {str(e)}[/red]")
    
    def list_facts(self, args=None):
        """List all facts in the knowledge graph."""
        try:
            results = self.kg.query()
            
            if not results:
                self.console.print("[yellow]No facts found in the knowledge graph.[/yellow]")
                return
                
            result_table = Table(title="All Facts")
            result_table.add_column("Subject", style="cyan")
            result_table.add_column("Predicate", style="magenta")
            result_table.add_column("Object", style="green")
            
            for result in results:
                result_table.add_row(
                    result['subject'],
                    result['predicate'],
                    result['object']
                )
                
            self.console.print(result_table)
            
        except Exception as e:
            self.console.print(f"[red]Error listing facts: {str(e)}[/red]")
    
    def show_treatments(self, args):
        """Show treatments for a medical condition."""
        if not args:
            self.console.print("[red]Error: treatments command requires a medical condition[/red]")
            self.console.print("Usage: treatments <condition>")
            return
            
        condition = args[0]
        
        try:
            # Use the updated query method
            results = self.kg.query(predicate="treats", object_value=condition)
            
            if not results:
                self.console.print(f"[yellow]No treatments found for {condition}.[/yellow]")
                return
                
            self.console.print(f"[bold]Treatments for {condition}:[/bold]")
            for result in results:
                self.console.print(f"  • {result['subject']}")
                
        except Exception as e:
            self.console.print(f"[red]Error retrieving treatments: {str(e)}[/red]")
    
    def show_symptoms(self, args):
        """Show symptoms of a medical condition."""
        if not args:
            self.console.print("[red]Error: symptoms command requires a medical condition[/red]")
            self.console.print("Usage: symptoms <condition>")
            return
            
        condition = args[0]
        
        try:
            # Use the updated query method
            results = self.kg.query(predicate="symptom_of", object_value=condition)
            
            if not results:
                self.console.print(f"[yellow]No symptoms found for {condition}.[/yellow]")
                return
                
            self.console.print(f"[bold]Symptoms of {condition}:[/bold]")
            for result in results:
                self.console.print(f"  • {result['subject']}")
                
        except Exception as e:
            self.console.print(f"[red]Error retrieving symptoms: {str(e)}[/red]")
    
    def show_risk_factors(self, args):
        """Show risk factors for a medical condition."""
        if not args:
            self.console.print("[red]Error: risk_factors command requires a medical condition[/red]")
            self.console.print("Usage: risk_factors <condition>")
            return
            
        condition = args[0]
        
        try:
            # Use the updated query method
            results = self.kg.query(predicate="risk_factor", object_value=condition)
            
            if not results:
                self.console.print(f"[yellow]No risk factors found for {condition}.[/yellow]")
                return
                
            self.console.print(f"[bold]Risk factors for {condition}:[/bold]")
            for result in results:
                self.console.print(f"  • {result['subject']}")
                
        except Exception as e:
            self.console.print(f"[red]Error retrieving risk factors: {str(e)}[/red]")
    
    def load_knowledge_base(self, args):
        """Load knowledge base from file."""
        if not args:
            self.console.print("[red]Error: load command requires a filename[/red]")
            self.console.print("Usage: load <filename>")
            return
            
        filename = args[0]
        
        try:
            self.kg.load_knowledge_base(filename)
            self.console.print(f"[green]Knowledge base loaded from {filename}[/green]")
        except Exception as e:
            self.console.print(f"[red]Error loading knowledge base: {str(e)}[/red]")
    
    def save_knowledge_base(self, args):
        """Save knowledge base to file."""
        if not args:
            self.console.print("[red]Error: save command requires a filename[/red]")
            self.console.print("Usage: save <filename>")
            return
            
        filename = args[0]
        
        try:
            self.kg.save_knowledge_base(filename)
            self.console.print(f"[green]Knowledge base saved to {filename}[/green]")
        except Exception as e:
            self.console.print(f"[red]Error saving knowledge base: {str(e)}[/red]")
    
    def clear_screen(self, args=None):
        """Clear the screen."""
        os.system('clear' if platform.system() != 'Windows' else 'cls')
        self.console.print("[bold green]MeTTa Knowledge Graph CLI[/bold green]")
        self.console.print("Type 'help' for available commands or 'exit' to quit.\n")
    
    def exit_cli(self, args=None):
        """Exit the CLI."""
        self.console.print("[yellow]Goodbye![/yellow]")
        sys.exit(0)

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="MeTTa Knowledge Graph CLI")
    parser.add_argument("--file", "-f", help="Load knowledge base from file")
    args = parser.parse_args()
    
    cli = MeTTaCLI()
    
    if args.file:
        try:
            cli.kg.load_knowledge_base(args.file)
            cli.console.print(f"[green]Knowledge base loaded from {args.file}[/green]")
        except Exception as e:
            cli.console.print(f"[red]Error loading knowledge base: {str(e)}[/red]")
            return
    
    cli.run()

if __name__ == "__main__":
    main() 