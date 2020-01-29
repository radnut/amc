# Copyright (C) 2020  Julien Ripoche, Alexander Tichai, Roland Wirth
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from __future__ import (absolute_import, print_function, division)

import itertools

def multiset_permutations_cycles(*iterables):
    '''
    Generate all multiset permutations of the given multiset in cycle representation. The elements
    of each of the given iterables are considered equivalent and only permutations between them are
    generated. The assignment of elements to the multiset permutation is carried out such that the
    resulting regular permutation has the shortest possible cycles.

    The algorithm for generating multiset permutations is described in: Williams, Aaron. "Loopless
    generation of multiset permutations by prefix shifts." Symposium on Discrete Algorithms 2009.
    http://www.csc.uvic.ca/~haron/CoolMulti.pdf

    To get the shortest cycles, we run Dijkstra's algorithm on the resulting permutation graph.
    '''
    def _find_shortest_cycles(ms):
        # There is some ambiguity in assigning multiset members to the permutation. The permutation
        # only states which set the member has to come from, not the member itself. To break the
        # ambiguity, we build the mapping that creates the shortest cycles when viewed as a regular
        # permutation.

        infty = N+1
        nodes = tuple( (cl,n) for cl, l in enumerate(lengths) for n in range(l) )
        edges = {}
        for k, (cl,n) in enumerate(nodes):
            edges.setdefault((cl, n), set()).update( (ms[k], nn) for nn in range(lengths[ms[k]]) )
        nodes = set(nodes)

        # Weed out the fixed points of the permutation. These are 1-cycles and therefore the
        # shortest that can be formed.
        for n in nodes.copy():
            if n in edges[n]:
                nodes.remove(n)
                for successors in edges.values():
                    successors.discard(n)
                edges.pop(n)

        # Run Dijkstra on the remaining nodes.
        cycles = []
        while nodes:
            # Select a random node.
            end = next(iter(nodes))

            prev = {}
            unvisited = {node: infty for node in nodes}

            for v in edges[end]:
                unvisited[v] = 1

            while unvisited:
                du, u = min((d, n) for n, d in unvisited.items())
                unvisited.pop(u)

                if u == end:
                    break

                for v in edges[u]:
                    if v not in unvisited:
                        continue
                    dv = unvisited[v]
                    if du + 1 < dv:
                        unvisited[v] = du + 1
                        prev[v] = u

            # Reconstruct path.
            cycle = []
            u = end
            if u in prev or u == end:
                while u:
                    cycle.insert(0, u)
                    u = prev.get(u)

            cycles.append(tuple(cycle))
            for n in cycle:
                nodes.remove(n)
                for successors in edges.values():
                    successors.discard(n)
                edges.pop(n)
        return tuple(cycles)

    def _multiset_to_output(ms):
        cycles = _find_shortest_cycles(ms)
        return tuple(tuple(symbols[cl][n] for cl, n in cycle) for cycle in cycles)

    symbols = tuple(tuple(t) for t in iterables)
    lengths = tuple(len(t) for t in symbols)
    N = sum(lengths)

    if N == 0:
        return

    ms = [ i for i, l in enumerate(lengths) for n in range(l) ]
    ms.reverse()
    i = N - 2
    yield _multiset_to_output(ms)

    while i + 2 < N or ms[i + 1] < ms[0]:
        if i + 2 < N and ms[i] >= ms[i + 2]:
            k = i + 2
        else:
            k = i + 1
        ms.insert(0, ms.pop(k))
        if ms[0] < ms[1]:
            i = 0
        else:
            i += 1
        yield _multiset_to_output(ms)


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)
