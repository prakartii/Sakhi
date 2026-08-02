"""GET /public/websites/{slug} — unauthenticated public access to a
published website's content, for the frontend's public preview route.
This represents the BUSINESS's own generated site, styled in its own
brand, not a page inside the Sakhi dashboard — deliberately a separate
router/prefix from the authenticated /websites endpoints, not just a
different route on the same one.

Read-only, no side effects. 404s for anything not found, not published,
or without content yet — an unpublished/empty site has no public
existence, by design (see websites.published and websites.content).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.website.models import WebsiteSpec
from app.api.deps import get_db_session
from app.models.enums import BrandAssetStatus
from app.repositories.brand_asset import BrandAssetRepository
from app.repositories.website import WebsiteRepository
from app.schemas.website_public import PublicBrandOut, PublicWebsiteResponse

router = APIRouter()


@router.get(
    "/{slug}",
    response_model=PublicWebsiteResponse,
    summary="Public, unauthenticated view of a published website",
    responses={404: {"description": "No published website with this slug"}},
)
async def get_public_website(
    slug: str,
    db: AsyncSession = Depends(get_db_session),
) -> PublicWebsiteResponse:
    websites = WebsiteRepository(db)
    items, _ = await websites.get_all(
        filters={"preview_slug": slug, "published": True}, limit=1
    )
    website = items[0] if items else None
    if website is None or website.content is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Website not found.")

    brand_assets = BrandAssetRepository(db)
    brands, _ = await brand_assets.list_by_business_profile(
        website.business_profile_id, status=BrandAssetStatus.DRAFT, limit=1
    )
    if not brands:
        brands, _ = await brand_assets.list_by_business_profile(
            website.business_profile_id, limit=1
        )
    brand = brands[0] if brands else None

    return PublicWebsiteResponse(
        website_name=website.website_name,
        content=WebsiteSpec.model_validate(website.content),
        images=website.images or {},
        brand=(
            PublicBrandOut(
                primary_color=brand.primary_color,
                secondary_color=brand.secondary_color,
                typography=brand.typography,
            )
            if brand is not None
            else None
        ),
    )
