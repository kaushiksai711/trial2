# Athena Disaster Response Agent

AI-powered disaster management chatbot combining MeTTa symbolic reasoning with modern web technologies.

## Quick Start

### Backend Setup

cd backend
pip install -r requirements.txt
python app.py


### Frontend Setup (using Vite)

npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm run dev


## Project Structure

athena_disaster_agent/
├── backend/ # FastAPI server and MeTTa integration
├── frontend/ # React frontend (created by Vite)
├── metta_scripts/ # MeTTa knowledge base and agents
├── data/ # Disaster management datasets
├── tests/ # Testing framework
└── deployment/ # Docker and deployment configs


## Development Phases

- **Athena Base**: Functional chatbot with voice capabilities (3 hours)
- **Athena Complete**: Advanced AI with symbolic reasoning and RAG

## Technologies

- **Backend**: Python, FastAPI, MeTTa-Motto
- **Frontend**: React, TypeScript, Vite, Web Speech API
- **AI**: MeTTa symbolic reasoning, Claude 4.0 Sonnet
