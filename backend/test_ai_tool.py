
import json

from app.ai_tools import lookup_customer_order


def test_order(order_id: str):
    print(f"\nTesting {order_id}")

    result = lookup_customer_order.invoke({
        "order_id": order_id
    })

    data = json.loads(result)
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    test_order("ORD-101")
    test_order("ORD-102")
    test_order("ORD-103")
    test_order("ORD-999")
