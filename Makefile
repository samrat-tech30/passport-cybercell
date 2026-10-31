# PASSPORT: one command for each common job. Windows without make: see README.md (raw commands).
PY ?= python3
VENV = backend/.venv
BIN = $(VENV)/bin

.PHONY: setup backend frontend test lint eval check examples tamper reset-db gateway gateway-test fooled-agent gmail-login gateway-gmail

setup:            ## create the backend venv and install both halves
	cd backend && $(PY) -m venv .venv && .venv/bin/pip install -q -r requirements-dev.txt
	test -f backend/.env || cp backend/.env.example backend/.env
	cd frontend && npm install --no-audit --no-fund
	test -f frontend/.env.local || cp frontend/.env.example frontend/.env.local

backend:          ## API on http://localhost:8000 (docs at /docs)
	cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000 --env-file .env

frontend:         ## UI on http://localhost:5173
	cd frontend && npm run dev

test:             ## backend tests
	cd backend && .venv/bin/pytest

lint:
	cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check .

eval:             ## shield OFF vs ON table (replay mode, measured)
	cd backend && .venv/bin/python -m app.eval_runner

check:            ## everything that must pass before "done"
	bash scripts/check.sh

examples:         ## regenerate contracts/examples + openapi.json from the real backend
	cd backend && .venv/bin/python ../scripts/make_contract_examples.py

tamper:           ## DEMO: flip one DENY to ALLOW in the audit log, then press Verify chain
	cd backend && .venv/bin/python ../scripts/tamper_audit.py

reset-db:         ## delete the local demo database (audit log too!)
	rm -f backend/var/passport.db backend/var/passport.db-wal backend/var/passport.db-shm

gateway:          ## PASSPORT MCP gateway over stdio (backend running with PASSPORT_GATEWAY_TOKEN; same token in this shell)
	$(BIN)/python integrations/passport_gateway/server.py

fooled-agent:     ## DEMO: scripted agent fooled by email #3, through the gateway (SHIELD=off for monitor mode)
	$(BIN)/python integrations/demo_agent/fooled_agent.py --shield $(or $(SHIELD),on)

gmail-login:      ## once: sign in to YOUR Gmail for the real connector (GMAIL_CLIENT_ID/SECRET in backend/.env)
	$(BIN)/python integrations/gmail_mcp/login.py --env-file backend/.env

gateway-gmail:    ## the gateway over stdio in front of YOUR real Gmail (read + drafts only)
	PASSPORT_UPSTREAM=gmail $(BIN)/python integrations/passport_gateway/server.py

gateway-test:     ## gateway + Nimbus + backend in one process (in-memory MCP, ASGI backend)
	cd integrations && ../$(BIN)/python -m pytest tests -q
