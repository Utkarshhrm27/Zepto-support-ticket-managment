from app.models import Order

def refund_amount(action: str, order: Order) -> int:
    amounts = {
        "full_refund": order.value_inr,
        "refund_reissue": order.value_inr,
        "partial_refund": round(order.value_inr * 0.5),
        "coupon": min(50, order.value_inr),
        "redelivery": 0,
        "apology_no_action": 0,
        "escalation": 0,
    }
    return min(amounts.get(action, 0), order.value_inr)
