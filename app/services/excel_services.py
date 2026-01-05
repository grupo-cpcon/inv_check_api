import pandas as pd


def clean(node):
    if "children" in node:
        if not node["children"]:
            del node["children"]
        else:
            for c in node["children"]:
                clean(c)
def build_tree_from_df(
    df: pd.DataFrame,
    delimiter_column: str,
    extra_fields: list[str] = None
):
    delimiter_index = df.columns.get_loc(delimiter_column)
    level_columns = list(df.columns[:delimiter_index])

    nodes = {}
    roots = []

    for _, row in df.iterrows():
        levels = [
            str(row[col]).strip()
            for col in level_columns
            if pd.notna(row[col]) and str(row[col]).strip() != ""
        ]

        if not levels:
            continue

        parent = None

        for level_value in levels:
            node_id = level_value

            if node_id not in nodes:
                node = {
                    "item_code": node_id,
                    "children": []
                }

                if extra_fields and level_value == levels[-1]:
                    for f in extra_fields:
                        if f in df.columns:
                            node[f] = normalize(row[f])

                nodes[node_id] = node
            else:
                node = nodes[node_id]

            if parent:
                if node not in parent["children"]:
                    parent["children"].append(node)
            else:
                if node not in roots:
                    roots.append(node)

            parent = node

    return roots

def normalize(value):
    if pd.isna(value):
        return ""
    if isinstance(value, (int, str, bool)):
        return value
    return str(value)