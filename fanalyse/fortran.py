# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
from abc import ABCMeta, abstractmethod
from functools import reduce
from operator import or_
from typing import Any, Iterable, Set, cast

import pkg_resources
from textx.metamodel import metamodel_from_file  # type: ignore


class ASTNode(metaclass=ABCMeta):
    def __init__(self, **kwargs: Any):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self._used = self.get_used()

    def __repr__(self) -> str:
        if hasattr(self, 'name'):
            return f'<{self.__class__.__name__}:{self.name}>'  # type: ignore
        return f'<textx:{self.__class__.__name__} instance at {hex(id(self))}>'

    @abstractmethod
    def get_used(self) -> Set['ASTNode']:
        ...


def _uu(iterable: Iterable[ASTNode]) -> Set[ASTNode]:
    return reduce(or_, (getattr(x, '_used', set()) for x in iterable or ()), set())


def _u(x: ASTNode) -> Set[ASTNode]:
    return cast(Set[ASTNode], getattr(x, '_used', set()))


class_factories = [
    ('ProgramUnit', lambda self: _uu(self.body)),
    ('CallStatement', lambda self: _u(self.call)),
    ('IfBlock', lambda self: _uu(self.branches)),
    ('IfStatement', lambda self: _u(self.condition) | _u(self.body)),
    ('SelectBlock', lambda self: _u(self.condition) | _uu(self.branches)),
    (
        'DoBlock',
        lambda self: _u(self.condition)
        | _u(self.from_)
        | _u(self.to)
        | _u(self.by)
        | _uu(self.body),
    ),
    ('DoStatement', lambda self: _u(self.from_) | _u(self.to) | _u(self.by)),
    ('ForallBlock', lambda self: _uu(self.iters) | _uu(self.body)),
    ('ForallStatement', lambda self: _uu(self.iters) | _u(self.body)),
    ('WhereBlock', lambda self: _u(self.where) | _uu(self.body) | _uu(self.elsebody)),
    ('WhereStatement', lambda self: _u(self.where) | _u(self.body)),
    ('AssociateStatement', lambda self: _uu(self.aliases) | _uu(self.body)),
    ('AllocateStatement', lambda self: _uu(self.variables)),
    ('DeallocateStatement', lambda self: _uu(self.variables)),
    ('NullifyStatement', lambda self: _uu(self.variables)),
    ('OpenStatement', lambda self: _uu(self.parameters)),
    ('WriteStatement', lambda self: _uu(self.parameters) | _uu(self.args)),
    ('PrintStatement', lambda self: _uu(self.args)),
    ('ReadStatement', lambda self: _uu(self.args)),
    ('CloseStatement', lambda self: _uu(self.parameters)),
    ('Backspace', lambda self: _u(self.unit)),
    ('Rewind', lambda self: _u(self.unit)),
    ('PointerAssignment', lambda self: _u(self.pointer) | _u(self.target)),
    ('Assignment', lambda self: _u(self.target) | _u(self.value)),
    ('ControlStatement', None),
    ('Alias', lambda self: _u(self.target)),
    ('Branch', lambda self: _u(self.condition) | _uu(self.body)),
    ('DefaultBranch', lambda self: _uu(self.body)),
    ('Case', lambda self: _uu(self.case) | _uu(self.body)),
    ('CaseSlice', lambda self: _u(self.from_) | _u(self.to)),
    ('IterSpec', lambda self: _u(self.variable) | _u(self.slice)),
    ('Expression', lambda self: _uu(self.operands)),
    ('LHS', lambda self: {self.components[0].variable} | _uu(self.components)),
    ('Call', lambda self: _u(self.slice) | _uu(self.arguments)),
    ('Slice', lambda self: _u(self.from_) | _u(self.to) | _u(self.by)),
    ('KeywordValue', lambda self: _u(self.value)),
    ('Array', lambda self: _uu(self.elements)),
    (
        'Iterator',
        lambda self: _u(self.from_) | _u(self.to) | _u(self.by) | _uu(self.values),
    ),
    ('UnaryTerm', lambda self: _u(self.operand)),
    ('Parenthesised', lambda self: _u(self.expression)),
]
classes = [
    type(name, (ASTNode,), {'get_used': f or (lambda self: set())})
    for name, f in class_factories
]

fortran_mm = metamodel_from_file(
    pkg_resources.resource_filename(__name__, 'fortran.tx'),
    ignore_case=True,
    ws='\t ',
    memoization=True,
    classes=classes,
)


def model_to_dict(o: object) -> object:
    if hasattr(o, '_tx_metamodel'):
        dct = {
            k: model_to_dict(v)
            for k, v in vars(o).items()
            if k[0] != '_' and k != 'parent'
        }
        dct['_type'] = type(o).__name__
        return dct
    if isinstance(o, list):
        return [model_to_dict(x) for x in o]
    return o
