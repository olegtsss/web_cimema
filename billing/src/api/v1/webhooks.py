import json
from ipaddress import ip_address, ip_network

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import ValidationError

from api.v1.utils import decode_yapay_token, get_yapay_public_jwks, payment_success
from core.config import settings
from schemas.webhooks import UkassaCallBackData, YapayCallBackData
from storages.cache import cache

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post(
    "/yapay",
    status_code=status.HTTP_200_OK,
)
async def get_webhook_from_yapay(request: Request) -> JSONResponse:
    """Webhook сервиса Yapay."""

    public_jwks = await cache.get("public_jwks")
    if not public_jwks:
        public_jwks = await get_yapay_public_jwks()
        await cache.put("public_jwks", public_jwks, ex=settings.jwk_cache_lifetime)
    token = await request.body()
    decoded_data = await decode_yapay_token(
        token=token.decode("utf-8"), public_jwks=public_jwks
    )
    if not decoded_data:
        public_jwks = await get_yapay_public_jwks()
        await cache.put("public_jwks", public_jwks, ex=settings.jwk_cache_lifetime)
        decoded_data = await decode_yapay_token(token=token, public_jwks=public_jwks)
    if not decoded_data:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid jwk")
    try:
        data = YapayCallBackData(
            merchant_id=decoded_data.get("merchantId"),
            product_id=decoded_data.get("order").get("orderId"),
        )
    except (ValidationError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid decoded data"
        )
    if str(data.merchant_id) != settings.yandex_merchant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid merchantId"
        )
    logger.info(f"Получен платеж по заказу {data.product_id}")
    await payment_success(order_id=data.product_id)
    return JSONResponse(status_code=status.HTTP_200_OK, content="OK")


@router.post(
    "/ukassa",
    status_code=status.HTTP_200_OK,
)
async def get_webhook_from_ukassa(request: Request) -> JSONResponse:
    """Webhook сервиса Yapay."""

    merchant_ip = request.client.host
    for network in settings.yookassa_merchant_ip_addresses:
        if ip_address(merchant_ip) in ip_network(network):
            data = await request.body()
            try:
                data = json.loads(data.decode("utf-8"))
                order = UkassaCallBackData(
                    payment_status=data.get("object").get("status"),
                    product_id=data.get("object").get("id"),
                )
            except (ValidationError, AttributeError, ValueError):
                logger.error(f"Не пройдена валидация принятых даных: {data}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="Invalid input data"
                )
            if order.payment_status != "succeeded":
                logger.error(f"Не верный статус заказа: {order.payment_status}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid payment status",
                )
            logger.info(f"Получен платеж по заказу {order.product_id}")
            await payment_success(order_id=order.product_id)
            return JSONResponse(status_code=status.HTTP_200_OK, content="OK")
    logger.error(f"Попытка доступа с неизвестного адреса: {merchant_ip}")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="error")
