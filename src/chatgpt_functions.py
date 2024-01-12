import sys
sys.path.append(".")
from src import configs
import base64
import json
from openai import OpenAI

client = OpenAI(api_key=configs.OPEN_AI_KEY)



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

    response = client.chat.completions.create(
        model = "gpt-4-1106-preview",
        stop = None,
        n=1,
        messages = [
            {"role": "user", "content": f"Answer this question in maximum {max_words} words: \nUser: {prompt}."}
        ])

    print("answer:", response.choices[0].message.content)
    
    return response.choices[0].message.content
