import astunparse
import gast
import logging
import sys

from collections import ChainMap

_ATTR_CALL = {"execute", "read_sql", "read_sql_query", "raw", "text"}
_NAME_CALL = {"text"}
_FORMAT = {"format", "format_map"}
_SAFE_FUNCS = {"len", "int"}

_log = logging.getLogger(__name__)


class _Cure(gast.NodeTransformer):

    def visit_Poison(self, node):
        node = self.generic_visit(node)
        return node.value

_cure = _Cure()


def _is_str_const(node):
    return isinstance(node, gast.Constant) and \
        isinstance(node.value, str)


def _is_attr_call(node):
    return isinstance(node.func, gast.Attribute) and \
        node.func.attr in _ATTR_CALL and \
        len(node.args) >= 1


def _is_name_call(node):
    return isinstance(node.func, gast.Name) and node.func.id in _NAME_CALL


def _is_format_call(node):
    return isinstance(node.func, gast.Attribute) and \
        node.func.attr in _FORMAT


def _is_safe_format(node):
    return all(_is_safe_format_arg(a) for a in node.args + node.keywords)


class FormatArgumentVisitor(gast.NodeVisitor):

    def generic_visit(self, node):
        return all(self.visit(child) for child in gast.iter_child_nodes(node))

    def visit_Name(self, node):
        return False

    def visit_Call(self, node):
        if isinstance(node.func, gast.Name) and node.func.id in _SAFE_FUNCS:
            return True

        return self.generic_visit(node)

_is_safe_format_arg = FormatArgumentVisitor().visit


class Poison(gast.AST):
    """
    A simple marker node.

    :param node: Original poisoned node
    """
    _fields = ["value"]

    def __init__(self, node):
        self.value = node

    def __repr__(self):
        return "<Poison value={}>".format(gast.dump(self.value))

    def get_lineno(self):
        return self.value.lineno

    def get_source(self):
        node = _cure.visit(self.value)
        try:
            return astunparse.unparse(gast.gast_to_ast(node))

        except Exception as e:
            _log.debug("unparsing failed: %s\nAST: %s", e, gast.dump(self.value))
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

    def _handle_add(self, node):
        if not _is_str_const(node.left) or not _is_str_const(node.right):
            node = Poison(node)

        return node

    def visit_BinOp(self, node):
        node = self.generic_visit(node)
        if isinstance(node.op, gast.Add):
            node = self._handle_add(node)

        elif isinstance(node.op, gast.Mod) and \
                not _is_safe_format_arg(node.right):
            node = Poison(node)

        return node

    def visit_JoinedStr(self, node):
        node = self.generic_visit(node)
        if any(not _is_str_const(v) and
               not _is_safe_format_arg(self._resolve(v.value))
               for v in node.values):
            node = Poison(node)

        return node

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

    def visit_AugAssign(self, node):
        node = self.generic_visit(node)
        if isinstance(node.target, gast.Name) and \
                isinstance(node.op, gast.Add):
            value = self._resolve(node.target)
            if not _is_str_const(value) or not _is_str_const(node.value):
                node = Poison(node)

        return node

    def _handle_format_call(self, node):
        func = self._resolve(node.func.value)

        if _is_str_const(func) and not _is_safe_format(node):
            node = Poison(node)

        elif isinstance(func, Poison):
            node = Poison(node)

        return node

    def _handle_sql_call(self, node):
        sql = node.args[0]
        resolved_sql = self._resolve(sql)
        if isinstance(resolved_sql, Poison):
            self.poisoned.append(resolved_sql)

    def visit_Call(self, node):
        node = self.generic_visit(node)

        if _is_attr_call(node) or _is_name_call(node):
            self._handle_sql_call(node)

        elif _is_format_call(node):
            node = self._handle_format_call(node)

        return node


def check(source):
    try:
        tree = gast.parse(source)

    except Exception as e:
        _log.debug("parsing failed: %s\n%s", e, source)
        raise

    checker = SQLChecker()
    checker.visit(tree)
    return checker.poisoned
