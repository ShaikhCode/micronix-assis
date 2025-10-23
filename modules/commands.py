import os
import webbrowser
import datetime
import json
import pyttsx3

# Initialize TTS engine
engine = pyttsx3.init()

def speak(text):
    print(f"Assistant: {text}")
    engine.say(text)
    engine.runAndWait()

# Load custom commands
with open("data/commands.json", "r") as f:
    CUSTOM_COMMANDS = json.load(f)

def execute_command(command):
    command = command.lower()

    # 🔹 1. Check JSON Custom Commands first
    for key, action in CUSTOM_COMMANDS.items():
        if key in command:
            speak(f"Executing {key}")
            try:
                if action.startswith("http"):
                    webbrowser.open(action)
                elif action.endswith(".exe"):
                    os.system(f"start {action}")
                else:
                    os.startfile(action)
            except Exception as e:
                speak(f"Sorry, I couldn’t execute {key}: {e}")
            return f"Custom command executed: {key}"

    # 🔹 2. Built-in Commands (Fallback)
    if "time" in command:
        now = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The current time is {now}.")
        return f"The current time is {now}."

    elif "date" in command:
        today = datetime.date.today().strftime("%B %d, %Y")
        speak(f"Today’s date is {today}.")
        return f"Today’s date is {today}."

    elif "how are you" in command:
        speak("I’m doing great, ready to assist you!")
        return "I’m doing great, ready to assist you!"

    elif "open youtube" in command:
        webbrowser.open("https://www.youtube.com")
        speak("Opening YouTube.")
        return "Opening YouTube."

    elif "open google" in command:
        webbrowser.open("https://www.google.com")
        speak("Opening Google.")
        return "Opening Google."

    elif "notepad" in command:
        os.system("notepad")
        speak("Opening Notepad.")
        return "Opening Notepad."

    elif "exit" in command or "bye" in command:
        speak("Goodbye! Have a nice day.")
        exit()

    # 🔹 3. If no match found
    speak("Sorry, I didn’t understand that command.")
    return "Unknown command."
