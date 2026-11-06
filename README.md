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

## ⬇️ Download

Get the latest **LensFlow-windows.zip** from the
[Releases page](https://github.com/Praveena-Kiran/LensFlow/releases), extract it
and run `LensFlow\LensFlow.exe`. No Python needed. Requires Windows 10/11 and a webcam.

## 🚀 Installation (from source)

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

### Motions

Swipe left, right, up and down work out of the box (in Presentation Studio
they change slides). Record your own movements, like a wave or a circle, under
**Gesture Studio → + Record Custom Motion**, then pick them as a trigger like
any gesture. Bringing your hand back after a swipe is ignored, so it doesn't
trigger the opposite swipe.

### Your window

Home shows your camera through a foggy pane. **Point** your index finger to
write on it, make a **fist** to pause, and hold an **open palm** for a second to
wipe it. **Save note** keeps your writing, so it greets you next time. Only
the writing is saved, never a camera image. Filters: Fog, Clear, Mono.

### Routines

LensFlow notices when you do the same thing around the same time on most days
(for example, launching a studio at 10:00) and asks, when you open it, whether
to do it for you. Nothing is automated until you click **Automate**. **Not now**
keeps the suggestion in **Notifications**, which also lists your automations
(pause or delete them). **History** shows recent activity, which you can clear.
Activity stays on this computer only, for at most 90 days.

Automations need LensFlow to be running: in Notifications, turn on *Keep
LensFlow running in the system tray* and/or *Start LensFlow when I sign in to
Windows*.

### Themes

**Settings → Appearance** offers Dark, Light, Jungle and Galaxy. Jungle and
Galaxy paint a backdrop of leaves or stars behind the app. Every theme's text
passes WCAG AA contrast (checked by `tests/test_themes.py`).

### Accessibility settings

**Settings** (sidebar) adjusts recognition to how you move:

- **Sensitivity**: from strict to forgiving. Forgiving accepts less exact poses
  and movements, which helps with tremor or limited range of motion.
- **Hold to trigger**: a pose must be held (up to 1.5 s) before it does anything.
- **Activation gesture**: LensFlow ignores gestures until you make a chosen
  gesture, then switches off again after a few idle seconds, so everyday hand
  movement doesn't trigger anything.

**Test Gestures** opens a live view showing what LensFlow recognises and what
it would trigger, without running anything.

To use gestures in your own studios, open the studio, pick a gesture for each
event (built-in or your own), then press **Start Gesture Control**. Making the
gesture runs that event.

Your studios, settings and custom gestures are stored per user in
`%APPDATA%\LensFlow` (Windows), so they survive app updates.

### Building the Windows app

GitHub Actions builds it automatically (`.github/workflows/build.yml`): every
pull request builds and self-tests `LensFlow.exe`, and pushing a version tag
publishes a release:

```bash
git tag v1.0.0
git push origin v1.0.0
```

To build locally instead:

```bash
pip install -r requirements.txt pyinstaller
pyinstaller LensFlow.spec --noconfirm
dist\LensFlow\LensFlow.exe --self-test
```

### Tests

```bash
python -m unittest discover tests
```
