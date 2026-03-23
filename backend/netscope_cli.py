"""NetScope CLI - query API and manage configuration."""
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(name="netscope", help="NetScope network observability CLI")
console = Console()


@app.command()
def login(
    url: str = typer.Option("http://localhost:8000", "--url", "-u"),
    username: str = typer.Option("admin", "--user"),
    password: str = typer.Option("admin", "--password", prompt=True, hide_input=True),
):
    """Login and print token."""
    import httpx
    try:
        r = httpx.post(f"{url}/api/v1/auth/login", json={"username": username, "password": password})
        r.raise_for_status()
        data = r.json()
        console.print(f"[green]Token:[/green] {data['access_token'][:50]}...")
        console.print("Set NETSCOPE_TOKEN env or use --token in other commands.")
    except Exception as e:
        console.print(f"[red]Login failed:[/red] {e}")


@app.command()
def devices(
    url: str = typer.Option("http://localhost:8000", "--url", "-u"),
    token: str = typer.Option(None, "--token", "-t", envvar="NETSCOPE_TOKEN"),
):
    """List devices."""
    import httpx
    if not token:
        console.print("[red]Set NETSCOPE_TOKEN or use --token[/red]")
        raise typer.Exit(1)
    try:
        r = httpx.get(f"{url}/api/v1/devices", headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        devices = r.json()
        table = Table(title="Devices")
        table.add_column("IP", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("TX bps")
        table.add_column("RX bps")
        for d in devices:
            table.add_row(
                d.get("ip", ""),
                d.get("status", ""),
                str(d.get("bandwidth_tx_bps", 0)),
                str(d.get("bandwidth_rx_bps", 0)),
            )
        console.print(table)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@app.command()
def alerts(
    url: str = typer.Option("http://localhost:8000", "--url", "-u"),
    token: str = typer.Option(None, "--token", "-t", envvar="NETSCOPE_TOKEN"),
    limit: int = typer.Option(10, "--limit", "-n"),
):
    """List alerts."""
    import httpx
    if not token:
        console.print("[red]Set NETSCOPE_TOKEN or use --token[/red]")
        raise typer.Exit(1)
    try:
        r = httpx.get(f"{url}/api/v1/alerts?limit={limit}", headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        alerts = r.json()
        for a in alerts:
            console.print(f"[yellow]{a.get('severity', '')}[/yellow] {a.get('title', '')}: {a.get('message', '')}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@app.command()
def threat_lookup(
    ip: str = typer.Argument(..., help="IP to lookup"),
    url: str = typer.Option("http://localhost:8000", "--url", "-u"),
    token: str = typer.Option(None, "--token", "-t", envvar="NETSCOPE_TOKEN"),
):
    """Lookup IP in threat intel (AbuseIPDB, VirusTotal, Shodan)."""
    import httpx
    if not token:
        console.print("[red]Set NETSCOPE_TOKEN or use --token[/red]")
        raise typer.Exit(1)
    try:
        r = httpx.get(f"{url}/api/v1/threat-intel/lookup/{ip}", headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        data = r.json()
        console.print(f"[bold]IP:[/bold] {data.get('ip')}")
        console.print(f"[bold]Risk score:[/bold] {data.get('risk_score', 0)}")
        console.print(f"[bold]Sources:[/bold] {', '.join(data.get('sources', []))}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


if __name__ == "__main__":
    app()
