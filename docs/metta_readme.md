# MeTTa Programming Language: The Language of Thought for AGI

## Table of Contents
- [Introduction](#introduction)
- [Core Concepts](#core-concepts)
- [Installation](#installation)
- [Basic Syntax](#basic-syntax)
- [Advanced Features](#advanced-features)
- [Integration with Python](#integration-with-python)
- [Use Cases](#use-cases)
- [Contributing](#contributing)
- [License](#license)
- [References](#references)

## Introduction

MeTTa (Meta Type Talk) is a novel, multi-paradigm programming language designed specifically for Artificial General Intelligence (AGI) development. It serves as the foundational language for the OpenCog Hyperon AGI framework and is developed as part of the Artificial Superintelligence Alliance.

### Key Features
- **Self-modifying Code**: Native support for reflection and metaprogramming
- **Neural-Symbolic Integration**: Seamlessly combines symbolic AI with neural networks
- **Knowledge Representation**: Built on the Atomspace knowledge metagraph
- **Multi-paradigm**: Supports functional, logical, and probabilistic programming
- **AGI-focused**: Designed specifically for artificial general intelligence applications

## Core Concepts

### 1. Atomspace
MeTTa programs operate within an Atomspace - a weighted, labeled metagraph that serves as a knowledge database. Unlike traditional graphs, Atomspace allows links to connect to other links, enabling higher-order relationships.

### 2. Atoms
Atoms are the fundamental building blocks in MeTTa, with four primary types:
- **Symbols**: Named constants (e.g., `Socrates`)
- **Variables**: Placeholders that can be bound to values (e.g., `$x`)
- **Expressions**: Parenthesized lists of other atoms (e.g., `(human Socrates)`)
- **Grounded Atoms**: References to external data or functions

### 3. S-Expressions
MeTTa uses Lisp-like S-expressions for its syntax:
```lisp
; Facts
(human Socrates)
(mortal Socrates)

; Rules
(implies (human $x) (mortal $x))
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation Steps
```bash
# Install the Hyperon MeTTa implementation
pip install hyperon-experimental

# Verify installation
python -c "from hyperon import MeTTa; print('MeTTa installed successfully!')"
```

## Basic Syntax

### Defining Facts
```lisp
; Define facts about Socrates
(human Socrates)
(philosopher Socrates)

; Define relationships
(teacher-of Plato Socrates)
(student-of Aristotle Plato)
```

### Writing Rules
```lisp
; If X is human, then X is mortal
(implies (human $x) (mortal $x))

; Transitive relationship
(implies (teacher-of $x $y) (student-of $y $x))
```

### Querying the Knowledge Base
```lisp
; Find all humans
!(match &self (human $x) $x)

; Check if Socrates is mortal
!(match &self (mortal Socrates) true)
```

## Advanced Features

### 1. Pattern Matching
```lisp
; Match with variables
!(match &self (human $who) $who)
; Returns all entities that are human
```

### 2. Function Definition
```lisp
; Define a function to check ancestors
(ancestor $x $y) :-
  (parent $x $y)
  (parent $x $z) (ancestor $z $y)
```

### 3. Type System
MeTTa includes a sophisticated type system that supports:
- Type inference
- Parametric polymorphism
- Type constraints

### 4. Non-deterministic Evaluation
MeTTa can explore multiple execution paths:
```lisp
; Multiple possible solutions
!(match &self (parent $x $y) ($x $y))
```

## Integration with Python

MeTTa can be easily integrated with Python:

```python
from hyperon import MeTTa, E, S, V, OperationAtom

# Create a MeTTa instance
metta = MeTTa()

# Define a Python function
def python_add(a, b):
    return a + b

# Register the function in MeTTa
metta.register_atom('python-add', OperationAtom('python-add', python_add, [int, int], int))

# Call Python from MeTTa
result = metta.run(''"
    !(python-add 2 3)
"'')
print(result)  # Output: [5]
```

## Use Cases

### 1. Knowledge Representation
- Building and querying knowledge graphs
- Semantic reasoning systems
- Expert systems

### 2. Cognitive Architectures
- Natural language understanding
- Planning and decision making
- Learning systems

### 3. Data Integration
- Combining structured and unstructured data
- Cross-domain knowledge fusion
- Context-aware systems

## Contributing

Contributions to MeTTa are welcome! Here's how you can help:

1. Report bugs and request features
2. Improve documentation
3. Contribute code via pull requests
4. Join the community discussions

## License

MeTTa is open-source software distributed under the Apache License 2.0.

## References

1. [MeTTa Language Documentation](https://metta-lang.dev/)
2. [OpenCog Hyperon](https://hyperon.opencog.org/)
3. [Artificial Superintelligence Alliance](https://superintelligence.io/)
4. [GitHub Repository](https://github.com/trueagi-io/hyperon-experimental)

---
*This README provides a comprehensive overview of the MeTTa programming language. For more detailed information, please refer to the official documentation and resources.*
