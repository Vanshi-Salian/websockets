from typing import AsyncGenerator, List, Dict
from openai import AsyncOpenAI
import os
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # New syntax for OpenAI v1.3.0
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found. Using mock responses.")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=api_key)
        
    async def stream_response(self, query: str, context: Dict, session_id: str) -> AsyncGenerator[str, None]:
        """Stream AI response with actual OpenAI integration"""
        
        # If no API key, use mock
        if not self.client:
            async for chunk in self._mock_response(query):
                yield chunk
            return
            
        try:
            # Prepare messages with context
            messages = [
                {"role": "system", "content": self._build_system_prompt(context)},
                {"role": "user", "content": query}
            ]
            
            # Create streaming completion
            stream = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                stream=True,
                temperature=0.7,
                max_tokens=500
            )
            
            # Stream the response
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            # Fallback to mock response
            async for chunk in self._mock_response(query):
                yield chunk
    
    async def get_embeddings(self, text: str) -> List[float]:
        """Get text embeddings using OpenAI's embedding model"""
        if not self.client:
            return []
            
        try:
            response = await self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return []
    
    async def _mock_response(self, query: str) -> AsyncGenerator[str, None]:
        """Generate mock responses when no API key is available"""
        query_lower = query.lower()
        
        if "schedule" in query_lower:
            response = "Based on your schedule, you have classes Monday to Friday. Your next class is at 10 AM tomorrow."
        elif "assignment" in query_lower:
            response = "You have 3 pending assignments. The Mathematics assignment is due in 2 days."
        elif "grade" in query_lower:
            response = "Your current overall grade is 85%. You're doing great! Keep it up."
        else:
            response = f"I understand you're asking about '{query}'. How can I help you with that?"
        
        for word in response.split():
            yield word + " "
            await asyncio.sleep(0.05)
    
    def _build_system_prompt(self, context: Dict) -> str:
        """Build system prompt with context"""
        prompt = """You are an AI tutor for a Smart Classroom system. 
        Your role is to help students with their questions about:
        - Course schedules and timetables
        - Assignments and submissions
        - Learning materials and resources
        - Academic progress and grades
        
        Be helpful, concise, and educational in your responses.
        """
        
        if context.get("course_id"):
            prompt += f"\n\nContext: The student is asking about course: {context['course_id']}"
            
        if context.get("user_role"):
            prompt += f"\nUser role: {context['user_role']}"
            
        return prompt


# Optional: LangChain integration (commented out to avoid import errors)
# To use LangChain, update to latest version: pip install langchain langchain-openai
"""
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

class LangChainAIService:
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=0.7,
            model="gpt-3.5-turbo",
            streaming=True,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
    async def stream_response(self, query: str, context: Dict, session_id: str) -> AsyncGenerator[str, None]:
        from langchain.schema import HumanMessage, SystemMessage
        
        system_prompt = "You are an AI tutor for a Smart Classroom system."
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ]
        
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield chunk.content
"""