# 🚨 Athena Multi-Domain Expert System

**A sophisticated AI-powered expert system built with MeTTa symbolic reasoning, providing specialized assistance across three critical domains: Disaster Response, Healthcare, and Legal Consultation.**

---

## 🎯 What We Built

### Three Specialized AI Experts
- **🚨 Athena** - Disaster Response Specialist (earthquakes, fires, floods, hurricanes)
- **🩺 Dr. Alex Rivera** - Medical Advisor (health conditions, symptoms, wellness)
- **⚖️ Attorney Sam Chen** - Legal Consultant (contracts, family law, employment law)

### Complete Working Features
- ✅ **Multi-domain chat interface** with domain switching
- ✅ **WhatsApp-style UI** with domain-specific themes
- ✅ **Voice recognition** for speech-to-text input
- ✅ **Text-to-speech** with synchronized read-aloud controls
- ✅ **Enhanced text formatting** (line breaks, **bold text**)
- ✅ **Action buttons** (copy, share, print, read-aloud)
- ✅ **Perfect domain boundaries** with smart redirects
- ✅ **Independent conversation histories** per domain

---

## 🛠️ Tech Stack (Implemented)

### Backend
- **FastAPI** - Web API framework
- **MeTTa** - Symbolic reasoning (.msa agent scripts)
- **OpenRouter** - LLM integration
- **Python 3.8+** - Runtime environment

### Frontend  
- **React 18** - User interface
- **CSS3** - Styling with themes
- **Speech API** - Voice features
- **Responsive design** - Mobile/desktop support

---

## 🚀 How to Run

### Prerequisites
- Python 3.8+
- Node.js 16+
- OpenRouter API Key

### Backend Setup
\`\`\`bash
cd athena_disaster_agent/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\\Scripts\\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Set API key
export OPENROUTER_API_KEY="your_key_here"

# Start server
python app.py
\`\`\`

### Frontend Setup
\`\`\`bash
cd athena_disaster_agent/frontend

# Install and start
npm install
npm run dev
\`\`\`

### Access
- **App:** http://localhost:3000
- **API:** http://localhost:8000

---

## 📱 How It Works

### 1. Choose Your Expert Domain
Click tabs to switch between domains:
\`\`\`
[🚨 Disaster] [🩺 Healthcare] [⚖️ Legal]
\`\`\`

### 2. Chat with Specialized Experts
Each domain has its own expert with strict boundaries:

**Disaster queries** → Athena responds  
**Medical queries** → Dr. Rivera responds  
**Legal queries** → Attorney Chen responds  

**Cross-domain queries** get smart redirects.

### 3. Enhanced Features
- **Voice input:** Click 🎤 to speak your question
- **Read responses:** Click 🔊 to hear answers
- **Action buttons:** Copy, share, print any response
- **Auto read-aloud:** Toggle automatic speech
- **Perfect formatting:** Line breaks and **bold text** work

---

## 🏗️ Architecture

### File Structure
\`\`\`
athena_disaster_agent/
├── backend/
│   ├── domains/
│   │   ├── disaster.msa     # Athena's expertise
│   │   ├── healthcare.msa   # Dr. Rivera's expertise
│   │   └── legal.msa        # Attorney Chen's expertise
│   ├── app.py              # FastAPI server
│   └── requirements.txt    # Dependencies
└── frontend/
    ├── src/components/     # React components
    ├── package.json        # Dependencies
    └── public/            # Assets
\`\`\`

### MeTTa Agents
Each expert is powered by a specialized \`.msa\` script with:
- **Domain-specific expertise** and knowledge
- **Professional personality** and communication style  
- **Strict boundaries** - won't answer out-of-domain questions
- **Smart redirects** - guides users to correct domain

---

## ✨ Key Features Implemented

### Domain Intelligence
- **Perfect separation:** Each expert stays in their lane
- **Smart routing:** Questions go to the right expert
- **Professional redirects:** "I'm a disaster specialist, not a medical expert. Please click the 🩺 Healthcare tab..."

### Voice Integration  
- **Speech recognition:** Browser-native voice input
- **Text-to-speech:** High-quality voice output
- **Synchronized controls:** All voice buttons work together
- **Visual feedback:** Shows when listening/speaking

### User Experience
- **WhatsApp-style chat:** Familiar bubble interface
- **Domain themes:** Red for disaster, blue for healthcare, navy for legal
- **Responsive design:** Works on desktop and mobile
- **Action buttons:** Every response has copy/share/print/read options

### Text Formatting
- **Line breaks:** \`\\n\` converts to actual line spacing
- **Bold text:** \`**text**\` renders as **bold**
- **Clean copying:** Removes formatting when copying
- **Print-friendly:** Professional formatted printing

---

## 🔧 API Endpoints

### Health Check
\`\`\`
GET /health
\`\`\`

### Chat with Expert
\`\`\`
POST /chat/{domain}
Body: {"message": "your question", "session_id": "optional"}
Response: {"response": "expert answer", "expert_name": "🚨 Athena", "success": true}
\`\`\`

**Domains:** \`disaster\`, \`healthcare\`, \`legal\`

---

## ⚠️ Important Notes

### Medical Disclaimer
Dr. Rivera provides **health information only** - not medical diagnosis. For emergencies, call 911.

### Legal Disclaimer  
Attorney Chen provides **legal information only** - not legal advice. Consult licensed attorneys for specific cases.

### Emergency Disclaimer
**For life-threatening emergencies, call 911 immediately** before using any AI system.

---

## 🎉 What Makes This Special

- **Real MeTTa Integration:** Uses symbolic reasoning, not just plain LLMs
- **Perfect Domain Boundaries:** Experts won't step outside their expertise
- **Production-Ready:** Professional UI/UX with error handling
- **Voice-Enabled:** Full speech integration with synchronized controls
- **Multi-Domain Architecture:** Scales to add more expert domains
- **Enhanced Formatting:** Proper text rendering with markdown support

Built with ❤️ using MeTTa symbolic reasoning and modern web technologies.
