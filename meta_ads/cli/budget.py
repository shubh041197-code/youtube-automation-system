import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from meta_ads.services.budget_service import BudgetService

app = typer.Typer(help="Budget optimization and auto-rules")
console = Console()
svc = BudgetService()


@app.command("recommend")
def recommend(
    campaign_id: str = typer.Argument(..., help="Campaign ID to analyze"),
    days: int = typer.Option(7, help="Number of days to analyze"),
):
    """Get budget recommendations for a campaign."""
    result = svc.get_budget_recommendations(campaign_id, days=days)

    if result.get("recommendation") == "INSUFFICIENT_DATA":
        console.print(f"[yellow]{result['message']}[/yellow]")
        return

    metrics = result.get("metrics", {})
    panel = Panel(
        f"[bold]Campaign:[/bold] {result['campaign_name']}\n"
        f"[bold]Current Daily Budget:[/bold] ${result['current_daily_budget']:,.2f}\n"
        f"[bold]Suggested Daily Budget:[/bold] ${result['suggested_daily_budget']:,.2f}\n"
        f"\n[bold]Metrics ({days}d):[/bold]\n"
        f"  Spend: ${metrics.get('spend', 0):,.2f}\n"
        f"  Impressions: {metrics.get('impressions', 0):,}\n"
        f"  Clicks: {metrics.get('clicks', 0):,}\n"
        f"  CTR: {metrics.get('ctr', 0):.2f}%\n"
        f"  CPC: ${metrics.get('cpc', 0):.2f}\n"
        f"  CPM: ${metrics.get('cpm', 0):.2f}",
        title="Budget Recommendations",
        border_style="blue",
    )
    console.print(panel)

    recommendations = result.get("recommendations", [])
    if recommendations:
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in recommendations:
            color = "red" if rec["priority"] == "HIGH" else "yellow"
            console.print(f"  [{color}][{rec['priority']}][/{color}] {rec['action']}")


@app.command("set")
def set_budget(
    campaign_id: str = typer.Argument(..., help="Campaign ID"),
    amount: float = typer.Argument(..., help="Daily budget in dollars (e.g., 50.00)"),
):
    """Set daily budget for a campaign."""
    cents = int(amount * 100)
    result = svc.set_campaign_budget(campaign_id, cents)
    console.print(f"[green]Budget set:[/green] ${amount:.2f}/day for campaign {campaign_id}")


@app.command("pause-losers")
def pause_underperformers(
    campaign_id: str = typer.Argument(..., help="Campaign ID"),
    ctr_threshold: float = typer.Option(0.5, help="Pause ads with CTR below this (%)"),
    min_impressions: int = typer.Option(1000, help="Minimum impressions before evaluating"),
):
    """Auto-pause underperforming ads."""
    paused = svc.pause_underperforming_ads(campaign_id, ctr_threshold=ctr_threshold, min_impressions=min_impressions)

    if not paused:
        console.print("[green]No underperforming ads found.[/green]")
        return

    table = Table(title="Paused Ads")
    table.add_column("Ad ID", style="cyan")
    table.add_column("Name")
    table.add_column("Impressions", justify="right")
    table.add_column("CTR", justify="right")

    for ad in paused:
        table.add_row(ad["ad_id"], ad.get("ad_name", "—"), str(ad["impressions"]), f"{ad['ctr']:.2f}%")

    console.print(table)
    console.print(f"\n[yellow]Paused {len(paused)} underperforming ad(s).[/yellow]")


@app.command("scale-winners")
def scale_winners(
    campaign_id: str = typer.Argument(..., help="Campaign ID"),
    ctr_threshold: float = typer.Option(2.0, help="Scale ad sets with CTR above this (%)"),
    budget_increase: float = typer.Option(0.2, help="Budget increase ratio (0.2 = 20%)"),
):
    """Increase budget for top-performing ad sets."""
    scaled = svc.scale_winning_adsets(campaign_id, ctr_threshold=ctr_threshold, budget_increase=budget_increase)

    if not scaled:
        console.print("[yellow]No ad sets met the threshold for scaling.[/yellow]")
        return

    table = Table(title="Scaled Ad Sets")
    table.add_column("Ad Set ID", style="cyan")
    table.add_column("Name")
    table.add_column("Old Budget", justify="right")
    table.add_column("New Budget", justify="right")
    table.add_column("CTR", justify="right")

    for s in scaled:
        table.add_row(
            s["adset_id"], s.get("adset_name", "—"),
            f"${s['old_budget_cents'] / 100:.2f}", f"${s['new_budget_cents'] / 100:.2f}",
            f"{s['ctr']:.2f}%",
        )

    console.print(table)
    console.print(f"\n[green]Scaled up {len(scaled)} ad set(s).[/green]")
