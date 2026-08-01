"""Windows-safe local dev entrypoint — use this instead of the bare
`uvicorn app.main:app --reload` command on Windows.

`uvicorn app.main:app` creates its own asyncio event loop (via
`asyncio.run()`) before it ever imports app.main, so setting the event loop
policy from inside the app (see app/db/session.py) is too late on Windows:
the loop already exists and defaults to ProactorEventLoop, which psycopg 3's
async driver can't use ("Psycopg cannot use the 'ProactorEventLoop'...").
Setting the policy here, before uvicorn.run() is even called, fixes it —
this file must be run directly (`python run_dev.py`), not imported.

Linux/Docker (see Dockerfile, docker-compose.yml) never hits this — asyncio
defaults to a selector-based loop there already — so `uvicorn app.main:app`
directly remains correct in those environments and is unchanged.
"""

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
