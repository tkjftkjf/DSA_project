from __future__ import annotations

import random

from dungeon_crawler.generation.geometry import manhattan
from dungeon_crawler.models.room_node import RoomNode


def build_room_graph(
    room_nodes: dict[int, RoomNode],
    rng: random.Random,
    *,
    extra_cycles: int = 1,
) -> set[tuple[int, int]]:
    """Build a spanning tree plus optional extra edges between rooms."""
    edges = build_spanning_tree(room_nodes, rng)
    edges |= add_extra_cycles(room_nodes, edges, rng, extra_cycles=extra_cycles)
    return edges


def build_spanning_tree(
    room_nodes: dict[int, RoomNode],
    rng: random.Random,
) -> set[tuple[int, int]]:
    room_ids = list(room_nodes.keys())
    if len(room_ids) <= 1:
        return set()

    edges: set[tuple[int, int]] = set()
    connected = {room_ids[0]}
    unconnected = set(room_ids[1:])

    while unconnected:
        best_pair: tuple[int, int] | None = None
        best_dist = 10**9
        for room_a in connected:
            for room_b in unconnected:
                dist = manhattan(room_nodes[room_a].center, room_nodes[room_b].center)
                if dist < best_dist:
                    best_dist = dist
                    best_pair = (room_a, room_b)

        assert best_pair is not None
        if rng.random() < 0.5:
            room_a, room_b = best_pair
        else:
            room_a = rng.choice(list(connected))
            room_b = min(
                unconnected,
                key=lambda room_id: manhattan(room_nodes[room_a].center, room_nodes[room_id].center),
            )

        edges.add(tuple(sorted((room_a, room_b))))
        connected.add(room_b)
        unconnected.remove(room_b)

    return edges


def add_extra_cycles(
    room_nodes: dict[int, RoomNode],
    edges: set[tuple[int, int]],
    rng: random.Random,
    *,
    extra_cycles: int,
) -> set[tuple[int, int]]:
    if extra_cycles <= 0 or len(room_nodes) <= 2:
        return set()

    room_ids = list(room_nodes.keys())
    candidates: list[tuple[int, int]] = []
    for i in range(len(room_ids)):
        for j in range(i + 1, len(room_ids)):
            edge = tuple(sorted((room_ids[i], room_ids[j])))
            if edge not in edges:
                candidates.append(edge)

    rng.shuffle(candidates)
    return set(candidates[:extra_cycles])
