"""JSON parsing and manipulation utilities."""

import json
import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def parse_json_response(response_text: str) -> Dict[str, Any]:
    """Parse JSON response with fallback mechanisms.
    
    This function attempts to parse JSON from LLM responses, which may contain
    JSON wrapped in markdown code blocks or embedded in text. It tries multiple
    fallback strategies to extract valid JSON.
    
    Args:
        response_text: The response text from the LLM that may contain JSON
        
    Returns:
        Parsed JSON data as a dictionary
        
    Raises:
        ValueError: If JSON parsing fails after all attempts
        
    Examples:
        >>> parse_json_response('{"key": "value"}')
        {'key': 'value'}
        >>> parse_json_response('```json\n{"key": "value"}\n```')
        {'key': 'value'}
        >>> parse_json_response('Some text {"key": "value"} more text')
        {'key': 'value'}
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

