# Gaps And Recommendations

| Severity | Issue | Evidence | Minimal correction | Impact |
|---|---|---|---|---|
| HIGH | Backend auth/authorization not applied | controllers lack auth dependencies | add JWT dependency and role policies | API bypass risk |
| HIGH | Default JWT secrets in production config | Docker config shows placeholder | fail startup on placeholder when `APP_ENV=production` | token compromise |
| HIGH | Provider error leakage | 502 returns `reason=str(error)` | redact provider bodies | secret leakage |
| MEDIUM | OpenAPI response schemas empty | generated schema has `{}` success schemas | add `response_model=ApiResponse[...]` or explicit models | client/docs mismatch |
| MEDIUM | ChromaDB requested but absent | no dependency/source | implement vector store or document JSON memory only | capability gap |
| MEDIUM | Video API lifecycle incomplete | no list/get/delete/retry/timeline routes | add CRUD/job control endpoints | frontend/API gap |
| MEDIUM | Original audio not preserved | no audio code | ffmpeg demux/mux pipeline | output quality gap |
| MEDIUM | Cleanup/retention absent | large storage listing | add scheduled cleanup and retention config | disk/privacy risk |
| MEDIUM | No migrations | empty migrations package | Alembic migration baseline | deployment drift |
| MEDIUM | Cloud AI upload validation weaker than image pipeline | extension-only save | reuse signature/size validator | spoofing risk |
| MEDIUM | Model registry activation does not reload/copy manually registered model | `ModelRegistryService.activate_model_async` only DB status | validate artifact, copy active path, reload services | activation not operational |
| LOW | File-backed users not concurrency-safe | direct JSON write | atomic write + lock or SQL user table | corruption under parallel register |
| LOW | Docker warning on config ACL | compose config warning | fix Docker credential config permission | operational noise |
| LOW | Duplicate response sanitizers | ApiResponse and local `_public_*` | centralize sanitizer | maintenance risk |
| INFORMATIONAL | `enable_duplicate_pruning` video setting unused | setting present; no pruning logic | implement or remove | confusing API |
| INFORMATIONAL | `save_detector_annotated_image` video setting unused | setting present; no branch found | implement or remove | confusing API |

## Dead Or Stale Code

- Stale `__pycache__/ollama_vlm_client` without source.
- `VisualMemoryEntity` exists but is not written by current video or image memory pipelines found in source.

## Deployment Blockers

- Secrets must be set externally.
- Storage volume must be writable and persistent.
- Model files must exist at configured paths.
- Docker backend uses `/app/storage`; host path mapping must match model files.
- No database migration process exists.
