from app.extensions import db
from datetime import datetime
import uuid

def gen_txn_id():
    return f"txn-{str(uuid.uuid4())[:8]}"

class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.String(50), primary_key=True, default=gen_txn_id)
    user_id = db.Column(db.String(50), db.ForeignKey("users.id"))
    type = db.Column(db.String(50))  # earning, withdrawal
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))
    status = db.Column(db.String(50), default="pending")
    order_id = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="transactions", lazy=True)
