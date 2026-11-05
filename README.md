# LensFlow
### AI-Powered Gesture-Based Accessibility Platform

LensFlow is an AI-powered desktop accessibility platform that enables hands-free computer interaction using customizable hand gestures and computer vision.

The project uses real-time hand gesture recognition to trigger configurable actions, including application launching and PowerPoint presentation control.

## ✨ Features

- Real-time hand gesture recognition using MediaPipe
- Computer vision processing with OpenCV
- Customizable gesture-based actions
- Hands-free application launching
- Gesture-controlled PowerPoint presentation navigation
- Presentation Studio for configuring gesture-based workflows
- Desktop application interface built with PySide6
- Gesture recognition stabilization for more reliable interaction

## 🏗️ Architecture

LensFlow is organized into separate components for gesture recognition, action handling, and the desktop interface.

- **Backend** — gesture recognition and action-handling logic
- **Frontend / UI** — desktop interface and studio navigation
- **Presentation Studio** — configuration and PowerPoint integration
- **Assets** — project resources and supporting files

## 🛠️ Technologies

- Python
- OpenCV
- MediaPipe
- PySide6

## 🚀 Installation

### Requirements

- Python 3.x
- Webcam
- Windows OS

### Setup

Clone the repository:

```bash
git clone https://github.com/Praveena-Kiran/LensFlow.git
cd LensFlow
```

Install the dependencies (a virtual environment is recommended):

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Run the app:

```bash
python main.py
```

### Manual hardware checks

```bash
python -m tools.webcam_gesture_check
python -m tools.camera_preview_check
```

### Custom gestures

Open **Gesture Studio → + Record Custom Gesture**, name the gesture and hold any
comfortable hand pose for three short takes. LensFlow rejects poses that look
like a built-in gesture or another of your gestures, so actions don't trigger by
accident. Then use **+ Add Gesture** to assign it to an action.

Your studios, settings and custom gestures are stored per user in
`%APPDATA%\LensFlow` (Windows), so they survive app updates.

### Tests

```bash
python -m unittest discover tests
```
