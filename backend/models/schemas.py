"""Pydantic request/response models."""

from pydantic import BaseModel, Field


class Permission(BaseModel):
    collection: str = Field(min_length=1)
    access: str = Field(pattern="^(r|rw)$")


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern="^[a-zA-Z0-9_.-]+$")
    password: str = Field(min_length=6, max_length=128)
    permissions: list[Permission] = Field(default_factory=list)


class CreateRoleRequest(BaseModel):
    role_name: str = Field(min_length=2, max_length=100, pattern="^[a-zA-Z0-9_.-]+$")
    description: str = Field(default="", max_length=200)
    permissions: list[Permission] = Field(default_factory=list)


class UpdateRolePermissionsRequest(BaseModel):
    permissions: list[Permission]


class AssignUserRolesRequest(BaseModel):
    roles: list[str] = Field(default_factory=list)


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    qdrant_token: str


class AccessTokenTestRequest(BaseModel):
    collection: str = Field(min_length=1)
    action: str = Field(default="read", pattern="^(read|write)$")


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminLoginResponse(BaseModel):
    admin_token: str
    qdrant_token: str
    expires_at: str
    username: str


class CreateCollectionRequest(BaseModel):
    collection_name: str = Field(min_length=1, max_length=100, pattern="^[a-zA-Z0-9_.-]+$")
    vector_size: int = Field(default=384, ge=1, le=65536)
    distance: str = Field(default="Cosine", pattern="^(Cosine|Dot|Euclid)$")
    shard_number: int = Field(default=1, ge=1)
    replication_factor: int = Field(default=1, ge=1)
    write_consistency_factor: int = Field(default=1, ge=1)
    on_disk_payload: bool = True


class UpdateCollectionConfigRequest(BaseModel):
    indexing_threshold: int | None = Field(default=None, ge=1)
    hnsw_ef_construct: int | None = Field(default=None, ge=1)
    hnsw_m: int | None = Field(default=None, ge=1)
    write_consistency_factor: int | None = Field(default=None, ge=1)
    strict_mode_enabled: bool | None = None
