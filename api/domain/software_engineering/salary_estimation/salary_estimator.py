from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Set

from pydantic import BaseModel, Field

from domain.software_engineering.seniority_scoring.seniority_scorer import (
    SeniorityScoring,
)
from domain.software_engineering.structure_extraction.models.models import CVExtraction


# ============================================================
# SOFTWARE ENGINEER HEURISTIC SALARY ESTIMATION
# ============================================================
#
# Philosophy
# ----------
# This estimator produces a heuristic salary range for software
# engineers in the Czech Republic (2026 market conditions).
#
# The salary represents:
#
# - gross monthly compensation in CZK
# - full-time employee equivalent (FTE)
# - Prague/Brno/remote-CZ-oriented software engineering market
#
#
# The estimation intentionally emphasizes:
#
# - demonstrated capability
# - engineering seniority
# - ownership
# - technical breadth
# - leadership
# - production/system complexity
#
# rather than simply:
#
# - years worked
# - formal education
#
#
# The system is NOT intended to:
#
# - replace compensation benchmarking
# - estimate FAANG-level outliers precisely
# - estimate contracting/freelance rates
# - estimate startup equity compensation
#
#
# Design Principles
# -----------------
# 1. Salary is built incrementally from explainable components.
# 2. Every category has explicit caps.
# 3. Strong candidates require multiple independent signals.
# 4. The system is intentionally tunable through constants.
# 5. Output contains detailed reasoning and breakdowns.
#
#
# Important Note
# --------------
# This is intentionally:
#
# - conservative
# - explainable
# - deterministic
#
# instead of:
#
# - opaque
# - ML-based
# - overfit to current market spikes
#
#
# Salary Reality Reference (CZ 2026)
# ----------------------------------
#
# Approximate market bands:
#
# 50k-80k     -> junior
# 80k-130k    -> mid-level
# 130k-180k   -> senior
# 180k-260k   -> staff/principal
# 260k+       -> exceptional niche/high-scale/lead roles
#
#
# ============================================================


# ============================================================
# OUTPUT MODELS
# ============================================================


class SalaryComponent(BaseModel):
    name: str
    contribution: int
    explanation: str


class SalaryEstimation(BaseModel):
    lowerBound: int
    upperBound: int

    estimatedMidpoint: int

    components: List[SalaryComponent] = Field(default_factory=list)

    reasoning: List[str] = Field(default_factory=list)

    confidence: float = Field(ge=0.0, le=1.0)


# ============================================================
# TUNABLE CONSTANTS
# ============================================================


@dataclass(frozen=True)
class SalaryConstants:

    # --------------------------------------------------------
    # Baseline
    # --------------------------------------------------------

    BASE_SALARY = 50000

    # --------------------------------------------------------
    # Hard caps
    # --------------------------------------------------------

    SENIORITY_MAX_CONTRIBUTION = 120000
    YEARS_MAX_CONTRIBUTION = 30000
    LEADERSHIP_MAX_CONTRIBUTION = 50000
    EDUCATION_MAX_CONTRIBUTION = 15000
    TECH_BREADTH_MAX_CONTRIBUTION = 40000
    HIGH_VALUE_SKILLS_MAX_CONTRIBUTION = 60000
    TOP_COMPANY_MAX_CONTRIBUTION = 40000
    PRODUCT_SCALE_MAX_CONTRIBUTION = 50000
    SIGNALS_MAX_CONTRIBUTION = 15000

    # --------------------------------------------------------
    # Thresholds
    # --------------------------------------------------------

    YEARS_FOR_MAX_SCORE = 15.0
    LEADERSHIP_YEARS_FOR_MAX = 8.0

    MAX_TECHNOLOGIES_COUNTED = 20
    MAX_DOMAINS_COUNTED = 8

    # --------------------------------------------------------
    # Salary spread
    # --------------------------------------------------------

    DEFAULT_RANGE_PERCENT = 0.15
    LOW_CONFIDENCE_RANGE_PERCENT = 0.25


# ============================================================
# HIGH VALUE SKILLS
# ============================================================


HIGH_VALUE_SKILLS = {
    # Backend / architecture
    "kubernetes",
    "distributed systems",
    "microservices",
    "event sourcing",
    "grpc",
    "high availability",

    # Cloud
    "aws",
    "azure",
    "gcp",
    "terraform",

    # Data / AI
    "machine learning",
    "ai",
    "llm",
    "rag",
    "vector database",

    # Performance / scale
    "postgresql",
    "redis",
    "kafka",

    # Mobile
    "android",
    "ios",

    # Strong backend stacks
    "c#",
    ".net",
    "java",
    "go",
    "rust",
    "python",
}


# ============================================================
# TOP COMPANIES / HIGH SIGNAL EMPLOYERS
# ============================================================


TOP_COMPANY_KEYWORDS = {
    "google",
    "meta",
    "microsoft",
    "amazon",
    "apple",
    "netflix",
    "reddit",
    "oracle",
    "sap",
    "red hat",
    "jetbrains",
    "atlassian",
    "rockstar",
    "warhorse",
    "clearscore",
}


# ============================================================
# MAIN ESTIMATOR
# ============================================================


class SoftwareEngineerHeuristicSalaryEstimator:

    def createSalaryEstimation(
        self,
        extraction: CVExtraction,
        seniority_scoring: SeniorityScoring,
    ) -> SalaryEstimation:

        components: List[SalaryComponent] = []

        base_salary = SalaryConstants.BASE_SALARY

        seniority_component = self._calculate_seniority_component(
            seniority_scoring
        )

        years_component = self._calculate_years_component(
            extraction
        )

        leadership_component = self._calculate_leadership_component(
            extraction
        )

        education_component = self._calculate_education_component(
            extraction
        )

        tech_component = self._calculate_technical_breadth_component(
            extraction
        )

        high_value_skills_component = (
            self._calculate_high_value_skills_component(
                extraction
            )
        )

        top_company_component = (
            self._calculate_top_company_component(
                extraction
            )
        )

        product_scale_component = (
            self._calculate_product_scale_component(
                extraction
            )
        )

        signals_component = self._calculate_signals_component(
            extraction
        )

        components.extend([
            seniority_component,
            years_component,
            leadership_component,
            education_component,
            tech_component,
            high_value_skills_component,
            top_company_component,
            product_scale_component,
            signals_component,
        ])

        estimated_midpoint = (
            base_salary
            + sum(component.contribution for component in components)
        )

        confidence = self._calculate_confidence(
            extraction=extraction,
            seniority_scoring=seniority_scoring,
        )

        lower_bound, upper_bound = self._calculate_range(
            estimated_midpoint=estimated_midpoint,
            confidence=confidence,
        )

        reasoning = self._build_reasoning(
            seniority_scoring=seniority_scoring,
            components=components,
        )

        return SalaryEstimation(
            lowerBound=lower_bound,
            upperBound=upper_bound,
            estimatedMidpoint=estimated_midpoint,
            components=components,
            reasoning=reasoning,
            confidence=confidence,
        )

    # ========================================================
    # SENIORITY
    # ========================================================

    def _calculate_seniority_component(
        self,
        seniority_scoring: SeniorityScoring,
    ) -> SalaryComponent:

        ratio = seniority_scoring.seniorityScore / 100.0

        contribution = int(
            ratio * SalaryConstants.SENIORITY_MAX_CONTRIBUTION
        )

        return SalaryComponent(
            name="seniority",
            contribution=contribution,
            explanation=(
                "Primary capability-driven seniority multiplier "
                "based on overall engineering profile."
            ),
        )

    # ========================================================
    # YEARS OF EXPERIENCE
    # ========================================================

    def _calculate_years_component(
        self,
        extraction: CVExtraction,
    ) -> SalaryComponent:

        if not extraction.experience_summary:
            return SalaryComponent(
                name="years_experience",
                contribution=0,
                explanation="No experience summary available.",
            )

        years = (
            extraction
            .experience_summary
            .software_engineering_years
        )

        ratio = min(
            years / SalaryConstants.YEARS_FOR_MAX_SCORE,
            1.0,
        )

        contribution = int(
            ratio * SalaryConstants.YEARS_MAX_CONTRIBUTION
        )

        return SalaryComponent(
            name="years_experience",
            contribution=contribution,
            explanation=(
                f"{years:.1f} years of software engineering "
                f"experience."
            ),
        )

    # ========================================================
    # LEADERSHIP
    # ========================================================

    def _calculate_leadership_component(
        self,
        extraction: CVExtraction,
    ) -> SalaryComponent:

        score = 0

        summary = extraction.experience_summary

        if summary:

            leadership_ratio = min(
                summary.leadership_years
                / SalaryConstants.LEADERSHIP_YEARS_FOR_MAX,
                1.0,
            )

            score += int(
                leadership_ratio * 35000
            )

        large_team_bonus = 0

        for leadership in extraction.leadership_experience:

            if leadership.scope == "large":
                large_team_bonus += 5000

            if leadership.team_size and leadership.team_size >= 10:
                large_team_bonus += 5000

        score += min(large_team_bonus, 15000)

        score = min(
            score,
            SalaryConstants.LEADERSHIP_MAX_CONTRIBUTION,
        )

        return SalaryComponent(
            name="leadership",
            contribution=score,
            explanation=(
                "Engineering leadership, organizational scope, "
                "and team ownership."
            ),
        )

    # ========================================================
    # EDUCATION
    # ========================================================

    def _calculate_education_component(
        self,
        extraction: CVExtraction,
    ) -> SalaryComponent:

        score = 0

        relevant_education = [
            education
            for education in extraction.education
            if education.software_engineering_related
        ]

        if relevant_education:
            score += 8000

        advanced_degree_keywords = [
            "master",
            "msc",
            "phd",
            "doctor",
        ]

        has_advanced_degree = any(
            any(
                keyword in education.degree.lower()
                for keyword in advanced_degree_keywords
            )
            for education in relevant_education
        )

        if has_advanced_degree:
            score += 7000

        score = min(
            score,
            SalaryConstants.EDUCATION_MAX_CONTRIBUTION,
        )

        return SalaryComponent(
            name="education",
            contribution=score,
            explanation=(
                "Formal software engineering education."
            ),
        )

    # ========================================================
    # TECHNICAL BREADTH
    # ========================================================

    def _calculate_technical_breadth_component(
        self,
        extraction: CVExtraction,
    ) -> SalaryComponent:

        technologies = self._collect_unique_technologies(
            extraction
        )

        domains = self._collect_unique_domains(
            extraction
        )

        technologies_ratio = min(
            len(technologies)
            / SalaryConstants.MAX_TECHNOLOGIES_COUNTED,
            1.0,
        )

        domains_ratio = min(
            len(domains)
            / SalaryConstants.MAX_DOMAINS_COUNTED,
            1.0,
        )

        weighted_ratio = (
            technologies_ratio * 0.7
            + domains_ratio * 0.3
        )

        contribution = int(
            weighted_ratio
            * SalaryConstants.TECH_BREADTH_MAX_CONTRIBUTION
        )

        return SalaryComponent(
            name="technical_breadth",
            contribution=contribution,
            explanation=(
                f"{len(technologies)} technologies and "
                f"{len(domains)} business domains detected."
            ),
        )

    # ========================================================
    # HIGH VALUE SKILLS
    # ========================================================

    def _calculate_high_value_skills_component(
        self,
        extraction: CVExtraction,
    ) -> SalaryComponent:

        technologies = self._collect_unique_technologies(
            extraction
        )

        skills = self._collect_unique_skills(
            extraction
        )

        normalized = {
            value.lower().strip()
            for value in technologies.union(skills)
        }

        matched_skills = normalized.intersection(
            HIGH_VALUE_SKILLS
        )

        contribution = min(
            len(matched_skills) * 6000,
            SalaryConstants.HIGH_VALUE_SKILLS_MAX_CONTRIBUTION,
        )

        return SalaryComponent(
            name="high_value_skills",
            contribution=contribution,
            explanation=(
                f"Detected high-market-value skills: "
                f"{sorted(matched_skills)}"
            ),
        )

    # ========================================================
    # TOP COMPANY EXPERIENCE
    # ========================================================

    def _calculate_top_company_component(
        self,
        extraction: CVExtraction,
    ) -> SalaryComponent:

        matched_companies = []

        for employment in extraction.employment_history:

            employer = employment.employer.lower()

            for keyword in TOP_COMPANY_KEYWORDS:

                if keyword in employer:
                    matched_companies.append(
                        employment.employer
                    )

        contribution = min(
            len(set(matched_companies)) * 20000,
            SalaryConstants.TOP_COMPANY_MAX_CONTRIBUTION,
        )

        return SalaryComponent(
            name="top_company_experience",
            contribution=contribution,
            explanation=(
                f"Detected high-signal employers: "
                f"{sorted(set(matched_companies))}"
            ),
        )

    # ========================================================
    # PRODUCT / SCALE
    # ========================================================

    def _calculate_product_scale_component(
        self,
        extraction: CVExtraction,
    ) -> SalaryComponent:

        score = 0

        if extraction.product_experience:

            if (
                extraction
                .product_experience
                .greenfield_products_built
                > 0
            ):
                score += 20000

            if (
                extraction
                .product_experience
                .operated_production_systems
            ):
                score += 15000

            if (
                extraction
                .product_experience
                .maintained_existing_products
            ):
                score += 5000

        if (
            extraction.signals
            and extraction.signals.high_scale_systems
        ):
            score += 10000

        for project in extraction.projects:

            if project.production_scale == "large":
                score += 5000

        score = min(
            score,
            SalaryConstants.PRODUCT_SCALE_MAX_CONTRIBUTION,
        )

        return SalaryComponent(
            name="product_and_scale",
            contribution=score,
            explanation=(
                "Production ownership and system scale."
            ),
        )

    # ========================================================
    # SIGNALS
    # ========================================================

    def _calculate_signals_component(
        self,
        extraction: CVExtraction,
    ) -> SalaryComponent:

        if not extraction.signals:
            return SalaryComponent(
                name="signals",
                contribution=0,
                explanation="No public engineering signals.",
            )

        score = 0

        signals = extraction.signals

        if signals.open_source_contributor:
            score += 5000

        if signals.public_speaker:
            score += 3000

        if signals.technical_blog:
            score += 2000

        if signals.startup_founder:
            score += 3000

        if signals.ai_experience:
            score += 2000

        score = min(
            score,
            SalaryConstants.SIGNALS_MAX_CONTRIBUTION,
        )

        return SalaryComponent(
            name="signals",
            contribution=score,
            explanation=(
                "Public technical credibility and ecosystem signals."
            ),
        )

    # ========================================================
    # CONFIDENCE
    # ========================================================

    def _calculate_confidence(
        self,
        extraction: CVExtraction,
        seniority_scoring: SeniorityScoring,
    ) -> float:

        confidence = 0.5

        if extraction.experience_summary:
            confidence += 0.15

        if extraction.skills:
            confidence += 0.10

        if extraction.employment_history:
            confidence += 0.10

        if extraction.projects:
            confidence += 0.05

        if extraction.product_experience:
            confidence += 0.05

        confidence += (
            extraction.detection.confidence * 0.05
        )

        return round(min(confidence, 1.0), 2)

    # ========================================================
    # RANGE CALCULATION
    # ========================================================

    def _calculate_range(
        self,
        estimated_midpoint: int,
        confidence: float,
    ) -> tuple[int, int]:

        if confidence >= 0.8:
            spread_percent = (
                SalaryConstants.DEFAULT_RANGE_PERCENT
            )
        else:
            spread_percent = (
                SalaryConstants.LOW_CONFIDENCE_RANGE_PERCENT
            )

        spread = int(
            estimated_midpoint * spread_percent
        )

        return (
            estimated_midpoint - spread,
            estimated_midpoint + spread,
        )

    # ========================================================
    # REASONING
    # ========================================================

    def _build_reasoning(
        self,
        seniority_scoring: SeniorityScoring,
        components: List[SalaryComponent],
    ) -> List[str]:

        reasoning: List[str] = []

        reasoning.append(
            f"Overall seniority score: "
            f"{seniority_scoring.seniorityScore}/100."
        )

        for component in components:

            if component.contribution <= 0:
                continue

            reasoning.append(
                f"{component.name}: "
                f"+{component.contribution:,} CZK "
                f"({component.explanation})"
            )

        return reasoning

    # ========================================================
    # HELPERS
    # ========================================================

    def _collect_unique_technologies(
        self,
        extraction: CVExtraction,
    ) -> Set[str]:

        technologies: Set[str] = set()

        for employment in extraction.employment_history:
            technologies.update(
                tech.lower().strip()
                for tech in employment.technologies
            )

        for project in extraction.projects:
            technologies.update(
                tech.lower().strip()
                for tech in project.technologies
            )

        return technologies

    def _collect_unique_domains(
        self,
        extraction: CVExtraction,
    ) -> Set[str]:

        domains: Set[str] = set()

        for employment in extraction.employment_history:
            domains.update(
                domain.lower().strip()
                for domain in employment.domains
            )

        return domains

    def _collect_unique_skills(
        self,
        extraction: CVExtraction,
    ) -> Set[str]:

        return {
            skill.name.lower().strip()
            for skill in extraction.skills
        }
