from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models.user import User
from app.utils.response_formatter import success_response, error_response

bp = Blueprint("admin_writers", __name__, url_prefix="/api/v1/admin/writers")

def admin_required(user):
    return user and user.role == "admin"

@bp.route("", methods=["GET"])
@jwt_required()
def list_writers():
    uid = get_jwt_identity()
    admin = User.query.get(uid)
    if not admin_required(admin):
        return error_response("FORBIDDEN", "Admin privileges required", status=403)

    writers = User.query.filter_by(role="writer", application_status="approved").all()
    data = [
        {
            "id": w.id,
            "email": w.email,
            "full_name": w.full_name,
            "rating": w.rating,
            "completed_orders": w.completed_orders,
            "total_earned": w.total_earned,
            "joined_at": w.joined_at.isoformat(),
            "status": "active" if w.is_verified else "suspended-temporary"
        }
        for w in writers
    ]
    return success_response({"writers": data})