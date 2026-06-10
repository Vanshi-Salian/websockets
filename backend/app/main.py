from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse  # Add this import
from contextlib import asynccontextmanager
import json
import os
from dotenv import load_dotenv

from app.websocket.connection_manager import ConnectionManager
from app.websocket.chat_handler import ChatHandler
from app.websocket.ai_tutor_handler import AITutorHandler
from app.websocket.schedule_handler import ScheduleHandler
from app.database.database import Database
from app.services.auth_service import AuthService
from app.api import chat

# Load environment variables
load_dotenv()

# Global instances
connection_manager = ConnectionManager()
database = Database()
auth_service = AuthService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting WebSocket Server...")
    await database.connect()
    print("✅ Database connected")
    yield
    # Shutdown
    print("🛑 Shutting down...")
    await database.disconnect()
    await connection_manager.close_all_connections()
    print("✅ Cleanup complete")

app = FastAPI(
    title="Smart Classroom WebSocket Server",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=eval(os.getenv("CORS_ORIGINS", '["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:5500"]')),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize handlers
chat_handler = ChatHandler(connection_manager, database, auth_service)
ai_tutor_handler = AITutorHandler(connection_manager, database)
schedule_handler = ScheduleHandler(connection_manager)

# Include REST API routes
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

# Add this route to serve the test HTML file
@app.get("/test", response_class=HTMLResponse)
async def get_test_client():
    """Serve WebSocket test client"""
    html_file_path = "test_websocket.html"
    
    # Check if file exists in current directory
    if os.path.exists(html_file_path):
        with open(html_file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    else:
        # Return inline HTML if file doesn't exist
        return HTMLResponse(content=get_inline_test_html())

@app.get("/")
async def root():
    return {
        "message": "Smart Classroom WebSocket Server",
        "websocket_endpoint": "ws://localhost:8000/ws/{user_id}",
        "version": "1.0.0",
        "test_client": "http://localhost:8000/test"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_connections": len(connection_manager.active_connections),
        "online_users": list(connection_manager.active_connections.keys())
    }

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    # Get token from query params
    token = websocket.query_params.get("token")
    
    # Authenticate user
    user = await auth_service.authenticate_websocket(token, user_id)
    
    if not user:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    # Accept connection
    await connection_manager.connect(websocket, user_id, user)
    
    # Send offline messages if any
    await chat_handler.send_offline_messages(user_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Route message based on type
            message_type = message.get("type")
            
            if message_type == "chat":
                await chat_handler.handle_chat_message(user_id, message)
            elif message_type == "ai_query":
                await ai_tutor_handler.handle_ai_query(user_id, message)
            elif message_type == "ai_feedback":
                await ai_tutor_handler.handle_ai_feedback(user_id, message)
            elif message_type == "schedule":
                await schedule_handler.handle_schedule_message(user_id, message)
            elif message_type == "typing":
                await chat_handler.handle_typing_indicator(user_id, message)
            elif message_type == "read_receipt":
                await chat_handler.handle_read_receipt(user_id, message)
            elif message_type == "ping":
                await websocket.send_json({"type": "pong", "timestamp": message.get("timestamp")})
                
    except WebSocketDisconnect:
        connection_manager.disconnect(user_id)
        await chat_handler.broadcast_user_status(user_id, "offline")
        print(f"User {user_id} disconnected")
    except Exception as e:
        print(f"Error in websocket connection: {e}")
        connection_manager.disconnect(user_id)

# Add this helper function for inline HTML (in case file doesn't exist)
def get_inline_test_html():
    """Return inline HTML for testing"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Test Client</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .status.connected { background: #d4edda; color: #155724; }
        .status.disconnected { background: #f8d7da; color: #721c24; }
        .messages { border: 1px solid #ddd; padding: 10px; height: 400px; overflow-y: scroll; margin: 10px 0; }
        .message { margin: 5px 0; padding: 5px; border-radius: 4px; }
        .input-group { display: flex; gap: 10px; margin-top: 10px; }
        input, button { padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #007bff; color: white; cursor: pointer; }
        button:hover { background: #0056b3; }
    </style>
</head>
<body>
    <h1>📡 Smart Classroom WebSocket Test</h1>
    
    <div>
        <input type="text" id="userId" placeholder="User ID" value="student1">
        <button onclick="connect()">Connect</button>
        <button onclick="disconnect()">Disconnect</button>
    </div>
    
    <div id="status" class="status disconnected">⚫ Disconnected</div>
    
    <div class="messages" id="messages"></div>
    
    <div class="input-group">
        <input type="text" id="recipient" placeholder="Recipient ID" value="teacher1">
        <input type="text" id="messageText" placeholder="Type your message..." style="flex: 2;">
        <button onclick="sendMessage()">Send</button>
    </div>
    
    <div class="input-group">
        <input type="text" id="aiQuery" placeholder="Ask AI Tutor..." style="flex: 2;">
        <button onclick="sendAIQuery()">Ask AI</button>
    </div>

    <script>
        let ws = null;
        
        function connect() {
            const userId = document.getElementById('userId').value;
            const wsUrl = `ws://localhost:8000/ws/${userId}`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                const statusDiv = document.getElementById('status');
                statusDiv.className = 'status connected';
                statusDiv.innerHTML = '✅ Connected to WebSocket';
                addMessage('System', `Connected as ${userId}`);
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                handleMessage(data);
            };
            
            ws.onclose = function() {
                const statusDiv = document.getElementById('status');
                statusDiv.className = 'status disconnected';
                statusDiv.innerHTML = '❌ Disconnected';
                addMessage('System', 'Disconnected from server');
            };
            
            ws.onerror = function(error) {
                addMessage('Error', 'WebSocket error occurred');
            };
        }
        
        function disconnect() {
            if (ws) {
                ws.close();
                ws = null;
            }
        }
        
        function handleMessage(data) {
            switch(data.type) {
                case 'chat_message':
                    addMessage(data.payload.sender_name, data.payload.content);
                    break;
                case 'ai_stream_chunk':
                    updateAIResponse(data.payload.partial_response);
                    break;
                case 'ai_complete':
                    addMessage('AI Tutor', data.payload.full_response);
                    break;
                default:
                    addMessage('Server', JSON.stringify(data));
            }
        }
        
        function sendMessage() {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                alert('WebSocket is not connected');
                return;
            }
            
            const recipient = document.getElementById('recipient').value;
            const content = document.getElementById('messageText').value;
            
            const message = {
                type: 'chat',
                payload: {
                    recipient_id: recipient,
                    message_type: 'text',
                    content: content
                }
            };
            
            ws.send(JSON.stringify(message));
            addMessage('You', `To ${recipient}: ${content}`);
            document.getElementById('messageText').value = '';
        }
        
        function sendAIQuery() {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                alert('WebSocket is not connected');
                return;
            }
            
            const query = document.getElementById('aiQuery').value;
            if (!query) return;
            
            const message = {
                type: 'ai_query',
                payload: {
                    query: query,
                    session_id: document.getElementById('userId').value,
                    context: {}
                }
            };
            
            ws.send(JSON.stringify(message));
            addMessage('You', `AI Query: ${query}`);
            document.getElementById('aiQuery').value = '';
        }
        
        function updateAIResponse(response) {
            const messagesDiv = document.getElementById('messages');
            const lastMessage = messagesDiv.lastChild;
            if (lastMessage && lastMessage.textContent.includes('AI Tutor')) {
                lastMessage.innerHTML = `<strong>AI Tutor:</strong> ${response}`;
            } else {
                addMessage('AI Tutor', response);
            }
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        function addMessage(sender, text) {
            const messagesDiv = document.getElementById('messages');
            const messageElement = document.createElement('div');
            messageElement.className = 'message';
            messageElement.innerHTML = `<strong>${sender}:</strong> ${text}`;
            messagesDiv.appendChild(messageElement);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        // Auto-connect on page load
        window.onload = function() {
            setTimeout(connect, 1000);
        };
    </script>
</body>
</html>
    """