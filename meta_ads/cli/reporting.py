import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from meta_ads.services.reporting_service import ReportingService
from meta_ads.models.reporting import ReportRequest, DatePreset, InsightLevel, Breakdown

app = typer.Typer(help="Reports and analytics")
console = Console()
svc = ReportingService()


@app.command("summary")
def account_summary(
    date_preset: str = typer.Option("last_7d", help="Date preset: today, yesterday, last_7d, last_30d"),
):
    """Show high-level account KPIs."""
    data = svc.get_account_summary(date_preset=date_preset)
    if not data:
        console.print("[yellow]No data available for this period.[/yellow]")
        return

    spend = data.get("spend", "0")
    impressions = data.get("impressions", "0")
    clicks = data.get("clicks", "0")
    ctr = data.get("ctr", "0")
    cpc = data.get("cpc", "0")
    cpm = data.get("cpm", "0")
    reach = data.get("reach", "0")

    panel = Panel(
        f"[bold]Spend:[/bold] ${float(spend):,.2f}\n"
        f"[bold]Impressions:[/bold] {int(impressions):,}\n"
        f"[bold]Reach:[/bold] {int(reach):,}\n"
        f"[bold]Clicks:[/bold] {int(clicks):,}\n"
        f"[bold]CTR:[/bold] {float(ctr):.2f}%\n"
        f"[bold]CPC:[/bold] ${float(cpc):,.2f}\n"
        f"[bold]CPM:[/bold] ${float(cpm):,.2f}",
        title=f"Account Summary ({date_preset})",
        border_style="blue",
    )
    console.print(panel)


@app.command("insights")
def get_insights(
    level: InsightLevel = typer.Option(InsightLevel.CAMPAIGN, help="Level: account, campaign, adset, ad"),
    date_preset: DatePreset = typer.Option(DatePreset.LAST_7D, help="Date preset"),
    campaign_id: str = typer.Option(None, help="Filter by campaign ID"),
    breakdowns: str = typer.Option(None, help="Comma-separated breakdowns: age,gender,country"),
    limit: int = typer.Option(50),
):
    """Get detailed ad insights."""
    breakdown_list = [Breakdown(b.strip()) for b in breakdowns.split(",")] if breakdowns else []

    request = ReportRequest(
        level=level, date_preset=date_preset, campaign_id=campaign_id,
        breakdowns=breakdown_list, limit=limit,
    )
    result = svc.get_insights(request)

    if not result.data:
        console.print("[yellow]No data for this query.[/yellow]")
        return

    table = Table(title=f"Insights ({level.value} level, {date_preset.value})")
    table.add_column("Campaign", style="cyan")
    table.add_column("Impressions", justify="right")
    table.add_column("Clicks", justify="right")
    table.add_column("CTR", justify="right")
    table.add_column("CPC", justify="right")
    table.add_column("Spend", justify="right")

    for row in result.data:
        table.add_row(
            row.campaign_name or row.campaign_id or "—",
            row.impressions or "0",
            row.clicks or "0",
            f"{float(row.ctr or 0):.2f}%",
            f"${float(row.cpc or 0):.2f}",
            f"${float(row.spend or 0):,.2f}",
        )

    console.print(table)
    console.print(f"\n[dim]Total rows: {result.total_count}[/dim]")


@app.command("campaign")
def campaign_performance(
    campaign_id: str = typer.Argument(..., help="Campaign ID"),
    date_preset: str = typer.Option("last_7d"),
):
    """Show daily performance for a campaign."""
    rows = svc.get_campaign_performance(campaign_id, date_preset=date_preset)

    if not rows:
        console.print("[yellow]No data available.[/yellow]")
        return

    table = Table(title=f"Campaign {campaign_id} — Daily Performance")
    table.add_column("Date")
    table.add_column("Impressions", justify="right")
    table.add_column("Clicks", justify="right")
    table.add_column("CTR", justify="right")
    table.add_column("CPC", justify="right")
    table.add_column("Spend", justify="right")

    for row in rows:
        table.add_row(
            row.date_start or "—",
            row.impressions or "0",
            row.clicks or "0",
            f"{float(row.ctr or 0):.2f}%",
            f"${float(row.cpc or 0):.2f}",
            f"${float(row.spend or 0):,.2f}",
        )

    console.print(table)
