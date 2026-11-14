import asyncio
import os
import subprocess
import tempfile
import time

import edge_tts
import pygame
import speech_recognition as sr


class Voice:
    def __init__(self, voice):
        self.voice = voice
        self.rec = sr.Recognizer()
        self.rec.pause_threshold = 0.9
        self.rec.non_speaking_duration = 0.5
        self.rec.operation_timeout = 10
        self.rec.dynamic_energy_threshold = False

        names = sr.Microphone.list_microphone_names()
        index = os.getenv("MIC_INDEX")
        index = int(index) if index and index.strip().isdigit() else None
        print("mic:", names[index] if index is not None and index < len(names) else "default")
        self.mic = sr.Microphone(device_index=index)

        with self.mic as src:
            self.rec.adjust_for_ambient_noise(src, duration=1.5)
        fixed = os.getenv("MIC_THRESHOLD", "").strip()
        if fixed.isdigit():
            self.rec.energy_threshold = int(fixed)
        else:
            self.rec.energy_threshold = max(120, min(self.rec.energy_threshold * 1.2, 350))
        print("mic threshold:", int(self.rec.energy_threshold))

        pygame.mixer.init()

    def listen(self, timeout=None, limit=10, alts=False):
        with self.mic as src:
            try:
                audio = self.rec.listen(src, timeout=timeout, phrase_time_limit=limit)
            except sr.WaitTimeoutError:
                return None
        try:
            result = self.rec.recognize_google(audio, language="en-IN", show_all=True)
        except Exception as e:
            print("speech error:", e)
            return ""
        if not result or not result.get("alternative"):
            return [] if alts else ""
        options = [a["transcript"] for a in result["alternative"] if a.get("transcript")]
        return options if alts else options[0]

    def speak(self, text):
        path = os.path.join(tempfile.gettempdir(), f"dummy_{int(time.time() * 1000)}.mp3")
        try:
            asyncio.run(asyncio.wait_for(edge_tts.Communicate(text, self.voice, rate="+8%").save(path), 12))
        except Exception as e:
            print("edge voice failed, using windows voice:", e)
            self.backup(text)
            return
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.05)
        pygame.mixer.music.unload()
        try:
            os.remove(path)
        except OSError:
            pass

    def backup(self, text):
        if os.name != "nt":
            return
        safe = text.replace("'", "''")
        cmd = f"Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{safe}')"
        subprocess.run(["powershell", "-NoProfile", "-Command", cmd], capture_output=True)
