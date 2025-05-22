import ast
import operator

# Supported operators
ops = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
}

def eval_expr(expr: str) -> float:
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        elif isinstance(node, ast.BinOp):
            return ops[type(node.op)](_eval(node.left), _eval(node.right))
        elif isinstance(node, ast.UnaryOp):
            return ops[type(node.op)](_eval(node.operand))
        elif isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        else:
            raise TypeError(f"Unsupported type: {type(node)}")

    node = ast.parse(expr, mode='eval')
    return _eval(node.body)
