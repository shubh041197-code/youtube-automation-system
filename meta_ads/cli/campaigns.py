import json
import typer
from rich.console import Console
from rich.table import Table

from meta_ads.services.campaign_service import CampaignService
from meta_ads.models.campaigns import (
    CampaignCreate, CampaignUpdate, CampaignObjective, CampaignStatus, BidStrategy,
    AdSetCreate, AdSetUpdate, TargetingSpec, TargetingGeo, OptimizationGoal,
    AdCreate, AdUpdate,
)

app = typer.Typer(help="Manage campaigns, ad sets, and ads")
console = Console()
svc = CampaignService()


# --- Campaigns ---

@app.command("create")
def create_campaign(
    name: str = typer.Option(..., help="Campaign name"),
    objective: CampaignObjective = typer.Option(CampaignObjective.OUTCOME_TRAFFIC, help="Campaign objective"),
    daily_budget: int = typer.Option(None, help="Daily budget in cents (e.g., 5000 = $50)"),
    status: CampaignStatus = typer.Option(CampaignStatus.PAUSED, help="Initial status"),
    bid_strategy: BidStrategy = typer.Option(BidStrategy.LOWEST_COST_WITHOUT_CAP, help="Bid strategy"),
):
    """Create a new campaign."""
    data = CampaignCreate(
        name=name, objective=objective, daily_budget=daily_budget,
        status=status, bid_strategy=bid_strategy,
    )
    result = svc.create_campaign(data)
    console.print(f"[green]Campaign created:[/green] {result.id} — {result.name}")


@app.command("list")
def list_campaigns(
    status: str = typer.Option(None, help="Filter: ACTIVE, PAUSED, ARCHIVED"),
):
    """List all campaigns."""
    campaigns = svc.list_campaigns(status=status)
    if not campaigns:
        console.print("[yellow]No campaigns found.[/yellow]")
        return

    table = Table(title="Campaigns")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Objective")
    table.add_column("Status", style="bold")
    table.add_column("Daily Budget")

    for c in campaigns:
        budget = f"${int(c.daily_budget) / 100:.2f}" if c.daily_budget else "—"
        table.add_row(c.id, c.name, c.objective or "—", c.status or "—", budget)

    console.print(table)


@app.command("get")
def get_campaign(campaign_id: str = typer.Argument(..., help="Campaign ID")):
    """Get campaign details."""
    c = svc.get_campaign(campaign_id)
    console.print_json(c.model_dump_json())


@app.command("update")
def update_campaign(
    campaign_id: str = typer.Argument(..., help="Campaign ID"),
    name: str = typer.Option(None),
    status: CampaignStatus = typer.Option(None),
    daily_budget: int = typer.Option(None, help="Daily budget in cents"),
):
    """Update a campaign."""
    data = CampaignUpdate(name=name, status=status, daily_budget=daily_budget)
    result = svc.update_campaign(campaign_id, data)
    console.print(f"[green]Updated:[/green] {result.id} — {result.name} ({result.status})")


@app.command("pause")
def pause_campaign(campaign_id: str = typer.Argument(...)):
    """Pause a campaign."""
    result = svc.pause_campaign(campaign_id)
    console.print(f"[yellow]Paused:[/yellow] {result.id} — {result.name}")


@app.command("resume")
def resume_campaign(campaign_id: str = typer.Argument(...)):
    """Resume a paused campaign."""
    result = svc.resume_campaign(campaign_id)
    console.print(f"[green]Resumed:[/green] {result.id} — {result.name}")


@app.command("delete")
def delete_campaign(campaign_id: str = typer.Argument(...)):
    """Delete a campaign."""
    svc.delete_campaign(campaign_id)
    console.print(f"[red]Deleted:[/red] {campaign_id}")


# --- Ad Sets ---

@app.command("adset-create")
def create_adset(
    name: str = typer.Option(...),
    campaign_id: str = typer.Option(..., help="Parent campaign ID"),
    countries: str = typer.Option(..., help="Comma-separated country codes, e.g. US,GB"),
    daily_budget: int = typer.Option(None, help="Daily budget in cents"),
    optimization_goal: OptimizationGoal = typer.Option(OptimizationGoal.LINK_CLICKS),
    age_min: int = typer.Option(18),
    age_max: int = typer.Option(65),
):
    """Create an ad set."""
    targeting = TargetingSpec(
        geo_locations=TargetingGeo(countries=countries.split(",")),
        age_min=age_min, age_max=age_max,
    )
    data = AdSetCreate(
        name=name, campaign_id=campaign_id, daily_budget=daily_budget,
        optimization_goal=optimization_goal, targeting=targeting,
    )
    result = svc.create_adset(data)
    console.print(f"[green]Ad Set created:[/green] {result.id} — {result.name}")


@app.command("adset-list")
def list_adsets(campaign_id: str = typer.Option(None)):
    """List ad sets."""
    adsets = svc.list_adsets(campaign_id=campaign_id)
    if not adsets:
        console.print("[yellow]No ad sets found.[/yellow]")
        return

    table = Table(title="Ad Sets")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Campaign ID")
    table.add_column("Status")
    table.add_column("Daily Budget")

    for a in adsets:
        budget = f"${int(a.daily_budget) / 100:.2f}" if a.daily_budget else "—"
        table.add_row(a.id, a.name, a.campaign_id or "—", a.status or "—", budget)

    console.print(table)


@app.command("adset-delete")
def delete_adset(adset_id: str = typer.Argument(...)):
    """Delete an ad set."""
    svc.delete_adset(adset_id)
    console.print(f"[red]Deleted ad set:[/red] {adset_id}")


# --- Ads ---

@app.command("ad-create")
def create_ad(
    name: str = typer.Option(...),
    adset_id: str = typer.Option(..., help="Ad Set ID"),
    creative_id: str = typer.Option(..., help="Creative ID"),
):
    """Create an ad."""
    data = AdCreate(name=name, adset_id=adset_id, creative_id=creative_id)
    result = svc.create_ad(data)
    console.print(f"[green]Ad created:[/green] {result.id} — {result.name}")


@app.command("ad-list")
def list_ads(adset_id: str = typer.Option(None)):
    """List ads."""
    ads = svc.list_ads(adset_id=adset_id)
    if not ads:
        console.print("[yellow]No ads found.[/yellow]")
        return

    table = Table(title="Ads")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Ad Set ID")
    table.add_column("Status")

    for a in ads:
        table.add_row(a.id, a.name, a.adset_id or "—", a.status or "—")

    console.print(table)


@app.command("ad-delete")
def delete_ad(ad_id: str = typer.Argument(...)):
    """Delete an ad."""
    svc.delete_ad(ad_id)
    console.print(f"[red]Deleted ad:[/red] {ad_id}")
