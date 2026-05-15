from utils.ai_client import AIClient


class AnalysisExplainer:
    """
    Generates a natural-language explanation for deterministic analysis outputs.
    """

    def __init__(self, ai_client: AIClient):
        self.ai_client = ai_client

    async def createExplanation(
        self,
        structured_information_json: str,
        analysis_outputs_json: str,
    ) -> str:
        prompt = (
            "You are an expert Job Candidate evaluation system capable of clear "
            "explanations of its decisions.\n\n"
            "Based on the data in the input explain:\n"
            "Why candidate was awarded the seniority score.\n"
            "Why provided salary range was estimated.\n"
            "Strong points of the candidate.\n"
            "Weak points/gaps of the candidate.\n"
            "Provided concrete examples how the candidate can improve (gain the "
            "salary increase.\n\n"
            "Structure the response as a text with sections starting with these "
            "headings:\n\n"
            "Seniority Score\n"
            "Salary Estimation\n"
            "Candidate Strong Points\n"
            "Candidate Weak Points\n"
            "Improvement Suggestions \n\n"
            "Input:\n"
            "Extracted CV information, use only to fill in details:\n\n"
            f"{structured_information_json}\n\n"
            "Analysis outputs, base your explanations mainly on those:\n\n"
            f"{analysis_outputs_json}"
        )

        result = await self.ai_client.get_structured_response(prompt=prompt)

        if not isinstance(result, str):
            return str(result)

        return result
