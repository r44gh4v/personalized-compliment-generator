# Smart Mirror Feature

A smart mirror feature that detects faces, analyzes expressions, and provides personalized compliments.

## Features
- Real-time face detection
- Emotion analysis
- Personalized compliments with text-to-speech
- Privacy-focused (all processing done locally)

## Installation & Running
1. Install requirements:
```bash
pip install fer
pip install tensorflow-cpu
pip install opencv-contrib-python>=3.2
pip install moviepy==1.0
pip install numpy==1.24
pip install pyttsx3
```

2. Run the application:
```bash
python main.py
```

## Usage
- The program will open your camera
- Stand in front of the camera
- Your emotion will be detected and displayed
- Compliments will be shown and spoken based on your emotion
- Press 'q' to quit

## Files
- main.py: Main program file
- config.json: Configuration settings
- compliments.json: Emotion-based compliments
- README.md: This documentation

## Note
Make sure you have a working camera and speakers/headphones for the full experience.
