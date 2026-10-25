import os
import streamlit as st


def analyze_code_error(code_str: str, error_msg: str) -> str:
  """Uses Gemini to explain execution errors with multi-model fallback."""
  api_key = st.secrets.get("GEMINI_API_KEY", "") or os.environ.get(
      "GEMINI_API_KEY", ""
  )

  if not api_key:
    return (
        "⚠️ AI Debugger is in offline mode. Please configure your"
        " GEMINI_API_KEY in Streamlit secrets."
    )

  from google import genai

  client = genai.Client(api_key=api_key)

  prompt = f"""
    You are DevHive AI Assistant. A developer executed the following code and encountered an error.

    ### Code Snippet:
    ```python
    {code_str}
    ```

    ### Error Output:
    ```text
    {error_msg}
    ```

    ### Directives:
    1. Provide a short, 2-sentence explanation of why the error occurred.
    2. Provide the corrected code block.
    3. Keep explanation brief and structured.
    """

  # Try a list of stable model IDs in order until one responds successfully
  models_to_try = [
      "gemini-2.5-flash",
      "gemini-3.1-flash-lite",
      "gemini-3.8-flash",
  ]

  for model_name in models_to_try:
    try:
      response = client.models.generate_content(
          model=model_name,
          contents=prompt,
      )
      if response and response.text:
        return response.text
    except Exception:
      continue  # Try the next model if this one is experiencing high traffic

  return (
      "⚠️ Google AI servers are currently experiencing high traffic (503"
      " congestion). Please wait 10 seconds and click the button again."
  )