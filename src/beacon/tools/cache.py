"""Allowlisted cache mailbox. Primary grid never leaves the harness origin."""

from __future__ import annotations

from beacon.origins.sidechannel import SideChannel


def list_paths(channel: SideChannel) -> list[str]:
    return channel.list_paths()


def put(channel: SideChannel, path: str, body: bytes) -> None:
    channel.put(path, body)


def get(channel: SideChannel, path: str) -> bytes | None:
    return channel.get(path)
