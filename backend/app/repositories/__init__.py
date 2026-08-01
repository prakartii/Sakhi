"""Data-access layer: one repository per aggregate, wrapping the
SQLAlchemy queries a service needs. Services depend on repositories, never
on AsyncSession directly, so persistence details stay swappable and
mockable in tests. See base.py for the shared structural base class.
"""
