# ![(icon)](other/icon.svg) GrabUIText <small>(v1.0.0)</small>

A free tool for grabbing UI text from under the cursor.
Designed for language learners who have just switched their OS to the target language.
It lets you copy, translate, and read aloud UI text with simple keyboard shortcuts. It doesn't use OCR. Instead, it uses native OS functions to retrieve the raw text.

![(Windows search bar example)](other/search-bar-example.png)<br>
<small>"スタート", "検索", "タスク ビュー", "Copilot 固定済み" etc., ... from the Windows Search Bar</small>

## Features

- Grab UI text directly from under the mouse cursor
- Translate text automatically (powered by Google Translate)  
- Read text aloud (using Microsoft Edge TTS voices)
- Works globally across the system
- Optional on-screen overlay showing grabbed area
- Currently supported platform: **Windows**

## Installation

1. Install Python (if it's not already installed): https://www.python.org/downloads/
2. Download the repository and unzip it somewhere (for example, into a `grab-ui-text` directory), or clone it using Git:
```bash
git clone https://github.com/zegalur/grab-ui-text.git
cd grab-ui-text
```
3. Install the dependencies by running `install.bat` or by running the following in the console:
```bash
pip install -r requirements.txt
```
4. Additionally, for [Yomitan](https://yomitan.wiki/) users, you can turn ON the "Enable background clipboard text monitoring" option in Yomitan - a Yomitan pop-up window will appear whenever a UI text is copied.
5. (Optional) Create a (desktop) shortcut to `GrabUIText.bat` and set its icon to `other/logo.ico`.

## Usage

1. To start the program, run `GrabUIText.bat` (on **Windows**).
2. A console window will open. After a short moment, the icon ![(icon)](other/icon.svg) will appear in the system tray, and you should see `READY!` in the console.
3. You can now use the app.
4. Right-click the tray icon to access the app controls.
5. A history of all grabbed text is available in the console window.
6. **Translation and text-to-speech require an Internet connection.**

## Default shortcuts

| Shortcut             | Action                        |
|----------------------|-------------------------------|
| `Ctrl + Alt + C`     | Copy UI text under cursor     |
| `Ctrl + Alt + S`     | Read UI text aloud            |
| `Ctrl + Alt + T`     | Translate text and read aloud |

The overlay will highlight the grabbed element in green.

## ⚙️ Configuration

All configurable settings are at the top of `grab-ui.py`:

- `VOICE` and `VOICE_TR` - TTS voices  
- `TR_FROM` and `TR_TO` - translation languages  
- `COPY_TEXT_CMD`, `SAY_TEXT_CMD`, `TR_TEXT_CMD` - hotkeys  
- `OVERLAY_BORDER_COLOR` - overlay color  
- `MP3_COUNT` - MP3 buffering for playback

## Limitations

- Because GrabUIText doesn't use OCR, it works only with applications that render their UI using the OS's native API. 
- Currently, only Windows is supported. 
- Linux support is planned in the near future.
- Translation and text-to-speech require an Internet connection.

## License

Python script is licensed under CC BY 4.0<br>
*Pavlo Savchuk 2025*

Music files are not covered by the open-source license of this project.<br>
See `other/LICENSE-music` for more details.
