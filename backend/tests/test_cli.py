"""The create-admin command used to bootstrap a new installation."""

from typer.testing import CliRunner

from app import cli as cli_module
from app.modules.identity import service


def test_create_admin_command(db, monkeypatch):
    # Run the command inside the test transaction so it is rolled back afterwards.
    class _Ctx:
        def __enter__(self):
            return db

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(cli_module, "SessionLocal", lambda: _Ctx())

    runner = CliRunner()
    result = runner.invoke(
        cli_module.cli,
        ["create-admin", "--email", "Owner@Store.com", "--name", "Store Owner"],
        input="a-strong-password\na-strong-password\n",
    )
    assert result.exit_code == 0, result.output
    assert "Created admin" in result.output

    user = service.get_by_email(db, "owner@store.com")
    assert user is not None and user.role == "admin"

    # Running it again for the same email fails cleanly
    again = runner.invoke(
        cli_module.cli,
        ["create-admin", "--email", "owner@store.com", "--name", "Dup"],
        input="a-strong-password\na-strong-password\n",
    )
    assert again.exit_code == 1
