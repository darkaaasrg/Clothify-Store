import sys
import os

# Цей блок знаходить шлях до папки team1 і додає її в систему
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_path not in sys.path:
    sys.path.insert(0, base_path)

import unittest
from flask import Flask
# Тепер імпорт точно спрацює
from domain.models import db
from service.review_service import create_review

class TestReviewService(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()

    def test_create_review_success(self):
        with self.app.app_context():
            # Перевіряємо успішний випадок (Пункт 1.a вимог)
            result = create_review(text="Це чудовий товар, рекомендую!", item_id=1, user_id=1)
            self.assertEqual(result.text, "Це чудовий товар, рекомендую!")
            self.assertIsNotNone(result.id)

    def test_create_review_validation_error(self):
        with self.app.app_context():
            # Перевіряємо помилковий випадок (Пункт 1.b вимог)
            with self.assertRaises(ValueError):
                create_review(text="", item_id=1, user_id=1)

if __name__ == '__main__':
    unittest.main()