"""API flow tests: auth, household, catalogue, inventory, purchases,
consumption, plans, ownership and error handling."""
from datetime import date, timedelta
from unittest.mock import patch

from sqlalchemy.exc import OperationalError

from tests.conftest import ApiClient, add_item, create_household, register

TODAY = date.today().isoformat()


def data(response):
    return response.get_json()["data"]


def stock_of(api, item_id):
    items = data(api.get("/api/groceries?per_page=100"))["items"]
    return next(i for i in items if i["id"] == item_id)["current_stock"]


# 1-2. Registration and login -------------------------------------------------

def test_register_login_me_logout(api):
    email = register(api, password="Secret123")
    me = api.get("/api/auth/me")
    assert me.status_code == 200
    assert "password_hash" not in me.get_json()["data"]["user"]

    api.post("/api/auth/logout")
    assert api.get("/api/auth/me").status_code == 401

    login = api.post("/api/auth/login", {"email": email, "password": "Secret123"})
    assert login.status_code == 200
    assert api.get("/api/auth/me").status_code == 200


def test_duplicate_email_rejected(api):
    email = register(api)
    api.post("/api/auth/logout")
    response = api.post("/api/auth/register", {"name": "X", "email": email, "password": "Secret123",
                                               "confirm_password": "Secret123"})
    assert response.status_code == 409


def test_invalid_login(api):
    email = register(api)
    api.post("/api/auth/logout")
    response = api.post("/api/auth/login", {"email": email, "password": "Wrong1234"})
    assert response.status_code == 401
    assert response.get_json() == {"success": False, "message": "Invalid email or password."}


def test_register_validation(api):
    response = api.post("/api/auth/register", {"name": "A", "email": "bad", "password": "x",
                                               "confirm_password": "x"})
    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_mutation_without_csrf_token_rejected(app, api):
    register(api)
    raw = app.test_client()
    raw.set_cookie("access_token_cookie", api.client.get_cookie("access_token_cookie").value)
    response = raw.post("/api/household", json={"household_name": "X"})
    assert response.status_code == 401


# 3. Household ------------------------------------------------------------------

def test_household_create_and_get(api):
    register(api)
    assert data(api.get("/api/household"))["household"] is None
    create_household(api, budget=6000)
    household = data(api.get("/api/household"))["household"]
    assert household["monthly_budget"] == 6000
    assert api.post("/api/household", {"household_name": "Again", "family_size": 2,
                                       "shopping_frequency": "Weekly", "monthly_budget": 100}).status_code == 409


def test_routes_need_household_first(api):
    register(api)
    response = api.get("/api/groceries")
    assert response.status_code == 409
    assert "household" in response.get_json()["message"].lower()


# 4-5. Grocery CRUD and validation ------------------------------------------------

def test_grocery_crud(user_api):
    item = add_item(user_api, "Rice", price=60)
    item_id = item["id"]
    assert data(user_api.get(f"/api/groceries/{item_id}"))["item"]["unit_price"] == 60

    updated = user_api.put(f"/api/groceries/{item_id}", {
        "name": "Basmati Rice", "category": "Rice and Grains", "unit": "kg", "unit_price": 95,
        "priority": "Essential"})
    assert updated.status_code == 200
    assert data(updated)["item"]["name"] == "Basmati Rice"

    listed = data(user_api.get("/api/groceries?search=basmati"))["items"]
    assert len(listed) == 1

    deleted = user_api.delete(f"/api/groceries/{item_id}")
    assert data(deleted)["archived"] is False
    assert user_api.get(f"/api/groceries/{item_id}").status_code == 404


def test_item_with_history_is_archived_not_deleted(user_api):
    item = add_item(user_api)
    user_api.post("/api/purchases", {"item_id": item["id"], "quantity": 2, "purchase_date": TODAY})
    response = user_api.delete(f"/api/groceries/{item['id']}")
    assert data(response)["archived"] is True
    assert len(data(user_api.get("/api/purchases"))["purchases"]) == 1  # history kept
    assert data(user_api.get("/api/groceries"))["items"] == []


def test_rejects_negative_price_and_quantity(user_api):
    bad_price = user_api.post("/api/groceries", {"name": "X", "category": "Other", "unit": "kg",
                                                 "unit_price": -5, "priority": "Optional"})
    assert bad_price.status_code == 400
    assert bad_price.get_json()["message"] == "Unit price must be zero or greater."

    item = add_item(user_api)
    bad_qty = user_api.post("/api/purchases", {"item_id": item["id"], "quantity": -1, "purchase_date": TODAY})
    assert bad_qty.status_code == 400
    bad_unit = user_api.post("/api/groceries", {"name": "Y", "category": "Other", "unit": "bag",
                                                "unit_price": 5, "priority": "Optional"})
    assert bad_unit.status_code == 400


# 6. Inventory ----------------------------------------------------------------------

def test_inventory_add_adjust_and_never_negative(user_api):
    item = add_item(user_api)
    created = user_api.post("/api/inventory", {"item_id": item["id"], "quantity": 5, "low_stock_threshold": 2})
    assert created.status_code == 201
    record_id = data(created)["inventory"]["id"]

    up = user_api.patch(f"/api/inventory/{record_id}/quantity", {"change": 2.5})
    assert data(up)["inventory"]["quantity"] == 7.5
    down = user_api.patch(f"/api/inventory/{record_id}/quantity", {"change": -7})
    assert data(down)["inventory"]["quantity"] == 0.5
    assert data(down)["inventory"]["is_low_stock"] is True

    too_much = user_api.patch(f"/api/inventory/{record_id}/quantity", {"change": -1})
    assert too_much.status_code == 400
    assert "Not enough stock" in too_much.get_json()["message"]

    set_abs = user_api.put(f"/api/inventory/{record_id}", {"quantity": 3, "low_stock_threshold": 1})
    assert data(set_abs)["inventory"]["quantity"] == 3
    assert user_api.put(f"/api/inventory/{record_id}", {"quantity": -2}).status_code == 400


# 7. Purchases and stock reconciliation -------------------------------------------

def test_purchase_updates_stock_and_edits_reconcile(user_api):
    item = add_item(user_api)
    created = user_api.post("/api/purchases", {"item_id": item["id"], "quantity": 5, "unit_price": 50,
                                               "purchase_date": TODAY, "client_reference": "abc-1"})
    assert created.status_code == 201
    purchase = data(created)["purchase"]
    assert purchase["total_price"] == 250
    assert stock_of(user_api, item["id"]) == 5

    # Accidental double submit with the same reference is ignored.
    again = user_api.post("/api/purchases", {"item_id": item["id"], "quantity": 5, "unit_price": 50,
                                             "purchase_date": TODAY, "client_reference": "abc-1"})
    assert again.status_code == 409
    assert stock_of(user_api, item["id"]) == 5

    # Editing 5 -> 3 should leave stock at 3, not 8 or 2.
    user_api.put(f"/api/purchases/{purchase['id']}", {"item_id": item["id"], "quantity": 3, "unit_price": 50,
                                                      "purchase_date": TODAY})
    assert stock_of(user_api, item["id"]) == 3

    user_api.delete(f"/api/purchases/{purchase['id']}")
    assert stock_of(user_api, item["id"]) == 0


def test_purchase_filters_and_total(user_api):
    item = add_item(user_api)
    old = (date.today() - timedelta(days=40)).isoformat()
    user_api.post("/api/purchases", {"item_id": item["id"], "quantity": 1, "unit_price": 100, "purchase_date": old})
    user_api.post("/api/purchases", {"item_id": item["id"], "quantity": 2, "unit_price": 100, "purchase_date": TODAY})
    recent = data(user_api.get(f"/api/purchases?start_date={(date.today() - timedelta(days=7)).isoformat()}"))
    assert len(recent["purchases"]) == 1
    assert recent["total_expenditure"] == 200
    assert user_api.get("/api/purchases?start_date=2026-05-01&end_date=2026-01-01").status_code == 400


def test_future_purchase_date_rejected(user_api):
    item = add_item(user_api)
    future = (date.today() + timedelta(days=3)).isoformat()
    response = user_api.post("/api/purchases", {"item_id": item["id"], "quantity": 1, "purchase_date": future})
    assert response.status_code == 400


# 8. Consumption --------------------------------------------------------------------

def test_consumption_deducts_stock_without_double_counting(user_api):
    item = add_item(user_api)
    user_api.post("/api/purchases", {"item_id": item["id"], "quantity": 10, "purchase_date": TODAY})
    created = user_api.post("/api/consumption", {"item_id": item["id"], "quantity": 4, "consumed_at": TODAY})
    assert created.status_code == 201
    assert stock_of(user_api, item["id"]) == 6

    record_id = data(created)["consumption"]["id"]
    user_api.put(f"/api/consumption/{record_id}", {"item_id": item["id"], "quantity": 1, "consumed_at": TODAY})
    assert stock_of(user_api, item["id"]) == 9
    user_api.delete(f"/api/consumption/{record_id}")
    assert stock_of(user_api, item["id"]) == 10


def test_consumption_cannot_exceed_stock_unless_not_deducting(user_api):
    item = add_item(user_api)
    blocked = user_api.post("/api/consumption", {"item_id": item["id"], "quantity": 2, "consumed_at": TODAY})
    assert blocked.status_code == 400
    history_only = user_api.post("/api/consumption", {"item_id": item["id"], "quantity": 2,
                                                      "consumed_at": TODAY, "deduct_from_stock": False})
    assert history_only.status_code == 201
    assert stock_of(user_api, item["id"]) == 0


# 9-12, 14. Plan generation, optimisation, persistence, mark purchased ---------------

def _record_history(api, item_id, monthly_totals):
    """Record consumption totals for the last 30-day periods (most recent first)."""
    for index, quantity in enumerate(monthly_totals):
        day = (date.today() - timedelta(days=index * 30 + 5)).isoformat()
        api.post("/api/consumption", {"item_id": item_id, "quantity": quantity, "consumed_at": day,
                                      "deduct_from_stock": False})


def test_generate_plan_uses_average_and_subtracts_stock(user_api):
    rice = add_item(user_api, "Rice", price=50)
    _record_history(user_api, rice["id"], [9, 8, 7])
    user_api.post("/api/inventory", {"item_id": rice["id"], "quantity": 3})

    response = user_api.post("/api/predictions/generate")
    assert response.status_code == 201
    plan = data(response)["recommendation"]
    line = plan["items"][0]
    assert line["predicted_quantity"] == 8
    assert line["stock_quantity"] == 3
    assert line["recommended_quantity"] == 5
    assert line["estimated_cost"] == 250
    assert line["prediction_source"] == "consumption_history"

    # Persistence: the plan can be fetched again later.
    assert data(user_api.get("/api/predictions/latest"))["recommendation"]["id"] == plan["id"]
    assert len(data(user_api.get("/api/recommendations"))["recommendations"]) == 1


def test_plan_without_items_gives_helpful_error(user_api):
    response = user_api.post("/api/predictions/generate")
    assert response.status_code == 400
    assert "catalogue" in response.get_json()["message"]


def test_optimise_endpoint_reduces_optional_first(app):
    api = ApiClient(app.test_client())
    register(api)
    create_household(api, budget=300)
    rice = add_item(api, "Rice", price=50, priority="Essential", initial_monthly_estimate=4)   # 200
    chips = add_item(api, "Chips", unit="packet", price=30, priority="Optional", initial_monthly_estimate=6)  # 180
    plan = data(api.post("/api/predictions/generate"))["recommendation"]
    assert plan["budget_status"] == "needs_optimisation"

    optimised = data(api.post(f"/api/recommendations/{plan['id']}/optimise-budget"))
    lines = {l["item_name"]: l for l in optimised["recommendation"]["items"]}
    assert lines["Rice"]["final_quantity"] == 4
    assert lines["Chips"]["final_quantity"] == 3
    assert optimised["recommendation"]["final_total_cost"] == 290
    assert optimised["summary"]["budget_status"] == "optimised_to_fit"
    assert chips["id"] and rice["id"]


def test_checkbox_does_not_create_purchase_but_mark_purchased_does(user_api):
    rice = add_item(user_api, "Rice", price=50, initial_monthly_estimate=4)
    plan = data(user_api.post("/api/predictions/generate"))["recommendation"]
    line_id = plan["items"][0]["id"]

    user_api.patch(f"/api/recommendations/{plan['id']}/items/{line_id}", {"is_checked": True})
    assert data(user_api.get("/api/purchases"))["purchases"] == []
    assert stock_of(user_api, rice["id"]) == 0

    edited = data(user_api.patch(f"/api/recommendations/{plan['id']}/items/{line_id}", {"final_quantity": 3}))
    assert edited["recommendation"]["final_total_cost"] == 150

    bought = user_api.post(f"/api/recommendations/{plan['id']}/items/{line_id}/mark-purchased")
    assert bought.status_code == 201
    assert stock_of(user_api, rice["id"]) == 3
    assert data(bought)["recommendation"]["status"] == "completed"

    twice = user_api.post(f"/api/recommendations/{plan['id']}/items/{line_id}/mark-purchased")
    assert twice.status_code == 409
    assert stock_of(user_api, rice["id"]) == 3

    # Deleting that purchase reverses stock and un-marks the plan line.
    purchase_id = data(bought)["purchase"]["id"]
    user_api.delete(f"/api/purchases/{purchase_id}")
    assert stock_of(user_api, rice["id"]) == 0
    refreshed = data(user_api.get(f"/api/recommendations/{plan['id']}"))["recommendation"]
    assert refreshed["items"][0]["is_purchased"] is False


def test_whole_number_required_for_packets(user_api):
    add_item(user_api, "Chips", unit="packet", price=20, initial_monthly_estimate=2)
    plan = data(user_api.post("/api/predictions/generate"))["recommendation"]
    response = user_api.patch(f"/api/recommendations/{plan['id']}/items/{plan['items'][0]['id']}",
                              {"final_quantity": 1.5})
    assert response.status_code == 400


# 13. Ownership -------------------------------------------------------------------------

def test_users_cannot_access_other_households(app):
    alice = ApiClient(app.test_client())
    register(alice)
    create_household(alice)
    item = add_item(alice, "Rice", initial_monthly_estimate=2)
    purchase = data(alice.post("/api/purchases", {"item_id": item["id"], "quantity": 1, "purchase_date": TODAY}))
    plan = data(alice.post("/api/predictions/generate"))["recommendation"]

    bob = ApiClient(app.test_client())
    register(bob)
    create_household(bob)
    assert bob.get(f"/api/groceries/{item['id']}").status_code == 404
    assert bob.delete(f"/api/groceries/{item['id']}").status_code == 404
    assert bob.get(f"/api/purchases/{purchase['purchase']['id']}").status_code == 404
    assert bob.get(f"/api/recommendations/{plan['id']}").status_code == 404
    assert bob.post("/api/purchases", {"item_id": item["id"], "quantity": 1,
                                       "purchase_date": TODAY}).status_code == 404
    assert data(bob.get("/api/groceries"))["items"] == []


def test_unauthenticated_requests_rejected(api):
    assert api.get("/api/groceries").status_code == 401
    assert api.get("/api/dashboard/summary").status_code == 401


# Dashboard, reports, feedback --------------------------------------------------------

def test_dashboard_and_reports_use_real_data(user_api):
    item = add_item(user_api, price=100)
    user_api.post("/api/purchases", {"item_id": item["id"], "quantity": 2, "purchase_date": TODAY})
    summary = data(user_api.get("/api/dashboard/summary"))
    assert summary["spent_this_month"] == 200
    assert summary["remaining_budget"] == 4800
    assert summary["item_count"] == 1
    assert summary["monthly_spending"][-1]["total"] == 200

    spending = data(user_api.get("/api/reports/spending"))
    assert spending["by_category"] == [{"category": "Rice and Grains", "total": 200.0}]
    assert user_api.get(f"/api/reports/consumption?item_id={item['id']}").status_code == 200
    assert user_api.get("/api/reports/recommendations").status_code == 200


def test_feedback_validation(user_api):
    assert user_api.post("/api/feedback", {"rating": 6}).status_code == 400
    assert user_api.post("/api/feedback", {"rating": 0}).status_code == 400
    assert user_api.post("/api/feedback", {"rating": 5, "comment": "Useful"}).status_code == 201
    assert len(data(user_api.get("/api/feedback"))["feedback"]) == 1


# 15. Database failure ----------------------------------------------------------------

def test_database_failure_returns_clean_error_and_rolls_back(user_api):
    with patch("app.routes.grocery_routes.db.session.commit",
               side_effect=OperationalError("INSERT", {}, Exception("connection lost"))):
        response = user_api.post("/api/groceries", {"name": "Oil", "category": "Cooking Oil", "unit": "litre",
                                                    "unit_price": 150, "priority": "Essential"})
    assert response.status_code == 500
    body = response.get_json()
    assert body["success"] is False
    assert "connection lost" not in body["message"]  # no internal details leaked
    assert data(user_api.get("/api/groceries"))["items"] == []  # nothing half-saved


# Demo seed ------------------------------------------------------------------------

def test_demo_seed_can_run_twice_and_produces_a_plan(app):
    from app.demo_data import DEMO_EMAIL, DEMO_PASSWORD, seed

    seed()
    seed()  # re-running must replace, not fail on foreign keys
    api = ApiClient(app.test_client())
    assert api.post("/api/auth/login", {"email": DEMO_EMAIL, "password": DEMO_PASSWORD}).status_code == 200
    plan = data(api.post("/api/predictions/generate", {"optimise": True}))["recommendation"]
    assert plan["final_total_cost"] <= plan["budget"] or plan["budget_status"] == "over_budget"
