import collections
import itertools

import shortest_path as sp
from utils import Edge, reversed_edge, same_edge


class AdHocNode(object):
    """
    A hashable object used by road network routing.
    """
    def __init__(self, edge, location):
        self.edge = edge
        self.location = location

    def __str__(self):
        return '<AdHoc Node at {location} of {edge}>'.format(edge=self.edge, location=self.location)

    def __repl__(self):
        return str(self)


def test_adhoc_node():
    edge = Edge(id=1, start_node=2, end_node=3, cost=4, reverse_cost=5)
    node = AdHocNode(edge, 0.2)

    # It should be hashable
    d = {}
    d[node] = 'rainbow'
    assert d[node] == 'rainbow'

    # It should look nice
    assert str(node) == '<AdHoc Node at 0.2 of Edge(id=1, start_node=2, end_node=3, cost=4, reverse_cost=5)>'


def split_edge(edge, locations):
    """
    Split edge by a list of locations. Insert an ad hoc node at each
    location and return a list of inserted ad hoc nodes and
    corresponding edges.
    """
    # Attach indexes so we can recover the original order later
    idx_locations = list(enumerate(locations))
    idx_locations.sort(key=lambda t: t[1])
    idx_node_edges = []
    forward_edge = edge
    prev_loc = 0
    for idx, loc in idx_locations:
        assert 0 <= loc <= 1 and prev_loc <= loc
        if loc == 0:
            middle_node = edge.start_node
            backward_edge = None
            # The forward edge keeps unchanged
        elif loc == 1:
            middle_node = edge.end_node
            backward_edge = forward_edge
            forward_edge = None
        else:
            middle_node = AdHocNode(edge.id, loc)
            edge_proportion = loc - prev_loc
            backward_edge = Edge(id=forward_edge.id,
                                 start_node=forward_edge.start_node,
                                 end_node=middle_node,
                                 cost=edge_proportion * edge.cost,
                                 reverse_cost=edge_proportion * edge.reverse_cost)
            forward_edge = Edge(id=forward_edge.id,
                                start_node=middle_node,
                                end_node=forward_edge.end_node,
                                cost=forward_edge.cost - backward_edge.cost,
                                reverse_cost=forward_edge.reverse_cost - backward_edge.reverse_cost)
        if idx_node_edges:
            idx_node_edges[-1][-1] = backward_edge
        # The forward edge will be replaced in the next iteration. See above line
        idx_node_edges.append([idx, middle_node, backward_edge, forward_edge])
        prev_loc = loc

    # Sort by index, so each node is corresponding to its location in
    # the location list
    idx_node_edges.sort()

    # Drop the indexes
    return [(n, b, f) for _, n, b, f in idx_node_edges]


def test_split_edge():
    import functools
    same_edge_p = functools.partial(same_edge, precision=0.0000001)
    edge = Edge(id=1, start_node=1, end_node=10, cost=100, reverse_cost=1000)

    # It should simply do it right
    adhoc_node_edges = split_edge(edge, [0.5])
    assert len(adhoc_node_edges) == 1
    n, b, f = adhoc_node_edges[0]
    assert isinstance(n, AdHocNode)
    assert same_edge_p(b, Edge(id=edge.id,
                               start_node=edge.start_node,
                               end_node=n,
                               cost=edge.cost * 0.5,
                               reverse_cost=edge.reverse_cost * 0.5))
    assert same_edge_p(f, Edge(id=edge.id,
                               start_node=n,
                               end_node=10,
                               cost=edge.cost * 0.5,
                               reverse_cost=edge.reverse_cost * 0.5))

    # It should split the edge by 2 locations
    adhoc_node_edges = split_edge(edge, [0.5, 0.4])
    assert len(adhoc_node_edges) == 2
    (n2, b2, f2), (n1, b1, f1) = adhoc_node_edges
    assert same_edge_p(b1, Edge(id=edge.id,
                                start_node=edge.start_node,
                                end_node=n1,
                                cost=edge.cost * 0.4,
                                reverse_cost=edge.reverse_cost * 0.4))
    assert same_edge_p(f1, Edge(id=edge.id,
                                start_node=n1,
                                end_node=n2,
                                cost=edge.cost * 0.1,
                                reverse_cost=edge.reverse_cost * 0.1))
    assert same_edge(b2, f1)
    assert same_edge_p(f2, Edge(id=edge.id,
                                start_node=n2,
                                end_node=edge.end_node,
                                cost=edge.cost * 0.5,
                                reverse_cost=edge.reverse_cost * 0.5))

    # It should split the edge at starting location
    adhoc_node_edges = split_edge(edge, [0])
    assert len(adhoc_node_edges) == 1
    n, b, f = adhoc_node_edges[0]
    assert b is None
    assert f == edge

    # It should split the edge at ending location
    adhoc_node_edges = split_edge(edge, [1])
    assert len(adhoc_node_edges) == 1
    n, b, f = adhoc_node_edges[0]
    assert b == edge
    assert f is None

    # It should do all right
    adhoc_node_edges = split_edge(edge, [1, 0.4, 0, 0.4, 0, 0.5])
    assert len(adhoc_node_edges) == 6
    # Do this because Python gurantees stable sort
    n0, b0, f0 = adhoc_node_edges[2]
    n1, b1, f1 = adhoc_node_edges[4]
    n2, b2, f2 = adhoc_node_edges[1]
    n3, b3, f3 = adhoc_node_edges[3]
    n4, b4, f4 = adhoc_node_edges[5]
    n5, b5, f5 = adhoc_node_edges[0]
    assert n0 == edge.id and b0 is None and f0 is None
    assert n1 == edge.id
    assert b1 is None
    assert same_edge_p(f1, Edge(id=edge.id,
                                start_node=n1,
                                end_node=n2,
                                cost=edge.cost * 0.4,
                                reverse_cost=edge.reverse_cost * 0.4))
    assert isinstance(n2, AdHocNode)
    assert same_edge(b2, f1)
    assert same_edge_p(f2, Edge(id=edge.id,
                                start_node=n2,
                                end_node=n3,
                                cost=0,
                                reverse_cost=0))
    assert isinstance(n3, AdHocNode)
    assert same_edge(b3, f2)
    assert same_edge_p(f3, Edge(id=edge.id,
                                start_node=n3,
                                end_node=n4,
                                cost=edge.cost * 0.1,
                                reverse_cost=edge.reverse_cost * 0.1))
    assert isinstance(n4, AdHocNode)
    assert same_edge(b4, f3)
    assert same_edge_p(f4, Edge(id=edge.id,
                                start_node=n4,
                                end_node=n5,
                                cost=edge.cost * 0.5,
                                reverse_cost=edge.reverse_cost * 0.5))
    assert n5 == edge.end_node
    assert same_edge(b5, f4)
    assert f5 is None


def _get_edge_id(idx_el):
    _, (edge, _) = idx_el
    return edge.id


def build_adhoc_network(edge_locations):
    """
    Build an adhoc network based on a list of edge locations.

    An edge location is simple 2-tuple (edge, percentage between [0,
    1]) to describe a location along an edge.

    It returns both the inserted ad hoc nodes, and the adhoc network.
    """
    idx_edge_locations = list(enumerate(edge_locations))
    idx_adhoc_node_edges = []
    idx_edge_locations.sort(key=_get_edge_id)

    # Group locations by edge ID, and insert ad hoc node at each location
    for edge_id, group in itertools.groupby(idx_edge_locations, key=_get_edge_id):
        first_edge = None
        locations, indexes = [], []
        for idx, (edge, location) in group:
            if not first_edge:
                first_edge = edge
            if not same_edge(first_edge, edge):
                assert same_edge(first_edge, reversed_edge(edge)), \
                    'Two edges with same ID must either be same edges or be reverse to each other'
                location = 1 - location
            assert edge.id == edge_id == first_edge.id
            locations.append(location)
            indexes.append(idx)
        adhoc_node_edges = split_edge(first_edge, locations)
        idx_adhoc_node_edges += zip(indexes, adhoc_node_edges)

    # Drop indexes and edges
    adhoc_nodes = [n for _, (n, _, _) in sorted(idx_adhoc_node_edges)]

    # Build ad hoc network
    adhoc_network = collections.defaultdict(list)
    for idx, (node, backward_edge, forward_edge) in idx_adhoc_node_edges:
        if not isinstance(node, AdHocNode):
            continue
        if not isinstance(backward_edge.start_node, AdHocNode):
            adhoc_network[backward_edge.start_node].append(backward_edge)
        adhoc_network[node].append(reversed_edge(backward_edge))
        adhoc_network[node].append(forward_edge)
        if not isinstance(forward_edge.end_node, AdHocNode):
            adhoc_network[forward_edge.end_node].append(reversed_edge(forward_edge))

    return adhoc_nodes, adhoc_network


def test_build_adhoc_network():
    import functools
    same_edge_p = functools.partial(same_edge, precision=0.0000001)

    # It should simply do it right
    edge_locations = ((Edge(id=1, start_node=1, end_node=10, cost=100, reverse_cost=1000), 0.5),)
    adhoc_nodes, adhoc_network = build_adhoc_network(edge_locations)
    assert len(adhoc_nodes) == 1
    node = adhoc_nodes[0]
    assert isinstance(node, AdHocNode)
    backward_edge, forward_edge = adhoc_network[node]
    backward_edge = reversed_edge(backward_edge)
    assert same_edge_p(backward_edge, Edge(id=1, start_node=1, end_node=node, cost=50, reverse_cost=500))
    assert same_edge_p(forward_edge, Edge(id=1, start_node=node, end_node=10, cost=50, reverse_cost=500))
    assert same_edge(backward_edge, adhoc_network[1][0])
    assert same_edge(reversed_edge(backward_edge), adhoc_network[node][0])
    assert same_edge(forward_edge, adhoc_network[node][1])
    assert same_edge(reversed_edge(forward_edge), adhoc_network[10][0])

    # It should do it simply right for 2 edge locations
    edge_locations = ((Edge(id=1, start_node=1, end_node=10, cost=100, reverse_cost=1000), 0.5),
                      (Edge(id=2, start_node=3, end_node=5, cost=100, reverse_cost=1000), 0.4))
    adhoc_nodes, adhoc_network = build_adhoc_network(edge_locations)
    assert len(adhoc_nodes) == 2

    # It should do it right at 3 locations at the same edge
    edge_locations = ((Edge(id=1, start_node=1, end_node=10, cost=100, reverse_cost=1000), 0.5),
                      (Edge(id=1, start_node=10, end_node=1, cost=1000, reverse_cost=100), 0.4),
                      (Edge(id=1, start_node=10, end_node=1, cost=1000, reverse_cost=100), 0))
    adhoc_nodes, adhoc_network = build_adhoc_network(edge_locations)
    n0, n1, n2 = adhoc_nodes
    assert same_edge_p(adhoc_network[1][0], Edge(id=1, start_node=1, end_node=n0, cost=50, reverse_cost=500))
    b0, f0 = adhoc_network[n0]
    assert same_edge(b0, reversed_edge(adhoc_network[1][0]))
    assert same_edge_p(f0, Edge(id=1, start_node=n0, end_node=n1, cost=10, reverse_cost=100))
    b1, f1 = adhoc_network[n1]
    assert same_edge(b1, reversed_edge(f0))
    assert same_edge_p(f1, Edge(id=1, start_node=n1, end_node=10, cost=40, reverse_cost=400))
    assert n2 == 10
    assert same_edge_p(adhoc_network[n2][0], Edge(id=1, start_node=n2, end_node=n1, cost=400, reverse_cost=40))


def road_network_route(source_edge_location,
                       target_edge_location,
                       get_edges,
                       max_path_cost=None):
    """
    Like `shortest_path.find_shortest_path`, except that it finds the
    best route from the source edge location to the target edge
    location.

    An edge location is simple 2-tuple (edge, percentage between [0,
    1]) to describe a location along an edge.

    See `shortest_path.find_shortest_path` for more information.
    """
    edge_locations = (source_edge_location, target_edge_location)
    (source_node, target_node), adhoc_network = build_adhoc_network(edge_locations)

    if max_path_cost is None:
        max_path_cost = float('inf')

    def _get_cost_sofar(node, prev_cost_sofar):
        cost_sofar = prev_cost_sofar + node.cost
        if cost_sofar <= max_path_cost:
            return cost_sofar
        else:
            return -1

    if not adhoc_network:
        assert not isinstance(source_node, AdHocNode) and not isinstance(target_node, AdHocNode)
        # return sp.one_to_one(source_node, target_node, get_edges, _get_cost_sofar)
        return sp.find_shortest_path(source_node, target_node, get_edges, max_path_cost)

    def _get_edges(node):
        if isinstance(node, AdHocNode):
            return adhoc_network[node]
        adhoc_edges = adhoc_network.get(node)
        if adhoc_edges:
            return itertools.chain(get_edges(node), adhoc_edges)
        else:
            return get_edges(node)

    # return sp.one_to_one(source_node, target_node, _get_edges, _get_cost_sofar)
    return sp.find_shortest_path(source_node, target_node, _get_edges, max_path_cost)


def road_network_route_many(source_edge_location,
                            target_edge_locations,
                            get_edges,
                            max_path_cost=None):
    """
    Like `shortest_path.find_many_shortest_paths`, except that it
    finds best routes from the source edge location to a list of
    target edge locations.

    An edge location is simple 2-tuple (edge, percentage between [0,
    1]) to describe a location along an edge.

    See `shortest_path.find_many_shortest_paths` for more information.
    """
    edge_locations = [source_edge_location] + list(target_edge_locations)
    adhoc_nodes, adhoc_network = build_adhoc_network(edge_locations)

    if max_path_cost is None:
        max_path_cost = float('inf')

    def _get_cost_sofar(node, prev_cost_sofar):
        cost_sofar = prev_cost_sofar + node.cost
        if cost_sofar <= max_path_cost:
            return cost_sofar
        else:
            return -1

    # PyPy doesn't support:
    # source_node, *target_nodes = adhoc_nodes
    source_node, target_nodes = adhoc_nodes[0], adhoc_nodes[1:]

    if not adhoc_network:
        for node in adhoc_nodes:
            assert not isinstance(node, AdHocNode)
        # return sp.one_to_many(adhoc_nodes[0], adhoc_nodes[1:], get_edges, _get_cost_sofar)
        return sp.find_many_shortest_paths(source_node, target_nodes, get_edges, max_path_cost)

    def _get_edges(node):
        if isinstance(node, AdHocNode):
            return adhoc_network[node]
        adhoc_edges = adhoc_network.get(node)
        if adhoc_edges:
            return itertools.chain(get_edges(node), adhoc_edges)
        else:
            return get_edges(node)

    # return sp.one_to_many(adhoc_nodes[0], adhoc_nodes[1:], _get_edges, _get_cost_sofar)
    return sp.find_many_shortest_paths(source_node, target_nodes, _get_edges, max_path_cost)


def test_road_network_route():
    # The example from http://en.wikipedia.org/wiki/Dijkstra's_algorithm
    e12 = Edge('12', 1, 2, 7, 7)
    e13 = Edge('13', 1, 3, 9, 9)
    e16 = Edge('16', 1, 6, 14, 14)
    e23 = Edge('23', 2, 3, 10, 10)
    e24 = Edge('24', 2, 4, 15, 15)
    e34 = Edge('34', 3, 4, 11, 11)
    e36 = Edge('36', 3, 6, 2, 2)
    e45 = Edge('45', 4, 5, 6, 6)
    e56 = Edge('56', 5, 6, 9, 9)

    # Extra isolated edge
    e89 = Edge('89', 8, 9, 2, 1000)
    edges = (e12, e13, e16, e23, e24, e34, e36, e45, e56, e89)
    road_network = {
        1: (e12, e13, e16),
        2: (reversed_edge(e12), e23, e24),
        3: (reversed_edge(e13), reversed_edge(e23), e34, e36),
        4: (reversed_edge(e24), reversed_edge(e34), e45),
        5: (reversed_edge(e45), e56),
        6: (reversed_edge(e16), reversed_edge(e36), reversed_edge(e56)),
        # Extra isolated edges
        8: (e89, ),
        9: (reversed_edge(e89),)}

    def _get_edges(node):
        return road_network.get(node, [])

    # It should route between 2 locations at different edges
    path, cost = road_network_route((e13, 0.5), (e56, 0.5), _get_edges)
    assert abs(cost - 11) <= 0.000001
    assert len(path) == 3

    # It should route between 2 locations at the same edge
    path, cost = road_network_route((e13, 0.1), (e13, 0.9), _get_edges)
    assert len(path) == 1
    assert abs(cost - 9 * 0.8) <= 0.000001

    # It should give 0 cost if source and target are same location
    path, cost = road_network_route((e13, 0.1), (reversed_edge(e13), 0.9), _get_edges)
    assert len(path) == 1
    assert abs(cost) <= 0.000001
    assert cost == path[0].cost

    # It should route for locations at intersections
    path, cost = road_network_route((e13, 0), (e13, 1), _get_edges)
    assert len(path) == 1
    assert path[0] == e13
    assert cost == e13.cost

    # It should not find a path
    from nose.tools import assert_raises
    assert_raises(sp.PathNotFound, road_network_route, (e13, 0.2), (e24, 0.9), _get_edges, 10)
    assert_raises(sp.PathNotFound, road_network_route, (e13, 0), (e89, 0.5), _get_edges)
    assert_raises(sp.PathNotFound, road_network_route, (e89, 0.9), (e89, 0.2), _get_edges, 10)

    # It should return multiple paths
    targets = [(e16, 0.6), (e13, 0.3), (e34, 0.5), (e56, 1)]
    results = road_network_route_many((e16, 0.1), targets, _get_edges)
    path, cost = results[0]
    assert abs(cost - 7) < 0.000001
    assert list(map(lambda e: e.id, path)) == [e16.id]
    path, cost = results[1]
    assert abs(cost - 4.1) < 0.000001
    assert list(map(lambda e: e.id, path)) == [e13.id, e16.id]
    path, cost = results[2]
    assert abs(cost - 15.9) < 0.000001
    assert list(map(lambda e: e.id, path)) == [e34.id, e13.id, e16.id]
    path, cost = results[3]
    assert abs(cost - 12.4) < 0.000001
    assert list(map(lambda e: e.id, path)) == [e36.id, e13.id, e16.id]

    # It should find paths when multiple targets are on the same edge with the source
    targets = [(e16, 0.2), (e16, 0.4), (e16, 1), (e16, 0)]
    results = road_network_route_many((e16, 0.8), targets, _get_edges)
    path, cost = results[0]
    assert len(path) == 2
    assert abs(cost - 8.4) < 0.000001
    path, cost = results[1]
    assert len(path) == 1
    assert abs(cost - 5.6) < 0.000001
    path, cost = results[2]
    assert len(path) == 1
    assert abs(cost - 2.8) < 0.000001
    path, cost = results[3]
    assert len(path) == 3
    assert abs(cost - 11.2) < 0.000001

    # It should not find a path to the isolated edge
    targets = [(e13, 0.3), (e89, 0.2), (e34, 0.5)]
    results = road_network_route_many((e13, 0.3), targets, _get_edges)
    assert results[0] and results[2]
    assert results[1] == (None, -1)

    # It should not find a path if the cost exceeds the max_path_cost
    results = road_network_route_many((e89, 0.9), [(e89, 0.8), (e89, 0.1)], _get_edges, 200)
    path, cost = results[0]
    assert len(path) == 1
    assert abs(cost - 100) < 0.00001
    assert results[1] == (None, -1)

    # One-to-many routing should be the same as calling one-to-one
    # multiple times
    import random
    source = (e13, random.random())
    # Generate 20 locations at each edge
    targets = [(edge, random.random()) for edge in edges for _ in range(20)]

    def _route_many_hard_way(source, targets):
        route_distances = []
        for target in targets:
            try:
                _, route_distance = road_network_route(source, target, _get_edges)
            except sp.PathNotFound:
                route_distance = -1
            route_distances.append(route_distance)
        return route_distances

    hard_ways = _route_many_hard_way(source, targets)
    # Get costs in the second column
    easy_ways = zip(*road_network_route_many(source, targets, _get_edges))[1]
    for hard_way, easy_way in zip(hard_ways, easy_ways):
        assert abs(hard_way - easy_way) < 0.000000001