"""
Base agent class for Perplexity model interactions.
"""

import asyncio
import requests
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.db.models import Invocation
from src.db.models import PromptConfig

from config.settings import settings


class BaseAgent:
    """Base class for Perplexity-powered agents."""

    def __init__(
        self,
        max_tokens: Optional[int] = None,
        poll_interval: float = 1.0,
        max_poll_time: float = 300.0,  # 5 minutes timeout
    ):
        """Initialize the agent.

        Args:
            max_tokens: Maximum tokens in response
            poll_interval: Time between polling attempts in seconds
            max_poll_time: Maximum time to poll for completion in seconds
        """
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
        prompt_config: PromptConfig,
        params: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], str]:
        """Get a chat completion from Perplexity and store the invocation.

        Args:
            prompt_config: The prompt configuration to use
            params: Parameters to be interpolated in the prompt

        Returns:
            Tuple of (Perplexity chat completion response, invocation ID)

        Raises:
            TimeoutError: If polling exceeds max_poll_time
            ValueError: If the request fails or if required parameters are missing
        """
        # Validate required parameters
        missing_params = [param for param in prompt_config.params if param not in params]
        if missing_params:
            raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")

        # Interpolate prompts with parameters
        system_prompt = prompt_config.system_prompt
        user_prompt = prompt_config.user_prompt.format(**params)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Submit async request
        payload = {
            "request": {
                "model": prompt_config.model,
                "messages": messages,
                "temperature": prompt_config.temperature,
                "max_tokens": self.max_tokens,
            }
        }

        response = requests.post(self.base_url, json=payload, headers=self.headers)
        response.raise_for_status()
        request_data = response.json()
        request_id = request_data.get('id')

        if not request_id:
            raise ValueError("No request ID received from Perplexity API")

        # Poll for completion
        response_data = await self._poll_completion(request_id)

        # Store invocation
        invocation = Invocation(
            prompt_config_id=prompt_config.id,
            params=params,
            response=response_data['choices'][0]['message']['content'],
            metadata=response_data.get('usage', {}),
        )
        result = await async_db[COLLECTIONS["invocations"]].insert_one(invocation.dict())
        invocation_id = str(result.inserted_id)

        return response_data, invocation_id

    async def get_prompt_config(
        self,
        name: str,
    ) -> PromptConfig:
        """Get a prompt configuration by name.

        Args:
            name: Name of the prompt configuration

        Returns:
            PromptConfig object

        Raises:
            ValueError: If no prompt configuration is found with the given name
        """
        # Try to find existing default prompt
        prompt = await async_db[COLLECTIONS["prompt_configs"]].find_one({
            "name": name,
            "default": True
        })
        
        if prompt is None:
            # If no default prompt found, run the seeder
            from scripts.seed_prompts import seed_prompts
            await seed_prompts()
            
            # Try to find the prompt again after seeding
            prompt = await async_db[COLLECTIONS["prompt_configs"]].find_one({
                "name": name,
                "default": True
            })
            
            if prompt is None:
                raise ValueError(
                    f"No prompt configuration found for '{name}' even after seeding. "
                    "Please ensure the prompt is defined in scripts/seed_prompts.py"
                )
        
        return PromptConfig(**prompt)

