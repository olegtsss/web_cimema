from uuid import UUID

from schemas.entity import CustomBaseModel


class YapayCallBackData(CustomBaseModel):
    merchant_id: UUID
    product_id: UUID


class UkassaCallBackData(CustomBaseModel):
    payment_status: str
    product_id: UUID
