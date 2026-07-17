from pydantic import BaseModel
from typing import Literal, Optional


class ProductSearchItem(BaseModel):
    id: int                                  # PrdCustomerProduct.id
    customer_id: int
    customer_name: Optional[str] = None
    customer_model: Optional[str] = None
    product_name: Optional[str] = None       # 中文全称
    product_name_en: Optional[str] = None    # 英文全称
    product_short_name: Optional[str] = None # 中文简称
    product_short_name_en: Optional[str] = None
    detail_desc: Optional[str] = None
    brand: Optional[str] = None
    customer_code: Optional[str] = None      # 主客户产品编号
    product_code: Optional[str] = None       # 系统产品编号
    price_usd: Optional[float] = None
    image_url: Optional[str] = None
    sub_images: list[str] = []
    oes: list[str] = []
    matched_in: list[Literal[
        "customer_model",
        "product_name",
        "product_name_en",
        "product_short_name",
        "product_short_name_en",
        "detail_desc",
        "oe",
    ]] = []
    match_score: float

    class Config:
        from_attributes = True


class ProductSearchResponse(BaseModel):
    results: list[ProductSearchItem]
    total: int

    class Config:
        from_attributes = True
