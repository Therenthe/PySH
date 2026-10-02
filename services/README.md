# Local services

backend/ is the existing Python API and device adapters. Run from repository root using `python -m uvicorn services.backend.app:app --host 127.0.0.1 --port 8765`. No cloud or separate automation service is required by this migration.
