item_service = ItemService()

@app.route('/health')
def health(): return "ok", 200

@app.route('/api/items', methods=['GET'])
def list_items():
    items = item_service.get_all_items()
    return jsonify([{"id": i.id, "name": i.name} for i in items]), 200

@app.route('/api/items/<int:id>', methods=['GET'])
def item_detail(id):
    try:
        item = item_service.get_item_by_id(id)
        return jsonify({"id": item.id, "name": item.name}), 200
    except ValueError:
        return jsonify({"error": "Not Found", "code": "ITEM_NOT_FOUND"}), 404