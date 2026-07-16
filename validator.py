import ast

def validate_code_structure(code_content: str) -> tuple[bool, str]:
    """
    Statically analyzes code using Python AST to check for basic syntax validity 
    without executing it.
    """
    try:
        # Code code syntax tree format me parse karne ki koshish karega
        parsed_ast = ast.parse(code_content)
        
        # Security/Structure Check: AI ne functions change kiya hai ya nahi hum iterate kar sakte hain
        functions_defined = [node.name for node in ast.walk(parsed_ast) if isinstance(node, ast.FunctionDef)]
        
        return True, f"Syntax Valid. Functions detected: {functions_defined}"
    except SyntaxError as e:
        # Agar compile time pe hi syntax error hai, runtime sandbox ki zaroorat nahi hai
        return False, f"SyntaxError on line {e.lineno}: {e.msg}"