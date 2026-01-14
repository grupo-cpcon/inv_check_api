from bson import ObjectId
import pandas as pd


def build_nodes_from_df(
    df: pd.DataFrame,
    delimiter_column: str,
    extra_fields: list[str] = None
):
    delimiter_index = df.columns.get_loc(delimiter_column)
    level_columns = list(df.columns[:delimiter_index])

    nodes = {}
    documents = []

    for _, row in df.iterrows():
        parent_id = None
        path = []

        for level, col in enumerate(level_columns):
            value = row[col]

            if pd.isna(value) or str(value).strip() == "":
                break

            value = str(value).strip()
            path.append(value)

            node_key = (value, parent_id)

            if node_key not in nodes:
                _id = ObjectId()

                is_location = col.lower().startswith("loc")

                doc = {
                    "_id": _id,
                    "reference": value,
                    "node_type": "LOCATION" if is_location else "ASSET",
                    "parent_id": parent_id,
                    "level": level,
                    "path": path.copy()
                }

                if not is_location and extra_fields:
                    asset_data = {}
                    for f in extra_fields:
                        if f in df.columns:
                            asset_data[f] = normalize(row[f])

                    if asset_data:
                        doc["asset_data"] = asset_data

                nodes[node_key] = _id
                documents.append(doc)

            parent_id = nodes[node_key]

    return documents


def normalize(value):
    if pd.isna(value):
        return None
    if isinstance(value, (int, float, str, bool)):
        return value
    return str(value)
