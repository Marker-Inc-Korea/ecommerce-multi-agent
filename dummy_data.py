# dummy_data.py

# 삼성 제품 목록
PRODUCTS = [
    {"id": "P001", "name": "Galaxy S24 Ultra", "price": 1399.99},
    {"id": "P002", "name": "Galaxy Buds Pro 2", "price": 229.99},
    {"id": "P003", "name": "Galaxy Watch 6 Classic", "price": 399.99},
]

# 주문 정보
ORDERS = [
    {"order_id": "S1001", "status": "Shipped", "items": ["P001", "P002"]},
    {"order_id": "S1002", "status": "Preparing for shipment", "items": ["P003"]},
    {"order_id": "S1003", "status": "Delivered", "items": ["P001"]},
]

# 반품 요청 목록
RETURNS = []
