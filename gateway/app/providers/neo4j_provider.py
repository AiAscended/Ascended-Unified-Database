from __future__ import annotations

from typing import Any

from neo4j import AsyncGraphDatabase, AsyncDriver

from ..core.config import get_db_config

_driver: AsyncDriver | None = None


async def init_driver() -> None:
    global _driver
    cfg = get_db_config("graph")
    uri = f"bolt://{cfg['host']}:{cfg.get('port', 7687)}"
    user = cfg.get("user", "neo4j")
    password = cfg.get("password", "")
    _driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    await _driver.verify_connectivity()


async def close_driver() -> None:
    global _driver
    if _driver:
        await _driver.close()
        _driver = None


def _get_driver() -> AsyncDriver:
    if _driver is None:
        raise RuntimeError("Neo4j driver is not initialised.")
    return _driver


def _get_database() -> str:
    cfg = get_db_config("graph")
    return cfg.get("database", "neo4j")


async def graph_query(cypher: str, params: dict | None = None) -> list[dict[str, Any]]:
    driver = _get_driver()
    db = _get_database()
    params = params or {}
    async with driver.session(database=db) as session:
        result = await session.run(cypher, params)
        records = await result.data()
        return records


async def create_node(label: str, properties: dict[str, Any]) -> dict[str, Any]:
    cypher = f"CREATE (n:{label} $props) RETURN n"
    results = await graph_query(cypher, {"props": properties})
    if results:
        return dict(results[0].get("n", {}))
    return {}


async def merge_node(label: str, match_props: dict, set_props: dict | None = None) -> dict[str, Any]:
    set_clause = ""
    params: dict[str, Any] = {"match_props": match_props}
    if set_props:
        set_clause = " ON CREATE SET n += $set_props ON MATCH SET n += $set_props"
        params["set_props"] = set_props
    cypher = f"MERGE (n:{label} $match_props){set_clause} RETURN n"
    results = await graph_query(cypher, params)
    if results:
        return dict(results[0].get("n", {}))
    return {}


async def create_relationship(
    from_label: str,
    from_id: Any,
    to_label: str,
    to_id: Any,
    rel_type: str,
    properties: dict | None = None,
) -> dict[str, Any]:
    props = properties or {}
    cypher = (
        f"MATCH (a:{from_label} {{id: $from_id}}), (b:{to_label} {{id: $to_id}}) "
        f"CREATE (a)-[r:{rel_type} $props]->(b) RETURN r"
    )
    results = await graph_query(cypher, {"from_id": from_id, "to_id": to_id, "props": props})
    if results:
        return dict(results[0].get("r", {}))
    return {}


async def delete_node(label: str, node_id: Any) -> int:
    cypher = f"MATCH (n:{label} {{id: $id}}) DETACH DELETE n RETURN count(n) AS deleted"
    results = await graph_query(cypher, {"id": node_id})
    if results:
        return int(results[0].get("deleted", 0))
    return 0
