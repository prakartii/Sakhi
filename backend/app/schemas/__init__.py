"""Pydantic v2 request/response models (DTOs).

Kept separate from app.models (SQLAlchemy ORM classes) on purpose: schemas
describe the shape of data crossing the API boundary, models describe how
it's stored — the two evolve independently. Empty until endpoints exist.
"""
