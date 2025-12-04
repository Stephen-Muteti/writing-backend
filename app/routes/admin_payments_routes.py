from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.transaction import Transaction
from app.utils.response_formatter import success_response, error_response
from app.extensions import db
from sqlalchemy import or_
from app.services.payment_service import get_balance_for_user
from app.services.notification_service import send_notification_to_user

bp = Blueprint("admin_payments", __name__, url_prefix="/api/v1/admin")

def require_admin():
    uid = get_jwt_identity()
    user = User.query.get(uid)

    if not user or user.role != "admin":
        return None, error_response("FORBIDDEN", "Admin access required", status=403)

    return user, None


# ==========================================================
#  GET /admin/withdrawals
#  Filters:
#    page, limit
#    status=pending|approved|rejected
#    search (writer name or email)
# ==========================================================
@bp.route("/withdrawals", methods=["GET"])
@jwt_required()
def admin_list_withdrawals():
    admin, err = require_admin()
    if err:
        return err

    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))
    status = request.args.get("status")
    search = request.args.get("search")

    q = Transaction.query.filter_by(type="withdrawal")

    if status:
        q = q.filter(Transaction.status == status)

    if search:
        q = q.join(User).filter(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )

    total = q.count()
    items = (
        q.order_by(Transaction.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    withdrawals = []
    for t in items:

        # NEW: balance snapshot
        balance_snapshot = get_balance_for_user(t.user)

        withdrawals.append({
            "id": t.id,
            "amount": t.amount,
            "status": t.status,
            "created_at": t.created_at.isoformat() + "Z",
            "writer": {
                "id": t.user.id,
                "name": t.user.full_name,
                "email": t.user.email,
                "avatar": t.user.profile_image,
                "balance_snapshot": balance_snapshot
            }
        })

    pagination = {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
    }

    return success_response({"withdrawals": withdrawals, "pagination": pagination})


# ==========================================================
#  PATCH /admin/withdrawals/<id>/approve
# ==========================================================
@bp.route("/withdrawals/<wid>/approve", methods=["PATCH"])
@jwt_required()
def admin_approve_withdrawal(wid):
    admin, err = require_admin()
    if err:
        return err

    txn = Transaction.query.filter_by(id=wid, type="withdrawal").first()
    if not txn:
        return error_response("NOT_FOUND", "Withdrawal request not found", status=404)

    if txn.status != "pending":
        return error_response("INVALID_STATE", "Only pending withdrawals can be approved", status=400)

    txn.status = "approved"
    db.session.commit()

    # -----------------------------
    # SEND NOTIFICATION
    # -----------------------------
    send_notification_to_user(
        email=txn.user.email,
        title="Withdrawal Approved",
        message=f"Your withdrawal request of ${txn.amount:.2f} on {txn.created_at.strftime('%Y-%m-%d')} has been approved.",
        notif_type="success",
        details={"withdrawal_id": txn.id, "amount": txn.amount}
    )

    return success_response({"message": "Withdrawal approved"})


# ==========================================================
#  PATCH /admin/withdrawals/<id>/reject
# ==========================================================
@bp.route("/withdrawals/<wid>/reject", methods=["PATCH"])
@jwt_required()
def admin_reject_withdrawal(wid):
    admin, err = require_admin()
    if err:
        return err

    txn = Transaction.query.filter_by(id=wid, type="withdrawal").first()
    if not txn:
        return error_response("NOT_FOUND", "Withdrawal request not found", status=404)

    if txn.status != "pending":
        return error_response("INVALID_STATE", "Only pending withdrawals can be rejected", status=400)

    data = request.get_json() or {}
    reason = data.get("reason")

    txn.status = "rejected"
    if reason:
        txn.description = reason

    db.session.commit()

    # -----------------------------
    # SEND NOTIFICATION
    # -----------------------------
    send_notification_to_user(
        email=txn.user.email,
        title="Withdrawal Rejected",
        message=(
            f"Your withdrawal request of ${txn.amount:.2f} on {txn.created_at.strftime('%Y-%m-%d')} "
            f"has been rejected{f' — {reason}.' if reason else '.'}"
        ),
        notif_type="error",
        details={"withdrawal_id": txn.id, "amount": txn.amount, "reason": reason}
    )

    return success_response({"message": "Withdrawal rejected"})
