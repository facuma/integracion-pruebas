from pydantic import BaseModel
from typing import List

class AddressIn(BaseModel):
    """Address schema matching Logística API actual implementation"""
    street: str
    number: int
    postal_code: str
    locality_name: str

class CheckoutShippingProduct(BaseModel):
    id: int
    quantity: int

class CheckoutWithShippingIn(BaseModel):
    delivery_address: AddressIn
    transport_type: str  # "air" | "road" | "rail" | "sea"