"""
Names of MediaPipe's built-in gestures as shown in Wield.

Kept separate from google_gesture_recognizer.py (which needs OpenCV and
MediaPipe) so code and tests that only need the names stay lightweight.
"""

# MediaPipe category name -> name shown in Wield.
BUILTIN_GESTURES = {
    "Thumb_Up": "👍 Thumbs Up",
    "Thumb_Down": "👎 Thumbs Down",
    "Open_Palm": "✋ Open Palm",
    "Closed_Fist": "✊ Fist",
    "Victory": "✌️ Peace",
    "Pointing_Up": "☝️ Pointing Up",
}

BUILTIN_GESTURE_NAMES = list(BUILTIN_GESTURES.values())
