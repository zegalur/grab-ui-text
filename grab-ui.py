# A free tool for grabbing UI text from under the cursor.
# Designed for language learners who have just switched their OS to the target 
# language. For more information, please visit the official GitHub page:
# https://github.com/zegalur/grab-ui-text

# Released under CC BY 4.0 in 2025 by Pavlo Savchuk (aka zegalur)

APP_NAME = "GrabUIText"
APP_VERSION = "1.1.0"
GITHUB_PAGE = "https://github.com/zegalur/grab-ui-text"


################################## Settings ###################################

# Shortcuts (e.g. "<ctrl>+<alt>+c"):
COPY_TEXT_CMD = "<ctrl>+<alt>+c"
SAY_TEXT_CMD = "<ctrl>+<alt>+s"
TR_TEXT_CMD = "<ctrl>+<alt>+t"

# Voices (Edge TTS):
# (see: https://gist.github.com/BettyJJ/17cbaa1de96235a7f5773b8690a20462)
VOICE = "ja-JP-KeitaNeural"
VOICE_TR = "en-US-AriaNeural"

# Google translate options:
# (see: https://developers.google.com/workspace/admin/directory/v1/languages)
TR_FROM = "ja"
TR_TO = "en"

# When `True`, forces to print additional debug information.
PRINT_DEBUG_INFO = False

# Overlay rectangle colors:
OVERLAY_BORDER_COLOR = (0, 255, 71, 128)
OVERLAY_FILL_COLOR = (0, 255, 71, 50)

# For how long we see overlay rectangle (ms):
OVERLAY_DURATION = 10000

# The number of temporary MP3 files (must be >1):
MP3_COUNT = 10

# Maximum text length:
MAX_TEXT_LENGTH = 128

# Tray icon file:
ICON_FILE = "other/icon.svg"

# About window music MP3 file:
ABOUT_MUSIC_MP3 = "other/about_music.mp3"
ABOUT_MUSIC_VOLUME = 0.15

# About window text:
ABOUT_TEXT = (f"<b>{APP_NAME}</b> (v{APP_VERSION}) by <i>Pavlo Savchuk</i> " +
              f"(aka zegalur)<br>(music by King)<hr>For more information, " + 
              f"please visit the official GitHub page:<br>" +
              f"<a href='{GITHUB_PAGE}'>{GITHUB_PAGE}</a>")

# Help/Info window text:
HELP_TEXT = (f"<b>{APP_NAME}</b> (v{APP_VERSION})<hr>" + 
             f"A free tool that captures UI text from under the mouse cursor" +
             f", designed to help language learners who’ve just switched their"+
             f" OS to the target language.<hr>" + 
             f"<b>Shortcuts:</b><br>" + 
             f"1. Copy: " + 
             f"{COPY_TEXT_CMD.replace('<','&lt;').replace('>','&gt;').upper()}<br>" +
             f"2. Read ({TR_FROM}): " + 
             f"{SAY_TEXT_CMD.replace('<','&lt;').replace('>','&gt;').upper()}<br>" +
             f"3. Translate ({TR_FROM}&rarr;{TR_TO}): " + 
             f"{TR_TEXT_CMD.replace('<','&lt;').replace('>','&gt;').upper()}<hr>" +
             f"For more information, please visit the official GitHub page:<br>" +
             f"<a href='{GITHUB_PAGE}'>{GITHUB_PAGE}</a>")


################################### Imports ###################################

from pynput import keyboard
import sys

from PyQt5.QtWidgets import QApplication,QSystemTrayIcon
from PyQt5.QtWidgets import QMenu,QWidget,QAction
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIcon,QPainter,QPen,QColor
from PyQt5.QtCore import Qt,QThread,pyqtSignal,pyqtSlot,QObject,QTimer

import pyperclip
import asyncio
import edge_tts

from just_playback import Playback
from deep_translator import GoogleTranslator


########################### System Dependent Imports ##########################

# Possible sys.platform values:
# (https://stackoverflow.com/questions/446209/possible-values-from-sys-platform)
SYS_WINDOWS = "win32"
# TODO: Add Linux and MacOS support.
SYS_LINUX = "linux"
#SYS_MACOS = "darwin"
SUPPORTED_PLATFORMS = [ SYS_WINDOWS, SYS_LINUX ]

# Disable Keyboard Interrupt:
import signal
signal.signal(signal.SIGINT,  signal.SIG_IGN)
if sys.platform != SYS_WINDOWS:
    signal.signal(signal.SIGQUIT, signal.SIG_IGN)
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)

os_dep = {}

# System dependent imports.
# Returns a non-empty error message string on error.

sys_dep_init_err_msg = ""

if PRINT_DEBUG_INFO:
    print("Info: sys.platform == " + sys.platform)

if sys.platform == SYS_WINDOWS:
    import comtypes
    import comtypes.client
    from ctypes import windll, wintypes, byref
    # One-time module generation before the import:
    comtypes.client.GetModule('UIAutomationCore.dll')
    from comtypes.gen.UIAutomationClient import IUIAutomation

    # Initialize COM
    comtypes.CoInitialize()

    # CLSID of CUIAutomation
    CLSID_CUIAutomation = "{FF48DBA4-60EF-4201-AA87-54103EEF594E}"

    # Create the object and cast it to IUIAutomation
    os_dep["automation"] = comtypes.client.CreateObject(
            CLSID_CUIAutomation, interface=IUIAutomation)

elif sys.platform == SYS_LINUX:
    import pyatspi
    import pyautogui
    from Xlib import display,X

else:
    # Unsupported platform:
    sys_dep_init_err_msg = (
        "The platform \"{}\" is unsupported!\n".format(sys.platform) + 
        "Currently supported platforms are:\n{}".format(
               "\n".join(["- " + p for p in SUPPORTED_PLATFORMS])))


############################## Global Functions ###############################

# Translates `text` using Google translator.
def translate_text(text):
    return GoogleTranslator(source=TR_FROM, target=TR_TO).translate(text)


# Returns mouse cursor potion.
def get_cursor_pos():
    if sys.platform == SYS_WINDOWS:
        pt = wintypes.POINT()
        windll.user32.GetCursorPos(byref(pt))
        return pt.x, pt.y
    elif sys.platform == SYS_LINUX:
        return pyautogui.position() # x,y
    return 0,0


# Returns a list of window IDs in stacking order (bottom-to-top).
def get_stack_order_linux(displ):
    root = displ.screen().root
    prop = root.get_full_property(
            displ.intern_atom("_NET_CLIENT_LIST_STACKING"),
            X.AnyPropertyType)
    return prop.value if prop else []


# Returns X Window PID.
def get_window_pid_linux(displ, win_id):
    pid_atom = displ.intern_atom("_NET_WM_PID")
    window = displ.create_resource_object("window", win_id)
    pid_prop = window.get_full_property(pid_atom, X.AnyPropertyType)
    if pid_prop and pid_prop.value:
        return pid_prop.value[0]
    return None


# Checks if accessible is visible.
def is_visible_linux(d, acc):
    return True
    # TODO: fix: Visibility check isn't working.
    state = acc.getState()
    if state.contains(pyatspi.STATE_ICONIFIED):
        return False
    if state.contains(pyatspi.STATE_SHOWING):
        return True
    if state.contains(pyatspi.STATE_VISIBLE):
        return True
    return False


# Search a visible UI component under the cursor and get it's
# name and extensions.
def search_text_linux(d, x, y, accessible, spaces="  "):
    if is_visible_linux(d, accessible) == False:
        return None, None
    comp = accessible.queryComponent()
    el = comp.getAccessibleAtPoint(
            x, y, pyatspi.DESKTOP_COORDS)
    if not el:
        return None, None
    if is_visible_linux(d, el) == False:
        return None, None
    if PRINT_DEBUG_INFO:
        print(spaces + f"- {accessible} -> {el})")
    if el.name and len(el.name) > 0:
        if PRINT_DEBUG_INFO:
            print(spaces + f"=> Found! {el.name}")
        text = el.name
        extents = el.queryComponent().getExtents(
                pyatspi.DESKTOP_COORDS)
        return text, extents
    # Try another search method.
    for child in accessible:
        t,e = search_text_linux(
                d,x,y, child, spaces + "  ")
        if t: return t,e
    return None, None


# Linux version of get_text_under_cursor():
def get_text_under_cursor_linux(x, y):
    if sys.platform != SYS_LINUX:
        if PRINT_DEBUG_INFO:
            print("This script is only supported on Linux.")
        return "", (0,0,0,0)

    try:
        d = display.Display()
        stack_order = list(get_stack_order_linux(d))
        stack_order.reverse()
        pids = list(map(lambda wid: get_window_pid_linux(d, wid), stack_order))
        if PRINT_DEBUG_INFO:
            print(f"Info: stack order: {stack_order}")
            print(f"Info: PIDs (ordered): {pids}")
        desktop = pyatspi.Registry.getDesktop(0)
        for pid in pids:
            if PRINT_DEBUG_INFO:
                print(f"PID = {pid}:")
            apps = [app for app in desktop 
                    if app.get_process_id() == pid]
            for app in apps:
                if is_visible_linux(d, app) == False:
                    continue
                if PRINT_DEBUG_INFO:
                    print(f"- {app} {app.get_process_id()}")
                for obj in app:
                    try:
                        text, ext = search_text_linux(d,x,y,obj)
                        if text:
                            return text, ext
                    except Exception as e:
                        if PRINT_DEBUG_INFO:
                            print(f"Exception from " + 
                                  "search_text_linux(): " + 
                                  str(e))
                        pass
        return "", (0,0,0,0)

    except Exception as e:
        if PRINT_DEBUG_INFO:
            print("Exception: get_text_under_cursor_linux(): " + str(e))
        return "", (0,0,0,0)


# Returns UI's (text,(x,y,sx,sy)) from under the cursor.
def get_text_under_cursor():
    global os_dep
    x, y = get_cursor_pos()
    if PRINT_DEBUG_INFO:
        print(f"Info: Cursor position: ({x}, {y})")

    if sys.platform == SYS_WINDOWS:
        pt = wintypes.POINT(x, y)
        element = os_dep['automation'].ElementFromPoint(pt)

        rect = element.CurrentBoundingRectangle
        ps = (rect.left, rect.top, rect.right-rect.left, rect.bottom-rect.top)

        # Try Name property first
        name = element.CurrentName
        if name:
            return (name, ps)

        # Try ValuePattern if available
        UIA_ValuePatternId = 10002
        try:
            pattern = element.GetCurrentPattern(UIA_ValuePatternId)
            value = pattern.CurrentValue
            if value:
                return (value, ps)
        except Exception as e:
            if PRINT_DEBUG_INFO:
                print("get_text_under_cursor() Exception: " + e)

    if sys.platform == SYS_LINUX:
        return get_text_under_cursor_linux(x, y)

    if PRINT_DEBUG_INFO:
        print("Warning: get_text_under_cursor() will return an empty string.")
    
    # Returns an empty sting on error.
    return ("", (0,0,0,0))


############################### Overlay Widget ################################

class OverlayWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)
        wnd_flags = (Qt.FramelessWindowHint | 
                Qt.WindowStaysOnTopHint | 
                Qt.WindowTransparentForInput | 
                Qt.Tool)
        if sys.platform == SYS_LINUX:
            wnd_flags = wnd_flags | Qt.X11BypassWindowManagerHint
        self.setWindowFlags(wnd_flags)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setGeometry(0, 0, 0, 0)
        self.visible = False
        self.show_rect = True

    def paintEvent(self, event):
        if self.visible:
            # Paint a semi-transparent rectangle with 1px border:
            painter = QPainter(self)
            pen = QPen(QColor(*OVERLAY_BORDER_COLOR))
            painter.setPen(pen)
            painter.setBrush(QColor(*OVERLAY_FILL_COLOR))
            painter.drawRect(0, 0, self.width()-1, self.height()-1)

    def toggle_rect(self, checked):
        self.show_rect = checked
        if self.show_rect == False:
            self.hide()
            self.update()

    def set_pos(self, x, y, sx, sy):
        if self.show_rect == False:
            return
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint);
        self.timer.stop()
        self.setGeometry(x, y, sx, sy)  # Rectangle position and size
        self.visible = True
        self.show()
        self.update()
        self.repaint()
        self.timer.start(OVERLAY_DURATION)


############################### Hotkey Thread #################################

class HotkeyThread(QThread):
    copy_signal = pyqtSignal()
    say_signal = pyqtSignal()
    tr_signal = pyqtSignal()

    def run(self):
        if PRINT_DEBUG_INFO:
            print("Start hotkey thread.")
        while True:
            try:
            # Hotkeys:
                with keyboard.GlobalHotKeys({
                        COPY_TEXT_CMD: self.copy_hotkey,
                        SAY_TEXT_CMD: self.say_hotkey,
                        TR_TEXT_CMD: self.tr_hotkey
                        }) as h:
                    if PRINT_DEBUG_INFO:
                        print("Joining (hotkey thread).")
                    print("READY!")
                    h.join()
            except Exception as e:
                print("[!] Exception at hotkey thread: " + e)
                print("Trying to restore...")
        if PRINT_DEBUG_INFO:
            print("Stop hotkey thread.")

    def copy_hotkey(self):
        if PRINT_DEBUG_INFO:
            print("emit: copy_signal()")
        self.copy_signal.emit()
    
    def say_hotkey(self):
        if PRINT_DEBUG_INFO:
            print("emit: say_signal()")
        self.say_signal.emit()

    def tr_hotkey(self):
        if PRINT_DEBUG_INFO:
            print("emit: tr_signal()")
        self.tr_signal.emit()


############################# Main Application ################################

class SystemTrayApp(QObject):
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        if sys_dep_init_err_msg != "":
            self.critical_err_msg(sys_dep_init_err_msg)

        # Playback init:
        self.p = Playback()
        self.mp3_files = ["mp3/output_{}.mp3".format(i) for i in range(1,MP3_COUNT)]
        self.cur_mp3 = 0

        icon_file = ICON_FILE if sys.platform == SYS_WINDOWS else "other/logo-24px.png"
        self.tray = QSystemTrayIcon(QIcon(icon_file))
        self.tray.setToolTip(f"{APP_NAME} (v{APP_VERSION})")
        self.overlay = OverlayWidget()

        # System tray menu
        menu = QMenu()
        show_action = QAction("Show Overlay", self.tray)
        show_action.setCheckable(True)
        show_action.setChecked(True)
        help_action = QAction("Help / Info", self.tray)
        help_action.triggered.connect(self.show_help_wnd)
        about_action = QAction("About", self.tray)
        about_action.triggered.connect(self.show_about_wnd)
        quit_action = QAction("Quit", self.tray)
        show_action.triggered.connect(self.overlay.toggle_rect)
        quit_action.triggered.connect(self.app.quit)
        menu.addAction(show_action)
        menu.addSeparator()
        menu.addAction(help_action)
        menu.addAction(about_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.show()

        self.hokey_th = HotkeyThread()
        self.hokey_th.copy_signal.connect(self.copy_hotkey)
        self.hokey_th.say_signal.connect(self.say_hotkey)
        self.hokey_th.tr_signal.connect(self.tr_hotkey)
        self.hokey_th.start()

        self.app.setQuitOnLastWindowClosed(False)

        print("App init() completed.")
        
    def show_about_wnd(self):
        midi_player = Playback()
        midi_player.load_file(ABOUT_MUSIC_MP3)
        midi_player.play()
        midi_player.set_volume(ABOUT_MUSIC_VOLUME)
        midi_player.loop_at_end(True)
        msg = QMessageBox()
        msg.setWindowIcon(QIcon(ICON_FILE))
        msg.setIcon(QMessageBox.Information)
        msg.setTextFormat(Qt.RichText)
        msg.setWindowTitle("About Information")
        msg.setText(ABOUT_TEXT)
        timer = QTimer(self)
        snake_pos, snake = 0, ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"]
        def upd_snake():
            nonlocal snake, snake_pos
            snake_pos = (snake_pos + 1) % len(snake)
            s = "".join([snake[(i+snake_pos)%len(snake)] for i in range(1,80)])
            msg.setInformativeText(s)
        timer.timeout.connect(upd_snake)
        timer.start(100)
        msg.exec_()
        midi_player.stop()
        timer.stop()
        timer.deleteLater()

    def show_help_wnd(self):
        msg = QMessageBox()
        msg.setWindowIcon(QIcon(ICON_FILE))
        msg.setIcon(QMessageBox.Information)
        msg.setTextFormat(Qt.RichText)
        msg.setWindowTitle("Help Information")
        msg.setText(HELP_TEXT)
        msg.exec_()

    def toggle_overlay(self):
        self.overlay.toggle_visibility()
        if PRINT_DEBUG_INFO:
            print("Info: Overlay toggled.")

    def run(self):
        sys.exit(self.app.exec_())

    def critical_err_msg(self, text):
        msg = QMessageBox()
        msg.setWindowIcon(QIcon(ICON_FILE))
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Critical Error!")
        msg.setInformativeText(text)
        msg.setWindowTitle(APP_NAME + " v" + APP_VERSION + " - Critical Error")
        msg.exec_()
        exit(1)

    # Says aloud `text` using specified `voice`.
    async def tts(self, text, voice):
        communicate = edge_tts.Communicate(text, voice) 
        await communicate.save(self.mp3_files[self.cur_mp3])
        self.p.load_file(self.mp3_files[self.cur_mp3])
        self.p.play()
        self.cur_mp3 = (self.cur_mp3 + 1) % len(self.mp3_files)

    #@pyqtSlot()
    def copy_hotkey(self):
        try:
            (text, r) = get_text_under_cursor()
            self.overlay.set_pos(*r)
            if text:
                pyperclip.copy(text[:MAX_TEXT_LENGTH])
                print(f"[✓] Copied: {text}")
            else:
                print("[×] No text available at cursor")
                pass
        except Exception as e:
            print("[!] Error:", e)
            self.critical_err_msg(e)

    #@pyqtSlot()
    def say_hotkey(self):
        try:
            (text, r) = get_text_under_cursor()
            self.overlay.set_pos(*r)
            if text:
                mp3_file_name = self.mp3_files[self.cur_mp3]
                asyncio.run(self.tts(text[:MAX_TEXT_LENGTH], VOICE))
                print(f"[✓] Read: {text} ({mp3_file_name})")
            else:
                print("[×] No text available at cursor")
        except Exception as e:
            print("[!] Error:", e)
            #self.critical_err_msg(e)

    #@pyqtSlot()
    def tr_hotkey(self):
        try:
            (text, r) = get_text_under_cursor()
            self.overlay.set_pos(*r)
            if text:
                tr_text = translate_text(text[:MAX_TEXT_LENGTH])
                mp3_file_name = self.mp3_files[self.cur_mp3]
                asyncio.run(self.tts(tr_text[:MAX_TEXT_LENGTH], VOICE_TR))
                print(f"[✓] Translate: {text} -> {tr_text} ({mp3_file_name})")
            else:
                print("[×] No text available at cursor")
        except Exception as e:
            print("[!] Error:", e)
            #self.critical_err_msg(e)


if __name__ == "__main__":
    print(APP_NAME + " (v" + APP_VERSION + ") by Pavlo Savchuk (aka zegalur)")
    print("GitHub page: " + GITHUB_PAGE)
    app = SystemTrayApp()
    app.run()
    print("Normal exit.")

