"""
Base agent class for Google Gemini model interactions.
"""

import asyncio
import json
import logging
import re
import random
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone

from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch, ThinkingConfig
from google.genai.errors import ServerError

from src.db.database import COLLECTIONS
from src.db.database import async_db
from src.db.models import Invocation
from src.db.models import PromptConfig

from config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = 10
INITIAL_RETRY_DELAY = 1  # seconds
MAX_RETRY_DELAY = 300  # seconds (5 minutes)
JITTER_FACTOR = 0.1  # 10% jitter


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
        user_message: str,
        context: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Create message for Gemini completion.

        Args:
            user_message: The user's input message
            context: Optional additional context messages

        Returns:
            Combined message string
        """
        messages = []
        
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

        # Interpolate prompts with parameters using string replace
        system_prompt = prompt_config.system_prompt
        user_prompt = prompt_config.user_prompt
        
        # Replace parameters in both prompts
        for key, value in params.items():
            placeholder = f"{{{key}}}"
            system_prompt = system_prompt.replace(placeholder, str(value))
            user_prompt = user_prompt.replace(placeholder, str(value))

        # Combine messages
        content = self._create_messages(user_prompt)

        # Configure tools if needed
        tools = []
        if "google_search" in prompt_config.tools:
            tools.append(Tool(google_search=GoogleSearch()))

        # Create invocation record with start time
        invocation = Invocation(
            prompt_config_id=prompt_config.id,
            params=params,
            response="",  # Will be updated after response
            invocation_time=datetime.now(timezone.utc),
            metadata={
                "model": prompt_config.model,
                "config": prompt_config.config,
                "tools_used": prompt_config.tools,
            },
        )
        result = await async_db[COLLECTIONS["invocations"]].insert_one(invocation.model_dump())
        invocation_id = str(result.inserted_id)

        # Generate content with retry logic
        logger.info(f"Submitting request to Gemini API using model: {prompt_config.model}")
        
        # Extract configuration from PromptConfig
        config = prompt_config.config
        generation_config = config.get("generation_config", {})
        
        # Create GenerateContentConfig with all available parameters
        generate_config = GenerateContentConfig(
            tools=tools,
            response_modalities=["TEXT"],
            temperature=generation_config.get("temperature", config.get("temperature", 0.2)),
            max_output_tokens=generation_config.get("max_output_tokens", config.get("max_tokens", 4096)),
            top_p=generation_config.get("top_p", config.get("top_p", 0.8)),
            top_k=generation_config.get("top_k", config.get("top_k", 20)),
            candidate_count=config.get("candidate_count", 1),
            stop_sequences=config.get("stop_sequences", []),
            safety_settings=config.get("safety_settings", []),
            system_instruction=system_prompt
        )

        # Add response schema if specified
        if "response_schema" in config and config["response_schema"]:
            generate_config.response_schema = config["response_schema"]

        # Add response MIME type if specified
        if "response_mime_type" in config:
            generate_config.response_mime_type = config["response_mime_type"]

        # Add thinking config if specified
        thinking_config = None
        if "thinking_budget" in config or "include_thoughts" in config:
            thinking_config = ThinkingConfig(
                thinking_budget=config.get("thinking_budget"),
                include_thoughts=config.get("include_thoughts", False)
            )
        if thinking_config:
            generate_config.thinking_config = thinking_config

        
        retry_count = 0
        while True:
            try:
                response = self.client.models.generate_content(
                    model=prompt_config.model,
                    contents=content,
                    config=generate_config
                )
                break  # Success, exit retry loop
                
            except ServerError as e:
                if not str(e).startswith("503"):
                    raise  # Re-raise if not a 503 error
                    
                retry_count += 1
                if retry_count > MAX_RETRIES:
                    logger.error(f"Max retries ({MAX_RETRIES}) exceeded for 503 error")
                    raise ValueError(f"Service unavailable after {MAX_RETRIES} retries: {str(e)}")
                
                # Calculate delay with exponential backoff and jitter
                delay = min(INITIAL_RETRY_DELAY * (2 ** (retry_count - 1)), MAX_RETRY_DELAY)
                jitter = random.uniform(-JITTER_FACTOR * delay, JITTER_FACTOR * delay)
                total_delay = delay + jitter
                
                logger.warning(
                    f"Received 503 error, retrying in {total_delay:.2f} seconds "
                    f"(attempt {retry_count}/{MAX_RETRIES})"
                )
                await asyncio.sleep(total_delay)
                
            except Exception as e:
                logger.error(f"Unexpected error during Gemini API call: {str(e)}")
                raise ValueError(f"Failed to get completion: {str(e)}")

        # Extract response text
        response_text = ""
        for part in response.candidates[0].content.parts:
            response_text += part.text

        # Get grounding metadata if available
        grounding_metadata = None
        if (hasattr(response.candidates[0], 'grounding_metadata') and 
            response.candidates[0].grounding_metadata is not None):
            try:
                grounding_metadata = response.candidates[0].grounding_metadata.model_dump()
            except Exception as e:
                logger.warning(f"Failed to get grounding metadata: {e}")
        
        usage_metadata = None
        if response.usage_metadata is not None:
            try:
                usage_metadata = response.usage_metadata.model_dump()
            except Exception as e:
                logger.warning(f"Failed to get usage metadata: {e}")

        # Update invocation with response and end time
        await async_db[COLLECTIONS["invocations"]].update_one(
            {"_id": result.inserted_id},
            {
                "$set": {
                    "response": response_text,
                    "result_time": datetime.now(timezone.utc),
                    "metadata.grounding_metadata": grounding_metadata,
                    "metadata.usage_metadata": usage_metadata
                }
            }
        )

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

