from pymongo import ASCENDING


async def create_indexes(db):
    await db.inventory_items.create_index(
        [("parent_id", ASCENDING)]
    )

    await db.inventory_items.create_index(
        [("node_type", ASCENDING)]
    )

    await db.inventory_items.create_index(
        [("reference", ASCENDING)]
    )

    await db.inventory_items.create_index(
        [("path", ASCENDING)]
    )

    await db.inventory_checks.create_index(
        [("item_id", ASCENDING)],
    )

    await db.inventory_checks.create_index(
        [("session_id", ASCENDING)]
    )

    await db.inventory_checks.create_index(
        [("parent_id", ASCENDING)]
    )

    await db.inventory_checks.create_index(
        [("reference", ASCENDING)]
    )

    await db.inventory_checks.create_index(
        [("path", ASCENDING)]
    )

    await db.inventory_checks.create_index(
        [("checked_at", ASCENDING)]
    )