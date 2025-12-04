from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from app.models.order import Order
from app.utils.response_formatter import success_response
from app.utils.pagination import paginate_query

bp = Blueprint("available_orders", __name__, url_prefix="/api/v1")

@bp.route("/available-orders", methods=["GET"])
@jwt_required()
def available_orders():
    subject = request.args.get("subject")
    min_budget = request.args.get("min_budget")
    max_budget = request.args.get("max_budget")
    page = request.args.get("page", 1)
    q = Order.query.filter_by(status="pending")
    if subject:
        q = q.filter(Order.subject.ilike(f"%{subject}%"))
    if min_budget:
        try:
            minb = float(min_budget)
            q = q.filter(Order.budget >= minb)
        except:
            pass
    if max_budget:
        try:
            maxb = float(max_budget)
            q = q.filter(Order.budget <= maxb)
        except:
            pass
    items, pagination = paginate_query(q.order_by(Order.created_at.desc()), page, 10)
    orders = []
    for o in items:
        orders.append({
            "id": o.id,
            "title": o.title,
            "subject": o.subject,
            "type": o.type,
            "pages": o.pages,
            "deadline": o.deadline.isoformat() + "Z" if o.deadline else None,
            "budget": o.budget,
            "client_rating": o.client.rating if o.client else None,
            "description": o.description,
            "bids_count": len(o.bids) if hasattr(o, "bids") else 0,
            "posted_at": o.created_at.isoformat() + "Z" if o.created_at else None
        })
    return success_response({"orders": orders, "pagination": pagination})
