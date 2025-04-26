from typing import Optional

from pydantic import BaseModel, Field
from pydantic_core import Url

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.107 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.107 Safari/537.36 Edg/123.0.2420.65",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.107 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.107 Mobile Safari/537.36",
    "Mozilla/5.0 (Android 13; Mobile; rv:124.0) Gecko/124.0 Firefox/124.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]


criteria_handler = {
    "linkedin": {
        "Seniority level": "level",
        "Employment type": "type",
        "Job function": "function",
        "Industries": "industry",
    },
    "info_empleo": {
        "level": "level",
        "type": "type",
        "industry": "industry",
        "function": "function",
    },
}


class ScrapperSelectionError(Exception):
    """Exception raised when an invalid scrapper is selected."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"ScrapperSelectionError: {self.message}"


class JobOfferCriteria(BaseModel):
    profesional_level: Optional[str] = Field(
        None, description="Role of the candidate in the job offer"
    )
    function: Optional[str] = Field(
        None, description="Function of the candidate in the job offer"
    )
    worktime_type: Optional[str] = Field(
        None, description="Worktime type of the job offer (e.g., full-time, part-time)"
    )
    site_type: Optional[str] = Field(
        None, description="Site type of the job offer (e.g., remote, on-site)"
    )
    contract_type: Optional[str] = Field(
        None, description="Contract type of the job offer (e.g., permanent, temporary)"
    )
    salary: Optional[str] = Field(
        None, description="Salary offered for the job position"
    )


class CompanyInfo(BaseModel):
    company_name: Optional[str] = Field(None, description="Name of the company")
    company_location: Optional[str] = Field(None, description="Location of the company")
    company_website: Optional[Url] = Field(None, description="Website of the company")


class JobOffer(BaseModel):
    title: str = Field(..., description="Title of the job offer")
    criteria: JobOfferCriteria = Field(..., description="Criteria of the job offer")
    company_info: CompanyInfo = Field(..., description="Information about the company")
    url: Url = Field(..., description="URL of the job offer")
    description: Optional[str] = Field(None, description="Description of the job offer")
