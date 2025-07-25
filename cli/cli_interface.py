"""
Command Line Interface for the Medical FAQ Chatbot.

This module provides an interactive CLI for users to interact with the chatbot system.
"""

import os
import sys
import asyncio
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn
from dotenv import load_dotenv

# Add parent directory to path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.orchestrator import Orchestrator
from src.agents.query_interpreter import QueryInterpreter
from src.agents.query_decomposer import QueryDecomposer
from src.agents.retrieval_agent import RetrievalAgent
from src.db.neo4j_connector import Neo4jConnector
from src.db.qdrant_connector import QdrantConnector
from src.db.mongodb_connector import MongoDBConnector
from src.utils.logger import setup_logger

# Initialize rich console
console = Console()

class CLIInterface:
    """
    Command Line Interface for interacting with the chatbot system.
    """
    
    def __init__(self):
        """Initialize the CLI interface."""
        load_dotenv()
        self.logger = setup_logger("cli_interface")
        self.initialize_components()
        
    def initialize_components(self):
        """Initialize all required components."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Initializing components...", total=None)
            
            # Initialize database connectors
            self.neo4j = Neo4jConnector()
            
            self.qdrant = QdrantConnector()
            
            self.mongodb = MongoDBConnector(
                uri=os.getenv("MONGODB_URI"),
                db_name=os.getenv("MONGODB_DB")
            )
            
            # Connect to databases
            self.neo4j.connect()
            self.qdrant.connect()
            self.mongodb.connect()
            
            # Initialize agents
            self.query_interpreter = QueryInterpreter()
            self.query_decomposer = QueryDecomposer(self.query_interpreter)
            self.retrieval_agent = RetrievalAgent(self.neo4j, self.qdrant, self.mongodb)
            self.orchestrator = Orchestrator(
                self.query_interpreter,
                self.query_decomposer,
                self.retrieval_agent
            )
    
    async def process_query(self, query: str) -> Optional[str]:
        """
        Process a user query and return the response.
        
        Args:
            query: The user's query string
            
        Returns:
            The system's response or None if there was an error
        """
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description="Processing your query...", total=None)
                
                # Process the query through the orchestrator
                result = await self.orchestrator.process_query(query)
                print(result, "resultawdasdsad")
                # Format the response
                if result and "response" in result:
                    response = result["response"]
                    if "sources" in result and result["sources"]:
                        response += "\n\nSources:\n"
                        for source in result["sources"]:
                            response += f"- {source}\n"
                    return response
                return None
                
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return None
    
    def display_help(self):
        """Display help information."""
        help_text = """
        Medical FAQ Chatbot CLI
        
        Commands:
        /help     - Show this help message
        /exit     - Exit the program
        /clear    - Clear the screen
        /sources  - Show sources for the last response
        
        Type your medical questions directly to get answers.
        Example questions:
        - What are the symptoms of diabetes?
        - How is asthma treated?
        - What causes high blood pressure?
        """
        console.print(Panel(help_text, title="Help", border_style="blue"))
    
    def display_welcome(self):
        """Display welcome message."""
        welcome_text = """
        Welcome to the Medical FAQ Chatbot!
        
        This CLI allows you to ask medical questions and get accurate,
        well-sourced answers. Type /help for available commands.
        """
        console.print(Panel(welcome_text, title="Medical FAQ Chatbot", border_style="green"))
    
    async def run(self):
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
                
                # Process the query
                response = await self.process_query(query)
                
                if response:
                    # Display the response
                    console.print("\n[bold green]Chatbot[/bold green]")
                    console.print(Markdown(response))
                else:
                    console.print("[bold red]Sorry, I couldn't process your query. Please try again.[/bold red]")
                    
            except KeyboardInterrupt:
                console.print("\n[bold yellow]Use /exit to quit the program[/bold yellow]")
            except Exception as e:
                self.logger.error(f"Error in CLI: {str(e)}")
                console.print(f"[bold red]An error occurred: {str(e)}[/bold red]")

def main():
    """Main entry point for the CLI."""
    cli = CLIInterface()
    asyncio.run(cli.run())

if __name__ == "__main__":
    main() 

# """
# Command Line Interface for the Medical FAQ Chatbot.

# This module provides an interactive CLI for users to interact with the chatbot system.
# """

# import os
# import sys
# import asyncio
# import json
# import aiohttp
# from typing import Optional, Dict, Any
# from rich.console import Console
# from rich.prompt import Prompt
# from rich.panel import Panel
# from rich.markdown import Markdown
# from rich.progress import Progress, SpinnerColumn, TextColumn
# from dotenv import load_dotenv

# # Add parent directory to path to import from src
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# from src.agents.orchestrator import Orchestrator
# from src.agents.query_interpreter import QueryInterpreter
# from src.agents.query_decomposer import QueryDecomposer
# from src.agents.retrieval_agent import RetrievalAgent
# from src.db.neo4j_connector import Neo4jConnector
# from src.db.qdrant_connector import QdrantConnector
# from src.db.mongodb_connector import MongoDBConnector
# #from src.utils.logger import setup_logger

# # Initialize rich console
# console = Console()

# class OpenRouterClient:
#     """Client for interacting with the OpenRouter API."""
    
#     def __init__(self):
#         load_dotenv()
#         #self.logger = setup_logger("cli_interface")
#         self.initialize_components()
#         """Initialize the OpenRouter client."""
#         self.api_key = os.getenv("OPENROUTER_API_KEY") or "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"
#         self.base_url = "https://openrouter.ai/api/v1/chat/completions"
#         if not self.api_key:
#             raise ValueError("OPENROUTER_API_KEY environment variable not set")
            
#     async def generate_response(self, message: str, context: Optional[str] = None) -> Dict[str, Any]:
#         """
#         Generate a response using the OpenRouter API.
        
#         Args:
#             message: The user's message
#             context: Optional context to provide to the model
            
#         Returns:
#             The response from OpenRouter
#         """
#         headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type": "application/json"
#         }
        
#         # Build the messages with context if provided
#         messages = []
#         if context:
#             messages.append({"role": "system", "content": f"You are a medical assistant. Here's some relevant context: {context}"})
#         else:
#             messages.append({"role": "system", "content": "You are a medical assistant that provides helpful, accurate information."})
            
#         messages.append({"role": "user", "content": message})
        
#         data = {
#             "model": "nvidia/llama-3.1-nemotron-nano-8b-v1:free",  # You can change the model as needed
#             "messages": messages,
#             "max_tokens": 1024
#         }
        
#         async with aiohttp.ClientSession() as session:
#             async with session.post(self.base_url, headers=headers, json=data) as response:
#                 if response.status == 200:
#                     return await response.json()
#                 else:
#                     error_text = await response.text()
#                     raise Exception(f"OpenRouter API error: {response.status} - {error_text}")

# class CLIInterface:
#     """
#     Command Line Interface for interacting with the chatbot system.
#     """
    
#     def __init__(self):
#         """Initialize the CLI interface."""
#         load_dotenv()
#         self.logger = setup_logger("cli_interface")
#         self.initialize_components()
        
#     def initialize_components(self):
#         """Initialize all required components."""
#         with Progress(
#             SpinnerColumn(),
#             TextColumn("[progress.description]{task.description}"),
#             transient=True,
#         ) as progress:
#             progress.add_task(description="Initializing components...", total=None)
            
#             # Initialize database connectors
#             self.neo4j = Neo4jConnector()
            
#             self.qdrant = QdrantConnector()
            
#             self.mongodb = MongoDBConnector(
#                 uri=os.getenv("MONGODB_URI"),
#                 db_name=os.getenv("MONGODB_DB")
#             )
            
#             # Connect to databases
#             self.neo4j.connect()
#             self.qdrant.connect()
#             self.mongodb.connect()
            
#             # Initialize agents
#             self.query_interpreter = QueryInterpreter()
#             self.query_decomposer = QueryDecomposer(self.query_interpreter)
#             self.retrieval_agent = RetrievalAgent(self.neo4j, self.qdrant, self.mongodb)
#             self.orchestrator = Orchestrator(
#                 self.query_interpreter,
#                 self.query_decomposer,
#                 self.retrieval_agent
#             )
            
#             # Initialize OpenRouter client
#             self.openrouter = OpenRouterClient()
    
#     async def process_query(self, query: str) -> Optional[str]:
#         """
#         Process a user query and return the response.
        
#         Args:
#             query: The user's query string
            
#         Returns:
#             The system's response or None if there was an error
#         """
#         try:
#             with Progress(
#                 SpinnerColumn(),
#                 TextColumn("[progress.description]{task.description}"),
#                 transient=True,
#             ) as progress:
#                 progress.add_task(description="Processing your query...", total=None)
                
#                 # Process the query through the orchestrator
#                 result = await self.orchestrator.process_query(query)
                
#                 # Format the response
#                 if result and "response" in result:
#                     response = result["response"]
#                     sources = []
#                     if "sources" in result and result["sources"]:
#                         sources = result["sources"]
#                     return {"response": response, "sources": sources}
#                 return None
                
#         except Exception as e:
#             self.logger.error(f"Error processing query: {str(e)}")
#             return None
    
#     async def enhance_with_openrouter(self, query: str, initial_response: Dict[str, Any]) -> str:
#         """
#         Enhance the initial response with OpenRouter.
        
#         Args:
#             query: The original user query
#             initial_response: The response from the internal system
            
#         Returns:
#             Enhanced response
#         """
#         try:
#             with Progress(
#                 SpinnerColumn(),
#                 TextColumn("[progress.description]{task.description}"),
#                 transient=True,
#             ) as progress:
#                 progress.add_task(description="Enhancing response with OpenRouter...", total=None)
                
#                 # Create prompt with initial response as context
#                 context = f"Initial response: {initial_response['response']}"
#                 if initial_response.get('sources'):
#                     context += "\nSources:\n" + "\n".join([f"- {source}" for source in initial_response['sources']])
                
#                 prompt = (
#                     f"Please review and enhance this medical information response if needed. "
#                     f"The user asked: '{query}'. Provide a comprehensive, accurate response "
#                     f"that builds on the initial information provided, adding any missing details "
#                     f"or clarifications. Format your response in markdown."
#                 )
                
#                 # Get response from OpenRouter
#                 openrouter_response = await self.openrouter.generate_response(prompt, context)
                
#                 if openrouter_response and 'choices' in openrouter_response and openrouter_response['choices']:
#                     enhanced_response = openrouter_response['choices'][0]['message']['content']
                    
#                     # Add sources from the initial response
#                     if initial_response.get('sources'):
#                         enhanced_response += "\n\nSources:\n"
#                         for source in initial_response['sources']:
#                             enhanced_response += f"- {source}\n"
                            
#                     return enhanced_response
#                 else:
#                     # Fallback to original response if OpenRouter fails
#                     response = initial_response['response']
#                     if initial_response.get('sources'):
#                         response += "\n\nSources:\n"
#                         for source in initial_response['sources']:
#                             response += f"- {source}\n"
#                     return response
                
#         except Exception as e:
#             self.logger.error(f"Error enhancing with OpenRouter: {str(e)}")
#             # Return the original response if enhancement fails
#             response = initial_response['response']
#             if initial_response.get('sources'):
#                 response += "\n\nSources:\n"
#                 for source in initial_response['sources']:
#                     response += f"- {source}\n"
#             return response
    
#     def display_help(self):
#         """Display help information."""
#         help_text = """
#         Medical FAQ Chatbot CLI
        
#         Commands:
#         /help     - Show this help message
#         /exit     - Exit the program
#         /clear    - Clear the screen
#         /sources  - Show sources for the last response
#         /noai     - Process query without OpenRouter enhancement
        
#         Type your medical questions directly to get answers.
#         Example questions:
#         - What are the symptoms of diabetes?
#         - How is asthma treated?
#         - What causes high blood pressure?
#         """
#         console.print(Panel(help_text, title="Help", border_style="blue"))
    
#     def display_welcome(self):
#         """Display welcome message."""
#         welcome_text = """
#         Welcome to the Medical FAQ Chatbot!
        
#         This CLI allows you to ask medical questions and get accurate,
#         well-sourced answers. Responses are enhanced with advanced AI.
#         Type /help for available commands.
#         """
#         console.print(Panel(welcome_text, title="Medical FAQ Chatbot", border_style="green"))
    
#     async def run(self):
#         """Run the CLI interface."""
#         self.display_welcome()
#         self.use_openrouter = True
#         self.last_sources = []
        
#         while True:
#             try:
#                 # Get user input
#                 query = Prompt.ask("\n[bold blue]You[/bold blue]")
                
#                 # Handle commands
#                 if query.lower() == "/exit":
#                     console.print("[bold green]Goodbye![/bold green]")
#                     break
#                 elif query.lower() == "/help":
#                     self.display_help()
#                     continue
#                 elif query.lower() == "/clear":
#                     console.clear()
#                     continue
#                 elif query.lower() == "/sources":
#                     if self.last_sources:
#                         console.print("\n[bold green]Sources[/bold green]")
#                         for source in self.last_sources:
#                             console.print(f"- {source}")
#                     else:
#                         console.print("[italic yellow]No sources available for the last response.[/italic yellow]")
#                     continue
#                 elif query.lower() == "/noai":
#                     self.use_openrouter = not self.use_openrouter
#                     status = "enabled" if self.use_openrouter else "disabled"
#                     console.print(f"[italic yellow]OpenRouter enhancement {status}.[/italic yellow]")
#                     continue
                
#                 # Process the query
#                 initial_response = await self.process_query(query)
                
#                 if initial_response:
#                     # Save sources for later reference
#                     self.last_sources = initial_response.get('sources', [])
                    
#                     # Enhance with OpenRouter if enabled
#                     if self.use_openrouter:
#                         console.print("\n[bold green]Processing...[/bold green]")
#                         final_response = await self.enhance_with_openrouter(query, initial_response)
#                     else:
#                         # Use original response
#                         final_response = initial_response['response']
#                         if initial_response.get('sources'):
#                             final_response += "\n\nSources:\n"
#                             for source in initial_response['sources']:
#                                 final_response += f"- {source}\n"
                    
#                     # Display the response
#                     console.print("\n[bold green]Chatbot[/bold green]")
#                     console.print(Markdown(final_response))
#                 else:
#                     console.print("[bold red]Sorry, I couldn't process your query. Please try again.[/bold red]")
                    
#             except KeyboardInterrupt:
#                 console.print("\n[bold yellow]Use /exit to quit the program[/bold yellow]")
#             except Exception as e:
#                 self.logger.error(f"Error in CLI: {str(e)}")
#                 console.print(f"[bold red]An error occurred: {str(e)}[/bold red]")

# def main():
#     """Main entry point for the CLI."""
#     cli = CLIInterface()
#     asyncio.run(cli.run())

# if __name__ == "__main__":
#     main()