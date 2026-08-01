"""Request/response schemas for POST /websites/generate — thin wrapper
around app.ai.website.generator + the existing WebsiteService."""

import uuid

from pydantic import BaseModel

from app.schemas.website import WebsiteRead


class WebsiteGenerateRequest(BaseModel):
    business_profile_id: uuid.UUID


class HeroOut(BaseModel):
    headline: str
    subhead: str
    cta: str


class SectionOut(BaseModel):
    type: str
    heading: str
    body: str


class SiteProductOut(BaseModel):
    name: str
    description: str
    price: float | None = None


class FAQItemOut(BaseModel):
    q: str
    a: str


class WebsiteGenerateResponse(BaseModel):
    website: WebsiteRead
    hero: HeroOut
    sections: list[SectionOut]
    about: str
    products: list[SiteProductOut]
    contact: str
    faq: list[FAQItemOut]
    seo_keywords: list[str]
