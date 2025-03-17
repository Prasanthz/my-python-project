import pyautogui
from comtypes import CLSCTX_ALL
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

class SystemControl:
    
    def __init__(self, terminalprint_callback):
        self.terminalprint = terminalprint_callback

    def increase_volume(self):
        """Increases system volume by 10%"""
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        current_volume = volume.GetMasterVolumeLevelScalar()
        new_volume = min(1.0, current_volume + 0.1)  
        volume.SetMasterVolumeLevelScalar(new_volume, None)
        self.terminalprint(f"Volume Increased: {int(new_volume * 100)}%")

    def decrease_volume(self):
        """Decreases system volume by 10%"""
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = interface.QueryInterface(IAudioEndpointVolume)
        current_volume = volume.GetMasterVolumeLevelScalar()
        new_volume = max(0.0, current_volume - 0.1)  
        volume.SetMasterVolumeLevelScalar(new_volume, None)
        self.terminalprint(f"Volume Decreased: {int(new_volume * 100)}%")

    def mute_volume(self):
        """Mutes system using keyboard shortcut"""
        pyautogui.press("volumemute")  
        self.terminalprint("System Muted")

    def unmute_volume(self):
        """unmutes system using keyboard shortcut"""
        pyautogui.press("volumemute")  
        self.terminalprint("System Unmuted")

    def increase_brightness(self):
        """Increases screen brightness by 10%"""
        current_brightness = sbc.get_brightness()
        new_brightness = min(100, current_brightness[0] + 10)  
        sbc.set_brightness(new_brightness)
        self.terminalprint(f"Brightness Increased: {new_brightness}%")

    def decrease_brightness(self):
        """Decreases screen brightness by 10%"""
        current_brightness = sbc.get_brightness()
        new_brightness = max(0, current_brightness[0] - 10)  
        sbc.set_brightness(new_brightness)
        self.terminalprint(f"Brightness Decreased: {new_brightness}%")