from uuid import UUID, uuid4

import aiohttp

from core.config import settings
from schemas.orders import OrderUkassaStatus


class Ukassa:
    def __init__(self):
        self.merchant_url = "https://api.yookassa.ru"

    def get_http_headers(self, idempotence_key: UUID) -> dict:
        return {
            "Content-Type": "application/json",
            "Idempotence-Key": idempotence_key or str(uuid4()),
        }

    async def get_payment_url(
        self, price: float, description: str = "test_description"
    ) -> str:
        """Запрос на создание ссылки на оплату заказа."""

        body = {
            "amount": {"value": str(price), "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": settings.redirect_url_on_success,
            },
            "capture": True,
            "description": description,
        }
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.post(
                url=self.merchant_url + "/v3/payments",
                headers=self.get_http_headers(idempotence_key=str(uuid4())),
                auth=aiohttp.BasicAuth(
                    settings.yookassa_merchant_id, settings.yookassa_merchant_key
                ),
                json=body,
            ) as response:
                result = await response.json()
        return (result.get("id"), result.get("confirmation").get("confirmation_url"))

    async def get_order_payment_status(self, order_id: UUID) -> OrderUkassaStatus:
        """Запрос на получение статуса заказа."""

        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(
                url=self.merchant_url + f"/v3/payments/{order_id}",
                headers=self.get_http_headers(idempotence_key=str(uuid4())),
                auth=aiohttp.BasicAuth(
                    settings.yookassa_merchant_id, settings.yookassa_merchant_key
                ),
            ) as response:
                result = await response.json()
        return result.get("status")

    async def cancel_order_payment(self, order_id: UUID, price: float) -> str:
        """Запрос на полный возврат."""

        body = {
            "amount": {"value": str(price), "currency": "RUB"},
            "payment_id": str(order_id),
        }
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.post(
                url=self.merchant_url + "/v3/refunds",
                headers=self.get_http_headers(idempotence_key=str(uuid4())),
                auth=aiohttp.BasicAuth(
                    settings.yookassa_merchant_id, settings.yookassa_merchant_key
                ),
                json=body,
            ) as response:
                result = await response.json()
        return result.get("id")

    async def get_cancel_order_payment_status(
        self, order_id: UUID
    ) -> OrderUkassaStatus:
        """Запрос на получение статуса отмененного заказа."""

        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(
                url=self.merchant_url + f"/v3/refunds/{order_id}",
                headers=self.get_http_headers(idempotence_key=str(uuid4())),
                auth=aiohttp.BasicAuth(
                    settings.yookassa_merchant_id, settings.yookassa_merchant_key
                ),
            ) as response:
                result = await response.json()
        return result.get("status")

    async def rallback_order_payment(self, order_id: UUID) -> OrderUkassaStatus:
        """
        Запрос на отмену платежа. Отменяет платеж, находящийся в статусе
        waiting_for_capture. После отмены провайдер начинает возврат денег
        на счет плательщика.
        """

        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(
                url=self.merchant_url + f"/v3/payments/{order_id}/cancel",
                headers=self.get_http_headers(idempotence_key=str(uuid4())),
                auth=aiohttp.BasicAuth(
                    settings.yookassa_merchant_id, settings.yookassa_merchant_key
                ),
            ) as response:
                result = await response.json()
        return result.get("status")


ukassa_service = Ukassa()
