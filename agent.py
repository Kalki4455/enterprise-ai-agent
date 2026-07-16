from openai import OpenAI
from sandbox import SandboxManager

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "your-key-here"))
sandbox = SandboxManager()

def ask_llm_to_fix(prompt: str, current_code: str, error_logs: str = None) -> str:
    """
    LLM ko code generate ya correct karne ke liye input context dena.
    """
    system_instruction = (
        "You are an expert autonomous software engineer. "
        "Return ONLY the raw source code inside valid python code blocks. Do not explain anything."
    )
    
    user_content = f"User Request: {prompt}\n\nCurrent Code State:\n{current_code}"
    if error_logs:
        user_content += f"\n\n[CRITICAL ERROR/TEST FAILURE LOGS]:\n{error_logs}\n\nPlease fix the bug causing this error."

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content}
        ],
        temperature=0.2 # Lower temperature strictly keeps it analytical
    )
    
    # Extracting pure code from markdown blocks
    raw_output = response.choices[0].message.content
    clean_code = raw_output.replace("```python", "").replace("```", "").strip()
    return clean_code