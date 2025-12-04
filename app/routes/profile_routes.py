from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.extensions import db
from app.utils.response_formatter import success_response, error_response

bp = Blueprint("profile", __name__, url_prefix="/api/v1/profile")

@bp.route("", methods=["GET"])
@jwt_required()
def get_profile():
    uid = get_jwt_identity()
    u = User.query.get(uid)
    if not u:
        return error_response("NOT_FOUND", "User not found", status=404)
    return success_response({
        "id": u.id,
        "email": u.email,
        "full_name": u.full_name,
        "profile_image": u.profile_image,
        "bio": u.bio,
        "rating": u.rating,
        "completed_orders": u.completed_orders,
        "total_earned": u.total_earned,
        "success_rate": 0.0,
        "specializations": [],
        "joined_at": u.joined_at.isoformat() + "Z"
    })

@bp.route("", methods=["PATCH"])
@jwt_required()
def patch_profile():
    uid = get_jwt_identity()
    data = request.get_json() or {}
    u = User.query.get(uid)
    if not u:
        return error_response("NOT_FOUND", "User not found", status=404)
    if "full_name" in data:
        u.full_name = data.get("full_name")
    if "bio" in data:
        u.bio = data.get("bio")
    db.session.commit()
    return success_response({"id": u.id, "full_name": u.full_name, "bio": u.bio, "updated_at": u.joined_at.isoformat() + "Z"})
