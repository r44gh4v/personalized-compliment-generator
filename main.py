import cv2
import json
import numpy as np
from fer import FER
import pyttsx3
import threading
import queue
import random
import time

class TTSEngine:
    def __init__(self, settings):
        self.settings = settings
        self.speech_queue = queue.Queue()
        self.engine = None
        self.init_engine()
        self.start_thread()
    
    def init_engine(self):
        self.engine = pyttsx3.init()
        self.engine.setProperty('rate', self.settings['tts']['rate'])
        self.engine.setProperty('volume', self.settings['tts']['volume'])
    
    def start_thread(self):
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()
    
    def _process_queue(self):
        while True:
            try:
                text = self.speech_queue.get()
                if text:
                    self.engine.say(text)
                    self.engine.runAndWait()
                self.speech_queue.task_done()
            except Exception as e:
                print(f"TTS Error: {e}")
    
    def speak(self, text):
        if text:
            self.speech_queue.put(text)

class SmartMirror:
    def __init__(self):
        # Load configurations
        with open('config.json', 'r') as f:
            self.settings = json.load(f)
        with open('compliments.json', 'r') as f:
            self.compliments = json.load(f)
        
        # Initialize components
        self.detector = FER(mtcnn=True)
        self.cap = cv2.VideoCapture(self.settings['camera']['device_id'])
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings['camera']['width'])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings['camera']['height'])
        self.tts = TTSEngine(self.settings)
        
        # State tracking
        self.current_emotion = "neutral"
        self.last_compliment = ""
        self.last_compliment_time = 0
        
        # Create static overlay background
        self.overlay_height = 100
        self.create_overlay_background()
    
    def create_overlay_background(self):
        """Create a static background for the overlay"""
        width = self.settings['camera']['width']
        self.overlay = np.zeros((self.overlay_height, width, 3), dtype=np.uint8)
        # Add semi-transparent black background
        cv2.rectangle(self.overlay, (0, 0), (width, self.overlay_height),
                     self.settings['display']['overlay_color'], -1)
    
    def get_emotion(self, frame):
        try:
            result = self.detector.detect_emotions(frame)
            if result and len(result) > 0:
                emotions = result[0]['emotions']
                dominant_emotion = max(emotions.items(), key=lambda x: x[1])
                if dominant_emotion[1] >= self.settings['compliments']['min_confidence']:
                    return dominant_emotion[0], result[0]['box']
                return self.current_emotion, result[0]['box']
        except Exception as e:
            print(f"Emotion detection error: {e}")
        return self.current_emotion, None
    
    def get_compliment(self, emotion):
        if emotion in self.compliments:
            return random.choice(self.compliments[emotion])
        return None
    
    def should_give_compliment(self):
        current_time = time.time()
        if current_time - self.last_compliment_time >= self.settings['compliments']['interval_seconds']:
            self.last_compliment_time = current_time
            return True
        return False
    
    def update_overlay(self, emotion):
        """Update the overlay with current emotion and compliment"""
        # Create a fresh copy of the background
        overlay = self.overlay.copy()
        
        # Add emotion text
        emotion_text = f"Current Emotion: {emotion.title()}"
        cv2.putText(overlay, emotion_text,
                   (20, 30),
                   eval(self.settings['display']['font']),
                   self.settings['display']['font_scale'],
                   self.settings['display']['text_color'],
                   self.settings['display']['thickness'])
        
        # Add compliment text
        if self.last_compliment:
            cv2.putText(overlay, self.last_compliment,
                       (20, 70),
                       eval(self.settings['display']['font']),
                       self.settings['display']['font_scale'],
                       self.settings['display']['text_color'],
                       self.settings['display']['thickness'])
        
        return overlay
    
    def blend_overlay(self, frame, overlay):
        """Blend the overlay with the main frame"""
        result = frame.copy()
        alpha = self.settings['display']['overlay_alpha']
        result[0:self.overlay_height, 0:frame.shape[1]] = cv2.addWeighted(
            frame[0:self.overlay_height, 0:frame.shape[1]],
            1-alpha,
            overlay,
            alpha,
            0
        )
        return result
    
    def process_frame(self, frame):
        # Get emotion and update current emotion if detected
        emotion, face_box = self.get_emotion(frame)
        if emotion:
            self.current_emotion = emotion
        
        # Handle compliments based on interval
        if self.should_give_compliment():
            compliment = self.get_compliment(self.current_emotion)
            if compliment:
                self.last_compliment = compliment
                self.tts.speak(compliment)
        
        # Draw face box if detected
        if face_box:
            x, y, w, h = face_box
            cv2.rectangle(frame, (x, y), (x+w, y+h), 
                         self.settings['display']['box_color'], 
                         self.settings['display']['thickness'])
        
        # Update and blend overlay
        overlay = self.update_overlay(self.current_emotion)
        frame = self.blend_overlay(frame, overlay)
        
        return frame
    
    def run(self):
        print("Starting Smart Mirror... Press 'q' to quit.")
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break
                
                processed_frame = self.process_frame(frame)
                cv2.imshow('Smart Mirror', processed_frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            print("Cleaning up...")
            self.cap.release()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    mirror = SmartMirror()
    mirror.run()
    