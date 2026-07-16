import os
from agent import ask_llm_to_fix
from sandbox import SandboxManager
from validator import validate_code_structure

def run_advanced_autonomous_loop():
    user_prompt = "Add an input class validation type check to ensure inputs 'a' and 'b' are either integer or float. If not, raise a TypeError."
    
    current_code = """
def divide(a, b):
    if b == 0:
        return 0
    return a / b

def test_divide_types():
    try:
        divide("10", 2)
        assert False, "Should have raised TypeError"
    except TypeError:
        assert True
"""

    sandbox = SandboxManager()
    max_retries = 3
    error_context = None

    print("🚀 Starting Advanced Guardrail-Protected Agent Engine...")

    for iteration in range(1, max_retries + 1):
        print(f"\n--- 🤖 Engine Iteration {iteration} ---")
        
        # 1. Ask LLM for patch
        raw_ai_code = ask_llm_to_fix(user_prompt, current_code, error_context)
        
        # 2. STEP UPGRADE: Pre-flight AST Validation Guardrail
        print("Executing AST Static Code Graph Validation...")
        is_valid, message = validate_code_structure(raw_ai_code)
        
        if not is_valid:
            print(f"🛑 Static Check Failed: {message}. Skipping Sandbox infrastructure.")
            # LLM text model ko direct input loop me loopback trace pass karega execution bacha ke
            error_context = f"Static Analysis Error: {message}. Fix the indentation or syntax explicitly."
            continue
            
        print(f"🛡️ Guardrail Passed: {message}")
        
        # 3. Execution inside Isolated Environment Sandbox
        print("Deploying safe container instances for testing execution logs...")
        result = sandbox.execute_code(raw_ai_code, test_command="pytest app.py")
        
        print(f"Sandbox Output Trace:\n{result['logs']}")
        
        if result["exit_code"] == 0:
            print("\n✅ TARGET MET: All structural code implementations and test instances are stable!")
            print("Final Validated System Production Code:")
            print(raw_ai_code)
            return
        else:
            print("❌ Test cases asserted failure conditions.")
            error_context = result["logs"]

    print("\n⚠️ Failed to optimize source framework within max computation boundaries.")

if __name__ == "__main__":
    run_advanced_autonomous_loop()