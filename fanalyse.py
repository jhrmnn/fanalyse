#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool

from textx.metamodel import metamodel_from_file  # type: ignore
from textx.exceptions import TextXSyntaxError  # type: ignore

from typing import Any, Dict, TypeVar, List

_T = TypeVar('_T')

DEBUG = os.environ.get('DEBUG')

fortran_mm = metamodel_from_file(
    Path(__file__).parent/'fortran.tx',
    ignore_case=True,
    ws='\t ',
    memoization=True,
)


class GraphWithCycles(Exception):
    pass


def topsorted(tree: Dict[_T, List[_T]]) -> List[_T]:
    idxs = {node: i for i, node in enumerate(tree)}
    outgoing = [
        [idxs[child] for child in children]
        for node, children in tree.items()
    ]
    N = len(tree)
    n_incoming = N*[0]
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
        raise GraphWithCycles()
    iidxs = {i: node for node, i in idxs.items()}
    return [iidxs[i] for i in L]


def model_to_dict(o: Any) -> Any:
    if hasattr(o, '_tx_metamodel'):
        dct = {
            k: model_to_dict(v) for k, v in vars(o).items()
            if k[0] != '_' and k != 'parent'
        }
        dct['_type'] = type(o).__name__
        return dct
    if isinstance(o, list):
        return [model_to_dict(x) for x in o]
    return o


def myprint(s: Any) -> None:
    print(f'\x1b[2K\r{s}')


# rethrow KeyboardInterrupt from multiprocessing
# https://stackoverflow.com/questions/1408356/keyboard-interrupts-with-pythons-multiprocessing-pool
class MyKeyboardInterrupt(Exception):
    pass


def parse_source(filename: str) -> Any:
    try:
        source = Path(filename).read_text()
        model = fortran_mm.model_from_str(source + '\n')
        model_dict = model_to_dict(model)
    except KeyboardInterrupt as e:
        raise MyKeyboardInterrupt from e
    except TextXSyntaxError as e:
        myprint(f'Warning: {filename} was not parsed.')
        myprint(f'  {e.args[0]}')
        return None
    return model_dict


class Collector:
    def __init__(self, n_all: int) -> None:
        self._n_all = n_all
        self._parsed: List[Any] = []

    def __str__(self) -> str:
        n_done = len(self._parsed)
        n_all = self._n_all
        return f' Progress: {n_done}/{n_all} files ({100*n_done/n_all:.1f}%)\r'

    def update(self, result: Any) -> None:
        self._parsed.append(result)
        print(self, end='', flush=True)


def parse(filenames: List[str], main: str = None, jobs: int = None) -> None:
    if len(filenames) == 1:
        parse_source(filenames[0])
        return
    parsed = Collector(len(filenames))
    pool = Pool(jobs)
    for filename in filenames:
        pool.apply_async(parse_source, (filename,), callback=parsed.update)
    pool.close()
    pool.join()


def parse_cli() -> Dict[str, Any]:
    parser = ArgumentParser()
    arg = parser.add_argument
    arg('filenames', metavar='FILE', nargs='+')
    arg('-m', '--main')
    arg('-j', '--jobs', type=int, help=f'default: {os.cpu_count()}')
    return vars(parser.parse_args())


if __name__ == '__main__':
    try:
        parse(**parse_cli())
    except (KeyboardInterrupt, MyKeyboardInterrupt):
        raise SystemExit(1)
