# Bomber

Async multi-user load tester focused on the Nyx `POST /messages` endpoint.

## What it does

Before the measured load phase, the bomber can:

- create synthetic users
- authenticate them through `/auth/challenge` and `/auth/login`
- create conversations between those users

Then it stress tests `POST /messages` by simulating both sides of each conversation sending encrypted-looking payloads.

## Usage

From the repository root:

```powershell
python backend/bomber/main.py --base-url https://your-api-id.execute-api.us-east-1.amazonaws.com/main --users 200 --requests 100000 --concurrency 1000 --warmup 5000
```

Optional outputs:

```powershell
python backend/bomber/main.py --base-url https://your-api-id.execute-api.us-east-1.amazonaws.com/main --export-json backend/bomber/results.json --failure-log backend/bomber/failures.jsonl
```

## Notes

- `--base-url` should point to the HTTP API stage root, not directly to `/messages`
- the bomber targets `POST /messages`
- rerunning with the same username prefix can reuse previously created users if you pass `--skip-register`
