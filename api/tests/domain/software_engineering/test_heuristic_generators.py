from domain.software_engineering.salary_estimation.salary_estimator import (
    SoftwareEngineerHeuristicSalaryEstimator,
)
from domain.software_engineering.seniority_scoring.seniority_scorer import (
    SoftwareEngineerHeuristicAnalyzer,
)
from domain.software_engineering.structure_extraction.models.models import CVExtraction

null = None
true = True
false = False

RAW_CV_JSON = {
  "candidate": {
    "first_name": "Luk\u00e1\u0161",
    "last_name": "Asn\u00edk",
    "email": "lukas.asnik@gmail.com",
    "phone": "+420 737 412 747",
    "location": {
      "country": "Czech Republic",
      "city": null
    },
    "linkedin_url": null,
    "github_url": null,
    "website_url": null
  },
  "detection": {
    "is_software_engineer_cv": true,
    "detected_role_family": "Software Engineer",
    "detected_specializations": [
      "Cloud Native",
      "DevOps",
      "Backend Development",
      "Mobile Development"
    ],
    "confidence": 0.95
  },
  "experience_summary": null,
  "employment_history": [
    {
      "employer": "Everpure (formerly Pure Storage)",
      "position": "Site Reliability Engineer / Platform Engineer",
      "employment_type": null,
      "start_date": "2026-03",
      "end_date": null,
      "is_current": true,
      "location": {
        "country": "Czech Republic",
        "city": "Prague"
      },
      "description": "Developing and operating Pure Storage Cloud Azure Native, the Azure-integrated high-performance block storage for the cloud. Provisioning regions, developing observability, writing internal tools.",
      "technologies": [
        "Azure",
        "Cloud Native",
        "Observability"
      ],
      "domains": [
        "Storage"
      ],
      "leadership": null
    },
    {
      "employer": "Warhorse Studios",
      "position": "Tools Developer in DevOps Team",
      "employment_type": null,
      "start_date": "2022-12",
      "end_date": "2026-01",
      "is_current": false,
      "location": {
        "country": "Czech Republic",
        "city": "Prague"
      },
      "description": "Developed and maintained tools to support development of Kingdom Come: Deliverance II and its DLCs. Maintained and implemented new features in C# WPF .NET 8 application used for distributing game and development data (from local shared storage or cloud) to developers while utilising Clean Architecture and SOLID principles to improve maintainability and testability. Developed a C# .NET Framework 4.7.2 console application retrieving production application crashes information from third-party crash reporting tool, processing and reporting them into the internal issue tracking system and storing them into PostgreSQL database utilising Entity Framework. Implemented C# .NET Framework 4.7.2 wrapper library around OpenTelemetry to be used in C# applications as well as in MAXScript for metrics and log tracking. Created several Python 3 scripts, e.g. a script regularly scraping internal issue tracking system data through the REST API and storing them into PostgreSQL database utilising SQLAlchemy. Designed, created and adjusted PostgreSQL tables and queries. Provided support and wrote documentation and guides for the developed tools. Modified used third-party tools to provide additional functionality, e.g. adjusting visual representation of builds in CI/CD monitoring tool (React). Maintained and extended internal web applications (HTML, CSS, JavaScript) along their PHP APIs.",
      "technologies": [
        "C#",
        ".NET 8",
        "WPF",
        "Python",
        "PostgreSQL",
        "Entity Framework",
        "SQLAlchemy",
        "OpenTelemetry",
        "React",
        "HTML",
        "CSS",
        "JavaScript",
        "PHP"
      ],
      "domains": [
        "Game Development Tools",
        "DevOps"
      ],
      "leadership": null
    },
    {
      "employer": "Self-employed",
      "position": "Flutter and Node.js Applications Developer, Content Creator, Community Manager",
      "employment_type": "freelance",
      "start_date": "2020-12",
      "end_date": "2022-12",
      "is_current": false,
      "location": {
        "country": "Czech Republic",
        "city": "Dobro\u010dovice"
      },
      "description": "Learned Dart language and Flutter, created several Flutter mobile apps using the Clean Architecture and modularized codebase through separate packages for different features such as in-app purchases, ads, privacy policy handling, UI and settings. Developed Node.js tools, improved communication skills and streamed gaming content, built and managed a Discord community with 500+ members, deployed and ran game servers.",
      "technologies": [
        "Dart",
        "Flutter",
        "Node.js"
      ],
      "domains": [
        "Mobile Development",
        "Web Backend",
        "Community Management"
      ],
      "leadership": null
    },
    {
      "employer": "ClearScore",
      "position": "Senior Android Developer",
      "employment_type": null,
      "start_date": "2017-09",
      "end_date": "2020-12",
      "is_current": false,
      "location": {
        "country": "United Kingdom",
        "city": "London"
      },
      "description": "Developed new features for the Android version of ClearScore app (more than 5 million installs to date) after leading the development of the first versions, designed architecture and led the development of changes required to release the application in multiple international markets. Participated in the hiring process (screening calls, tech task review, interviews) and experienced working with 7+ Android developers on a single code base within a rapidly growing company (30 to 160+ employees) with dynamically evolving structure and processes.",
      "technologies": [
        "Android",
        "Kotlin"
      ],
      "domains": [
        "Mobile Development"
      ],
      "leadership": null
    },
    {
      "employer": "nextap solutions",
      "position": "Co-founder, Lead Android Developer, Project Manager",
      "employment_type": null,
      "start_date": "2015-04",
      "end_date": "2018-10",
      "is_current": false,
      "location": {
        "country": "Czech Republic",
        "city": null
      },
      "description": "Co-founded and co-managed a small (5-15) software development company (hiring, contracts, management). Developed and managed multiple projects (Android, C#) for international clients (USA, UK, Germany).",
      "technologies": [
        "Android",
        "C#"
      ],
      "domains": [
        "Software Development",
        "Project Management"
      ],
      "leadership": null
    },
    {
      "employer": "Pixely Technologies (formerly Erteco Technologies)",
      "position": "Software Engineer",
      "employment_type": null,
      "start_date": "2014-03",
      "end_date": "2015-03",
      "is_current": false,
      "location": {
        "country": "Germany",
        "city": "Munich"
      },
      "description": "Worked on Android and C# WPF applications, developed point-of-sale software prototypes with integration of barcode and RFID readers.",
      "technologies": [
        "Android",
        "C# WPF"
      ],
      "domains": [],
      "leadership": null
    },
    {
      "employer": "Algorim",
      "position": "Software Engineer",
      "employment_type": null,
      "start_date": "2013-09",
      "end_date": "2014-08",
      "is_current": false,
      "location": {
        "country": "Czech Republic",
        "city": "Nymburk"
      },
      "description": "Developed Android applications (Java), implemented and maintained ASP .NET MVC applications (C#).",
      "technologies": [
        "Android",
        "Java",
        "ASP.NET MVC",
        "C#"
      ],
      "domains": [],
      "leadership": null
    }
  ],
  "education": [
    {
      "institution_name": "Charles University in Prague",
      "degree": "Bachelor\u2019s degree",
      "field_of_study": "Computer Science",
      "start_date": null,
      "end_date": "2014-12",
      "completed": true,
      "software_engineering_related": true
    }
  ],
  "certifications": [],
  "skills": [
    {
      "name": "C#",
      "category": "Programming Language",
      "years_experience": null
    },
    {
      "name": "Python",
      "category": "Programming Language",
      "years_experience": null
    },
    {
      "name": "Kotlin",
      "category": "Programming Language",
      "years_experience": null
    },
    {
      "name": "Dart",
      "category": "Programming Language",
      "years_experience": null
    },
    {
      "name": "Java",
      "category": "Programming Language",
      "years_experience": null
    },
    {
      "name": "JavaScript",
      "category": "Programming Language",
      "years_experience": null
    },
    {
      "name": "PHP",
      "category": "Programming Language",
      "years_experience": null
    },
    {
      "name": "C++",
      "category": "Programming Language",
      "years_experience": null
    },
    {
      "name": ".NET / .NET Framework",
      "category": "Framework/Technology",
      "years_experience": null
    },
    {
      "name": "WPF",
      "category": "Framework/Technology",
      "years_experience": null
    },
    {
      "name": "Flutter",
      "category": "Framework/Technology",
      "years_experience": null
    },
    {
      "name": "Android Framework",
      "category": "Framework/Technology",
      "years_experience": null
    },
    {
      "name": "Node.js",
      "category": "Framework/Technology",
      "years_experience": null
    },
    {
      "name": "Entity Framework",
      "category": "Framework/Technology",
      "years_experience": null
    },
    {
      "name": "SQLAlchemy 2",
      "category": "Framework/Technology",
      "years_experience": null
    },
    {
      "name": "OpenTelemetry",
      "category": "Framework/Technology",
      "years_experience": null
    },
    {
      "name": "RxJava",
      "category": "Framework/Technology",
      "years_experience": null
    },
    {
      "name": "PostgreSQL",
      "category": "Database",
      "years_experience": null
    }
  ],
  "languages": [],
  "projects": [],
  "leadership_experience": [],
  "product_experience": null,
  "signals": null,
  "metadata": null
}

def test_seniority_scorer_produces_expected_seniority_score():
    extraction = CVExtraction.model_validate(RAW_CV_JSON)

    scoring = SoftwareEngineerHeuristicAnalyzer().createSeniorityScoring(extraction)

    assert scoring.seniorityScore == 32
    assert scoring.breakdown.years_experience_score == 0
    assert scoring.breakdown.technical_breadth_score == 24
    assert scoring.breakdown.leadership_score == 0
    assert scoring.breakdown.education_score == 8
    assert scoring.breakdown.product_and_scale_score == 0
    assert scoring.breakdown.signals_score == 0
    assert scoring.strengths == [
        "Broad technical exposure across technologies and domains",
    ]
    assert scoring.gaps == [
        "Limited overall software engineering experience",
        "Limited engineering leadership or ownership signals",
        "Missing evidence of product lifecycle ownership",
        "Few public technical credibility signals",
        "Profile currently aligns more with junior or mid-level engineering",
    ]


def test_salary_estimator_produces_expected_salary_estimation():
    extraction = CVExtraction.model_validate(RAW_CV_JSON)
    seniority_scoring = SoftwareEngineerHeuristicAnalyzer().createSeniorityScoring(
        extraction
    )

    estimation = SoftwareEngineerHeuristicSalaryEstimator().createSalaryEstimation(
        extraction=extraction,
        seniority_scoring=seniority_scoring,
    )

    assert estimation.estimatedMidpoint == 212400
    assert estimation.lowerBound == 159300
    assert estimation.upperBound == 265500
    assert estimation.confidence == 0.75
    assert {component.name: component.contribution for component in estimation.components} == {
        "seniority": 38400,
        "years_experience": 0,
        "leadership": 0,
        "education": 8000,
        "technical_breadth": 40000,
        "high_value_skills": 36000,
        "top_company_experience": 40000,
        "product_and_scale": 0,
        "signals": 0,
    }
    assert estimation.reasoning == [
        "Overall seniority score: 32/100.",
        (
            "seniority: +38,400 CZK (Primary capability-driven seniority "
            "multiplier based on overall engineering profile.)"
        ),
        "education: +8,000 CZK (Formal software engineering education.)",
        (
            "technical_breadth: +40,000 CZK (24 technologies and 8 business "
            "domains detected.)"
        ),
        (
            "high_value_skills: +36,000 CZK (Detected high-market-value skills: "
            "['android', 'azure', 'c#', 'java', 'postgresql', 'python'])"
        ),
        (
            "top_company_experience: +40,000 CZK (Detected high-signal employers: "
            "['ClearScore', 'Warhorse Studios'])"
        ),
    ]
