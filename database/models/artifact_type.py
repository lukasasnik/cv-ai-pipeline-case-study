import enum

class ArtifactType(enum.Enum):
    EXTRACTED_INPUT = "extracted_input"
    LLM_STRUCTURED_RAW = "llm_structured_raw"
    ANALYSIS_OUTPUTS = "analysis_outputs"
