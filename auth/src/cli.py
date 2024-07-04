import asyncio
from typing import Annotated

import typer

from schemas.entity import UserCreate, UserRead
from storages.postgres import get_dbm

dbm = get_dbm()


async def create_superuser(email: str, password: str):
    return await dbm.create_user(
        UserCreate(
            email=email,
            password=password,
            is_active=True,
            is_superuser=True,
            is_verified=False,
        )
    )


def main(
    email: Annotated[str, typer.Option(prompt=True, confirmation_prompt=True)],
    password: Annotated[
        str,
        typer.Option(prompt=True, confirmation_prompt=True, hide_input=True),
    ],
):
    superuser = asyncio.run(create_superuser(email, password))
    print(f"Superuser created: {UserRead.model_validate(superuser)}")


if __name__ == "__main__":
    typer.run(main)
