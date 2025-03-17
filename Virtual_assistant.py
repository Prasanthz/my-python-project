import os
import sys
import cv2
import time
import alarm
import socket
import random
import psutil
import smtplib
import pyttsx3
import requests
import threading
import speedtest
import wikipedia
import pyautogui
import pywhatkit
import webbrowser
from PyQt5 import QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from Front_page import Ui_Dialog
from PyQt5.QtWidgets import *
from twilio.rest import Client
import speech_recognition as sr
import face_recognition_function
from googletrans import Translator
from PyQt5.QtCore import pyqtSignal
from system_control import SystemControl
from datetime import datetime, timedelta
from PyQt5.QtCore import QTimer, QTime, QDate
from database import connect_to_database, initialize_database

# Initialize the text-to-speech engine
engine = pyttsx3.init('sapi5')
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id)

# Establish a connection to the MySQL database
connection = connect_to_database()
cursor = initialize_database(connection)


def speak(text):
    engine.say(text)
    engine.runAndWait()

class SpeechRecognition:
    def __init__(self, terminalprint_callback):
        self.terminalprint = terminalprint_callback

    def recognize(self):
        r = sr.Recognizer()
        with sr.Microphone() as source:
            self.terminalprint("Listening...")
            r.pause_threshold = 1
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, phrase_time_limit=3)

        try:
            self.terminalprint("Recognizing...")
            query = r.recognize_google(audio, language='en-in')
            self.terminalprint(f"User said: {query}\n")
            return query
        except Exception as e:
            return ""

class WeatherService:
    def __init__(self, terminalprint_callback):
        self.terminalprint = terminalprint_callback

    def get_weather(self, city):
        api_key = "018da447cd5b45a397183656251402"
        base_url = f"https://api.weatherapi.com/v1/current.json?key={api_key}&q={city}"
        response = requests.get(base_url)
        data = response.json()
        if "error" not in data:
            current = data["current"]
            temperature = current["temp_c"]
            humidity = current["humidity"]
            description = current["condition"]["text"]
            weather_report = f"Temperature: {temperature}°C\nHumidity: {humidity}%\nDescription: {description}"
            self.terminalprint(weather_report)
            return weather_report
        else:
            self.terminalprint("City Not Found")
            return "City Not Found"


class NewsService:
    def __init__(self, terminalprint_callback):
        self.terminalprint = terminalprint_callback

    def get_headlines(self):
        url = "https://api.worldnewsapi.com/top-news?source-country=in&language=en&date=2025-03-17"
        api_key = "249c966855a9413a8f41a4d58b76f216"

        headers = {
            'x-api-key': api_key
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if 'top_news' in data and isinstance(data['top_news'], list):
                news_articals = data['top_news'][0].get('news',[])
                headlines=[f"🔹 {article.get('title', 'No Title')}\n{article.get('summary', 'No Summary')}"
                for article in news_articals]
                return headlines[:1]
            else:
                return ["No news articles found."]
        else:
            return [f"Error fetching news:{response.status_code}"]
        
class MainThread(QThread):
    stopSignal = pyqtSignal()
    def __init__(self, ui, terminalprint_callback):
        super(MainThread, self).__init__()
        self.ui = ui
        self.terminalprint = terminalprint_callback
        self.failed_attempts = 0
        self.print_buffer = []
        self.speech_recognition = SpeechRecognition(terminalprint_callback)
        self.weather_service = WeatherService(terminalprint_callback)
        self.news_service = NewsService(terminalprint_callback)
        self.system_control = SystemControl(terminalprint_callback)

    def run(self):
        try:
            self.TaskExecution()
        finally:
            self.stopSignal.emit()

    # text to speech
    def speak(self, *messages):
        for msg in messages:
            self.terminalprint(msg)
            engine.say(msg)
            engine.runAndWait()


    def get_ip_address(self):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        return ip_address

    def commands(self):
        query = self.speech_recognition.recognize()
        if query:
            cursor.execute("INSERT INTO command_history (command) VALUES (%s)", (query,))
            connection.commit()
        return query

    def show_command_history(self, date=None):
        if date:
            cursor.execute("SELECT command, timestamp FROM command_history WHERE DATE(timestamp) = %s ORDER BY timestamp ASC", (date,))
        else:
            cursor.execute("SELECT command, timestamp FROM command_history ORDER BY timestamp ASC")

        history = cursor.fetchall()

        if history:
            history_report = "\n".join([f"{timestamp}: {command}" for command, timestamp in history])
            self.terminalprint(history_report)
        else:
            self.speak(f"No command history found for {date if date else 'all records'}.")
            self.terminalprint(f"No command history found for {date if date else 'all records'}.")


    def set_alarm(self):
        self.speak("At what time should I set the alarm?")
        alarm_time_str = self.commands()
        alarm_time = alarm.parse_time(alarm_time_str)

        if alarm_time:
            self.speak(f"Alarm set for {alarm_time}")
            self.terminalprint(f"Alarm set for {alarm_time}")

            # Corrected threading calls
            alarm_thread = threading.Thread(target=alarm.set_alarm, args=(alarm_time, self.terminalprint))
            alarm_thread.start()

            listener_thread = threading.Thread(target=alarm.alarm_listener, args=(self.terminalprint,))
            listener_thread.start()

        else:
            self.speak("I couldn't detect a valid time. Try again.")
            self.terminalprint("Invalid time detected.")

    def wakeUpCommands(self):
        self.speak("Jarvis is sleeping...")
        return self.commands().lower()

    # To wish
    def wishMe(self):
        hour = int(datetime.now().hour)
        if hour >= 0 and hour < 12:
            self.speak("Good Morning!")
        elif hour >= 12 and hour < 18:
            self.speak("Good Afternoon!")
        else:
            self.speak("Good Evening!")

    def get_weather(self, city):
        weather_report = self.weather_service.get_weather(city)
        self.speak(weather_report)

    def gtranslator(self, gquery):
        translator = Translator()
        gquery = gquery.replace("Jarvis", "").replace("translation", "").replace("translate", "").strip()
        try:
            texttotranslate = translator.translate(gquery, src='auto', dest='ta')
            result = texttotranslate.text
            self.terminalprint(f"Translated Text: {result}")

        except Exception as e:
            error_message = f"Error occurred while translating: {str(e)}"
            self.terminalprint(error_message)
            self.speak("An error occurred while translating.")

    def load_authorized_users(self,filename="authorized_users.txt"):
        if os.path.exists(filename):
            with open(filename, "r") as file:
                return [line.strip().lower() for line in file.readlines()]
        return []

    def faceunlock(self):
        global name
        sfr = face_recognition_function.simplefacerec()

        if not os.path.exists("face_encodings.npy") or not os.path.exists("authorized_users.txt"):
            self.speak("Encoding faces and generating authorized users list...")
            sfr.load_encoding_images("C:/Users/prasa/OneDrive/Documents/FACEDB")

        else:
            self.speak("Loading stored encodings...")
            sfr.load_stored_encodings()

        self.speak("Face recognition is required.")

        cap = cv2.VideoCapture(0)
        self.speak("Please show your face to the camera.")

        start_time = time.time()
        authorized_users = self.load_authorized_users()
        authorized = False
        found_face = False

        while time.time() - start_time <= 10:
            ret, frame = cap.read()
            if not ret:
                continue

            facelocation, facename = sfr.detect_known_faces(frame)
            name = "Unknown"

            if len(facelocation):
                found_face = True

            for faceloc, detected_name in zip(facelocation, facename):
                y1, x2, y2, x1 = map(int, faceloc)
                if detected_name.lower() == "unknown":
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Red box for unknown
                    cv2.putText(frame, detected_name, (x1, y2 + 20), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2)
                else:
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Green box for known
                    cv2.putText(frame, detected_name, (x1, y2 + 20), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 2)
                    name = detected_name.lower()

            cv2.imshow("CAMERA", frame)
            cv2.waitKey(1)

            if time.time() - start_time > 15 and not len(facelocation):
                self.speak("You cannot access this assistant.")
                break

            if name in authorized_users:
                authorized = True
                break

        cap.release()
        cv2.destroyAllWindows()

        if authorized:
            self.speak(f"Welcome back {name.capitalize()}")
            self.terminalprint(f"Welcome back {name.capitalize()}")
        else:
            self.speak("Unauthorized person detected.")
            self.terminalprint("Unauthorized person detected.")
            self.speak("Shutting down...")

            app = QApplication.instance()
            if app:
                app.quit()
            sys.exit(0)

    def set_reminder(self, reminder_time, message):
        global reminder_time_obj
        reminder_time = reminder_time.strip().lower().replace(".", "")
        self.terminalprint(f"The input: {reminder_time}")

        reminder_time = reminder_time.replace("a m", "AM").replace("p m", "PM")

        time_formats = ['%I:%M %p', '%H:%M']
        parsed = False

        for time_format in time_formats:
            try:
                reminder_time_obj = datetime.strptime(reminder_time, time_format)
                parsed = True
                break
            except ValueError:
                continue

        if not parsed:
            self.speak("Sorry, I couldn't understand the time.")
            return

        now = datetime.now()
        reminder_time_obj = reminder_time_obj.replace(year=now.year, month=now.month, day=now.day)

        if reminder_time_obj < now:
            reminder_time_obj += timedelta(days=1)

        self.speak(f"Reminder set for {reminder_time_obj.strftime('%I:%M %p')}")

        delay = (reminder_time_obj - now).total_seconds()

        def trigger_reminder():
            self.speak(f"Reminder: {message}")
            self.terminalprint(f"Reminder: {message}")

        threading.Timer(delay, trigger_reminder).start()

    def send_email(self, to_email, body):
        if not body.strip():
            self.speak("No message said.")
            self.terminalprint("No message said.")
            return
        
        sender_email = "prasanthpirates001@gmail.com"
        sender_password = "bykk yypn jmvc ycxo"
        message = f"{body}"

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message)
            server.quit()
            self.speak("Email sent successfully!")

        except Exception as e:
            self.speak("Failed to send email.")
            self.terminalprint(e)

    def send_whatsapp_message(self,phone_number, message):
        if not phone_number.startswith("+"):
            phone_number = "+91" + phone_number
        try:
            pywhatkit.sendwhatmsg_instantly(phone_number, message)
            pyautogui.press('enter')
            self.speak("WhatsApp message sent successfully!")
        except Exception as e:
            self.speak("Failed to send WhatsApp message.")
            self.terminalprint(e)

    def send_sms(self,to_number, message):
        if not message:
            self.terminalprint("No message said")
            self.speak("No message said")
            return

        if not to_number.startswith("+"):
            to_number = "+91" + to_number

        account_sid = "AC6e1259a3a9c85c2ead31d45eed6203e6"
        auth_token = "9e80ecc076a73f57c9d7d1edf9591d75"
        twilio_number = "+18454489152"

        try:
            client = Client(account_sid, auth_token)
            client.messages.create(
                body=message,
                from_=twilio_number,
                to=to_number
            )
            self.speak("SMS sent successfully!")
        except Exception as e:
            error_message = f"Twilio Error: {str(e)}"
            self.terminalprint(error_message)
            print(error_message)

    def TaskExecution(self):
                face_unlocked = False
                while True:
                    if not face_unlocked:
                        #self.faceunlock()
                        face_unlocked = True
                    self.query = self.commands().lower()

                    if not self.query.strip():  
                        self.failed_attempts += 1
                        if self.failed_attempts >= 3:
                            self.speak("Three failed attempts. Shutting down...")
                            self.terminalprint("Three failed attempts. Shutting down...")
                            app = QApplication.instance()
                            if app:
                                app.quit()
                            else:
                                os._exit(0)
                    else:
                        self.failed_attempts = 0

                    if "who are you" in self.query or "what is your name" in self.query:
                        jarvis_responses = [
                            "I am Jarvis, your virtual assistant. I can help you with tasks, provide information, and make your life easier.",
                            "I'm Jarvis, designed to assist you with whatever you need. Just let me know!",
                            "I'm Jarvis, your digital companion, always here to support you."
                        ]
                        self.speak(random.choice(jarvis_responses))
                        self.terminalprint("I'm Jarvis, your virtual assistant.")

                    elif "who created you" in self.query or "who made you" in self.query:
                        self.speak("I was created by an intelligent developer with great vision. I'm here to help you every step of the way!")
                        self.terminalprint("I was designed to be your helpful companion.")

                    elif "what can you do" in self.query or "your abilities" in self.query:
                        self.speak(
                            "I can send emails, play music, provide weather updates, search Wikipedia, control your system, and much more! Just ask."
                        )
                        self.terminalprint("I can assist with various tasks like sending emails, controlling your system, and fetching information.")

                    elif "introduce yourself" in self.query or "yourself" in self.query:
                        self.speak(
                            "I am Jarvis, your personal assistant. Created to simplify your tasks, answer your questions, and make your day more productive. Feel free to ask me anything!"
                        )
                        self.terminalprint("I am Jarvis, your intelligent assistant designed to make life easier.")
                    
                    elif "how are you" in self.query:
                        jarvis_responses = [
                            "I'm feeling fantastic, sir! What about you?",
                            "I'm here, running at full power! How are you?",
                            "Feeling sharp as ever! Ready to assist you, sir., What's up?",
                            "I'm feeling unstoppable! How's your day going?",
                            "I'm fully operational and ready to help! What about you?"
                        ]

                        self.speak(random.choice(jarvis_responses))
                        self.terminalprint("Jarvis: I'm feeling great! 😊")

                        wishQuery = self.commands().lower()

                        if "i am also" in wishQuery or "fine" in wishQuery:
                            happy_responses = [
                                "That's awesome, sir!",
                                "Glad to hear that! 😊",
                                "Fantastic! Let's keep that positive energy going!"
                            ]
                            self.speak(random.choice(happy_responses))
                        
                        elif "not good" in wishQuery or "bad" in wishQuery or "sad" in wishQuery:
                            comfort_responses = [
                                "I'm sorry to hear that. If you need anything, I'm here for you.",
                                "Tough times don't last, sir. You've got this!",
                                "Don't worry, things will get better. I'm always here to help!"
                            ]
                            self.speak(random.choice(comfort_responses))
                        
                        else:
                            self.speak("I hope you are doing well!")

                    elif "time" in self.query:
                        strTime = datetime.now().strftime("%H:%M:%S")
                        self.terminalprint(strTime)
                        self.speak(f"Sir, the time is {strTime}")

                    elif "date" in self.query:
                        strDate = datetime.now().strftime("%Y-%m-%d")
                        self.terminalprint(strDate)
                        self.speak(f"Sir, today's date is {strDate}")

                    elif "show history" in self.query or "history" in self.query:
                        self.speak("Do you want the complete history or for a specific date?")
                        user_response = self.commands().lower()

                        if "all" in user_response or "complete" in user_response:
                            self.show_command_history()
                        elif "date" in user_response or "specific" in user_response:
                            self.speak("Please specify the date.")
                            date_query = self.commands().strip()

                            try:
                                date_obj = datetime.strptime(date_query, "%Y-%m-%d").date()
                            except ValueError:
                                try:
                                    date_obj = datetime.strptime(date_query, "%B %d").date()
                                    date_obj = date_obj.replace(year=datetime.now().year)  # Add current year
                                except ValueError:
                                    self.speak("Invalid date format. Please try again.")
                                    self.terminalprint("Invalid date format. Example: 2025-03-01 or June 01")
                                    break
                            self.show_command_history(str(date_obj))
                        else:
                            self.speak("I couldn't understand your response. Please try again.")

                    elif "system status" in self.query or "performance" in self.query:
                        cpu_usage = psutil.cpu_percent(interval=1)
                        memory = psutil.virtual_memory().percent
                        battery = psutil.sensors_battery()
                        battery_percent = battery.percent if battery else "Unknown"

                        status_message = f"CPU usage: {cpu_usage}%\nMemory usage: {memory}%\nBattery level: {battery_percent}%"
                        self.speak(status_message)
                        self.terminalprint(status_message)

                    elif "translate" in self.query or "translation" in self.query:
                        self.speak("Please provide the text to translate.")
                        text_to_translate = self.commands()
                        self.gtranslator(text_to_translate)

                    elif "internet speed" in self.query or "speed test" in self.query:
                        self.speak("Checking internet speed. Please wait...")

                        st = speedtest.Speedtest()
                        download_speed = round(st.download() / 1_000_000, 2)  # Convert to Mbps
                        upload_speed = round(st.upload() / 1_000_000, 2)      # Convert to Mbps
                        ping = st.results.ping

                        speed_message = f"Download speed: {download_speed} Mbps\nUpload speed: {upload_speed} Mbps\nPing: {ping} ms"
                        
                        self.speak(speed_message)
                        self.terminalprint(speed_message)

                    elif "open notepad" in self.query or "notepad" in self.query:
                        self.speak("Opening Notepad...")
                        os.system("C:/Windows/System32/notepad.exe")
                        time.sleep(2)
                        while True:
                            notepadquery = self.commands().lower()
                            if "copy" in notepadquery:
                                pyautogui.hotkey('ctrl', 'A')
                                pyautogui.hotkey('ctrl', 'c')
                                self.speak("Done sir!")

                            elif "paste" in notepadquery:
                                pyautogui.hotkey('ctrl', 'v')
                                self.speak("Done sir!")

                            elif "save this file" in notepadquery:
                                pyautogui.hotkey('ctrl', 's')
                                self.speak("Sir,Please specify a name for this file")
                                notepadsavingquery = self.commands()
                                pyautogui.write(notepadsavingquery)
                                pyautogui.press('enter')

                            elif "type" in notepadquery:
                                self.speak("Please tell me what should i write")
                                while True:
                                    writeNotepad = self.commands()
                                    if writeNotepad == 'exit typing':
                                        self.speak("Done sir")
                                        break
                                    else:
                                        pyautogui.write(writeNotepad)

                            elif "exit notepad" in notepadquery or "close notepad" in notepadquery:
                                self.speak("Quiting notepad sir...")
                                pyautogui.hotkey('ctrl', 'w')
                                break

                    elif "weather" in self.query:
                        self.speak("Please tell me the city name")
                        city = self.commands().lower()
                        self.get_weather(city)

                    elif "send email" in self.query:
                        self.speak("Please provide the recipient's email address.")
                        to_email = input("Enter recipient's email: ").strip().lower()
                        self.speak("What should be the message?")
                        body = self.commands().lower()
                        self.send_email(to_email, body)

                    elif "whatsapp" in self.query:
                        self.speak("Please provide the recipient's phone number with country code.")
                        phone_number = input("Enter phone number: ").strip().lower()
                        self.speak("What message should I send?")
                        message = self.commands().lower()
                        self.send_whatsapp_message(phone_number, message)

                    elif "send message" in self.query or "send sms" in self.query:
                        self.speak("Please provide the recipient's phone number.")
                        to_number = input("Enter phone number: ").strip().lower()
                        self.speak("What message should I send?")
                        message = self.commands().lower()
                        self.send_sms(to_number, message)

                    elif "reminder" in self.query:
                        self.speak("Please tell me the time for the reminder")
                        reminder_time = self.commands().lower()
                        self.speak("What should I remind you about?")
                        message = self.commands().lower()
                        self.set_reminder(reminder_time, message)

                    elif "open command prompt" in self.query or "command prompt" in self.query:
                            os.system("start cmd")
                            while True:
                                cmquery=self.commands().lower()
                                if "copy" in cmquery:
                                    pyautogui.hotkey('ctrl', 'A')
                                    pyautogui.hotkey('ctrl', 'c')
                                    self.speak("Done sir!")

                                elif "paste" in cmquery:
                                    pyautogui.hotkey('ctrl', 'v')
                                    self.speak("Done sir!")

                                elif "type" in cmquery:
                                    self.speak("Please tell me what should i write")
                                    while True:
                                        writecm= self.commands()
                                        if writecm=="exit typing":
                                            self.speak("Done sir")
                                            break
                                        else:
                                            pyautogui.write(writecm)

                                elif "enter" in cmquery or "okay" in cmquery:
                                    pyautogui.press('enter')

                                elif "exit command prompt" in cmquery or "close command prompt" in cmquery or "close" in cmquery:
                                    self.speak("quiting command prompt sir...")
                                    pyautogui.hotkey('alt','f4')
                                    break

                    elif "play music" in self.query or "music" in self.query:
                        music_dir="C:/Users/prasa/Music"
                        songs =os.listdir(music_dir)
                        os.startfile(os.path.join(music_dir,songs[0]))
                        self.terminalprint(f"Playing:{songs[0]}")

                    elif "stop"in self.query or "break" in self.query:
                        pyautogui.press('space')
                        self.speak("Done sir!")
                        self.terminalprint("Done sir!")

                    elif "ip address" in self.query:
                        ip=self.get_ip_address()
                        self.speak(f"Your IP address is {ip}")
                        self.terminalprint(f"Your IP address is {ip}")

                    elif "wikipedia" in self.query:
                        self.speak("Searching Wikipedia...")
                        try:
                            self.query=self.query .replace("wikipedia","")
                            results=wikipedia.summary(self.query,sentences=2)
                            self.speak("According to Wikipedia")
                            self.speak(results)
                            self.terminalprint(results)
                        except wikipedia.exceptions.PageError as e:
                            self.speak("No results found..")
                            self.terminalprint("No result found.")

                    elif "open youtube" in self.query or "youtube" in self.query:
                        webbrowser.open("www.youtube.com")

                    elif "open instagram" in self.query or "instagram" in self.query:
                        webbrowser.open("www.instagram.com")

                    elif "open google" in self.query or "google" in self.query:
                        self.speak("opening google chrome sir")
                        os.startfile("C:/Program Files/Google/Chrome/Application/chrome.exe")
                        while True:
                            chromequery=self.commands().lower()
                            if "find" in chromequery:
                                chromequery=chromequery.replace("find","")
                                pyautogui.write(chromequery)
                                pyautogui.press('enter')
                                self.speak("Searching...")

                            elif "history" in chromequery:
                                pyautogui.hotkey('ctrl','h')
                                self.speak("Showing history sir...")

                            elif "quit chrome" in chromequery or "close" in chromequery:
                                pyautogui.hotkey('ctrl','w')
                                self.speak("Closing Google chrome sir...")
                                break

                    elif "play" in self.query:
                        webbrowser.open(f"https://www.youtube.com/results?search_query={self.query}")

                    elif "sleep"  in self.query or "shut up" in self.query:
                        self.terminalprint("I'm muting sir!")
                        self.speak("I'm muting sir!")
                        while True:
                            wake_command = self.wakeUpCommands()
                            if "wake up" in wake_command or "jarvis" in wake_command:
                                self.speak("I'm back, sir!")
                                break

                    elif "open camera" in self.query or "camera" in self.query:
                        self.speak("Opening camera sir")
                        os.startfile("microsoft.windows.camera:")
                        self.terminalprint("Opening camera sir")
                        time.sleep(2)
                        while True:
                            cameraquery=self.commands().lower()
                            if "take" in cameraquery or "photo" in cameraquery:
                                pyautogui.press('space')
                                self.speak("Clicking the picture sir")
                            elif "close camera" in cameraquery or "exit camera" in cameraquery:
                                self.speak("Closing camera sir")
                                pyautogui.hotkey('alt','f4')
                                break   

                    elif "minimize" in self.query or "minimise" in self.query:
                        self.speak('Minimizing sir')
                        pyautogui.hotkey('win','down','down')

                    elif "maximize" in self.query or "maximise" in self.query:
                        self.speak("Maximizing sir")
                        pyautogui.hotkey('win','up','up')

                    elif "close window" in self.query or "close the application" in self.query:
                        self.speak("Closing sir")
                        pyautogui.hotkey('ctrl','w')

                    elif "screenshot" in self.query:
                        self.speak("Taking a screenshot of the full screen")
                        screenshot = pyautogui.screenshot()
                        screenshot.save("screenshot.png")

                    elif "no thanks" in self.query or "thanks" in self.query:
                        self.speak("Thank you for using Jarvis,have a good day")
                        self.stopSignal.emit()
                        return

                    elif "increase volume" in self.query:
                        self.system_control.increase_volume()
                        self.speak("Volume increased.")

                    elif "decrease volume" in self.query:
                        self.system_control.decrease_volume()
                        self.speak("Volume decreased.")

                    elif "mute volume" in self.query:
                        self.system_control.mute_volume()
                        self.speak("Volume muted.")

                    elif "unmute volume" in self.query:
                        self.system_control.unmute_volume()
                        self.speak("Volume unmuted.")

                    elif "increase brightness" in self.query:
                        self.system_control.increase_brightness()
                        self.speak("Brightness increased.")

                    elif "decrease brightness" in self.query:
                        self.system_control.decrease_brightness()
                        self.speak("Brightness decreased.")

                    elif "news" in self.query:
                        self.speak("Fetching the latest news headlines...")
                        headlines = self.news_service.get_headlines()
                        if isinstance(headlines,list) and len(headlines)>0:
                            for headline in headlines:
                                self.speak(headline)
                                self.terminalprint(headline)
                        else:
                            self.speak("Sorry, I couldn't fetch the latest news.")


                    elif "set alarm" in self.query or "alarm" in self.query:
                        self.set_alarm()

                    self.speak("Sir,do you have any other work")

class Main(QMainWindow):
    def __init__(self):
        super(Main, self).__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.print_buffer = []
        self.buffer_timer = QTimer()
        self.buffer_timer.timeout.connect(self.flush_terminal_buffer)
        self.buffer_timer.start(100)
        self.is_task_running = False
        self.ui.startbutton.clicked.connect(self.startTask)
        self.ui.stopbutton.clicked.connect(self.close)

    def terminalprint(self, text):
        if text not in self.print_buffer:
            self.print_buffer.append(text)

    def flush_terminal_buffer(self):
        if self.print_buffer:
            self.ui.terminaloutput.appendPlainText("\n".join(self.print_buffer))
            self.print_buffer.clear()

    def startTask(self):
        if self.is_task_running:
            self.terminalprint("⚠️ The loop is already running. Please wait.")
            return  # Prevents further execution if already running
        self.is_task_running = True
        # Jarvis GUI
        self.ui.movie = QtGui.QMovie("C:/Users/prasa/PycharmProjects/pythonProject/GUI/jarvis.gif")
        self.ui.jarvis.setMovie(self.ui.movie)
        self.ui.movie.start()
        # stop command
        self.startExecution = MainThread(self.ui, self.terminalprint)
        self.startExecution.stopSignal.connect(self.ui.stopbutton.click)
        self.startExecution.start()

        # Ironman corner
        self.ui.movie = QtGui.QMovie("C:/Users/prasa/PycharmProjects/pythonProject/GUI/ironman.jpg")
        self.ui.cornerironman.setMovie(self.ui.movie)
        self.ui.movie.start()
        # coding
        self.ui.movie = QtGui.QMovie("C:/Users/prasa/PycharmProjects/pythonProject/GUI/download.gif")
        self.ui.coding.setMovie(self.ui.movie)
        self.ui.movie.start()
        # date label
        self.ui.movie = QtGui.QMovie("C:/Users/prasa/PycharmProjects/pythonProject/GUI/date.jpg")
        self.ui.date.setMovie(self.ui.movie)
        self.ui.movie.start()
        # time label
        self.ui.movie = QtGui.QMovie("C:/Users/prasa/PycharmProjects/pythonProject/GUI/date.jpg")
        self.ui.time.setMovie(self.ui.movie)
        self.ui.movie.start()
        # start label
        self.ui.movie = QtGui.QMovie("C:/Users/prasa/PycharmProjects/pythonProject/GUI/starts.jpg")
        self.ui.start.setMovie(self.ui.movie)
        self.ui.movie.start()
        # stop label
        self.ui.movie = QtGui.QMovie("C:/Users/prasa/PycharmProjects/pythonProject/GUI/stops.jpg")
        self.ui.stop.setMovie(self.ui.movie)
        self.ui.movie.start()

        # Set up a timer to update the time and date every second
        timer = QTimer(self)
        timer.timeout.connect(self.showTime)
        timer.start(1000)
        self.startExecution.start()
    def onTaskStopped(self):
        self.is_task_running = False

    def showTime(self):
        # Get the current time and date
        currentTime = QTime.currentTime()
        currentDate = QDate.currentDate()
        # Format the time and date
        labelTime = currentTime.toString('hh:mm:ss')
        labelDate = currentDate.toString(Qt.ISODate)
        # Update the labels on the GUI
        self.ui.datebutton.setText(f"Date:{labelDate}")
        self.ui.timebutton.setText(f"Time:{labelTime}")

# Create the application and main window
app = QApplication(sys.argv)
jarvis = Main()
jarvis.show()
# Start the application event loop
exit(app.exec_())