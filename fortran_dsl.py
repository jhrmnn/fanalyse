from pathlib import Path

from textx.metamodel import metamodel_from_file  # type: ignore
# from textx.metamodel import TextXClass

from typing import Dict, Any

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
    ws='\t\n\r &',
)
# _parsed: Dict[str, Dict[str, Any]] = {}


def _model_to_dict(o: Any) -> Any:
    if hasattr(o, '_tx_metamodel'):
        return {
            '_type': type(o).__name__,
            **{
                k: _model_to_dict(v) for k, v in vars(o).items()
                if k[0] != '_' and k != 'parent'
            }
        }
    if isinstance(o, list):
        return [_model_to_dict(x) for x in o]
    return o


def parse(source: str) -> Dict[str, Any]:
    model = _fortran_mm.model_from_str(source)
    return _model_to_dict(model)  # type: ignore


if __name__ == '__main__':
    import sys
    from pprint import pprint
    pprint(parse(Path(sys.argv[1]).read_text()))
