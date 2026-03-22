import typer
from rich.console import Console
from rich.table import Table

from meta_ads.services.audience_service import AudienceService
from meta_ads.models.audiences import CustomAudienceCreate, LookalikeAudienceCreate, AudienceSubtype

app = typer.Typer(help="Manage audiences")
console = Console()
svc = AudienceService()


@app.command("create-custom")
def create_custom_audience(
    name: str = typer.Option(..., help="Audience name"),
    subtype: AudienceSubtype = typer.Option(AudienceSubtype.CUSTOM),
    description: str = typer.Option(None),
    pixel_id: str = typer.Option(None, help="Meta Pixel ID (for website audiences)"),
    retention_days: int = typer.Option(None, help="Retention period in days"),
):
    """Create a custom audience."""
    data = CustomAudienceCreate(
        name=name, subtype=subtype, description=description,
        pixel_id=pixel_id, retention_days=retention_days,
    )
    result = svc.create_custom_audience(data)
    console.print(f"[green]Custom audience created:[/green] {result.id} — {result.name}")


@app.command("create-lookalike")
def create_lookalike_audience(
    name: str = typer.Option(..., help="Audience name"),
    source_audience_id: str = typer.Option(..., help="Source custom audience ID"),
    country: str = typer.Option(..., help="Country code (e.g., US)"),
    ratio: float = typer.Option(0.01, help="Lookalike ratio 0.01-0.20 (1%-20%)"),
):
    """Create a lookalike audience from an existing audience."""
    data = LookalikeAudienceCreate(
        name=name, source_audience_id=source_audience_id,
        country=country, ratio=ratio,
    )
    result = svc.create_lookalike_audience(data)
    console.print(f"[green]Lookalike audience created:[/green] {result.id} — {result.name}")


@app.command("list")
def list_audiences():
    """List all audiences."""
    audiences = svc.list_audiences()
    if not audiences:
        console.print("[yellow]No audiences found.[/yellow]")
        return

    table = Table(title="Audiences")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Subtype")
    table.add_column("Size")

    for a in audiences:
        size = f"{a.approximate_count:,}" if a.approximate_count else "—"
        table.add_row(a.id, a.name, a.subtype or "—", size)

    console.print(table)


@app.command("get")
def get_audience(audience_id: str = typer.Argument(...)):
    """Get audience details."""
    a = svc.get_audience(audience_id)
    console.print_json(a.model_dump_json())


@app.command("delete")
def delete_audience(audience_id: str = typer.Argument(...)):
    """Delete an audience."""
    svc.delete_audience(audience_id)
    console.print(f"[red]Deleted audience:[/red] {audience_id}")
