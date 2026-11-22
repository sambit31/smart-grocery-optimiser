from app.extensions import db
from app.models.user import utc_now


class Feedback(db.Model):
    __tablename__ = "feedback"
    __table_args__ = (db.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_feedback_rating_range"),)

    id = db.Column(db.Integer, primary_key=True)
    household_id = db.Column(db.Integer, db.ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(1000))
    created_at = db.Column(db.DateTime, nullable=False, default=utc_now)

    def to_dict(self):
        return {
            "id": self.id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
        }
