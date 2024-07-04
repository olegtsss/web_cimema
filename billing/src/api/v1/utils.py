import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

import aiohttp
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
from loguru import logger

from core.config import PUBLIC_KEY
from schemas.orders import (OrderEventSchema, OrderEventTypeEnum,
                            OrderStatusEnum, PaymentSchema,
                            UpdateOrderSchemaAfterWebhook)
from schemas.subs import CreateSubSchema, SubEventSchema
from storages.storage import storage

YANDEX_JWK_ENDPOINT = "https://sandbox.pay.yandex.ru/api/jwks"


def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            audience="BILLING",
        )
    except Exception:
        return None

    try:
        UUID(payload.get("sub"))
    except Exception:
        return None

    return payload


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> dict:
        credentials = await super().__call__(request)

        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code",
            )

        if not credentials.scheme == "Bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Only Bearer token might be accepted",
            )

        decoded_token = self.parse_token(credentials.credentials)
        if not decoded_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired token",
            )

        return decoded_token

    @staticmethod
    def parse_token(jwt_token: str) -> Optional[dict]:
        return decode_token(jwt_token)


security_jwt = JWTBearer()


async def security_admin_jwt(
    jwt_payload: dict = Depends(security_jwt),
) -> dict[Any, Any]:
    """Зависмость проверки jwt-пользователя.

    Рейзит `403` ошибку, если роль `ADMIN` не была найдена в ролях
    пользователя.
    """
    user_roles = jwt_payload.get("roles")
    if user_roles is None or "ADMIN" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )

    return jwt_payload


async def get_yapay_public_jwks() -> dict:
    try:
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(YANDEX_JWK_ENDPOINT) as response:
                return await response.json()
    except (aiohttp.ClientConnectorError, aiohttp.ContentTypeError) as error:
        logger.error(
            "Запрос получения публичных ключей для JWT от серверов Яндекс "
            "завершился не удачей: {error}"
        )


async def decode_yapay_token(
    token: str, public_jwks: dict, algorithms: list = ["ES256"]
) -> dict:
    try:
        return jwt.decode(token, public_jwks, algorithms=algorithms)
    except JWTError as error:
        logger.error(
            f"При декодировании полученного JWT токена возникла ошибка: {error}"
        )


async def payment_success(
    order_id: UUID, data: dict = {"from": "Getted webhook from provider"}
) -> None:
    """Действия после получения webhook об оплате заказа."""

    order = await storage.get_order(order_id=order_id)
    # Создаем платеж
    new_order_payment = await storage.create_payment(
        create_payment=PaymentSchema(
            payment_id=uuid4(),
            order_id=order_id,
            data=data,
            created=datetime.datetime.now(),
        )
    )
    # Создаем событие оплаты заказа
    new_order_event = await storage.create_order_event(
        create_order_event=OrderEventSchema(
            event_id=uuid4(),
            order_id=order_id,
            event_type=OrderEventTypeEnum.PAYMENT_CREATED,
            description="The order has been paid",
            data=data,
            created=datetime.datetime.now(),
        )
    )
    # Обновляем заказ
    order = await storage.update_order(
        order_id=order_id,
        update_order_schema=UpdateOrderSchemaAfterWebhook(
            status=OrderStatusEnum.ACTIVE, updated=datetime.datetime.now()
        ),
    )
    # Создаем событие активации заказа
    new_order_event = await storage.create_order_event(
        create_order_event=OrderEventSchema(
            event_id=uuid4(),
            order_id=order.order_id,
            event_type=OrderEventTypeEnum.ACTIVATED,
            description="The order has been activated",
            data=data,
            created=datetime.datetime.now(),
        )
    )
    # Создаем соответствующую подписку пользователя
    new_sub = await storage.create_sub(
        create_sub_schema=CreateSubSchema(
            order_id=order.order_id,
            plan_id=order.plan_id,
            user_id=order.user_id,
            expired=order.expired,
        )
    )
    # Создаем событие создания для подписки
    new_sub_event = await storage.create_sub_event(
        create_sub_event=SubEventSchema(
            event_id=uuid4(),
            sub_id=new_sub.sub_id,
            description="Subscription has been created",
            data=data,
            created=datetime.datetime.now(),
        )
    )
