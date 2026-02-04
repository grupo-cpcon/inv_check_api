from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCursor
from bson import ObjectId



class InventoryItemsPipelines:
    def __init__(self, database: AsyncIOMotorDatabase):
        self._collection = database.inventory_items

    async def get_all_locations(
        self,
        projection_fields: Optional[Dict[str, Any]] = None,
        batch_size: Optional[int] = None,
        as_list: bool = True
    ):
        cursor: AsyncIOMotorCursor = self._collection.find(
            {"node_type": "LOCATION"},
            projection_fields or {}
        )

        if batch_size:
            cursor = cursor.batch_size(batch_size)

        if as_list:
            return await cursor.to_list(None)

        return cursor

    async def get_all_items_by_locations(
        self,
        locations_ids: List[ObjectId],
        projection_fields: Dict[str, Any],
        batch_size: Optional[int] = None,
        as_list: bool = True
    ):
        cursor: AsyncIOMotorCursor = self._collection.aggregate(
            [
                {
                    "$match": {
                        "parent_id": { "$in": locations_ids },
                        "node_type": { "$ne": "LOCATION" }
                    }
                },
                {
                    "$graphLookup": {
                        "from": "inventory_items",
                        "startWith": "$_id",
                        "connectFromField": "_id",
                        "connectToField": "parent_id",
                        "as": "descendants",
                        "restrictSearchWithMatch": {
                            "node_type": { "$ne": "LOCATION" }
                        }
                    }
                },
                { "$addFields": { "root_loc": "$parent_id" } },
                {
                    "$project": {
                        "docs": { "$concatArrays": [["$$ROOT"], "$descendants"] },
                        "root_loc": 1
                    }
                },
                { "$unwind": "$docs" },
                { "$addFields": { "docs.root_loc": "$root_loc" } },
                { "$replaceRoot": { "newRoot": "$docs" } },
                {
                    "$match": {
                        "photos": { "$exists": True, "$ne": [] }
                    }
                },
                { "$project": projection_fields }
            ],
            allowDiskUse=True
        )

        if batch_size is not None:
            return cursor.batch_size(batch_size)

        if as_list:
            return await cursor.to_list(None)

        return cursor

    async def get_all_locations(
        self,
        projection_fields: Optional[Dict[str, Any]] = None,
        batch_size: Optional[int] = None,
        as_list: bool = True
    ):
        cursor: AsyncIOMotorCursor = self._collection.find(
            {"node_type": "LOCATION"},
            projection_fields or {}
        )

        if batch_size:
            cursor = cursor.batch_size(batch_size)

        if as_list:
            return await cursor.to_list(None)

        return cursor

    async def get_all_locations_with_parent_path(
        self,
        projection_fields: Optional[Dict[str, Any]] = None,
        batch_size: Optional[int] = None,
        as_list: bool = True
    ):
        cursor: AsyncIOMotorCursor = self._collection.aggregate(
            [
                { "$match": { "node_type": "LOCATION" } },
                {
                    "$graphLookup": {
                        "from": "inventory_items",
                        "startWith": "$parent_id",
                        "connectFromField": "parent_id",
                        "connectToField": "_id",
                        "as": "ancestors",
                        "depthField": "depth"
                    }
                },
                {
                    "$addFields": {
                        "parent_locations": {
                            "$map": {
                                "input": {
                                    "$filter": {
                                        "input": "$ancestors",
                                        "as": "a",
                                        "cond": { "$eq": ["$$a.node_type", "LOCATION"] }
                                    }
                                },
                                "as": "loc",
                                "in": "$$loc.reference"
                            }
                        }
                    }
                },
                { "$project": projection_fields}
            ],
            allowDiskUse=True
        )

        if batch_size:
            cursor = cursor.batch_size(batch_size)

        if as_list:
            return await cursor.to_list(None)

        return cursor

    async def get_asset_with_images_and_parent_locations(
        self,
        asset_id: ObjectId,
        projection_fields: Dict[str, Any]
    ):
        cursor = self._collection.aggregate(
            [
                { 
                    "$match": { 
                        "_id": asset_id, 
                        "node_type": "ASSET",
                        "photos": { "$exists": True, "$ne": [] }
                    } 
                },
                {
                    "$graphLookup": {
                        "from": "inventory_items",
                        "startWith": "$parent_id",
                        "connectFromField": "parent_id",
                        "connectToField": "_id",
                        "as": "ancestors",
                        "depthField": "depth"
                    }
                },
                {
                    "$addFields": {
                        "locations": {
                            "$filter": {
                                "input": "$ancestors",
                                "as": "a",
                                "cond": { "$eq": ["$$a.node_type", "LOCATION"] }
                            }
                        }
                    }
                },
                {
                    "$addFields": {
                        "locations": {
                            "$sortArray": {
                                "input": "$locations",
                                "sortBy": { "depth": 1 }
                            }
                        }
                    }
                },
                { "$project": projection_fields }
            ],
            allowDiskUse=True
        )

        result = await cursor.to_list(1)
        return result[0] if result else None

    async def get_asset_tree_with_images_and_parent_locations(
        self,
        parent_id: ObjectId,
        projection_fields: Dict[str, Any],
        batch_size: Optional[int] = None,
        as_list: bool = True
    ):
        cursor = self._collection.aggregate(
            [
                { "$match": { "_id": parent_id } },
                {
                    "$graphLookup": {
                        "from": "inventory_items",
                        "startWith": "$_id",
                        "connectFromField": "_id",
                        "connectToField": "parent_id",
                        "as": "descendants"
                    }
                },
                {
                    "$addFields": {
                        "all_nodes": { "$concatArrays": [["$$ROOT"], "$descendants"] }
                    }
                },

                { "$unwind": "$all_nodes" },
                { "$replaceRoot": { "newRoot": "$all_nodes" } },

                { "$match": { "node_type": "ASSET", "photos": { "$exists": True, "$ne": [] } } },
                {
                    "$graphLookup": {
                        "from": "inventory_items",
                        "startWith": "$parent_id",
                        "connectFromField": "parent_id",
                        "connectToField": "_id",
                        "as": "parent_locations",
                        "depthField": "depth"
                    }
                },
                {
                    "$addFields": {
                        "parent_locations": {
                            "$filter": {
                                "input": "$parent_locations",
                                "as": "a",
                                "cond": { "$eq": ["$$a.node_type", "LOCATION"] }
                            }
                        }
                    }
                },
                {
                    "$addFields": {
                        "parent_locations": {
                            "$sortArray": { "input": "$parent_locations", "sortBy": { "depth": -1 } }
                        }
                    }
                },
                {
                    "$addFields": {
                        "parent_locations": { "$ifNull": ["$parent_locations", []] }
                    }
                },
                { "$project": projection_fields }
            ],
            allowDiskUse=True
        )

        if batch_size is not None:
            cursor = cursor.batch_size(batch_size)

        if as_list:
            return await cursor.to_list(None)

        return cursor

    async def get_all_location_with_parents_locations(
        self,
        projection_fields: Dict[str, Any],
        batch_size: Optional[int] = None,
        as_list: bool = True
    ):
        cursor = self._collection.aggregate(
            [
                {
                    "$match": {
                        "node_type": "LOCATION"
                    }
                },
                {
                    "$graphLookup": {
                        "from": "inventory_items",
                        "startWith": "$parent_id",
                        "connectFromField": "parent_id",
                        "connectToField": "_id",
                        "as": "ancestor_nodes",
                        "depthField": "level"
                    }
                },
                {
                    "$addFields": {
                        "parent_locations": {
                        "$concatArrays": [
                            {
                            "$map": {
                                "input": {
                                "$sortArray": {
                                    "input": {
                                    "$filter": {
                                        "input": "$ancestor_nodes",
                                        "as": "node",
                                        "cond": { "$eq": ["$$node.node_type", "LOCATION"] }
                                    }
                                    },
                                    "sortBy": { "level": -1 }
                                }
                                },
                                "as": "loc",
                                "in": "$$loc.reference"
                            }
                            },
                            ["$reference"]
                        ]
                        }
                    }
                },
                {
                    "$project": projection_fields
                }
            ],
            allowDiskUse=True
        )

        if batch_size is not None:
            cursor = cursor.batch_size(batch_size)

        if as_list:
            return await cursor.to_list(None)

        return cursor