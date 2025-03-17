import time
import datetime
import winsound
import keyboard
import dateparser

def parse_time(command):
    """Extracts time from the command using NLP"""
    parsed_time = dateparser.parse(command)
    if parsed_time:
        return parsed_time.strftime("%I:%M %p")  # 12-hour format with AM/PM
    return None

def play_alarm(terminalprint):
    """Plays alarm sound"""
    terminalprint("Time to wake up!")
    for _ in range(5):  # Beep 5 times
        winsound.Beep(2000, 500)
        time.sleep(1)

def set_alarm(alarm_time, terminalprint):
    """Waits until the specified alarm time and then plays a sound"""
    now = datetime.datetime.now().strftime("%I:%M %p")
    terminalprint(f"Current Time: {now}, Alarm Set for: {alarm_time}")

    while now != alarm_time:
        now = datetime.datetime.now().strftime("%I:%M %p")
        time.sleep(10)  # Check time every 10 seconds

    play_alarm(terminalprint)

def alarm_listener(terminalprint):
    """Keeps listening for snooze or stop commands while alarm rings"""
    while True:
        if keyboard.is_pressed("q"):
            terminalprint("Alarm stopped.")
            break
        elif keyboard.is_pressed("s"):
            terminalprint("Snoozing for 5 minutes.")
            time.sleep(300)  # 5 minutes snooze
            play_alarm(terminalprint)
        time.sleep(0.1)