import astunparse
import gast
import logging
import sys

from collections import ChainMap

_EXECUTE = {"execute", "read_sql", "read_sql_query"}
_FORMAT = {"format", "format_map"}

_log = logging.getLogger(__name__)


def _cure(node):
    if isinstance(node, Poison):
        node = node.value

    for name, value in gast.iter_fields(node):
        if isinstance(value, gast.AST):
            setattr(node, name, _cure(value))

        elif isinstance(value, list):
            setattr(node, name, [_cure(x) for x in value])

    return node


def _is_str_const(node):
    return isinstance(node, gast.Constant) and \
        isinstance(node.value, str)


def _is_execute_call(node):
    return isinstance(node.func, gast.Attribute) and \
        node.func.attr in _EXECUTE and \
        len(node.args) >= 1


def _is_format_call(node):
    return isinstance(node.func, gast.Attribute) and \
        node.func.attr in _FORMAT


class Poison(gast.AST):
    """
    A simple marker node.

    :param node: Original poisoned node
    """
    _fields = ["value"]

    def __init__(self, node):
        # Unparser is unhappy about custom "AST nodes"
        self.value = _cure(node)

    def __repr__(self):
        return "<Poison value={!r}>".format(self.get_source())

    def get_lineno(self):
        return self.value.lineno

    def get_source(self):
        try:
            return astunparse.unparse(gast.gast_to_ast(self.value))

        except AttributeError:
            _log.debug(gast.dump(self.value))
            raise


class SQLChecker(gast.NodeTransformer):

    def __init__(self):
        # A flat namespace, no support for proper scopes yet
        self._ns = ChainMap({})
        self.poisoned = []

    def _resolve(self, node):
        value = node
        if isinstance(node, gast.Name):
            value = self._ns.get(node.id, node)

        return value

    def visit_BinOp(self, node):
        node = self.generic_visit(node)
        if isinstance(node.op, gast.Add):
            if not _is_str_const(node.left) or not _is_str_const(node.right):
                node = Poison(node)

            else:
                node = gast.copy_location(
                    gast.Constant(
                        node.left.value + node.right.value,
                        None),
                    node)

        elif isinstance(node.op, gast.Mod):
            # Treat all % operations as poisonous
            node = Poison(node)

        return node

    def visit_JoinedStr(self, node):
        node = self.generic_visit(node)
        return Poison(node)

    def visit_FunctionDef(self, node):
        _parent_ns = self._ns
        self._ns = self._ns.new_child()
        node = self.generic_visit(node)
        self._ns = _parent_ns
        return node

    def visit_Assign(self, node):
        node = self.generic_visit(node)
        if len(node.targets) == 1 and \
                isinstance(node.targets[0], gast.Name):
            self._ns[node.targets[0].id] = node.value

        return node

    def _handle_format_call(self, node):
        value = self._resolve(node.func.value)

        if _is_str_const(value):
            node = Poison(node)

        elif isinstance(value, Poison):
            node.func.value = node.func.value.value
            node = Poison(node)

        return node

    def _handle_execute_call(self, node):
        sql = node.args[0]
        resolved_sql = self._resolve(sql)
        if isinstance(resolved_sql, Poison):
            self.poisoned.append(resolved_sql)

    def visit_Call(self, node):
        node = self.generic_visit(node)

        # Look for <cursor like>.execute(...)
        if _is_execute_call(node):
            self._handle_execute_call(node)

        elif _is_format_call(node):
            node = self._handle_format_call(node)

        return node


def check(source):
    checker = SQLChecker()
    tree = gast.parse(source)
    checker.visit(tree)
    return checker.poisoned
