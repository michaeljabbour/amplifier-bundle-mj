"""Checkout math for the shop."""
from shop.catalog import PRODUCTS, SHIPPING_FEE


def subtotal(items):
    """items: list of (product_name, quantity) tuples. Returns dollars."""
    return sum(PRODUCTS[name] * qty for name, qty in items)


def compute_total(items):
    """Order total = subtotal + a flat shipping fee."""
    return subtotal(items) + SHIPPING_FEE
