from flask import Blueprint, jsonify, request
from .models import create_event

api_blueprint = Blueprint("api", __name__)

@api_blueprint.route('/events', methods=['POST'])
def add_event():
    data = request.json
    create_event(data)
    return jsonify({"msg": "Event added successfully"}), 201


@api_blueprint.route('/events', methods=['GET'])
def get_events():
    events = mongo.db.events.find()
    return jsonify([event for event in events])