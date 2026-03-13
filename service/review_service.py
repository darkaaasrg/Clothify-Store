from domain.models import db, Review


def create_review(text, item_id, user_id):
    # Валідація вхідних даних (Пункт 2.a)
    if not text or len(text.strip()) < 1:
        raise ValueError("Текст не може бути порожнім")

    new_r = Review(text=text, item_id=item_id, user_id=user_id)
    db.session.add(new_r)
    db.session.commit()
    return new_r