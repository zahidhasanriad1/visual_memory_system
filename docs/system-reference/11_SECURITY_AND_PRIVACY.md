# Security And Privacy Audit

## Findings

| Severity | Finding | Evidence | Minimal correction | Impact |
|---|---|---|---|---|
| HIGH | Backend authorization missing on most routes | only `/auth/me` checks `Authorization`; routers lack auth dependencies | add backend auth/role dependencies to protected routers | frontend role guard can be bypassed |
| HIGH | Insecure default JWT secrets | `appsettings.py`, `jwt_token_service.py`, Docker config default `change-this-secret-in-production` | require non-default secret in production startup | token forgery risk |
| HIGH | Provider error bodies may leak details | cloud controller returns `reason: str(error)` in 502 | sanitize provider exceptions and disable debug reasons | secret or operational leakage |
| MEDIUM | File-backed user repository has no locking | `UserRepository._save_users` writes JSON directly | atomic write + lock or DB-backed users | race/corruption risk |
| MEDIUM | Public media endpoints unauthenticated | `/media/*` routes return files by filename | require auth or signed URLs | uploaded/crop media exposure |
| MEDIUM | Response path leakage inconsistently handled | `ApiResponse` strips `_path`, custom controllers also strip, but HTTPException/debug may include paths | central response sanitization | host/container path exposure |
| MEDIUM | Cleanup/retention absent | storage listing shows many uploads/crops; no cleanup service | retention policy and cleanup jobs | storage growth/privacy risk |
| MEDIUM | No Alembic migrations | migrations package empty | introduce migrations | schema drift/deploy risk |
| MEDIUM | Cloud AI upload validation is weaker than image pipeline | cloud `_save_uploaded_image` checks extension and nonempty only | reuse `ImageFileValidator` | content spoofing risk |
| LOW | CORS allows local network regex | `main.py` allow_origin_regex for private IP ranges | narrow production origins | broader attack surface |
| LOW | Docker Compose attempts to read denied Docker config | `docker compose config` warning | fix Docker config ACL | operational warning |
| INFORMATIONAL | Password hashing is PBKDF2-HMAC SHA256 with 120k iterations | `PasswordHasher` | consider Argon2/bcrypt policy | acceptable prototype |
| INFORMATIONAL | JWT implementation is custom HS256 | `JwtTokenService` | consider vetted JWT library and key rotation | maintenance risk |

## Upload Validation

Image feature uploads validate extension, declared content type, byte signature, size, and pixel count. TIFF decompression/pixel safety is handled via Pillow `MAX_IMAGE_PIXELS` and explicit pixel limit. Cloud AI uploads do not perform the same signature check.

## Path Traversal

Image media uses `safe_resolve_file` and media service uses `SafePathResolver`. These block `..`, child escape, unsupported suffixes, and missing files.

## Secrets

Secrets found as configuration names only: `JWT_SECRET_KEY`, `HF_TOKEN`, `OPENAI_API_KEY`, `GEMINI_API_KEY`. This audit did not print real key values; Docker config output showed blank provider keys and default JWT placeholder.

## SSRF And Prompt Injection

No URL-fetching endpoint for arbitrary remote images was found, reducing SSRF surface. Cloud AI prompts include user context/report text and are susceptible to prompt injection as with any LLM feature; no prompt-injection guardrails beyond prompt wording were found.
