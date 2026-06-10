import uvicorn
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    print("=" * 50)
    print("Starting Smart Classroom WebSocket Server")
    print("=" * 50)
    print(f"Server will run on: http://{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', 8000)}")
    print(f"WebSocket endpoint: ws://localhost:{os.getenv('PORT', 8000)}/ws/{{user_id}}")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )