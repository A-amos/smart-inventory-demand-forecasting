"""Create a local authorized account without a public registration endpoint."""
import argparse
import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.database import SessionLocal
from app.models import User


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--role", choices=["manager", "researcher"], default="manager")
    args = parser.parse_args()
    password = getpass.getpass("Password (minimum 12 characters): ")
    if not 12 <= len(password) <= 128 or password != getpass.getpass("Confirm password: "):
        raise SystemExit("Passwords must match and contain 12–128 characters")
    email = args.email.strip().lower()
    if "@" not in email or len(email) > 254 or not args.name.strip() or len(args.name) > 120:
        raise SystemExit("A valid email and name are required")
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == email)):
            raise SystemExit("Account already exists; no changes made")
        db.add(User(email=email, name=args.name.strip(), role=args.role, password_hash=hash_password(password)))
        db.commit()
    print("Authorized account created")


if __name__ == "__main__":
    main()
