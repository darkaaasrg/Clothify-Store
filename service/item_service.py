from domain.models import db, Item, Review, User


class ItemService:
    def get_all_items(self):
        """Отримання всіх товарів для головної сторінки"""
        return Item.query.all()

    def get_item_by_id(self, item_id):
        """Детальна інформація про товар"""
        item = Item.query.get(item_id)
        if not item:
            raise ValueError("ITEM_NOT_FOUND")
        return item


class ReviewService:
    @staticmethod
    def add_review(item_id, username, text):
        """Бізнес-логіка створення відгуку"""
        user = User.query.filter_by(username=username).first()
        if not user:
            raise ValueError("AUTH_REQUIRED")

        if not text or len(text.strip()) < 2:
            raise ValueError("TEXT_TOO_SHORT")

        new_review = Review(item_id=item_id, user_id=user.id, text=text)
        db.session.add(new_review)
        db.session.commit()
        return new_review

    @staticmethod
    def delete_review(review_id, username):
        """Видалення відгуку з перевіркою власника (Business Rule)"""
        review = Review.query.get(review_id)
        if not review:
            raise ValueError("REVIEW_NOT_FOUND")

        user = User.query.filter_by(username=username).first()

        # Перевірка безпеки: видалити може тільки той, хто написав
        if not user or review.user_id != user.id:
            raise ValueError("ACCESS_DENIED")

        db.session.delete(review)
        db.session.commit()
        return True

class UserService:
    @staticmethod
    def get_user_by_username(username):
        user = User.query.filter_by(username=username).first()
        if not user:
            raise ValueError("USER_NOT_FOUND")
        return user