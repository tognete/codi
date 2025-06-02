from fastapi import FastAPI, HTTPException
from src.core.agent import CodiAgent, CodingTask, CodeResponse

app = FastAPI(
    title="Codi - AI Coding Agent",
    description="An AI agent designed to code at the level of a senior software engineer",
    version="0.1.0"
)

# Initialize the AI agent
agent = CodiAgent()

@app.post("/task", response_model=CodeResponse)
async def process_task(task: CodingTask):
    """Process a coding task and return the AI's response"""
    try:
        response = await agent.process_task(task)
        return response
    except NotImplementedError:
        raise HTTPException(
            status_code=501,
            detail=f"Task type '{task.task_type}' not implemented yet"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"} 