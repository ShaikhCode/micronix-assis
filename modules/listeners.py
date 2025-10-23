# modules/listener.py
import speech_recognition as sr

def listen_command(timeout=6, phrase_time_limit=6):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.4)
        try:
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = r.recognize_google(audio).lower()
            return text
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            return ""
