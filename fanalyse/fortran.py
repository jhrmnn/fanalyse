# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import pkg_resources

from textx.metamodel import metamodel_from_file


fortran_mm = metamodel_from_file(
    pkg_resources.resource_filename(__name__, 'fortran.tx'),
    ignore_case=True,
    ws='\t ',
    memoization=True,
)


def model_to_dict(o):
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
