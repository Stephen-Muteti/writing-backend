from app.extensions import db
from app.models.bid import Bid
from app.models.order import Order
from datetime import datetime, timedelta
from app.utils.response_formatter import error_response

def place_bid(order_id, user_id, bid_amount, message=None, estimated_completion=None):
    order = Order.query.get(order_id)
    if not order:
        raise ValueError("Order not found")

    # Prevent multiple open bids by same user
    existing_bid = Bid.query.filter_by(order_id=order_id, user_id=user_id, status="open").first()
    if existing_bid:
        raise ValueError("You already have an active bid on this order")

    bid = Bid(
        order_id=order_id,
        user_id=user_id,
        bid_amount=bid_amount,
        original_budget=order.budget,
        message=message,
        response_deadline=datetime.utcnow() + timedelta(days=3)  # default client response window
    )

    # Assign estimated completion if provided (already validated as datetime)
    if estimated_completion and isinstance(estimated_completion, datetime):
        bid.response_deadline = estimated_completion

    db.session.add(bid)
    db.session.commit()
    return bid
