from typing import Literal, Optional

from pydantic import BaseModel, Field

Verdict = Literal["likely_scam", "suspicious", "likely_safe"]
Situation = Literal["not_responded", "paid", "shared_info"]


class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)
    language: str = "en"
    situation: Situation = "not_responded"


class Reason(BaseModel):
    signal: str
    text: str
    weight: float
    source_url: Optional[str] = None
    source_title: Optional[str] = None


class Source(BaseModel):
    title: str
    url: str
    snippet: Optional[str] = None


class Entities(BaseModel):
    claimed_agency: Optional[str] = None
    phone_numbers: list[str] = []
    urls: list[str] = []
    emails: list[str] = []
    payment_methods: list[str] = []
    amounts: list[str] = []


class AnalyzeResponse(BaseModel):
    verdict: Verdict
    risk_score: float
    category: str
    category_label: str
    category_probs: dict[str, float]
    summary: str
    explanation: str
    reasons: list[Reason]
    tactics: list[str]
    entities: Entities
    actions: list[str]
    report_text: Optional[str] = None
    sources: list[Source]
    language: str
    llm_used: bool
    redacted_text: str
    extracted_text: Optional[str] = None
    latency_ms: int


class Example(BaseModel):
    title: str
    text: str
    label: str
