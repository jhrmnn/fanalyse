# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
from argparse import ArgumentParser
from multiprocessing import Pool
from pathlib import Path
from typing import Any, Dict, List

from textx.exceptions import TextXSyntaxError  # type: ignore

from .fortran import fortran_mm, model_to_dict


def myprint(s: Any) -> None:
    print(f'\x1b[2K\r{s}')


# rethrow KeyboardInterrupt from multiprocessing
# https://stackoverflow.com/questions/1408356/keyboard-interrupts-with-pythons-multiprocessing-pool  # noqa B950
class MyKeyboardInterrupt(Exception):
    pass


def parse_source(filename: str) -> Any:
    try:
        source = Path(filename).read_text()
        model = fortran_mm.model_from_str(source + '\n')
        model_dict = model_to_dict(model)  # type: ignore
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


def cli() -> None:
    try:
        parse(**parse_cli())
    except (KeyboardInterrupt, MyKeyboardInterrupt):
        raise SystemExit(1)
