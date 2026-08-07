# Sơ đồ Sequence — Cơ chế phân quyền RBAC End-to-End

## 1. Admin Setup (Thiết lập phân quyền)

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│ Admin UI │      │ Backend  │      │ Oracle   │      │ Qdrant   │
└────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘
     │                  │                  │                  │
     │ POST /admin/login│                  │                  │
     │ {admin, pass}    │                  │                  │
     │─────────────────>│                  │                  │
     │                  │ SELECT USERS     │                  │
     │                  │ WHERE USERNAME=  │                  │
     │                  │─────────────────>│                  │
     │                  │   password_hash  │                  │
     │                  │<─────────────────│                  │
     │                  │ verify_password()│                  │
     │                  │ encode_admin_jwt │                  │
     │  admin_token     │                  │                  │
     │<─────────────────│                  │                  │
     │                  │                  │                  │
     │ POST /admin/collections             │                  │
     │ {name, vector_size, distance, ...}  │                  │
     │─────────────────>│                  │                  │
     │                  │        PUT /collections/{name}      │
     │                  │────────────────────────────────────>│
     │                  │              200 OK                  │
     │                  │<────────────────────────────────────│
     │                  │ INSERT COLLECTIONS                  │
     │                  │─────────────────>│                  │
     │  ok: true        │                  │                  │
     │<─────────────────│                  │                  │
     │                  │                  │                  │
     │ POST /admin/roles│                  │                  │
     │ {ROLE_READER,    │                  │                  │
     │  permissions:[   │                  │                  │
     │   {test, r}]}    │                  │                  │
     │─────────────────>│                  │                  │
     │                  │ INSERT ROLES     │                  │
     │                  │ INSERT ROLE_PERM │                  │
     │                  │─────────────────>│                  │
     │  ok: true        │                  │                  │
     │<─────────────────│                  │                  │
     │                  │                  │                  │
     │ POST /admin/users│                  │                  │
     │ {TuanNa46, pass} │                  │                  │
     │─────────────────>│                  │                  │
     │                  │ INSERT USERS     │                  │
     │                  │─────────────────>│                  │
     │  ok: true        │                  │                  │
     │<─────────────────│                  │                  │
     │                  │                  │                  │
     │ PUT /admin/users/TuanNa46/roles     │                  │
     │ {roles:[ROLE_READER]}               │                  │
     │─────────────────>│                  │                  │
     │                  │ INSERT USER_ROLE │                  │
     │                  │─────────────────>│                  │
     │  ok: true        │                  │                  │
     │<─────────────────│                  │                  │
     │                  │                  │                  │
```

## 2. User Login & Lấy Qdrant JWT Token

```
┌──────────┐      ┌──────────┐      ┌──────────┐      ┌──────────┐
│  Client  │      │ Backend  │      │ Oracle   │      │ Qdrant   │
└────┬─────┘      └────┬─────┘      └────┬─────┘      └────┬─────┘
     │                  │                  │                  │
     │ POST /login      │                  │                  │
     │ {TuanNa46, pass} │                  │                  │
     │─────────────────>│                  │                  │
     │                  │                  │                  │
     │                  │ SELECT u.*, r.ROLE_NAME,            │
     │                  │ c.COLLECTION_NAME, rp.PERMISSION   │
     │                  │ FROM USERS u                        │
     │                  │ JOIN USER_ROLE → ROLES              │
     │                  │ JOIN ROLE_PERMISSION → COLLECTIONS  │
     │                  │─────────────────>│                  │
     │                  │                  │                  │
     │                  │ Result:          │                  │
     │                  │ roles: [ROLE_READER]                │
     │                  │ permissions: [{test, r}]            │
     │                  │<─────────────────│                  │
     │                  │                  │                  │
     │                  │ verify_password()│                  │
     │                  │                  │                  │
     │                  │ encode_qdrant_token():              │
     │                  │ JWT payload = {                     │
     │                  │   sub: "TuanNa46",                  │
     │                  │   roles: ["ROLE_READER"],           │
     │                  │   access: [{collection:"test",      │
     │                  │             access:"r"}],           │
     │                  │   exp: now + 120min                 │
     │                  │ }                                   │
     │                  │ Sign with Qdrant API Key            │
     │                  │                  │                  │
     │  qdrant_token    │                  │                  │
     │<─────────────────│                  │                  │
     │                  │                  │                  │
```

## 3. User truy cập Qdrant (Token được verify bởi Qdrant)

```
┌──────────┐      ┌──────────┐      ┌──────────┐
│  Client  │      │ Backend  │      │ Qdrant   │
│ (or App) │      │ (proxy)  │      │ (JWT)    │
└────┬─────┘      └────┬─────┘      └────┬─────┘
     │                  │                  │
     │ POST /debug/test-access-token       │
     │ Header: Bearer <qdrant_token>       │
     │ {collection:"test", action:"read"}  │
     │─────────────────>│                  │
     │                  │                  │
     │                  │ POST /collections/test/points/scroll
     │                  │ Header: Bearer <qdrant_token>
     │                  │─────────────────>│
     │                  │                  │
     │                  │                  │ Qdrant verifies JWT:
     │                  │                  │ 1. Check signature (API key)
     │                  │                  │ 2. Check exp (not expired)
     │                  │                  │ 3. Check access claim:
     │                  │                  │    [{collection:"test",
     │                  │                  │      access:"r"}]
     │                  │                  │ 4. "test" + "read" → ALLOWED ✅
     │                  │                  │
     │                  │     200 OK       │
     │                  │<─────────────────│
     │                  │                  │
     │ verdict: allowed │                  │
     │<─────────────────│                  │
     │                  │                  │
     ═══════════════════════════════════════
     │ Trường hợp FORBIDDEN:              │
     │                  │                  │
     │ POST /debug/test-access-token       │
     │ {collection:"secret", action:"read"}│
     │─────────────────>│                  │
     │                  │ POST /collections/secret/points/scroll
     │                  │ Header: Bearer <qdrant_token>
     │                  │─────────────────>│
     │                  │                  │ Check access claim:
     │                  │                  │ "secret" NOT in
     │                  │                  │ [{collection:"test"}]
     │                  │                  │ → FORBIDDEN 🚫
     │                  │    403 Forbidden │
     │                  │<─────────────────│
     │ verdict: forbidden                  │
     │<─────────────────│                  │
```

## 4. Mô hình dữ liệu Oracle RBAC

```
┌─────────────────────────────────────────────────────────────────┐
│                        Oracle Database                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  USERS ──────< USER_ROLE >────── ROLES                          │
│  (USER_ID,     (USER_ID,         (ROLE_ID,                      │
│   USERNAME,     ROLE_ID)           ROLE_NAME,                   │
│   PASSWORD,                        DESCRIPTION)                 │
│   USER_TYPE)                            │                       │
│                                         │                       │
│                                    ROLE_PERMISSION              │
│                                    (ROLE_ID,                    │
│                                     COLLECTION_ID,             │
│                                     PERMISSION)                │
│                                         │                       │
│                                    COLLECTIONS                  │
│                                    (COLLECTION_ID,             │
│                                     COLLECTION_NAME)           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 5. Tổng quan luồng phân quyền

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                      │
│  ADMIN thiết lập:                                                   │
│  ┌────────────┐    ┌─────────────┐    ┌──────────────────┐         │
│  │ Collection │───>│    Role     │───>│  User            │         │
│  │ (Qdrant +  │    │ (có perms   │    │ (được gán roles) │         │
│  │  Oracle)   │    │  trên colls)│    │                  │         │
│  └────────────┘    └─────────────┘    └──────────────────┘         │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  USER login:                                                        │
│  ┌────────┐  login   ┌─────────┐  query Oracle  ┌────────────────┐ │
│  │ Client │─────────>│ Backend │───────────────>│ USERS +        │ │
│  │        │          │         │                │ USER_ROLE +    │ │
│  │        │          │         │<───────────────│ ROLE_PERM +    │ │
│  │        │          │         │  permissions   │ COLLECTIONS    │ │
│  │        │  JWT     │         │                └────────────────┘ │
│  │        │<─────────│ mint JWT│                                    │
│  └────────┘  token   └─────────┘                                    │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  USER truy cập data:                                                │
│  ┌────────┐  Bearer token  ┌─────────┐  verify JWT   ┌──────────┐ │
│  │ Client │───────────────>│ Qdrant  │──────────────>│ Check    │ │
│  │        │                │         │               │ access[] │ │
│  │        │  200 / 403     │         │  allow/deny   │ claim    │ │
│  │        │<───────────────│         │<──────────────│          │ │
│  └────────┘                └─────────┘               └──────────┘ │
│                                                                      │
│  ⚡ Qdrant tự verify JWT — Backend KHÔNG proxy data requests       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Tóm tắt

| Bước | Actor | Action | Kết quả |
|------|-------|--------|---------|
| 1 | Admin | Tạo Collection trên Qdrant + sync Oracle | Collection sẵn sàng |
| 2 | Admin | Tạo Role + gán permissions (collection:access) | Role có quyền |
| 3 | Admin | Tạo User + gán Role cho User | User kế thừa permissions từ Role |
| 4 | User | POST /login → Backend query Oracle → mint JWT | User nhận Qdrant JWT token |
| 5 | User/App | Gửi request tới Qdrant với Bearer JWT | Qdrant tự verify + enforce |
| 6 | Qdrant | Verify JWT signature + check `access` claim | 200 (allowed) hoặc 403 (forbidden) |
