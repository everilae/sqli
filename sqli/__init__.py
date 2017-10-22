import sys
import ast
import astunparse

_EXECUTE = "execute"
_FORMAT = "format"


def _cure(node):
    if isinstance(node, Poison):
        node = node.expr

    for name, value in ast.iter_fields(node):
        if isinstance(value, ast.AST):
            setattr(node, name, _cure(value))

    return node


class Poison(ast.AST):
    """
    A simple marker node.
    
    :param node: Original poisoned node
    """
    _fields = ['expr']

    def __init__(self, node):
        # Unparser is unhappy about custom "AST nodes"
        self.expr = _cure(node)

    def __repr__(self):
        return "<Poison expr={!r}>".format(self.get_source())

    def get_lineno(self):
        return self.expr.lineno

    def get_source(self):
        return astunparse.unparse(self.expr)


class Injector(ast.NodeTransformer):

    def visit_BinOp(self, node):
        node = super().generic_visit(node)
        if isinstance(node.op, ast.Add):
            args = (node.left, node.right)
            if not all(isinstance(a, ast.Str) for a in args):
                node = Poison(node)

            else:
                new_node = ast.Str(s=node.left.s + node.right.s)
                ast.copy_location(new_node, node)
                node = new_node

        elif isinstance(node.op, ast.Mod):
            # Treat all % operations as poisonous
            node = Poison(node)

        return node

    def visit_Call(self, node):
        node = super().generic_visit(node)
        if isinstance(node.func, ast.Attribute) and \
                node.func.attr == _FORMAT:
            node = Poison(node)

        return node


class SQLChecker(ast.NodeVisitor):

    def __init__(self):
        # A flat namespace, no support for proper scopes yet
        self._ns = {}
        self.poisoned = []

    def _resolve(self, node):
        value = node
        if isinstance(node, ast.Name):
            value = self._ns.get(node.id, node)

        return value

    def visit_Assign(self, node):
        self.generic_visit(node)
        if len(node.targets) == 1 and \
                isinstance(node.targets[0], ast.Name):
            self._ns[node.targets[0].id] = node.value

    def visit_Call(self, node):
        self.generic_visit(node)
        # Look for <cursor like>.execute(...)
        if isinstance(node.func, ast.Attribute) and \
                node.func.attr == _EXECUTE:
            sql, *rest = node.args
            resolved_sql = self._resolve(sql)
            if isinstance(resolved_sql, Poison):
                self.poisoned.append(resolved_sql)


def check(source):
    injector = Injector()
    checker = SQLChecker()
    tree = ast.parse(source)
    new_tree = injector.visit(tree)
    checker.visit(new_tree)
    return checker.poisoned

