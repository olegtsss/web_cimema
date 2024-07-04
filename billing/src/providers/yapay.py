from enum import Enum
from functools import wraps
from uuid import UUID, uuid4

import aiohttp
from loguru import logger

from core.config import settings
from schemas.orders import OrderYapayStatus


class YaPay:
    def __init__(self):
        self.merchant_key = settings.yandex_merchant_id
        self.merchant_url = "https://sandbox.pay.yandex.ru/"
        self.request_timeout = 10
        self.order_ttl = 60 * 10

    @staticmethod
    def http_exception_handler(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except aiohttp.ClientError as error:
                logger.error(error)

        return wrapper

    def get_http_headers(self, attempt: int = 1) -> dict:
        return {
            "Accept": "application/json",
            "Authorization": f"Api-Key {self.merchant_key}",
            "X-Request-Id": str(uuid4()),
            "X-Request-Timeout": str(self.request_timeout),
            "X-Request-Attempt": str(attempt),
        }

    @http_exception_handler
    async def get_payment_url(
        self, product_id: UUID, order_id: UUID, price: float, title: str = "test_title"
    ) -> str:
        """Запрос на создание ссылки на оплату заказа."""

        price = str(price)
        body = {
            "cart": {
                "items": [
                    {
                        "productId": str(product_id),
                        "quantity": {
                            "count": "1",
                        },
                        "title": title,
                        "total": price,
                    }
                ],
                "total": {
                    "amount": price,
                },
            },
            "currencyCode": "RUB",
            "orderId": str(order_id),
            "redirectUrls": {
                "onAbort": settings.redirect_url_on_abort,
                "onError": settings.redirec_url_on_error,
                "onSuccess": settings.redirect_url_on_success,
            },
            "ttl": self.order_ttl,
        }
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.post(
                url=self.merchant_url + "api/merchant/v1/orders",
                headers=self.get_http_headers(),
                json=body,
            ) as response:
                result = await response.json()
                payment_url = result.get("data").get("paymentUrl")
                return payment_url

    @http_exception_handler
    async def get_order_payment_status(self, order_id: UUID) -> OrderYapayStatus:
        """Запрос на получение статуса заказа."""

        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.get(
                url=self.merchant_url + f"api/merchant/v1/orders/{order_id}",
                headers=self.get_http_headers(),
            ) as response:
                result = await response.json()
        payment_status = result.get("data").get("order").get("paymentStatus")
        return payment_status

    @http_exception_handler
    async def cancel_order_payment_full(
        self, order_id: UUID, price: float
    ) -> OrderYapayStatus:
        """Запрос на полный возврат."""

        body = {"refundAmount": str(price)}

        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.post(
                url=self.merchant_url + f"api/merchant/v2/orders/{order_id}/refund",
                headers=self.get_http_headers(),
                json=body,
            ) as response:
                result = await response.json()
        payment_status = (
            result.get("data").get("operation").get("operationType")
        )  # ожидается REFUND
        return payment_status

    @http_exception_handler
    async def cancel_order_payment(
        self, product_id: UUID, order_id: UUID, price: float, refund_amount: float
    ) -> OrderYapayStatus:
        """Запрос на частичный возврат."""

        body = {
            # "externalOperationId": str(uuid4()),  # можно присвоить свой номер возврату
            "refundAmount": str(refund_amount),
            "targetCart": {
                "items": [
                    {"price": str(price - refund_amount), "productId": str(product_id)}
                ]
            },
        }

        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.post(
                url=self.merchant_url + f"api/merchant/v2/orders/{order_id}/refund",
                headers=self.get_http_headers(),
                json=body,
            ) as response:
                result = await response.json()
        payment_status = (
            result.get("data").get("operation").get("operationType")
        )  # ожидается REFUND
        return payment_status

    @http_exception_handler
    async def rallback_order_payment(self, order_id: UUID) -> OrderYapayStatus:
        """
        Запрос на отмену платежа. Запрещает дальнейшую оплату заказа,
        а также, если оплата уже произошла, производит полный возврат
        средств клиенту. В случае успеха статус платежа изменится на FAILED.
        """

        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.post(
                url=self.merchant_url + f"api/merchant/v1/orders/{order_id}/rollback",
                headers=self.get_http_headers(),
            ) as response:
                result = await response.json()
        status = result.get("status")  # ожидается 'success'
        return status

    @http_exception_handler
    async def get_subscription_url(
        self,
        product_id: UUID,
        order_id: UUID,
        price: float,
        interval_count: int,
        title: str = "test_title",
    ) -> str:
        """Запрос на создание ссылки на оплату подписки."""

        price = str(price)
        body = {
            "cart": {
                "items": [
                    {
                        "productId": str(product_id),
                        "quantity": {
                            "count": "1",
                        },
                        "title": title,
                        "total": price,
                    }
                ],
                "total": {
                    "amount": price,
                },
            },
            "currencyCode": "RUB",
            "intervalCount": interval_count,
            "intervalUnit": "MONTH",
            "orderId": str(order_id),
            "redirectUrls": {
                "onAbort": settings.redirect_url_on_abort,
                "onError": settings.redirec_url_on_error,
                "onSuccess": settings.redirect_url_on_success,
            },
            "ttl": self.order_ttl,
        }
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.post(
                url=self.merchant_url + "api/merchant/v1/subscriptions",
                headers=self.get_http_headers(),
                json=body,
            ) as response:
                result = await response.json()
                payment_url = result.get("data").get("paymentUrl")
                subscription_id = result.get("data").get("subscriptionId")
                return payment_url

    @http_exception_handler
    async def get_recur_subscription_url(
        self,
        product_id: UUID,
        order_id: UUID,
        parent_order_id: UUID,
        price: float,
        interval_count: int,
        title: str = "test_title",
    ) -> str:
        """Запрос на создание ссылки на оплату подписки (рекурентной)."""

        price = str(price)
        body = {
            "amount": price,
            "cart": {
                "items": [
                    {
                        "productId": str(product_id),
                        "quantity": {
                            "count": "1",
                        },
                        "title": title,
                        "total": price,
                    }
                ],
                "total": {
                    "amount": price,
                },
            },
            "currencyCode": "RUB",
            "orderId": str(order_id),
            "parentOrderId": str(parent_order_id),
        }
        async with aiohttp.ClientSession(raise_for_status=True) as session:
            async with session.post(
                url=self.merchant_url + "api/merchant/v1/subscriptions/recur",
                headers=self.get_http_headers(),
                json=body,
            ) as response:
                result = await response.json()
                operation_id = result.get("data").get("operationId")
                return operation_id


yapay_service = YaPay()
