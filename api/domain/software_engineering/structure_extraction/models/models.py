from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class Location(BaseModel):
    country: str
    city: Optional[str] = None


class Leadership(BaseModel):
    has_leadership: bool
    team_size: Optional[int] = None
    scope: Optional[Literal["small", "medium", "large"]] = None


class Candidate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    location: Optional[Location] = None

    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    website_url: Optional[str] = None


class Detection(BaseModel):
    is_software_engineer_cv: bool
    detected_role_family: str
    detected_specializations: List[str]
    confidence: float = Field(ge=0.0, le=1.0)


class ExperienceSummary(BaseModel):
    total_years_experience: float
    software_engineering_years: float
    leadership_years: float
    management_years: float

    startup_experience: bool
    enterprise_experience: bool
    remote_experience: bool
    freelance_experience: bool


class EmploymentHistory(BaseModel):
    employer: str
    position: str
    employment_type: Optional[Literal["full_time", "part_time", "contract", "freelance"]] = None

    start_date: str  # YYYY or YYYY-MM
    end_date: Optional[str] = None
    is_current: bool = False

    location: Optional[Location] = None

    description: Optional[str] = None

    technologies: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)

    leadership: Optional[Leadership] = None


class Education(BaseModel):
    institution_name: str
    degree: str
    field_of_study: str

    start_date: Optional[str] = None  # YYYY
    end_date: Optional[str] = None    # YYYY

    completed: bool
    software_engineering_related: bool


class Certification(BaseModel):
    name: str
    issuer: Optional[str] = None

    issued_date: str  # YYYY
    expiration_date: Optional[str] = None


class Skill(BaseModel):
    name: str
    category: str
    years_experience: Optional[float] = None


class Language(BaseModel):
    name: str
    level: Literal["beginner", "intermediate", "advanced", "fluent", "native"]


class Project(BaseModel):
    id: Optional[str] = None

    name: str
    role: Optional[str] = None

    start_date: Optional[str] = None
    end_date: Optional[str] = None

    technologies: List[str] = Field(default_factory=list)

    greenfield: Optional[bool] = None
    production_scale: Optional[Literal["small", "medium", "large"]] = None


class LeadershipExperience(BaseModel):
    years: float
    scope: Literal["small", "medium", "large"]
    team_size: Optional[int] = None
    type: str


class ProductExperience(BaseModel):
    greenfield_products_built: int
    maintained_existing_products: bool
    operated_production_systems: bool


class Signals(BaseModel):
    open_source_contributor: Optional[bool] = None
    public_speaker: Optional[bool] = None
    technical_blog: Optional[bool] = None
    startup_founder: Optional[bool] = None
    high_scale_systems: Optional[bool] = None
    ai_experience: Optional[bool] = None


class CVExtraction(BaseModel):
    schema_version: str

    candidate: Candidate
    detection: Detection

    experience_summary: Optional[ExperienceSummary] = None

    employment_history: List[EmploymentHistory] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    skills: List[Skill] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)
    projects: List[Project] = Field(default_factory=list)
    leadership_experience: List[LeadershipExperience] = Field(default_factory=list)

    product_experience: Optional[ProductExperience] = None
    signals: Optional[Signals] = None

    metadata: Optional[dict] = None