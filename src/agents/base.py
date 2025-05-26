"""
Base agent class for OpenAI interactions.
"""
from typing import Any, Dict, List, Optional

import openai
from openai.types.chat import ChatCompletion

from config.settings import settings

# Configure OpenAI
openai.api_key = settings.openai_api_key

class BaseAgent:
    """Base class for OpenAI-powered agents."""
    
    def __init__(
        self,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ):
        """Initialize the agent.
        
        Args:
            model: The OpenAI model to use
            temperature: Controls randomness in responses
            max_tokens: Maximum tokens in response
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
    def _create_messages(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """Create message list for chat completion.
        
        Args:
            system_prompt: The system behavior definition
            user_message: The user's input message
            context: Optional additional context messages
            
        Returns:
            List of message dictionaries
        """
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        if context:
            messages.extend(context)
            
        messages.append({"role": "user", "content": user_message})
        return messages
    
    async def get_completion(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> ChatCompletion:
        """Get a chat completion from OpenAI.
        
        Args:
            system_prompt: The system behavior definition
            user_message: The user's input message
            context: Optional additional context messages
            
        Returns:
            OpenAI chat completion response
        """
        messages = self._create_messages(system_prompt, user_message, context)
        
        response = await openai.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        
        return response 