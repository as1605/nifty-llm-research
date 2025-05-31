"""
Base agent class for Perplexity model interactions.
"""

import asyncio
import requests
from typing import Optional, List, Dict, Any, Tuple

from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.db.models import Invocation
from src.db.models import PromptConfig

from config.settings import settings


class BaseAgent:
    """Base class for Perplexity-powered agents."""

    def __init__(
        self,
        model: str = "sonar-deep-research",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        poll_interval: float = 1.0,
        max_poll_time: float = 300.0,  # 5 minutes timeout
    ):
        """Initialize the agent.

        Args:
            model: The Perplexity model to use
            temperature: Controls randomness in responses
            max_tokens: Maximum tokens in response
            poll_interval: Time between polling attempts in seconds
            max_poll_time: Maximum time to poll for completion in seconds
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = settings.perplexity_api_key
        self.base_url = "https://api.perplexity.ai/async/chat/completions"
        self.poll_interval = poll_interval
        self.max_poll_time = max_poll_time
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _create_messages(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict[str, str]]] = None,
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

    async def _poll_completion(self, request_id: str) -> Dict[str, Any]:
        """Poll for completion of an async request.

        Args:
            request_id: The request ID to poll

        Returns:
            The completed response data

        Raises:
            TimeoutError: If polling exceeds max_poll_time
            ValueError: If the request fails
        """
        start_time = asyncio.get_event_loop().time()
        poll_url = f"{self.base_url}/{request_id}"

        while True:
            if asyncio.get_event_loop().time() - start_time > self.max_poll_time:
                raise TimeoutError(f"Polling exceeded maximum time of {self.max_poll_time} seconds")

            response = requests.get(poll_url, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            if data.get('status') == 'COMPLETED':
                return data.get('response', {})
            elif data.get('status') == 'FAILED':
                raise ValueError(f"Request failed: {data.get('error', 'Unknown error')}")

            await asyncio.sleep(self.poll_interval)

    async def get_completion(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict[str, str]]] = None,
        prompt_config: Optional[PromptConfig] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """Get a chat completion from Perplexity and store the invocation.

        Args:
            system_prompt: The system behavior definition
            user_message: The user's input message
            context: Optional additional context messages
            prompt_config: Optional prompt configuration for storing invocation
            params: Optional parameters used in the prompt

        Returns:
            Tuple of (Perplexity chat completion response, invocation ID)

        Raises:
            TimeoutError: If polling exceeds max_poll_time
            ValueError: If the request fails
        """
        messages = self._create_messages(system_prompt, user_message, context)

        # Submit async request
        payload = {
            "request": {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
            }
        }

        response = requests.post(self.base_url, json=payload, headers=self.headers)
        response.raise_for_status()
        request_data = response.json()
        request_id = request_data.get('request_id')

        if not request_id:
            raise ValueError("No request ID received from Perplexity API")

        # Poll for completion
        response_data = await self._poll_completion(request_id)

        # Store invocation if prompt_config is provided
        invocation_id = None
        if prompt_config:
            invocation = Invocation(
                prompt_config_id=prompt_config.id,
                params=params or {},
                response=response_data['choices'][0]['message']['content'],
                metadata=response_data.get('usage', {}),
            )
            result = await async_db[COLLECTIONS["invocations"]].insert_one(invocation.dict())
            invocation_id = str(result.inserted_id)

        return response_data, invocation_id

    async def get_prompt_config(
        self,
        name: str,
        system_prompt: str,
        user_prompt: str,
        params: List[str],
        model: Optional[str] = None,
    ) -> PromptConfig:
        """Get or create a prompt configuration.

        Args:
            name: Name of the prompt configuration
            system_prompt: The system prompt
            user_prompt: The user prompt template
            params: List of parameter names used in the prompt
            model: Optional model override

        Returns:
            The prompt configuration
        """
        config = await async_db[COLLECTIONS["prompt_configs"]].find_one({"name": name})

        if config:
            return PromptConfig(**config)

        config = PromptConfig(
            name=name,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            params=params,
            model=model or self.model,
            default=True,
        )

        result = await async_db[COLLECTIONS["prompt_configs"]].insert_one(config.dict())
        config.id = result.inserted_id
        return config

