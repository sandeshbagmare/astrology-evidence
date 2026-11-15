import pytest

from astrology_evidence.db import create_db
from astrology_evidence.manage import main
from astrology_evidence.models import User


def test_operator_grant_requires_existing_user(tmp_path, monkeypatch, capsys):
    url = f"sqlite:///{tmp_path}/db"
    db = create_db(url)
    db.initialize()
    with db.session() as session:
        user = User(issuer="fixture", subject="fixture")
        session.add(user)
        session.flush()
        user_id = user.id
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setattr("sys.argv", ["manage", "grant-curator", "missing"])
    with pytest.raises(SystemExit):
        main()
    monkeypatch.setattr("sys.argv", ["manage", "grant-curator", user_id])
    main()
    with db.session() as session:
        assert session.get(User, user_id).is_admin
    monkeypatch.setattr("sys.argv", ["manage", "users"])
    main()
    assert "fixture" not in capsys.readouterr().out
