from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Intelligent QA System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "running",
        "title": "Intelligent QA System",
        "endpoints": {
            "/health": "GET - Health check",
            "/qa": "POST - Ask a question"
        }
    }

@app.get("/health")
def health():
    return {"status": "ok"}

# Define the request model
class QARequest(BaseModel):
    question: str

# POST /qa endpoint
@app.post("/qa")
def qa_endpoint(request: QARequest):
    question = request.question
    # For now, just echo the question back
    return {"question_received": question, "answer": "This is a placeholder answer"}
