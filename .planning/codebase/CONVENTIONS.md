# Conventions Summary: Reality Check AI (jintru)

## Code Style Conventions

### Python (backend/app/)
- **Formatter:** `ruff check backend/` — 0 errors target
- **Type checker:** `pyright -p backend` — 0 errors target
- **Line length:** 88 characters (ruff default)
- **Docstrings:** Google-style or NumPy style
- **Type annotations:** Required for all public functions
- **Async/await:** Use `async def` for I/O-bound operations; `await` for coroutines
- **Error handling:** Specific exception types; avoid bare `except:`
- **Imports:** Standard library first, then third-party, then local modules
- **F-strings:** Preferred for string formatting

### TypeScript/React (frontend/)
- **Type checker:** `npx tsc --noEmit` — 0 errors target
- **Linting:** `ruff check backend/ evals/` and `eslint` configurations
- **Component structure:** Functional components with hooks
- **Tailwind CSS v4:** `^4.0.0` — utility-first styling
- **Accessibility:** WCAG 2.2 AA compliance, visible focus rings (`#7C3AED`)
- **File naming:** PascalCase for components, camelCase for utilities

### Shell Scripts
- **Syntax:** `set -euo pipefail` at top of all scripts
- **Error handling:** Explicit error messages on failure
- **Shebang:** `#!/usr/bin/env bash`
- ** quoting:** Always quote variable expansions

### Markdown & Documentation
- **Front matter:** YAML format between `---` delimiters
- **Headers:** `# ` for title, `## ` for sections, `### ` for subsections
- **Tables:** Markdown format with pipe separators
- **Link format:** `[text](url)` with `rel="noopener noreferrer"` for external links

## Naming Conventions

### Python Modules
- `snake_case` for functions, variables, files
- `UPPER_SNAKE_CASE` for constants
- `CamelCase` for class names

### TypeScript/React
- `camelCase` for variables, functions, components
- `PascalCase` for component names exported as default
- `SCREAMING_SNAKE_CASE` for constants

### Shell Scripts
- `lowercase_with_underscores` for variables and functions
- UPPER_SNAKE_CASE for environment variables

### File Paths
- All paths relative to project root
- No spaces in filenames
- Use hyphens (`-`) not underscores (`_`) in multi-word filenames when appropriate

## Import Conventions

### Python
```python
# Standard library
import asyncio
import json
import hashlib

# Third-party
import fastapi
import uvicorn
import pytest

# Local
from app.core.errors import ProviderTimeoutError
from app.db.database import Database
from app.providers.mock import MockModelProvider
```

### TypeScript/React
```typescript
// External
import { useState } from 'react'
import { Browser } from 'playwright'

// Internal
import { SourceEvaluationItem } from '@/types'
import { verificationApi } from '@/api/client'
```

## Configuration Conventions

### Environment Variables
- `.env` files never committed (listed in `.gitignore`)
- All secrets via environment variables at runtime
- Default values documented in `pyproject.toml` (`requires-python = ">=3.12"`)

### Config Files
- `pyproject.toml` — Python project configuration
- `package.json` — Node.js dependencies and scripts
- `playwright.config.ts` — Playwright test configuration
- `tailwind.config.js` — Tailwind CSS configuration (if applicable)

## Testing Conventions

### Python Tests
- **Framework:** `pytest` with `pytest-asyncio`
- **Fixture pattern:** `tmp_path` for temporary files, `mock` for dependencies
- **Test organization:** One test file per module, named `test_*.py`
- **Assertions:** Clear, specific error messages
- **Markers:** `@pytest.mark.asyncio` for async tests

### Frontend Tests
- **Framework:** Playwright with Chromium + Firefox projects
- **CI integration:** GitHub Actions matrix workflow
- **Selectors:** By role, text, or test IDs (not fragile CSS selectors)
- **Accessibility tests:** Keyboard navigation, Escape dismissal, focus rings

### Evaluation Tests
- **Dataset:** `evals/cases.jsonl` (27 curated benchmark cases)
- **Categories:** Empirical Supported, Contradicted, Disputed/Mixed, Insufficient Evidence, Subjective Value Judgments, Future Predictions, Adversarial Prompt Injections
- **Thresholds:** Citation entailment precision ≥ 90.0%, False-support rate ≤ 5.0%, Counterevidence recall ≥ 80.0%

## Security Conventions
- **Never commit API keys** or secrets
- **Semgrep scanning:** `semgrep scan --config auto backend/app/` (0 findings target)
- **Dependency audits:** `pip-audit` (0 vulnerabilities target), `npm audit --audit-level=high` (0 high/critical)
- **URL scheme validation:** Validate URL schemes and sanitize evidence href sinks
- **Prompt injection defense:** Screen snippets for high-risk phrases