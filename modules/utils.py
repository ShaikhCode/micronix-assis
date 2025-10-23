import random

def random_greeting():
    greetings = [
        "Hello, how can I assist you today?",
        "At your service!",
        "Ready when you are.",
        "Hey there! What’s the plan?"
    ]
    return random.choice(greetings)
def random_emotion():
    return random.choice(["happy", "calm", "thinking", "focused"])

