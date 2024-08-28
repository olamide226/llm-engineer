"""Anthropic model utilities"""

import os
from functools import lru_cache

from anthropic import Anthropic

from dotenv import load_dotenv

# Load environment variables from .env fil
load_dotenv()


@lru_cache(maxsize=1)
def get_anthropic_client() -> Anthropic:
    """Return the initialized Anthropic client"""
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
    return Anthropic(api_key=anthropic_api_key)


client = get_anthropic_client()
