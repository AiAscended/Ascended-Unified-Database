from datetime import datetime
from typing import Optional
from pydantic import BaseModel, SecretStr, field_validator
import uuid


class DatabaseConnection(BaseModel):
    id: str
    name: str
    db_type: str
    host: str
    port: int
    database_name: Optional[str] = None
    username: Optional[str] = None
    is_active: bool
    health_status: Optional[str] = None
    created_at: datetime


class CreateDatabaseConnectionRequest(BaseModel):
    name: str
    db_type: str
    host: str
    port: int
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[SecretStr] = None

    @field_validator("db_type")
    @classmethod
    def validate_db_type(cls, v: str) -> str:
        allowed = {"postgres", "redis", "qdrant", "neo4j", "minio", "clickhouse", "kafka"}
        if v not in allowed:
            raise ValueError(f"db_type must be one of {allowed}")
        return v


class ColumnDef(BaseModel):
    name: str
    type: str
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False


class TableInfo(BaseModel):
    name: str
    schema_name: Optional[str] = None
    row_count: Optional[int] = None
    size_bytes: Optional[int] = None
    columns: list[ColumnDef] = []


class CreateTableRequest(BaseModel):
    connection_id: str
    table_name: str
    columns: list[ColumnDef]


class UserSummary(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime


class MetricSnapshot(BaseModel):
    timestamp: datetime
    name: str
    value: float
    labels: dict[str, str] = {}


class SystemHealth(BaseModel):
    status: str
    databases: dict[str, bool]
    gateway_healthy: bool
    checked_at: datetime


class AuditEntry(BaseModel):
    id: str
    user_id: Optional[str] = None
    action: str
    resource: str
    resource_id: Optional[str] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRole(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"admin", "viewer", "editor"}
        if v not in allowed:
            raise ValueError(f"role must be one of {allowed}")
        return v
