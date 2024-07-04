from functools import wraps
from http import HTTPStatus
from typing import Callable, Optional
from uuid import UUID

import aiohttp
import backoff
from loguru import logger

from core.config import settings
from schemas.auth import SubCreationSchema


class AuthService:
    def __init__(self, session: Optional[aiohttp.ClientSession] = None) -> None:
        self.session = session

    @staticmethod
    def session_handler(method: Callable) -> Callable:
        @wraps(method)
        async def wrapper(self: "AuthService", *args, **kwargs):
            if self.session is None:
                self.session = aiohttp.ClientSession()

            return await method(self, *args, **kwargs)

        return wrapper

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        max_tries=settings.backoff_tries,
        max_time=settings.backoff_time,
    )
    @session_handler
    async def create_sub(
        self, user_id: UUID, create_sub_schema: SubCreationSchema
    ) -> bool:
        url = settings.auth_api_url + f"/users/{user_id}/subs"
        json_data = create_sub_schema.model_dump()

        logger.info(
            f"Requesting Auth API for user '{user_id}' sub"
            f" '{create_sub_schema.sub_id}' creation"
        )
        async with self.session.post(url=url, json=json_data) as response:
            if response.status == HTTPStatus.CREATED:
                logger.info(
                    f"Successfully added sub '{create_sub_schema.sub_id}'"
                    f" to user '{user_id}'"
                )
                return True

            logger.info(
                f"User '{user_id}' sub '{create_sub_schema.sub_id}'" f" creation failed"
            )
            return False

    @backoff.on_exception(
        backoff.expo,
        aiohttp.ClientConnectionError,
        max_tries=settings.backoff_tries,
        max_time=settings.backoff_time,
    )
    @session_handler
    async def delete_sub(self, user_id: UUID, sub_id: UUID) -> bool:
        url = settings.auth_api_url + f"/users/{user_id}/subs/{sub_id}"

        logger.info(f"Requesting Auth API for user '{user_id}' sub '{sub_id}' deletion")
        async with self.session.delete(url=url) as response:
            if response.status == HTTPStatus.NO_CONTENT:
                logger.info(f"Successfully deleted user '{user_id}' sub '{sub_id}'")
                return True

            logger.info(f"User '{user_id}' sub '{sub_id}' deletion failed")
            return False


auth_service = AuthService()
