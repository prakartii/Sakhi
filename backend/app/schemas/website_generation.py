"""Request/response schemas for POST /websites/generate and the Website
Studio chat endpoints — thin wrappers around app.ai.website + the
existing WebsiteService."""

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field

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


class WebsiteImagesOut(BaseModel):
    hero_url: str | None = None


class WebsiteChatRequest(BaseModel):
    business_profile_id: uuid.UUID
    message: Annotated[str, Field(min_length=1, max_length=2000)]


class ChatMessageOut(BaseModel):
    role: str
    content: str
    created_at: datetime


class WebsiteChatHistoryResponse(BaseModel):
    messages: list[ChatMessageOut]


class WebsiteChatResponse(BaseModel):
    website: WebsiteRead
    reply: str
    hero: HeroOut
    sections: list[SectionOut]
    about: str
    products: list[SiteProductOut]
    contact: str
    faq: list[FAQItemOut]
    seo_keywords: list[str]
    images: WebsiteImagesOut
    preview_path: str | None = Field(
        default=None, description="e.g. '/site/<slug>' — only set once the website is published."
    )
