"""Consistent JSON response helpers.

Success: {"success": true, "message": "...", "data": ...}
Error:   {"success": false, "message": "..."}
"""
from flask import jsonify


def success(data=None, message="OK", status=200):
    return jsonify({"success": True, "message": message, "data": data}), status


def error(message, status=400):
    return jsonify({"success": False, "message": message}), status
