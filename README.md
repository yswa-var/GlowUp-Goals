# GlowUp-Goals
Accountability Coach App

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- Node.js 18 or higher
- npm (comes with Node.js)
- OpenAI API key

### Backend Setup
1. Create and activate a Python virtual environment:
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

2. Install backend dependencies:
```bash
cd backend
pip install fastapi uvicorn python-dotenv openai
```

3. Create a `.env` file in the root directory:
```bash
# From the project root
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

### Frontend Setup
1. Install frontend dependencies:
```bash
cd frontend
npm install
```

## Running the Application

### Start the Backend Server
```bash
# Make sure you're in the backend directory and virtual environment is activated
cd backend
uvicorn app:app --reload
```
The backend server will start at http://localhost:8000

### Start the Frontend Development Server
```bash
# In a new terminal, from the frontend directory
cd frontend
npm run dev
```
The frontend will be available at http://localhost:5173 (or another port if 5173 is in use)

## Project Structure
```
GlowUp-Goals/
├── backend/
│   ├── app.py              # FastAPI backend server
│   └── llm_connector.py    # OpenAI integration
├── frontend/
│   ├── src/
│   │   ├── App.tsx        # Main React component
│   │   └── main.tsx       # React entry point
│   └── package.json       # Frontend dependencies
├── .env                   # Environment variables (create this)
└── README.md             # This file
```

## Development
- Backend API documentation is available at http://localhost:8000/docs when the server is running
- The frontend uses Vite for fast development and hot reloading
- The backend uses FastAPI with automatic API documentation
- OpenAI integration is configured to use GPT-4 with JSON responses

## Notes
- Make sure to keep your OpenAI API key secure and never commit it to version control
- The backend requires Python 3.8+ for proper async support
- The frontend uses Chakra UI for styling and components

