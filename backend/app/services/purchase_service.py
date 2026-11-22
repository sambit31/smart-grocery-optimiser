"""Purchase and consumption record logic that touches inventory.

Both purchases (add stock) and consumption (remove stock) remember whether
they changed inventory. Editing or deleting a record first REVERSES what it
applied, then applies the new values. Combined with one commit per request,
this keeps the stock balance correct even after corrections.
"""
from app.extensions import db
from app.models import Consumption, Purchase
from app.services.inventory_service import change_stock
from app.utils.numbers import round_money


def create_purchase(household_id, item, quantity, unit_price, purchase_date, store_name=None, notes=None,
                    apply_to_inventory=True, client_reference=None, recommendation_item_id=None):
    purchase = Purchase(
        household_id=household_id,
        item_id=item.id,
        quantity=quantity,
        unit_price=unit_price,
        total_price=round_money(quantity * unit_price),
        purchase_date=purchase_date,
        store_name=store_name,
        notes=notes,
        applied_to_inventory=apply_to_inventory,
        client_reference=client_reference,
        recommendation_item_id=recommendation_item_id,
    )
    db.session.add(purchase)
    db.session.flush()  # get purchase.id (also triggers unique-constraint checks)
    if apply_to_inventory:
        change_stock(household_id, item, quantity, "purchase", "purchase", purchase.id)
    return purchase


def reverse_purchase_stock(purchase):
    if purchase.applied_to_inventory:
        change_stock(purchase.household_id, purchase.item, -purchase.quantity, "purchase_reversal",
                     "purchase", purchase.id)


def update_purchase(purchase, new_item, quantity, unit_price, purchase_date, store_name, notes):
    reverse_purchase_stock(purchase)
    purchase.item_id = new_item.id
    purchase.item = new_item
    purchase.quantity = quantity
    purchase.unit_price = unit_price
    purchase.total_price = round_money(quantity * unit_price)
    purchase.purchase_date = purchase_date
    purchase.store_name = store_name
    purchase.notes = notes
    if purchase.applied_to_inventory:
        change_stock(purchase.household_id, new_item, quantity, "purchase_edit", "purchase", purchase.id)
    return purchase


def delete_purchase(purchase):
    reverse_purchase_stock(purchase)
    # If this purchase came from a shopping list, un-mark that list line.
    if purchase.recommendation_item_id:
        from app.models import RecommendationItem

        line = db.session.get(RecommendationItem, purchase.recommendation_item_id)
        if line:
            line.is_purchased = False
            if line.recommendation.status == "completed":
                line.recommendation.status = "optimised"
    db.session.delete(purchase)


def create_consumption(household_id, item, quantity, consumed_at, notes=None, deduct_from_stock=True):
    record = Consumption(
        household_id=household_id,
        item_id=item.id,
        quantity=quantity,
        consumed_at=consumed_at,
        notes=notes,
        deducted_from_stock=deduct_from_stock,
    )
    db.session.add(record)
    db.session.flush()
    if deduct_from_stock:
        change_stock(household_id, item, -quantity, "consumption", "consumption", record.id)
    return record


def update_consumption(record, new_item, quantity, consumed_at, notes):
    if record.deducted_from_stock:
        change_stock(record.household_id, record.item, record.quantity, "consumption_reversal",
                     "consumption", record.id)
    record.item_id = new_item.id
    record.item = new_item
    record.quantity = quantity
    record.consumed_at = consumed_at
    record.notes = notes
    if record.deducted_from_stock:
        change_stock(record.household_id, new_item, -quantity, "consumption_edit", "consumption", record.id)
    return record


def delete_consumption(record):
    if record.deducted_from_stock:
        change_stock(record.household_id, record.item, record.quantity, "consumption_reversal",
                     "consumption", record.id)
    db.session.delete(record)
