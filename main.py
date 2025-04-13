from fastapi import FastAPI, Request
from pydantic import BaseModel
from gemini_service import get_hotel_negotiation_reply, clear_conversation_history
import uvicorn

app = FastAPI()

class MessageRequest(BaseModel):
    message: str
    userId: str = "default"

@app.post("/negotiate")
async def negotiate(data: MessageRequest):
    try:
        reply = await get_hotel_negotiation_reply(data.message, data.userId)
        return {"reply": reply}
    except Exception as e:
        print(f"Gemini error: {e}")
        return {"error": "Gemini API failed"}

@app.post("/clear-history")
def clear_history(data: MessageRequest):
    try:
        clear_conversation_history(data.userId)
        return {"message": "Conversation history cleared successfully"}
    except Exception as e:
        print(f"Error clearing history: {e}")
        return {"error": "Failed to clear conversation history"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
