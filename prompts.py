PROMPTS = [
    "a skydiving chicken", "a shark eating a cupcake",
    "2 combined holidays", "a cowboy riding a polar bear",
    "a pirate playing soccer", "a rollerblading pineapple",
    "a cowboy with a wooden horse"
]

from random import choice

def get_prompt():
    return choice(PROMPTS)
