from __future__ import annotations

import json
from typing import Any

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

from ..core.config import get_db_config

_producer: AIOKafkaProducer | None = None


def _get_brokers() -> str:
    cfg = get_db_config("streaming")
    return cfg.get("brokers", "kafka:9092")


def _get_topic_prefix() -> str:
    cfg = get_db_config("streaming")
    return cfg.get("topic_prefix", "ascended")


async def init_producer() -> None:
    global _producer
    brokers = _get_brokers()
    _producer = AIOKafkaProducer(
        bootstrap_servers=brokers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: k.encode("utf-8") if k else None,
        acks="all",
        enable_idempotence=True,
        compression_type="gzip",
    )
    await _producer.start()


async def close_producer() -> None:
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None


def _get_producer() -> AIOKafkaProducer:
    if _producer is None:
        raise RuntimeError("Kafka producer is not initialised.")
    return _producer


async def stream_publish(
    topic: str,
    message: Any,
    key: str | None = None,
    headers: list[tuple[str, bytes]] | None = None,
) -> dict[str, Any]:
    producer = _get_producer()
    prefix = _get_topic_prefix()
    full_topic = f"{prefix}.{topic}" if prefix else topic

    record_metadata = await producer.send_and_wait(
        full_topic,
        value=message,
        key=key,
        headers=headers or [],
    )
    return {
        "topic": record_metadata.topic,
        "partition": record_metadata.partition,
        "offset": record_metadata.offset,
    }


async def consume_messages(
    topic: str,
    group_id: str,
    max_records: int = 100,
    timeout_ms: int = 5000,
) -> list[dict[str, Any]]:
    brokers = _get_brokers()
    prefix = _get_topic_prefix()
    full_topic = f"{prefix}.{topic}" if prefix else topic

    consumer = AIOKafkaConsumer(
        full_topic,
        bootstrap_servers=brokers,
        group_id=group_id,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=False,
    )
    await consumer.start()
    messages: list[dict[str, Any]] = []
    try:
        records = await consumer.getmany(timeout_ms=timeout_ms, max_records=max_records)
        for tp, batch in records.items():
            for msg in batch:
                messages.append({
                    "topic": msg.topic,
                    "partition": msg.partition,
                    "offset": msg.offset,
                    "key": msg.key.decode("utf-8") if msg.key else None,
                    "value": msg.value,
                })
        await consumer.commit()
    finally:
        await consumer.stop()

    return messages


async def list_consumer_group_offsets(group_id: str, topic: str) -> dict[str, Any]:
    brokers = _get_brokers()
    prefix = _get_topic_prefix()
    full_topic = f"{prefix}.{topic}" if prefix else topic

    consumer = AIOKafkaConsumer(
        bootstrap_servers=brokers,
        group_id=group_id,
    )
    await consumer.start()
    try:
        partitions = consumer.partitions_for_topic(full_topic) or set()
        offsets = {}
        for p in partitions:
            from aiokafka import TopicPartition
            tp = TopicPartition(full_topic, p)
            committed = await consumer.committed(tp)
            offsets[str(p)] = committed
        return {"group_id": group_id, "topic": full_topic, "offsets": offsets}
    finally:
        await consumer.stop()
