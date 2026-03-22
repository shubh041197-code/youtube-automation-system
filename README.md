# Meta Ads Automation System

Full automation for Meta (Facebook/Instagram) advertising — campaigns, creatives, audiences, reporting, and budget optimization.

## Features

- **Campaign Management** — Create, update, pause, resume, delete campaigns, ad sets, and ads
- **Creative Management** — Image, video, and carousel ad creatives with image upload
- **Audience Management** — Custom audiences and lookalike audiences
- **Reporting & Analytics** — Account/campaign/adset/ad-level insights with breakdowns
- **Budget Optimization** — Smart recommendations, auto-pause underperformers, scale winners

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env with your Meta API credentials
```

You need:
- **Meta App ID** and **App Secret** from [Meta for Developers](https://developers.facebook.com/)
- **Access Token** with `ads_management` and `ads_read` permissions
- **Ad Account ID** (format: `act_XXXXXXXXX`)

### 3. Use the CLI

```bash
# Show all commands
python -m meta_ads.cli.main --help

# Campaign commands
python -m meta_ads.cli.main campaigns list
python -m meta_ads.cli.main campaigns create --name "My Campaign" --objective OUTCOME_TRAFFIC --daily-budget 5000
python -m meta_ads.cli.main campaigns pause <campaign_id>

# Ad Set commands
python -m meta_ads.cli.main campaigns adset-create --name "US Adults" --campaign-id <id> --countries US --daily-budget 2000
python -m meta_ads.cli.main campaigns adset-list

# Creative commands
python -m meta_ads.cli.main creatives upload-image ./my-ad.jpg
python -m meta_ads.cli.main creatives create --name "Ad Creative" --page-id <page_id> --link "https://example.com" --image-hash <hash>

# Reporting
python -m meta_ads.cli.main reports summary --date-preset last_7d
python -m meta_ads.cli.main reports insights --level campaign --date-preset last_30d
python -m meta_ads.cli.main reports campaign <campaign_id>

# Budget optimization
python -m meta_ads.cli.main budget recommend <campaign_id>
python -m meta_ads.cli.main budget set <campaign_id> 75.00
python -m meta_ads.cli.main budget pause-losers <campaign_id> --ctr-threshold 0.5
python -m meta_ads.cli.main budget scale-winners <campaign_id> --ctr-threshold 2.0
```

### 4. Use the REST API

```bash
python run_api.py
# Open http://localhost:8000/docs for interactive Swagger UI
```

**API Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/campaigns` | List campaigns |
| POST | `/api/v1/campaigns` | Create campaign |
| PATCH | `/api/v1/campaigns/{id}` | Update campaign |
| POST | `/api/v1/campaigns/{id}/pause` | Pause campaign |
| POST | `/api/v1/campaigns/{id}/resume` | Resume campaign |
| DELETE | `/api/v1/campaigns/{id}` | Delete campaign |
| GET/POST/PATCH/DELETE | `/api/v1/adsets` | Ad set CRUD |
| GET/POST/PATCH/DELETE | `/api/v1/ads` | Ad CRUD |
| GET/POST/DELETE | `/api/v1/creatives` | Creative management |
| POST | `/api/v1/creatives/upload-image` | Upload ad image |
| GET/POST/DELETE | `/api/v1/audiences/*` | Audience management |
| POST | `/api/v1/reports/insights` | Custom insights report |
| GET | `/api/v1/reports/summary` | Account KPIs |
| GET | `/api/v1/reports/campaigns/{id}` | Campaign daily performance |
| GET | `/api/v1/budget/recommendations/{id}` | Budget recommendations |
| POST | `/api/v1/budget/set/{id}` | Set budget |
| POST | `/api/v1/budget/pause-underperforming/{id}` | Auto-pause bad ads |
| POST | `/api/v1/budget/scale-winners/{id}` | Scale winning ad sets |

## Architecture

```
meta_ads/
├── config.py           # .env-based settings
├── meta_client.py      # Meta API client init
├── models/             # Pydantic request/response schemas
├── services/           # Core business logic (shared by API + CLI)
├── api/                # FastAPI REST endpoints
└── cli/                # Typer CLI commands
```

CLI and API are thin layers over shared services — no logic duplication.

## License

MIT
