from django import template

register = template.Library()

@register.filter
def format_price(value):
    try:
        # Chuyển số thành chuỗi và thêm dấu phẩy
        formatted_price = "{:,}".format(int(value))
        # Thêm đơn vị tiền tệ VNĐ và /1h
        return f"{formatted_price} VNĐ/1h"
    except (ValueError, TypeError):
        return value 