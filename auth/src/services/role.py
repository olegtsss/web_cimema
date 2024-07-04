from functools import lru_cache

from fastapi import Depends, HTTPException, status

from models.entity import Role
from schemas.entity import RoleCreate, RoleUpdate
from storages.postgres import DatabaseManager, get_dbm


@lru_cache
def get_role_service(dbm: DatabaseManager = Depends(get_dbm)) -> "RoleService":
    return RoleService(dbm=dbm)


class RoleService:
    def __init__(self, dbm: DatabaseManager) -> None:
        self.dbm = dbm

    async def get_roles(self) -> list[Role]:
        """Метод получения ролей.

        Возвращает список существующих ролей Role (может быть пустым).
        """
        return await self.dbm.get_roles()

    async def get_role(self, name: str) -> Role:
        """Метод получения роли.

        Обязательные параметры:
        - `name` - название роли

        Возвращает модель Role.
        """
        role = await self.dbm.get_role(name)
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role not found",
            )

        return role

    async def create_role(self, params: RoleCreate) -> Role:
        """Метод создания роли.

        Обязательные параметры:
        - `params` - модель параметров создания роли

        Возвращает модель Role.
        """
        if await self.dbm.get_role(params.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{params.name}' already exists",
            )

        return await self.dbm.create_role(params)

    async def update_role(self, name: str, params: RoleUpdate) -> Role:
        """Метод обновления роли.

        Обязательные параметры:
        - `name` - название роли
        - `params` - модель параметров обновления роли

        Возвращает модель роли Role.
        """
        await self.get_role(name)

        if await self.dbm.get_role(params.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{params.name}' already exists",
            )

        return await self.dbm.update_role(name, params)

    async def delete_role(self, name: str) -> None:
        """Метод удаления роли.

        Обязательные параметры:
        - `name` - название роли
        """
        await self.get_role(name)

        return await self.dbm.delete_role(name)
