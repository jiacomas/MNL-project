"""
Service layer for item operations.
Provides functions to list, create, retrieve, update, and delete items.
"""

import uuid
from typing import List

from fastapi import HTTPException
from repositories.items_repo import load_all, save_all
from schemas.item import Item, ItemCreate, ItemUpdate


def list_items() -> List[Item]:
    """Return a list of all items."""
    return [Item(**it) for it in load_all()]


def create_item(payload: ItemCreate) -> Item:
    """Create a new item from the payload and return it."""
    items = load_all()
    new_id = str(uuid.uuid4())
    if any(it.get("id") == new_id for it in items):
        raise HTTPException(status_code=409, detail="ID collision; retry.")
    new_item = Item(
        id=new_id,
        title=payload.title.strip(),
        category=payload.category.strip(),
        tags=payload.tags,
    )
    items.append(new_item.dict())
    save_all(items)
    return new_item


def get_item_by_id(item_id: str) -> Item:
    """Retrieve an item by its ID or raise 404 if not found."""
    items = load_all()
    for it in items:
        if it.get("id") == item_id:
            return Item(**it)
    raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")


def update_item(item_id: str, payload: ItemUpdate) -> Item:
    """Update an existing item by ID with new payload data."""
    items = load_all()
    for idx, it in enumerate(items):
        if it.get("id") == item_id:
            updated = Item(
                id=item_id,
                title=payload.title.strip(),
                category=payload.category.strip(),
                tags=payload.tags,
            )
            items[idx] = updated.dict()
            save_all(items)
            return updated
    raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")


def delete_item(item_id: str) -> None:
    """Delete an item by its ID. Raises 404 if item not found."""
    items = load_all()
    new_items = [it for it in items if it.get("id") != item_id]
    if len(new_items) == len(items):
        raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")
    save_all(new_items)
