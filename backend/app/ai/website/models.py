"""Pydantic schema for Website Studio output — structured pages the
frontend renders directly. Generated from a BusinessProfile + BrandKit
together (see generator.py), so copy is grounded in the actual business
and sounds like the brand voice already established, not generic filler.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Hero(BaseModel):
    headline: str
    subhead: str
    cta: str


class Section(BaseModel):
    type: str = Field(..., description="e.g. 'features', 'story', 'testimonial', 'process'")
    heading: str
    body: str


class Landing(BaseModel):
    hero: Hero
    sections: list[Section] = Field(default_factory=list)


class About(BaseModel):
    body: str


class SiteProduct(BaseModel):
    name: str
    description: str
    price: float | None = None


class Contact(BaseModel):
    body: str = Field(..., description="Invitation-to-reach-out copy; contact details themselves live on the profile.")


class FAQItem(BaseModel):
    q: str
    a: str


class Pages(BaseModel):
    landing: Landing
    about: About
    products: list[SiteProduct] = Field(default_factory=list)
    contact: Contact
    faq: list[FAQItem] = Field(default_factory=list)


class SEO(BaseModel):
    title: str
    description: str
    keywords: list[str] = Field(default_factory=list)


class WebsiteSpec(BaseModel):
    pages: Pages
    seo: SEO
