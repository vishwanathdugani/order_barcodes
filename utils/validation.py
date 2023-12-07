from pydantic import BaseModel, field_validator


class OrderModel(BaseModel):
    order_id: str
    customer_id: str


class BarcodeModel(BaseModel):
    barcode: str
    order_id: str = None

    @field_validator('barcode')
    def validate_order_id(cls, v):
        if not v:
            raise ValueError("barcode is required")
        return v
