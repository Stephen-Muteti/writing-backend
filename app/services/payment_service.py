from app.extensions import db
from app.models.transaction import Transaction
from app.models.payment_method import PaymentMethod

def get_balance_for_user(user):
    # Simple computation using transactions - extend as needed
    earned = db.session.query(Transaction).filter_by(user_id=user.id, type="earning", status="completed").with_entities(db.func.coalesce(db.func.sum(Transaction.amount), 0)).scalar() or 0
    pending = db.session.query(Transaction).filter_by(user_id=user.id, type="earning", status="pending").with_entities(db.func.coalesce(db.func.sum(Transaction.amount), 0)).scalar() or 0
    total = db.session.query(Transaction).filter_by(user_id=user.id, type="earning").with_entities(db.func.coalesce(db.func.sum(Transaction.amount), 0)).scalar() or 0
    return {"available_balance": float(earned), "pending_balance": float(pending), "total_earned": float(total), "currency": "USD"}

def create_withdrawal(user_id, amount, method, details):
    # Save email into PaymentMethod if not exists
    pm = PaymentMethod.query.filter_by(user_id=user_id, method=method, details=details).first()
    if not pm:
        pm = PaymentMethod(user_id=user_id, method=method, details=details)
        db.session.add(pm)
        db.session.flush()  # so pm.id becomes available

    txn = Transaction(
        user_id=user_id,
        type="withdrawal",
        amount=amount,
        description=f"Withdrawal via {method}",
        status="pending",
        order_id=pm.id  # reuse order_id field to store method ID
    )
    db.session.add(txn)
    db.session.commit()
    return txn
