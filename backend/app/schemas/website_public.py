"""Response schema for GET /public/websites/{slug} — unauthenticated."""

from pydantic import BaseModel

from app.ai.website.models import WebsiteSpec


class PublicBrandOut(BaseModel):
    primary_color: str | None = None
    secondary_color: str | None = None
    typography: str | None = None


class PublicWebsiteResponse(BaseModel):
    website_name: str
    content: WebsiteSpec
    images: dict[str, str] = {}
    brand: PublicBrandOut | None = None
