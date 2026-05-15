"""
AI Client wrapper for OpenAI-compatible APIs.
"""

from typing import Any, Dict, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from openai import AsyncOpenAI
import structlog
from config import settings

logger = structlog.get_logger()

T = TypeVar("T", bound=BaseModel)

class AIClient:
    """
    Wrapper for the OpenAI SDK to provide a consistent interface for AI calls.
    """

    def __init__(
        self, 
        api_url: Optional[str] = None, 
        api_token: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_url = api_url or settings.ai_api_url
        self.api_token = api_token or settings.ai_api_token
        self.model = model or settings.ai_model
        self.reasoning_effort = settings.ai_reasoning_effort
        
        self.client = AsyncOpenAI(
            base_url=self.api_url,
            api_key=self.api_token,
            timeout=600.0
        )
        
        logger.info("ai_client_initialized", base_url=self.api_url)

    async def get_structured_response(
        self, 
        prompt: str, 
        reasoning_effort: Optional[str] = None,
        response_model: Optional[Type[T]] = None
    ) -> Union[T, Dict[str, Any], str]:
        """
        Calls the "responses api" and parses the structured result.
        If response_model is provided, validates the JSON against it.
        """
        logger.info("ai_call_start", prompt_length=len(prompt), reasoning_effort=reasoning_effort)
        
        try:
            # Use the SDK's Responses API as per the user's working snippet
            # We assume the latest version of the SDK has this attribute
            kwargs = {
                "model": self.model,
                "input": prompt
            }
            effort = reasoning_effort or self.reasoning_effort
            if effort:
                kwargs["reasoning"] = {"effort": effort}

            # If using AsyncOpenAI, it should be awaited
            response = await self.client.responses.create(**kwargs)
            
            # Manually extract the text content from the output items.
            raw_content = ""
            for item in response.output:
                if item.type == "message":
                    for content_block in item.content:
                        if content_block.type == "output_text":
                            raw_content += content_block.text
            
            if not raw_content:
                logger.error("ai_call_no_content")
                raise ValueError("AI returned no text content in 'message' blocks.")

            # Local models (LMStudio) often wrap JSON in markdown code blocks.
            # We strip them to ensure valid JSON parsing.
            clean_content = raw_content.strip()
            if "```" in clean_content:
                start_idx = clean_content.find("{")
                end_idx = clean_content.rfind("}")
                if start_idx != -1 and end_idx != -1:
                    clean_content = clean_content[start_idx : end_idx + 1]
            
            logger.info("ai_call_success")
            
            if response_model:
                return response_model.model_validate_json(clean_content)
            
            # Return the string without attempt to parse if parsing/validation fails
            return clean_content
            
        except Exception as e:
            logger.error("ai_call_failed", error=str(e))
            raise
