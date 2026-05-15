import json
from .models.models import CVExtraction
from utils.ai_client import AIClient

class SoftwareEngineerStructuredExtractor:
    """
    Specialized extractor for Software Engineering CVs.
    Uses an LLM to extract structured data based on a Pydantic schema.
    """
    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client

    async def extract(self, cv_text: str) -> CVExtraction:
        """
        Extracts structured information from CV text.
        
        Args:
            cv_text: The raw text of the CV.
            
        Returns:
            A validated CVExtraction pydantic object.
        """
        # Get the JSON schema from the Pydantic model
        schema = CVExtraction.model_json_schema()
        schema_json = json.dumps(schema, indent=2)

        # prompt = (
        #     "From the following CV text extract as much information as possible into a JSON. "
        #     "Do not return anything else, only the JSON object with correctly filled in data.\n\n"
        #     "Input CV:\n\n"
        #     f"{cv_text}\n\n"
        #     "JSON schema:\n\n"
        #     f"{schema_json}"
        # )

        prompt = (
            "You are an information extraction system.\n"
            "Your task is to extract structured data from a CV.\n\n"

            "CRITICAL RULES:\n"
            "1. Only extract information explicitly supported by the CV text.\n"
            "2. Do NOT guess, infer, or complete missing information.\n"
            "3. If a field is not present, use null or an empty list (depending on schema type).\n"
            "4. Do NOT add explanations, comments, or extra keys.\n"
            "5. Do NOT return any text outside the JSON object.\n"
            "6. Preserve factual accuracy over completeness.\n\n"

            "EXTRACTION PRINCIPLES:\n"
            "- Extract facts only (not opinions or inferred seniority, salary, or skill level).\n"
            "- Dates must be in ISO 860 format.\n"
            "- Technologies, roles, and companies should be standardized.\n\n"

            "HANDLING UNCERTAINTY:\n"
            "- If something is ambiguous, set it to null or omit it (per schema rules).\n"
            "- Never fabricate missing values.\n\n"

            "OUTPUT FORMAT:\n"
            "- Output must be valid JSON only.\n"
            "- Must strictly follow the provided schema.\n\n"

            "INPUT CV:\n\n"
            f"{cv_text}\n\n"

            "JSON SCHEMA:\n\n"
            f"{schema_json}\n"
        )

        # Call the AI client with the response_model to ensure we get a validated object back
        # Note: ai_client.get_structured_response handles parsing the LLM output and validating it against CVExtraction.
        result = await self.ai_client.get_structured_response(
            prompt=prompt,
            response_model=CVExtraction
        )
        
        # Ensure we return a CVExtraction object even if ai_client returned a dict (though it shouldn't)
        if isinstance(result, dict):
            return CVExtraction.model_validate(result)
            
        return result
