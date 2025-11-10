"""Data transformation and formatting utilities."""

from typing import Any


def round_floats_to_2_decimals(data: Any) -> Any:
    """Recursively round all floating point numbers to 2 decimal places.
    
    This function traverses nested dictionaries and lists, rounding all
    float values to 2 decimal places. Useful for preparing data for LLM
    consumption or JSON serialization.
    
    Args:
        data: Data structure (dict, list, float, etc.) to process
        
    Returns:
        Data structure with all floats rounded to 2 decimal places.
        Non-float values are returned unchanged.
        
    Examples:
        >>> round_floats_to_2_decimals(3.14159)
        3.14
        >>> round_floats_to_2_decimals({"price": 10.567, "quantity": 5})
        {"price": 10.57, "quantity": 5}
        >>> round_floats_to_2_decimals([1.234, 5.678, {"value": 9.999}])
        [1.23, 5.68, {"value": 10.0}]
    """
    if isinstance(data, float):
        return round(data, 2)
    elif isinstance(data, dict):
        return {key: round_floats_to_2_decimals(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [round_floats_to_2_decimals(item) for item in data]
    else:
        return data

