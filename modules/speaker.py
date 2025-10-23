import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)
engine.setProperty('rate', 175)

def speak(text):
    engine.say(text)
    engine.runAndWait()

speak("Hello,how Mycronix can assist you today?")