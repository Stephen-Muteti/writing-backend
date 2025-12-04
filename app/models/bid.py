from app.extensions import db
from datetime import datetime, timedelta
import uuid

def gen_bid_id():
    return f"BID-{str(uuid.uuid4())[:8]}"

class Bid(db.Model):
    __tablename__ = "bids"

    id = db.Column(db.String(50), primary_key=True, default=gen_bid_id)
    order_id = db.Column(db.String(50), db.ForeignKey("orders.id"), nullable=False, index=True)
    user_id = db.Column(db.String(50), db.ForeignKey("users.id"), nullable=False, index=True)

    bid_amount = db.Column(db.Float, nullable=False)
    original_budget = db.Column(db.Float)
    status = db.Column(db.String(50), default="open")
    message = db.Column(db.Text, nullable=True)
    is_counter_offer = db.Column(db.Boolean, default=False)

    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    response_deadline = db.Column(db.DateTime)

    # Relationships
    order = db.relationship("Order", backref=db.backref("bids", lazy=True, cascade="all, delete-orphan"))
    user = db.relationship("User", backref=db.backref("bids", lazy=True))

    def get_derived_status(self) -> str:
        """
        Compute the effective status for the bid, including unconfirmed bids.
        """
        if self.status in ["accepted", "rejected", "cancelled"]:
            return self.status
        if self.order and self.order.updated_at and self.order.updated_at > self.submitted_at:
            return "unconfirmed"
        return self.status

    def serialize(self, include_user_info: bool = False) -> dict:
        """
        Serialize the bid into a dictionary. Optionally include user info.
        """
        data = {
            "id": self.id,
            "order_id": self.order_id,
            "user_id": self.user_id,
            "order_title": self.order.title if self.order else None,
            "bid_amount": self.bid_amount,
            "original_budget": self.original_budget,
            "budget": self.order.budget if self.order else None,
            "status": self.get_derived_status(),
            "message": self.message,
            "is_counter_offer": self.is_counter_offer,
            "submitted_at": self.submitted_at.isoformat() + "Z" if self.submitted_at else None,
            "response_deadline": self.response_deadline.isoformat() + "Z" if self.response_deadline else None,
        }

        if include_user_info and self.user:
            data.update({
                "writerId": self.user.id,
                "writerName": self.user.full_name,
                "writerRating": getattr(self.user, "rating", 0),
                "writerCompletedOrders": getattr(self.user, "completed_orders", 0),
            })

        return data