"""Schema marshmallow, mỗi resource một file: products.py <-> api/products.py, orders.py <-> api/orders.py.

Nguyên tắc: schema là hàm thuần - không gọi DB trong validate (kiểm tra
tồn tại/trùng lặp với DB làm ở tầng resource).
"""
