import time
import pandas as pd
import openai
import sys
sys.path.append(".")
from src import configs


def generate_gpt_response(msg):
    """
    Generate a response using the OpenAI GPT-4 Turbo model based on a given prompt.

    Parameters:
    - msg (str): A message in the format "gpt <max_words>: <prompt>", where <max_words> is the maximum number
                of words for the response and <prompt> is the user's input prompt.

    Returns:
    - str: The generated response from the OpenAI GPT-4 Turbo model.

    Note:
    - The OpenAI API key must be set in the 'configs.OPEN_AI_KEY' variable before calling this function.
    - For more information on the OpenAI API:
    https://platform.openai.com/docs/api-reference/completions/create
    """

    # Extracting max_words and prompt from the message. e.g. "gpt 40: What is the trade wind?"
    try:
        _, params = msg.split(" ", 1)  # split at the first space to separate "gpt" and the rest
        max_words_str, prompt = params.split(":", 1)  # split at ":" to separate max_words and prompt
        max_words = int(max_words_str)
        print(max_words, prompt)
    except ValueError:
        print("Invalid message format. Please use 'gpt <max_words>: <prompt>'")
        return

    openai.api_key = configs.OPEN_AI_KEY

    response = openai.Completion.create(
        engine='gpt-4-1106-preview',  # GPT-4 Turbo model
        prompt=f'Answer this question in maximum {max_words} words: \nUser: {prompt}. Use only base64 characters',
        n=1,
        stop=None
    )
    print(response.choices[0].text.strip())
    return response.choices[0].text.strip()
