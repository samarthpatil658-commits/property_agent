UI_DEFAULTS = {
    "messages": [],
    "last_result": None,
    "shortlist": [],
    "compare": [],
    "selected_property_id": None,
}


def ensure_ui_state(state):
    for key, value in UI_DEFAULTS.items():
        if key not in state:
            state[key] = value.copy() if isinstance(value, list) else value


def set_selected_property(state, property_id):
    state["selected_property_id"] = property_id


def toggle_property_id(state, collection_name, property_id, limit=None):
    collection = list(state.get(collection_name, []))
    if property_id in collection:
        collection.remove(property_id)
        state[collection_name] = collection
        return False

    if limit is not None and len(collection) >= limit:
        collection = collection[-(limit - 1):] if limit > 1 else []
    collection.append(property_id)
    state[collection_name] = collection
    return True


def selected_items(result, property_ids):
    if not result:
        return []
    wanted = set(property_ids or [])
    items = result.get("results", [])
    if not wanted:
        return []
    return [item for item in items if item["property"]["id"] in wanted]


def find_property_item(result, property_id):
    if not result:
        return None
    for item in result.get("results", []):
        if item["property"]["id"] == property_id:
            return item
    return None
