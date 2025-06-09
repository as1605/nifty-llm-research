"""
Base agent class for Google Gemini model interactions.
"""

import asyncio
import json
import logging
import re
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime

from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.db.models import Invocation
from src.db.models import PromptConfig

from config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for Gemini-powered agents."""

    def __init__(self):
        """Initialize the agent."""
        # Initialize Gemini client
        self.client = genai.Client(api_key=settings.google_api_key)

    def _parse_json_response(self, response_text: str) -> dict:
        """Parse JSON response with fallback mechanisms.
        
        Args:
            response_text: The response text from the LLM
            
        Returns:
            Parsed JSON data
            
        Raises:
            ValueError: If JSON parsing fails after all attempts
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Initial JSON parsing failed, attempting fallback methods...")
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*({[\s\S]*?})\s*```', response_text)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON from markdown code block")
            
            # Try to find the first valid JSON object
            json_match = re.search(r'({[\s\S]*})', response_text)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON from text content")
            
            raise ValueError("Failed to parse JSON response from LLM")

    def _create_messages(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Create message for Gemini completion.

        Args:
            system_prompt: The system behavior definition
            user_message: The user's input message
            context: Optional additional context messages

        Returns:
            Combined message string
        """
        messages = [system_prompt]
        
        if context:
            for ctx in context:
                messages.append(ctx["content"])
                
        messages.append(user_message)
        return "\n\n".join(messages)

    async def get_completion(
        self,
        prompt_config: PromptConfig,
        params: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], str]:
        """Get a completion from Gemini and store the invocation.

        Args:
            prompt_config: The prompt configuration to use
            params: Parameters to be interpolated in the prompt

        Returns:
            Tuple of (Gemini completion response, invocation ID)

        Raises:
            ValueError: If the request fails or if required parameters are missing
        """
        # Validate required parameters
        missing_params = [param for param in prompt_config.params if param not in params]
        if missing_params:
            raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")

        # Interpolate prompts with parameters
        system_prompt = prompt_config.system_prompt
        user_prompt = prompt_config.user_prompt.format(**params)

        # Combine messages
        content = self._create_messages(system_prompt, user_prompt)

        # Configure tools if needed
        tools = []
        if "google_search" in prompt_config.tools:
            tools.append(Tool(google_search=GoogleSearch()))

        # Generate content
        logger.info(f"Submitting request to Gemini API using model: {prompt_config.model}")
        
        response = self.client.models.generate_content(
            model=prompt_config.model,
            contents=content,
            config=GenerateContentConfig(
                tools=tools,
                response_modalities=["TEXT"],
                temperature=prompt_config.temperature,
                max_output_tokens=prompt_config.max_tokens,
            )
        )

        # Extract response text
        response_text = ""
        for part in response.candidates[0].content.parts:
            response_text += part.text

        # Store invocation
        invocation = Invocation(
            prompt_config_id=prompt_config.id,
            params=params,
            response=response_text,
            metadata={
                "model": prompt_config.model,
                "temperature": prompt_config.temperature,
                "max_tokens": prompt_config.max_tokens,
                "tools_used": prompt_config.tools,
                "grounding_metadata": response.candidates[0].grounding_metadata.model_dump() if hasattr(response.candidates[0], 'grounding_metadata') else None
            },
        )
        result = await async_db[COLLECTIONS["invocations"]].insert_one(invocation.model_dump())
        invocation_id = str(result.inserted_id)

        logger.info(f"Stored invocation with ID: {invocation_id}")
        return {"choices": [{"message": {"content": response_text}}]}, invocation_id

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

