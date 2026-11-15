"""Local operator commands; never exposes a public administrator signup."""

import argparse
import json
from pathlib import Path

from sqlalchemy import select

from astrology_evidence.config import Settings
from astrology_evidence.corpus import CorpusService
from astrology_evidence.db import create_db
from astrology_evidence.models import User


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("users", help="List opaque IDs and administrator status only")
    grant = sub.add_parser("grant-curator")
    grant.add_argument("user_id")
    ingest = sub.add_parser("import-edition")
    ingest.add_argument("path", type=Path)
    args = parser.parse_args()
    settings = Settings()
    db = create_db(settings.database_url)
    if args.command == "import-edition":
        if args.path.stat().st_size > 5_000_000:
            parser.error("Edition JSON exceeds 5MB")
        payload = json.loads(args.path.read_text(encoding="utf-8-sig"))
        print(json.dumps({"edition_id": CorpusService(db).import_edition(payload)}))
    else:
        with db.session() as session:
            if args.command == "users":
                print(
                    json.dumps(
                        [
                            {"id": u.id, "is_admin": u.is_admin}
                            for u in session.scalars(select(User).where(User.deleted_at.is_(None)))
                        ]
                    )
                )
            else:
                user = session.get(User, args.user_id)
                if user is None or user.deleted_at:
                    parser.error("Active user not found")
                user.is_admin = True
                print("Curator role granted.")
    db.engine.dispose()


if __name__ == "__main__":
    main()
