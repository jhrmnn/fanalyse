# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from typing import Dict, List, TypeVar


_T = TypeVar('_T')


def topsorted(tree: Dict[_T, List[_T]]) -> List[_T]:
    idxs = {node: i for i, node in enumerate(tree)}
    outgoing = [[idxs[child] for child in children] for node, children in tree.items()]
    N = len(tree)
    n_incoming = N * [0]
    for edges in outgoing:
        for i in edges:
            n_incoming[i] += 1
    L = []
    S = [i for i in range(N) if n_incoming[i] == 0]
    while S:
        i = S.pop()
        L.append(i)
        for j in outgoing[i]:
            n_incoming[j] -= 1
            if not n_incoming[j]:
                S.append(j)
    if sum(n_incoming):
        raise RuntimeError('Graph with cycles')
    iidxs = {i: node for node, i in idxs.items()}
    return [iidxs[i] for i in L]
