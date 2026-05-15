from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from domain.software_engineering.salary_estimation.salary_estimator import (
    SalaryEstimation,
)
from domain.software_engineering.seniority_scoring.seniority_scorer import (
    SeniorityScoring,
)
from domain.software_engineering.structure_extraction.models.models import CVExtraction


# ============================================================
# GOAL: SALARY IMPROVEMENT RECOMMENDATION ENGINE
# ============================================================
#
# Core idea:
# ----------
# Salary growth in software engineering is not linear with skill growth.
#
# The biggest drivers are:
# - seniority bottlenecks (leadership, ownership)
# - market positioning (company tier, geography, remote access)
# - leverage skills (distributed systems, AI, scale)
# - visibility (signals: OSS, speaking)
#
# Years of experience alone has diminishing returns.
#
# This system identifies:
# - what is limiting salary upside
# - what unlocks next compensation band
# - what is realistically achievable within ~6–18 months
#
# Target:
# -------
# Default improvement target = +30% (configurable)
#
# ============================================================


# ============================================================
# CONSTANTS
# ============================================================

class RecommendationConstants:
    TARGET_INCREASE_RATIO = 1.30

    MAX_RECOMMENDATIONS = 8

    HIGH_IMPACT_THRESHOLD = 20
    MEDIUM_IMPACT_THRESHOLD = 10

    # caps for sanity (avoid unrealistic stacking)
    MAX_SINGLE_RECOMMENDATION_IMPACT = 25


# ============================================================
# OUTPUT MODELS
# ============================================================


class RecommendationPriority(str):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SalaryImprovementRecommendationItem(BaseModel):
    title: str
    priority: Literal["low", "medium", "high"]

    # estimated impact on monthly salary (%)
    estimated_salary_impact_percent: int

    # human-readable reasoning (for LLM consumption)
    reasoning: str


class SalaryImprovementRecommendation(BaseModel):
    target_increase_percent: int = 30

    realistically_achievable: bool

    current_estimated_salary: int
    target_estimated_salary: int

    gap_to_target_percent: float

    recommendations: List[SalaryImprovementRecommendationItem] = Field(
        default_factory=list
    )

    blockers: List[str] = Field(default_factory=list)

    strategic_summary: Optional[str] = None


# ============================================================
# MAIN RECOMMENDER
# ============================================================


class SoftwareEngineerHeuristicImprovementsRecommender:

    def createSalaryImprovementRecommendation(
        self,
        extraction: CVExtraction,
        seniority: SeniorityScoring,
        salary_estimation: SalaryEstimation,
    ) -> SalaryImprovementRecommendation:

        current = salary_estimation.estimatedMidpoint

        target = int(
            current * RecommendationConstants.TARGET_INCREASE_RATIO
        )

        gap_percent = (
            (target - current) / current
        ) * 100

        recommendations: List[SalaryImprovementRecommendationItem] = []

        recommendations.extend(
            self._analyze_leadership_gap(extraction, seniority)
        )

        recommendations.extend(
            self._analyze_technical_breadth_gap(extraction, seniority)
        )

        recommendations.extend(
            self._analyze_product_ownership_gap(extraction)
        )

        recommendations.extend(
            self._analyze_market_positioning_gap(extraction, seniority)
        )

        recommendations.extend(
            self._analyze_visibility_gap(extraction)
        )

        recommendations = sorted(
            recommendations,
            key=lambda r: r.estimated_salary_impact_percent,
            reverse=True,
        )[:RecommendationConstants.MAX_RECOMMENDATIONS]

        blockers = self._identify_blockers(extraction, seniority)

        realistically_achievable = gap_percent <= 60

        return SalaryImprovementRecommendation(
            target_increase_percent=30,
            realistically_achievable=realistically_achievable,
            current_estimated_salary=current,
            target_estimated_salary=target,
            gap_to_target_percent=round(gap_percent, 2),
            recommendations=recommendations,
            blockers=blockers,
            strategic_summary=self._build_summary(
                seniority, gap_percent
            ),
        )

    # ========================================================
    # LEADERSHIP GAP (highest leverage driver)
    # ========================================================

    def _analyze_leadership_gap(
        self,
        extraction: CVExtraction,
        seniority: SeniorityScoring,
    ) -> List[SalaryImprovementRecommendationItem]:

        items = []

        leadership_score = seniority.breakdown.leadership_score

        if leadership_score < 15:

            items.append(
                SalaryImprovementRecommendationItem(
                    title="Increase engineering leadership ownership",
                    priority="high",
                    estimated_salary_impact_percent=22,
                    reasoning=(
                        "Leadership is the strongest multiplier for "
                        "moving from senior → staff/principal roles. "
                        "Low leadership signals limit ceiling regardless of years."
                    ),
                )
            )

        if not extraction.leadership_experience:

            items.append(
                SalaryImprovementRecommendationItem(
                    title="Take ownership of team-level technical decisions",
                    priority="high",
                    estimated_salary_impact_percent=18,
                    reasoning=(
                        "No explicit leadership experience detected. "
                        "Even informal tech lead responsibilities significantly "
                        "increase market value."
                    ),
                )
            )

        return items

    # ========================================================
    # TECHNICAL BREADTH GAP
    # ========================================================

    def _analyze_technical_breadth_gap(
        self,
        extraction: CVExtraction,
        seniority: SeniorityScoring,
    ) -> List[SalaryImprovementRecommendationItem]:

        items = []

        if seniority.breakdown.technical_breadth_score < 15:

            items.append(
                SalaryImprovementRecommendationItem(
                    title="Expand system-level engineering exposure",
                    priority="high",
                    estimated_salary_impact_percent=18,
                    reasoning=(
                        "Limited breadth reduces eligibility for higher-paying "
                        "roles requiring distributed systems and architecture design."
                    ),
                )
            )

        technologies = {
            t.lower()
            for e in extraction.employment_history
            for t in e.technologies
        }

        if len(technologies) < 8:

            items.append(
                SalaryImprovementRecommendationItem(
                    title="Increase exposure to production-grade cloud and backend systems",
                    priority="medium",
                    estimated_salary_impact_percent=12,
                    reasoning=(
                        "Low technology diversity signals narrow specialization, "
                        "which limits senior/staff-level opportunities."
                    ),
                )
            )

        return items

    # ========================================================
    # PRODUCT OWNERSHIP GAP
    # ========================================================

    def _analyze_product_ownership_gap(
        self,
        extraction: CVExtraction,
    ) -> List[SalaryImprovementRecommendationItem]:

        items = []

        if (
            not extraction.product_experience
            or not extraction.product_experience.operated_production_systems
        ):

            items.append(
                SalaryImprovementRecommendationItem(
                    title="Gain production system ownership experience",
                    priority="high",
                    estimated_salary_impact_percent=20,
                    reasoning=(
                        "Operating production systems is a key differentiator "
                        "between senior and staff-level engineers."
                    ),
                )
            )

        return items

    # ========================================================
    # MARKET POSITIONING GAP
    # ========================================================

    def _analyze_market_positioning_gap(
        self,
        extraction: CVExtraction,
        seniority: SeniorityScoring,
    ) -> List[SalaryImprovementRecommendationItem]:

        items = []

        if seniority.seniorityScore >= 70:

            items.append(
                SalaryImprovementRecommendationItem(
                    title="Target higher-paying companies or international remote roles",
                    priority="high",
                    estimated_salary_impact_percent=30,
                    reasoning=(
                        "At high seniority levels, company selection "
                        "has greater impact than skill improvement alone."
                    ),
                )
            )

        return items

    # ========================================================
    # VISIBILITY / SIGNALS GAP
    # ========================================================

    def _analyze_visibility_gap(
        self,
        extraction: CVExtraction,
    ) -> List[SalaryImprovementRecommendationItem]:

        items = []

        signals = extraction.signals

        if not signals or not any([
            signals.open_source_contributor,
            signals.public_speaker,
            signals.technical_blog,
        ]):

            items.append(
                SalaryImprovementRecommendationItem(
                    title="Build public engineering visibility (OSS, writing, speaking)",
                    priority="medium",
                    estimated_salary_impact_percent=10,
                    reasoning=(
                        "Public signals increase inbound opportunities "
                        "and access to higher-paying roles."
                    ),
                )
            )

        return items

    # ========================================================
    # BLOCKERS
    # ========================================================

    def _identify_blockers(
        self,
        extraction: CVExtraction,
        seniority: SeniorityScoring,
    ) -> List[str]:

        blockers = []

        if seniority.seniorityScore < 40:
            blockers.append(
                "Current profile aligns with junior/mid-level ceiling"
            )

        if (
            not extraction.product_experience
            or not extraction.product_experience.operated_production_systems
        ):
            blockers.append(
                "No production ownership experience detected"
            )

        if seniority.breakdown.leadership_score < 10:
            blockers.append(
                "Insufficient leadership signals for staff-level roles"
            )

        return blockers

    # ========================================================
    # SUMMARY
    # ========================================================

    def _build_summary(
        self,
        seniority: SeniorityScoring,
        gap_percent: float,
    ) -> str:

        if gap_percent > 60:
            return (
                "30% salary increase is achievable but likely requires "
                "a company change or role upgrade rather than incremental skill growth."
            )

        if seniority.seniorityScore >= 70:
            return (
                "Primary leverage is market positioning rather than technical upskilling."
            )

        return (
            "Salary growth is primarily driven by leadership, production ownership, "
            "and technical breadth improvements."
        )
