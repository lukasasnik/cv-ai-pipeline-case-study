from pydantic import BaseModel

from domain.software_engineering.improvements_recommendation.improvements_recommender import (
    SalaryImprovementRecommendation,
)
from domain.software_engineering.salary_estimation.salary_estimator import (
    SalaryEstimation,
)
from domain.software_engineering.seniority_scoring.seniority_scorer import (
    SeniorityScoring,
)


class AnalysisOutputs(BaseModel):
    seniority_scoring: SeniorityScoring
    salary_estimation: SalaryEstimation
    improvement_recommendation: SalaryImprovementRecommendation
