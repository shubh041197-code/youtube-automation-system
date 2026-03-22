import typer
from rich.console import Console
from rich.table import Table

from meta_ads.services.creative_service import CreativeService
from meta_ads.models.creatives import CreativeCreate, CreativeFormat, CallToAction

app = typer.Typer(help="Manage ad creatives")
console = Console()
svc = CreativeService()


@app.command("create")
def create_creative(
    name: str = typer.Option(..., help="Creative name"),
    page_id: str = typer.Option(..., help="Facebook Page ID"),
    link: str = typer.Option(None, help="Destination URL"),
    message: str = typer.Option(None, help="Ad copy / primary text"),
    headline: str = typer.Option(None, help="Headline"),
    description: str = typer.Option(None, help="Description"),
    image_hash: str = typer.Option(None, help="Image hash from upload"),
    image_url: str = typer.Option(None, help="Image URL"),
    format: CreativeFormat = typer.Option(CreativeFormat.IMAGE, help="Ad format"),
    cta: CallToAction = typer.Option(CallToAction.LEARN_MORE, help="Call to action"),
):
    """Create an ad creative."""
    data = CreativeCreate(
        name=name, page_id=page_id, link=link, message=message,
        headline=headline, description=description,
        image_hash=image_hash, image_url=image_url,
        format=format, call_to_action=cta,
    )
    result = svc.create_creative(data)
    console.print(f"[green]Creative created:[/green] {result.id} — {result.name}")


@app.command("list")
def list_creatives():
    """List all ad creatives."""
    creatives = svc.list_creatives()
    if not creatives:
        console.print("[yellow]No creatives found.[/yellow]")
        return

    table = Table(title="Ad Creatives")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Status")

    for c in creatives:
        table.add_row(c.id, c.name or "—", c.status or "—")

    console.print(table)


@app.command("get")
def get_creative(creative_id: str = typer.Argument(...)):
    """Get creative details."""
    c = svc.get_creative(creative_id)
    console.print_json(c.model_dump_json())


@app.command("upload-image")
def upload_image(image_path: str = typer.Argument(..., help="Path to image file")):
    """Upload an image for use in creatives."""
    result = svc.upload_image(image_path)
    console.print(f"[green]Image uploaded![/green] Hash: {result.hash}")
    if result.url:
        console.print(f"URL: {result.url}")


@app.command("delete")
def delete_creative(creative_id: str = typer.Argument(...)):
    """Delete a creative."""
    svc.delete_creative(creative_id)
    console.print(f"[red]Deleted creative:[/red] {creative_id}")
