"""Command-line tasks.

Create the first admin (prompts for a password):
    python -m app.cli create-admin --email owner@example.com --name "Store Owner"
"""

import typer

from app.db.session import SessionLocal
from app.modules.identity import service
from app.modules.identity.models import Role
from app.modules.identity.schemas import MIN_PASSWORD_LENGTH, UserCreate

cli = typer.Typer(no_args_is_help=True)


@cli.callback()
def main() -> None:
    """StocktoShip admin commands."""


@cli.command("create-admin")
def create_admin(
    email: str = typer.Option(..., help="Admin login email"),
    name: str = typer.Option(..., help="Full name"),
    password: str = typer.Option(
        ...,
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help=f"At least {MIN_PASSWORD_LENGTH} characters",
    ),
) -> None:
    data = UserCreate(email=email, full_name=name, password=password, role=Role.ADMIN)
    with SessionLocal() as db:
        try:
            user = service.create_user(db, data, actor_id=None)
        except service.EmailAlreadyExists:
            typer.echo(f"A user with email {email} already exists.", err=True)
            raise typer.Exit(code=1) from None
    typer.echo(f"Created admin #{user.id} <{user.email}>")


if __name__ == "__main__":
    cli()
