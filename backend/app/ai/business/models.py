"""The central Business Profile — Sakhi's "digital twin" of a business.

Every generation service downstream (brand, website, content calendar,
analytics, orchestrator) takes a BusinessProfile as input and conditions
its output on it. Nothing in app.ai should generate business-facing
content without one — that's what keeps output specific to this business
rather than generic.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Product(BaseModel):
    name: str
    description: str
    price: float | None = None
    category: str | None = None


class BusinessProfile(BaseModel):
    id: str
    name: str
    business_type: str
    products: list[Product] = Field(default_factory=list)
    target_audience: str
    location: str
    languages: list[str] = Field(default_factory=list)
    goals: list[str] = Field(default_factory=list)
    has_website: bool = False
    has_instagram: bool = False
    has_logo: bool = False
    brand_voice: str | None = None
