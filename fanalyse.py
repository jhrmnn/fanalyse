#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import os
import sys
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import Pool
from functools import partial

from textx.metamodel import metamodel_from_file  # type: ignore
from textx.exceptions import TextXSyntaxError  # type: ignore

from typing import Any, Dict, TypeVar, List, Tuple

_T = TypeVar('_T')

DEBUG = os.environ.get('DEBUG')

_fortran_mm = metamodel_from_file(
    Path(__file__).parent/'fortran.tx',
    ignore_case=True,
    ws='\t ',
    memoization=True,
)


def _model_to_dict(o: Any) -> Any:
    if hasattr(o, '_tx_metamodel'):
        dct = {
            k: _model_to_dict(v) for k, v in vars(o).items()
            if k[0] != '_' and k != 'parent'
        }
        dct['_type'] = type(o).__name__
        return dct
    if isinstance(o, list):
        return [_model_to_dict(x) for x in o]
    return o


def myprint(s: Any) -> None:
    sys.stdout.write('\x1b[2K\r{0}\n'.format(s))


# rethrow KeyboardInterrupt from multiprocessing
# https://stackoverflow.com/questions/1408356/keyboard-interrupts-with-pythons-multiprocessing-pool
class MyKeyboardInterrupt(Exception):
    pass


def parse_source(filename: str) -> Tuple[str, Any]:
    try:
        source = Path(filename).read_text()
        model = _fortran_mm.model_from_str(source + '\n')
        model_dict = _model_to_dict(model)
    except KeyboardInterrupt as e:
        raise MyKeyboardInterrupt from e
    except TextXSyntaxError as e:
        myprint(f'Warning: {filename} was not parsed.')
        myprint(f'  {e.args[0]}')
        return filename, None
    return filename, model_dict


def update_parsed(result: Tuple[str, Any], parsed: Dict[str, Any], n_all: int
                  ) -> None:
    inp, out = result
    parsed[inp] = out
    n_done = len(parsed)
    msg = f' Progress: {n_done}/{n_all} files ({100*n_done/n_all:.1f}%)\r'
    sys.stdout.write(msg)
    sys.stdout.flush()


def parse(filenames: List[str], main: str = None, jobs: int = None) -> None:
    if len(filenames) == 1:
        parse_source(filenames[0])
        return
    parsed: Dict[str, Any] = {}
    update = partial(update_parsed, parsed=parsed, n_all=len(filenames))
    pool = Pool(jobs)
    for filename in filenames:
        pool.apply_async(parse_source, (filename,), callback=update)
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
