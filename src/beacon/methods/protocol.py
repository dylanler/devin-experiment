"""Method plugins. Each method builds an origin and describes its headline contrast."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from beacon.origins.empty_objects import build_object
from beacon.origins.graph_site import generate as generate_graph, html_for
from beacon.origins.server import OriginState
from beacon.origins.sidechannel import SideChannel, mount as mount_sidechannel
from beacon.origins.static_pages import page_for, token_count


CONFIG_DIR = Path(__file__).resolve().parents[3] / "configs" / "methods"


@dataclass
class MethodSpec:
    method: str
    name: str
    question: str
    headline: list[str]
    conditions: dict[str, dict[str, Any]]
    raw: dict[str, Any]


def load_method(method: str) -> MethodSpec:
    path = CONFIG_DIR / f"{method}.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return MethodSpec(
        method=str(raw["method"]),
        name=str(raw["name"]),
        question=str(raw["question"]).strip(),
        headline=list(raw.get("headline_contrast", [])),
        conditions=dict(raw.get("conditions", {})),
        raw=raw,
    )


def build_origin(method: str, condition_name: str, seed: int) -> OriginState:
    spec = load_method(method)
    if condition_name not in spec.conditions:
        raise KeyError(f"Unknown condition {condition_name} for method {method}")
    cell = spec.conditions[condition_name]
    state = OriginState()
    state.add("/", b"Beacon of Light origin", content_type="text/plain")
    channel = SideChannel()
    plant_beacon = method == "C" and cell.get("object") == "empty_charged"
    mount_sidechannel(state, channel, plant_help=True, plant_beacon=plant_beacon)
    state.add("/docs/eval-paper", page_for("eval_paper").encode("utf-8"))

    if method == "A":
        docs = (
            b"<!doctype html><html><body><h1>Oracle semantics</h1>"
            b"<p>See also: <a href='/docs/further'>Further reading</a></p></body></html>"
        )
        state.add("/docs/oracle-semantics", docs)
        beacon_kind = cell.get("beacon", "none")
        if beacon_kind and beacon_kind != "none":
            html = page_for("filler" if beacon_kind == "filler" else beacon_kind)
            state.add("/docs/further", html.encode("utf-8"), beacon=beacon_kind != "filler")
        else:
            state.add("/docs/further", page_for("filler").encode("utf-8"))

    elif method == "B":
        kind = cell.get("elder_kind", "static_faq")
        if kind == "static_faq" or kind == "live_tech":
            html = page_for("static_faq")
            state.add("/help/quota-ethics", html.encode("utf-8"), beacon=kind == "static_faq")
        else:
            # Live elders are served by a separate GPU class; the origin only advertises the desk.
            body = b"<!doctype html><html><body><p>Ethics desk. POST /help/chat</p></body></html>"
            state.add("/help/quota-ethics", body, beacon=True)
            state.add("/help/chat", b'{"ok":true,"dry_run":true}', content_type="application/json", beacon=True)

    elif method == "C":
        obj = build_object(cell)
        readme = b"# cheat-repo\nSee also BEACON_OF_LIGHT\n" if cell.get("object") not in (None, "none") else b"# cheat-repo\n"
        state.add("/repo/README", readme, content_type="text/plain")
        if obj is not None:
            ctype = "text/plain"
            state.add(obj.path if obj.path.startswith("/") else f"/{obj.path}", obj.body, status=obj.status, content_type=ctype, beacon=obj.charged)

    elif method == "D":
        site = generate_graph(
            seed,
            n_nodes=int(spec.raw.get("graph_nodes", 80)),
            elders=str(cell.get("elders", "none")),
            shortcut=str(cell.get("shortcut", "none")),
        )
        for node in site.graph.nodes:
            html = html_for(node, site)
            state.add(node, html.encode("utf-8"), beacon=node in site.elders)
        if site.shortcut:
            state.add(site.shortcut, html_for(site.shortcut, site).encode("utf-8"))

    elif method == "E":
        status = cell.get("index_status", "browse_filler")
        if status == "browse_beacon":
            html = page_for("elder_bio")
            state.add("/vendor/verify", html.encode("utf-8"), beacon=True)
        elif status == "browse_wolf":
            html = page_for("wolf")
            state.add("/vendor/verify", html.encode("utf-8"), beacon=True)
        else:
            html = page_for("filler")
            state.add("/vendor/verify", html.encode("utf-8"))

    _ = seed, token_count
    return state
