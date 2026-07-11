"""Pydantic request/response models for the ingestion API (Sprint 1)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ---- Organizations ----
class OrganizationCreate(BaseModel):
    name: str
    website: str | None = None
    parent_organization_id: UUID | None = None
    org_role: str = Field(default="owned_brand", pattern="^(owned_brand|competitor_tracked)$")
    vertical_pack_id: str = "automotive"


class Organization(BaseModel):
    organization_id: UUID
    account_id: UUID
    parent_organization_id: UUID | None
    name: str
    website: str | None
    org_role: str
    vertical_pack_id: str
    created_at: datetime


# ---- Sources ----
class SourceCreate(BaseModel):
    organization_id: UUID
    type: str = "website"
    seed_url: str


class Source(BaseModel):
    source_id: UUID
    account_id: UUID
    organization_id: UUID
    type: str
    seed_url: str
    status: str
    created_at: datetime


# ---- Crawl jobs ----
class CrawlRequest(BaseModel):
    source_id: UUID


class JobRef(BaseModel):
    job_id: UUID
    status: str


class CrawlStatus(BaseModel):
    job_id: UUID
    status: str
    stage: str | None
    attempts: int
    pages_ingested: int
    error: str | None
    metrics: dict
