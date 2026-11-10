# PyInstaller build recipe for Wield.
#
# Build (from the repo root):
#     pip install -r requirements.txt pyinstaller
#     pyinstaller Wield.spec --noconfirm
#
# Output: dist/Wield/Wield(.exe) plus its support files. Ship the whole
# dist/Wield folder (the GitHub workflow zips it).

from PyInstaller.utils.hooks import collect_all

datas = [
    # Read-only resources, found at runtime via backend/paths.py (APP_DIR).
    ("backend/models/gesture_recognizer.task", "backend/models"),
    ("backend/config", "backend/config"),
    ("frontend/styles/theme.qss", "frontend/styles"),
    ("assets/icons/wield.png", "assets/icons"),
]
binaries = []
hiddenimports = []

# MediaPipe loads native libraries and data files dynamically.
mp_datas, mp_binaries, mp_hidden = collect_all("mediapipe")
datas += mp_datas
binaries += mp_binaries
hiddenimports += mp_hidden

# Windows-only modules imported by the PowerPoint controller / hotkeys.
hiddenimports += ["win32com.client", "pyautogui"]

# Wield only uses QtCore, QtGui and QtWidgets. Leaving the rest of Qt
# out (web engine, QML, 3D, multimedia...) cuts the download by hundreds of MB.
UNUSED_QT = [
    "QtWebEngineCore", "QtWebEngineWidgets", "QtWebEngineQuick", "QtWebChannel",
    "QtWebSockets", "QtQml", "QtQuick", "QtQuick3D", "QtQuickWidgets",
    "QtQuickControls2", "Qt3DCore", "Qt3DRender", "Qt3DInput", "Qt3DLogic",
    "Qt3DExtras", "Qt3DAnimation", "QtMultimedia", "QtMultimediaWidgets",
    "QtCharts", "QtDataVisualization", "QtGraphs", "QtPdf", "QtPdfWidgets",
    "QtBluetooth", "QtNfc", "QtPositioning", "QtLocation", "QtSensors",
    "QtSerialPort", "QtSql", "QtTest", "QtDesigner", "QtHelp", "QtSvgWidgets",
    "QtRemoteObjects", "QtScxml", "QtSpatialAudio", "QtTextToSpeech",
    "QtHttpServer", "QtOpenGLWidgets",
]

EXCLUDES = [
    # (matplotlib must stay: mediapipe.tasks.vision imports it.)
    "tkinter", "tests", "tools",
] + [f"PySide6.{name}" for name in UNUSED_QT]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=EXCLUDES,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Wield",
    console=False,  # no terminal window behind the app
    icon="assets/icons/wield.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Wield",
)
