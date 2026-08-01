"""The Business Profile: Sakhi's central "digital twin" object, and
parse_onboarding(), which builds one from a free-text/voice description.
Every generation service downstream (brand, website, content, analytics,
orchestrator) takes a BusinessProfile as input.
"""

from app.ai.business.models import BusinessProfile, Product
from app.ai.business.onboarding import parse_onboarding

__all__ = ["BusinessProfile", "Product", "parse_onboarding"]
