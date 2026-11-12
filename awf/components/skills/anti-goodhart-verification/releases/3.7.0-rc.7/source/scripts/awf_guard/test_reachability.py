"""Conservative lexical reachability for assertions; not a general execution proof."""
import ast


def literal_truth(expression):
    try:
        return bool(ast.literal_eval(expression))
    except (ValueError, TypeError, SyntaxError):
        return None


def reachable_test_nodes(function):
    nodes = []

    def block(statements):
        for statement in statements:
            nodes.append(statement)
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(statement, ast.If):
                nodes.extend(ast.walk(statement.test))
                truth = literal_truth(statement.test)
                left = block(statement.body) if truth is not False else False
                right = block(statement.orelse) if truth is not True else False
                if left and truth is True or right and truth is False or left and right:
                    return True
            elif isinstance(statement, ast.While):
                nodes.extend(ast.walk(statement.test))
                if literal_truth(statement.test) is not False:
                    block(statement.body)
                block(statement.orelse)
            elif isinstance(statement, (ast.For, ast.AsyncFor)):
                nodes.extend(ast.walk(statement.iter))
                block(statement.body)
                block(statement.orelse)
            elif isinstance(statement, (ast.With, ast.AsyncWith)):
                for item in statement.items:
                    nodes.extend(ast.walk(item.context_expr))
                if block(statement.body):
                    return True
            elif isinstance(statement, ast.Try):
                ended = block(statement.body)
                handler_ends = [block(handler.body) for handler in statement.handlers]
                block(statement.orelse)
                final_ends = block(statement.finalbody)
                if final_ends or ended and all(handler_ends):
                    return True
            else:
                for child in ast.iter_child_nodes(statement):
                    if not isinstance(child, ast.Lambda):
                        nodes.extend(ast.walk(child))
                if isinstance(statement, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                    return True
        return False

    block(function.body)
    return nodes


def locally_shadowed_assertions(tree, accepted_names):
    shadowed = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name in accepted_names:
            shadowed.add(node.name)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store) and node.id in accepted_names:
            shadowed.add(node.id)
        elif isinstance(node, ast.arg) and node.arg in accepted_names:
            shadowed.add(node.arg)
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Store) and node.attr in accepted_names:
            shadowed.add(node.attr)
    return shadowed


def local_assertion_helpers(tree):
    helpers = set()
    for function in tree.body:
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in reachable_test_nodes(function):
            if isinstance(node, ast.Assert):
                helpers.add(function.name)
            elif isinstance(node, ast.Raise) and node.exc is not None:
                name = getattr(node.exc, 'id', None) or getattr(getattr(node.exc, 'func', None), 'id', None)
                if name == 'AssertionError':
                    helpers.add(function.name)
    return helpers
