from pydantic import BaseModel

class ProductMetric(BaseModel):
    product: str
    units_sold: int
    revenue: float

class SalesMetrics(BaseModel):
    row_count: int
    total_units_sold: int
    total_revenue: float
    average_unit_price: float | None
    distinct_products: int
    top_product_by_quantity: str | None
    top_product_by_revenue: str | None
    products: list[ProductMetric]
