import os
import uuid
import time
from flask import Flask, render_template, request, jsonify, make_response
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from domain.models import db, User, Item, Cart, Review

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db.init_app(app)

idem_store = {}
rate_limit_data = {}


@app.before_request
def middleware():
    rid = request.headers.get("X-Request-Id") or str(uuid.uuid4())
    request.rid = rid

    if request.path.startswith('/api/'):
        ip = request.remote_addr
        now = time.time()
        user_stats = rate_limit_data.get(ip, {"count": 0, "ts": now})

        if now - user_stats["ts"] < 10:
            user_stats["count"] += 1
        else:
            user_stats = {"count": 1, "ts": now}

        rate_limit_data[ip] = user_stats

        if user_stats["count"] > 5:  # Твій ліміт
            res = jsonify({
                "error": "too_many_requests",
                "requestId": rid,
                "details": "Перевищено ліміт запитів"
            })
            res.headers["Retry-After"] = "5"
            return make_response(res, 429)


@app.after_request
def add_headers(response):
    response.headers["X-Request-Id"] = getattr(request, 'rid', str(uuid.uuid4()))
    return response

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

with app.app_context():
    db.create_all()
    if not Item.query.first():
        db.session.add_all([
            Item(name="Худі 'Cloud'", price=1350, category="Верх", fabric="80% Бавовна", origin="Україна",
                 description="Теплий худі.",
                 image_url="https://i.pinimg.com/1200x/11/5b/2e/115b2ece01e065363bbc694c9565981d.jpg"),
            Item(name="Джинси 'Space'", price=1800, category="Низ", fabric="100% Денім", origin="Туреччина",
                 description="Вільні джинси.",
                 image_url="https://i.pinimg.com/1200x/0a/11/9f/0a119f6b14e4ba888bc35ecea6ca310c.jpg"),
            Item(name="Футболка 'Basic'", price=450, category="Верх", fabric="100% Бавовна", origin="Україна",
                 description="Базова річ.",
                 image_url="https://i.pinimg.com/736x/1b/7c/b6/1b7cb6fe341e990867f7f29d8fc44773.jpg"),
            Item(name="Карго штани", price=1600, category="Низ", fabric="Канвас", origin="Польща",
                 description="Багато кишень.",
                 image_url="https://i.pinimg.com/1200x/30/71/2a/30712a319b1df14598826dc4a97e3d21.jpg"),
            Item(name="Світшот 'Retro'", price=1100, category="Верх", fabric="Бавовна", origin="Польща",
                 description="Ретро стиль.",
                 image_url="https://i.pinimg.com/736x/18/ad/6e/18ad6ee702108e21f2633090e01bd8c3.jpg"),
            Item(name="Шорти 'Summer'", price=750, category="Низ", fabric="Льон", origin="Італія",
                 description="Легкі шорти.",
                 image_url="https://i.pinimg.com/736x/df/91/34/df9134c18abae3d1d73f1fb364a7b864.jpg")
        ])
        db.session.commit()


@app.route('/')
def index(): return render_template('index.html')


@app.route('/product/<int:item_id>')
def product_page(item_id): return render_template('product.html', id=item_id)


@app.route('/profile')
def profile_page(): return render_template('profile.html')


@app.route('/auth')
def auth_page(): return render_template('auth.html')


@app.route('/api/health')
def health(): return jsonify({"status": "ok"}), 200

@app.route('/api/items')
def get_items():
    query = Item.query
    cat = request.args.get('category')
    if cat and cat != 'Всі': query = query.filter_by(category=cat)
    search = request.args.get('search')
    if search: query = query.filter(Item.name.ilike(f'%{search}%'))
    items = query.all()
    return jsonify(
        [{"id": i.id, "name": i.name, "price": i.price, "img": i.image_url, "cat": i.category} for i in items])


@app.route('/api/product/<int:item_id>')
def get_product(item_id):
    i = Item.query.get_or_404(item_id)
    return jsonify({
        "id": i.id, "name": i.name, "price": i.price, "fabric": i.fabric, "origin": i.origin, "desc": i.description,
        "img": i.image_url,
        "reviews": [
            {"id": r.id, "user": r.user.name, "user_login": r.user.username, "text": r.text, "avatar": r.user.avatar}
            for r in i.reviews]
    })

@app.route('/api/add_to_cart', methods=['POST'])
def add_to_cart():
    key = request.headers.get("Idempotency-Key")
    if key and key in idem_store:
        return jsonify({**idem_store[key], "requestId": request.rid}), 201

    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    if not user: return jsonify({"error": "unauthorized", "message": "Потрібна авторизація"}), 401

    cart_item = Cart.query.filter_by(user_id=user.id, item_id=data.get('item_id')).first()
    if cart_item:
        cart_item.quantity += 1
    else:
        db.session.add(Cart(user_id=user.id, item_id=data.get('item_id'), quantity=1))
    db.session.commit()

    res_data = {"message": "Added"}
    if key: idem_store[key] = res_data
    return jsonify({**res_data, "requestId": request.rid}), 201


@app.route('/api/add_review', methods=['POST'])
def add_review():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    if not user: return jsonify({"error": "unauthorized", "message": "Тільки покупці можуть залишати відгуки"}), 401

    text = data.get('text', '').strip()
    if len(text) < 5:  # Валідація довжини
        return jsonify({"error": "bad_request", "message": "Відгук занадто короткий (мін. 5 симв.)"}), 400

    new_r = Review(text=text, item_id=data['item_id'], user_id=user.id)
    db.session.add(new_r)
    db.session.commit()
    return jsonify({"message": "Created"}), 201


@app.route('/api/edit_review/<int:review_id>', methods=['PUT'])
def edit_review(review_id):
    data = request.json
    text = data.get('text', '').strip()
    if len(text) < 5:
        return jsonify({"error": "bad_request", "message": "Відгук занадто короткий"}), 400

    review = Review.query.get_or_404(review_id)
    review.text = text
    db.session.commit()
    return jsonify({"message": "Updated"}), 200


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password, data['password']):
        return jsonify({"username": user.username, "name": user.name, "avatar": user.avatar})
    return jsonify({"message": "Error"}), 401


@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(username=data['username']).first(): return jsonify({"message": "Exists"}), 400
    new_user = User(username=data['username'], password=generate_password_hash(data['password']), name=data['username'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Ok"}), 201


@app.route('/api/get_profile/<username>')
def get_profile(username):
    u = User.query.filter_by(username=username).first()
    if not u: return jsonify({"error": "User not found"}), 404
    return jsonify({"username": u.username, "name": u.name, "avatar": u.avatar})


@app.route('/api/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username')
    user = User.query.filter_by(username=username).first()
    if not user: return jsonify({"error": "User not found"}), 404
    if request.form.get('name'): user.name = request.form.get('name')
    if 'avatar' in request.files:
        file = request.files['avatar']
        if file.filename:
            filename = secure_filename(f"{user.id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            user.avatar = filename
    db.session.commit()
    return jsonify({"message": "Success", "avatar": user.avatar, "name": user.name})


@app.route('/api/get_cart/<username>')
def get_cart(username):
    user = User.query.filter_by(username=username).first()
    if not user: return jsonify([]), 200
    items = Cart.query.filter_by(user_id=user.id).all()
    return jsonify([{"id": c.id, "name": c.item.name, "price": c.item.price, "qty": c.quantity} for c in items])


@app.route('/api/remove_from_cart/<int:cart_id>', methods=['DELETE'])
def remove_from_cart(cart_id):
    c = Cart.query.get(cart_id)
    if c:
        db.session.delete(c)
        db.session.commit()
        return '', 204
    return jsonify({"error": "Not found"}), 404


@app.route('/api/delete_review/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    return '', 204


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)