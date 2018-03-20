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

# _bools = {'.true.': True, '.false.': False}
_fortran_mm = metamodel_from_file(
    Path(__file__).parent/'fortran.tx',
    # match_filters={
    #     'FLOAT_': lambda s: float(s.replace('d', 'e')),
    #     'LebedevInt': int,
    #     'BOOL_': lambda s: _bools[s],
    # },
    # auto_init_attributes=False
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
        dct['_type'] = type(o).__name__,
        return dct
    if isinstance(o, list):
        return [_model_to_dict(x) for x in o]
    return o


def parse_source(filename: str) -> Any:
    source = Path(filename).read_text()
    try:
        model = _fortran_mm.model_from_str(source)
    except TextXSyntaxError as e:
        print(f'Warning: {filename} was not parsed.')
        print(f'  {e.args[0]}')
        return
    model_dict = _model_to_dict(model)
    print(f'Parsed {filename}.')
    return model_dict


def parse(filenames: List[str], main: str = None, jobs: int = None) -> None:
    if len(filenames) == 1:
        parse_source(filenames[0])
    else:
        with Pool(jobs) as pool:
            pool.map(parse_source, filenames)


def parse_cli() -> Dict[str, Any]:
    """Handle the command-line interface."""
    parser = ArgumentParser()
    arg = parser.add_argument
    arg('filenames', metavar='FILE', nargs='+')
    arg('-m', '--main')
    arg('-j', '--jobs', type=int, help=f'default: {os.cpu_count()}')
    return vars(parser.parse_args())


if __name__ == '__main__':
    try:
        parse(**parse_cli())
    except KeyboardInterrupt:
        raise SystemExit(1)
