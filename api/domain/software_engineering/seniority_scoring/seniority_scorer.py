from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Set

from pydantic import BaseModel, Field
from domain.software_engineering.structure_extraction.models.models import CVExtraction


# ============================================================
# SENIORITY SCORING HEURISTICS
# ============================================================
#
# Philosophy
# ----------
# This scoring system intentionally leans toward "capability-heavy"
# evaluation instead of "time-heavy" evaluation.
#
# Years of experience alone are NOT sufficient to achieve high
# seniority scores.
#
# The system rewards:
#
# - Breadth of technical exposure
# - Depth of engineering experience
# - Leadership and ownership
# - Product and production experience
# - Complexity and scale indicators
# - Public technical signals
#
# The system penalizes:
#
# - Lack of breadth
# - Lack of production ownership
# - Very low experience
# - Missing engineering leadership signals
#
#
# Seniority Bands
# ----------------
# 0-20   -> Junior / Entry-Level
# 21-40  -> Mid-Level
# 41-60  -> Senior Engineer
# 61-80  -> Staff / Principal
# 81-100 -> Exceptional / Architect / CTO-Level
#
#
# Design Principles
# -----------------
# 1. Every category has an explicit maximum cap.
# 2. High scores require multiple independent strong signals.
# 3. The system is intentionally tunable using constants.
# 4. The implementation favors readability and explainability.
# 5. Partial category scores are exposed for debugging/tuning.
#
#
# Important Note
# --------------
# This is a heuristic scoring system.
# It should NOT be treated as a definitive measure of engineering
# capability.
#
# It is designed for:
# - ranking
# - filtering
# - enrichment
# - coarse-grained seniority estimation
#
# It should ideally be combined with:
# - interview outcomes
# - coding assessments
# - portfolio review
# - recommendation systems
#
# ============================================================


# ============================================================
# OUTPUT MODELS
# ============================================================


class SeniorityScoreBreakdown(BaseModel):
    years_experience_score: int
    technical_breadth_score: int
    leadership_score: int
    education_score: int
    product_and_scale_score: int
    signals_score: int


class SeniorityScoring(BaseModel):
    seniorityScore: int = Field(ge=0, le=100)

    breakdown: SeniorityScoreBreakdown

    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)


# ============================================================
# INTERNAL SCORE DETAILS
# ============================================================


@dataclass(frozen=True)
class ScoreCaps:
    YEARS_EXPERIENCE_MAX = 25
    TECHNICAL_BREADTH_MAX = 25
    LEADERSHIP_MAX = 20
    EDUCATION_MAX = 10
    PRODUCT_AND_SCALE_MAX = 15
    SIGNALS_MAX = 5

    TOTAL_MAX = 100


# ============================================================
# TUNABLE THRESHOLDS
# ============================================================


@dataclass(frozen=True)
class Thresholds:
    # Years of experience thresholds
    YEARS_FOR_MAX_SCORE = 15.0
    SOFTWARE_ENGINEERING_YEARS_FOR_MAX = 12.0

    # Breadth thresholds
    MAX_TECHNOLOGIES_COUNTED = 20
    MAX_DOMAINS_COUNTED = 8
    MAX_LANGUAGES_COUNTED = 10

    # Leadership thresholds
    LEADERSHIP_YEARS_FOR_MAX = 8.0
    TEAM_SIZE_LARGE_THRESHOLD = 10

    # Project thresholds
    GREENFIELD_PROJECTS_FOR_MAX = 4

    # Skill thresholds
    SKILLS_FOR_MAX = 20


# ============================================================
# MAIN ANALYZER
# ============================================================


class SoftwareEngineerHeuristicAnalyzer:

    def createSeniorityScoring(
        self,
        extraction: CVExtraction,
    ) -> SeniorityScoring:

        years_score = self._calculate_years_experience_score(extraction)
        breadth_score = self._calculate_technical_breadth_score(extraction)
        leadership_score = self._calculate_leadership_score(extraction)
        education_score = self._calculate_education_score(extraction)
        product_score = self._calculate_product_and_scale_score(extraction)
        signals_score = self._calculate_signals_score(extraction)

        total_score = (
            years_score
            + breadth_score
            + leadership_score
            + education_score
            + product_score
            + signals_score
        )

        total_score = min(total_score, ScoreCaps.TOTAL_MAX)

        strengths = self._identify_strengths(
            extraction=extraction,
            total_score=total_score,
            leadership_score=leadership_score,
            breadth_score=breadth_score,
            product_score=product_score,
        )

        gaps = self._identify_gaps(
            extraction=extraction,
            total_score=total_score,
            leadership_score=leadership_score,
            breadth_score=breadth_score,
            years_score=years_score,
        )

        return SeniorityScoring(
            seniorityScore=total_score,
            breakdown=SeniorityScoreBreakdown(
                years_experience_score=years_score,
                technical_breadth_score=breadth_score,
                leadership_score=leadership_score,
                education_score=education_score,
                product_and_scale_score=product_score,
                signals_score=signals_score,
            ),
            strengths=strengths,
            gaps=gaps,
        )

    # ========================================================
    # YEARS OF EXPERIENCE
    # ========================================================

    def _calculate_years_experience_score(
        self,
        extraction: CVExtraction,
    ) -> int:

        summary = extraction.experience_summary

        if not summary:
            return 0

        # Weighted combination:
        #
        # - overall engineering years
        # - actual software engineering years
        #
        # We intentionally cap this aggressively so that
        # experience duration alone cannot dominate the score.

        total_years_ratio = min(
            summary.total_years_experience
            / Thresholds.YEARS_FOR_MAX_SCORE,
            1.0,
        )

        software_years_ratio = min(
            summary.software_engineering_years
            / Thresholds.SOFTWARE_ENGINEERING_YEARS_FOR_MAX,
            1.0,
        )

        weighted_ratio = (
            total_years_ratio * 0.4
            + software_years_ratio * 0.6
        )

        return round(
            weighted_ratio * ScoreCaps.YEARS_EXPERIENCE_MAX
        )

    # ========================================================
    # TECHNICAL BREADTH
    # ========================================================

    def _calculate_technical_breadth_score(
        self,
        extraction: CVExtraction,
    ) -> int:

        technologies = self._collect_unique_technologies(extraction)
        domains = self._collect_unique_domains(extraction)
        skills = self._collect_unique_skills(extraction)

        technologies_ratio = min(
            len(technologies)
            / Thresholds.MAX_TECHNOLOGIES_COUNTED,
            1.0,
        )

        domains_ratio = min(
            len(domains)
            / Thresholds.MAX_DOMAINS_COUNTED,
            1.0,
        )

        skills_ratio = min(
            len(skills)
            / Thresholds.SKILLS_FOR_MAX,
            1.0,
        )

        weighted_ratio = (
            technologies_ratio * 0.45
            + domains_ratio * 0.30
            + skills_ratio * 0.25
        )

        return round(
            weighted_ratio * ScoreCaps.TECHNICAL_BREADTH_MAX
        )

    # ========================================================
    # LEADERSHIP
    # ========================================================

    def _calculate_leadership_score(
        self,
        extraction: CVExtraction,
    ) -> int:

        score = 0

        summary = extraction.experience_summary

        if summary and summary.leadership_years > 0:
            years_ratio = min(
                summary.leadership_years
                / Thresholds.LEADERSHIP_YEARS_FOR_MAX,
                1.0,
            )

            score += round(years_ratio * 10)

        large_scope_count = 0
        managed_large_team = False

        for leadership in extraction.leadership_experience:

            if leadership.scope == "large":
                large_scope_count += 1

            if (
                leadership.team_size
                and leadership.team_size
                >= Thresholds.TEAM_SIZE_LARGE_THRESHOLD
            ):
                managed_large_team = True

        score += min(large_scope_count * 2, 6)

        if managed_large_team:
            score += 4

        return min(score, ScoreCaps.LEADERSHIP_MAX)

    # ========================================================
    # EDUCATION
    # ========================================================

    def _calculate_education_score(
        self,
        extraction: CVExtraction,
    ) -> int:

        if not extraction.education:
            return 0

        score = 0

        relevant_education = [
            e
            for e in extraction.education
            if e.software_engineering_related
        ]

        if relevant_education:
            score += 6

        completed_degrees = [
            e
            for e in relevant_education
            if e.completed
        ]

        if completed_degrees:
            score += 2

        advanced_degree_keywords = [
            "master",
            "msc",
            "phd",
            "doctor",
        ]

        has_advanced_degree = any(
            any(
                keyword in e.degree.lower()
                for keyword in advanced_degree_keywords
            )
            for e in completed_degrees
        )

        if has_advanced_degree:
            score += 2

        return min(score, ScoreCaps.EDUCATION_MAX)

    # ========================================================
    # PRODUCT / SCALE / OWNERSHIP
    # ========================================================

    def _calculate_product_and_scale_score(
        self,
        extraction: CVExtraction,
    ) -> int:

        score = 0

        product_experience = extraction.product_experience

        if product_experience:

            if product_experience.greenfield_products_built > 0:
                greenfield_ratio = min(
                    product_experience.greenfield_products_built
                    / Thresholds.GREENFIELD_PROJECTS_FOR_MAX,
                    1.0,
                )

                score += round(greenfield_ratio * 6)

            if product_experience.operated_production_systems:
                score += 5

            if product_experience.maintained_existing_products:
                score += 2

        signals = extraction.signals

        if signals and signals.high_scale_systems:
            score += 2

        return min(score, ScoreCaps.PRODUCT_AND_SCALE_MAX)

    # ========================================================
    # PUBLIC / COMMUNITY / SIGNALS
    # ========================================================

    def _calculate_signals_score(
        self,
        extraction: CVExtraction,
    ) -> int:

        signals = extraction.signals

        if not signals:
            return 0

        score = 0

        positive_signals = [
            signals.open_source_contributor,
            signals.public_speaker,
            signals.technical_blog,
            signals.startup_founder,
            signals.ai_experience,
        ]

        score += sum(1 for signal in positive_signals if signal)

        return min(score, ScoreCaps.SIGNALS_MAX)

    # ========================================================
    # STRENGTHS
    # ========================================================

    def _identify_strengths(
        self,
        extraction: CVExtraction,
        total_score: int,
        leadership_score: int,
        breadth_score: int,
        product_score: int,
    ) -> List[str]:

        strengths: List[str] = []

        if total_score >= 70:
            strengths.append(
                "Strong overall senior engineering profile"
            )

        if leadership_score >= 12:
            strengths.append(
                "Strong leadership and team ownership experience"
            )

        if breadth_score >= 18:
            strengths.append(
                "Broad technical exposure across technologies and domains"
            )

        if product_score >= 10:
            strengths.append(
                "Strong product ownership and production systems experience"
            )

        if extraction.signals:

            if extraction.signals.open_source_contributor:
                strengths.append(
                    "Open source contribution experience"
                )

            if extraction.signals.high_scale_systems:
                strengths.append(
                    "Experience with high-scale systems"
                )

            if extraction.signals.ai_experience:
                strengths.append(
                    "AI/ML engineering exposure"
                )

        return strengths

    # ========================================================
    # GAPS
    # ========================================================

    def _identify_gaps(
        self,
        extraction: CVExtraction,
        total_score: int,
        leadership_score: int,
        breadth_score: int,
        years_score: int,
    ) -> List[str]:

        gaps: List[str] = []

        if years_score < 10:
            gaps.append(
                "Limited overall software engineering experience"
            )

        if breadth_score < 10:
            gaps.append(
                "Limited technical breadth across technologies or domains"
            )

        if leadership_score < 6:
            gaps.append(
                "Limited engineering leadership or ownership signals"
            )

        if not extraction.product_experience:
            gaps.append(
                "Missing evidence of product lifecycle ownership"
            )

        if not extraction.signals:
            gaps.append(
                "Few public technical credibility signals"
            )

        if total_score < 40:
            gaps.append(
                "Profile currently aligns more with junior or mid-level engineering"
            )

        return gaps

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