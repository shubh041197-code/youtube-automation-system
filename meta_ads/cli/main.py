import typer

from meta_ads.cli import campaigns, creatives, audiences, reporting, budget

app = typer.Typer(
    name="meta-ads",
    help="Meta Ads Automation CLI — manage campaigns, creatives, audiences, reports, and budgets.",
    no_args_is_help=True,
)

app.add_typer(campaigns.app, name="campaigns")
app.add_typer(creatives.app, name="creatives")
app.add_typer(audiences.app, name="audiences")
app.add_typer(reporting.app, name="reports")
app.add_typer(budget.app, name="budget")


if __name__ == "__main__":
    app()
