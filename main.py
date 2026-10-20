import json, os, threading, time
from datetime import datetime, timedelta
from kivy.app import App
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
import requests
from zk import ZK

API_URL = "https://script.google.com/macros/s/AKfycbxua6VPiLPCTlO0KJwa0Oy2K9jCbdm5PZ0qqPryE4Vm8LRDtkWP7SnL7UJbPK5SSL6B/exec"
BATCH_SIZE = 5000

KV = r"""
<RootUI>:
    orientation: "vertical"
    padding: "16dp"
    spacing: "10dp"
    canvas.before:
        Color:
            rgba: 0.95, 0.97, 0.96, 1
        Rectangle:
            pos: self.pos
            size: self.size
    Label:
        text: "[b]Attendance Sync[/b]"
        markup: True
        color: 0.08, 0.24, 0.19, 1
        font_size: "25sp"
        size_hint_y: None
        height: "48dp"
    Label:
        text: "ZKTeco  →  Google Sheets"
        color: 0.25, 0.32, 0.29, 1
        size_hint_y: None
        height: "24dp"
    GridLayout:
        cols: 2
        spacing: "8dp"
        size_hint_y: None
        height: self.minimum_height
        row_default_height: "46dp"
        row_force_default: True
        Label:
            text: "IP Address"
            color: 0.1, 0.1, 0.1, 1
            halign: "left"
            text_size: self.size
        TextInput:
            id: ip_input
            text: root.saved_ip
            multiline: False
            write_tab: False
        Label:
            text: "Port"
            color: 0.1, 0.1, 0.1, 1
            halign: "left"
            text_size: self.size
        TextInput:
            id: port_input
            text: root.saved_port
            multiline: False
            input_filter: "int"
        Label:
            text: "Branch Code"
            color: 0.1, 0.1, 0.1, 1
            halign: "left"
            text_size: self.size
        TextInput:
            id: branch_input
            text: root.saved_branch
            multiline: False
    Button:
        text: "Save Settings"
        size_hint_y: None
        height: "48dp"
        background_normal: ""
        background_color: 0.12, 0.42, 0.31, 1
        on_release: root.save_settings()
    Button:
        text: "Test Connection"
        size_hint_y: None
        height: "52dp"
        background_normal: ""
        background_color: 0.14, 0.35, 0.55, 1
        on_release: root.test_connection()
    Button:
        text: "Start Attendance Sync"
        size_hint_y: None
        height: "56dp"
        background_normal: ""
        background_color: 0.08, 0.43, 0.29, 1
        on_release: root.start_sync()
    Label:
        text: root.status_text
        color: 0.08, 0.15, 0.12, 1
        halign: "left"
        valign: "top"
        text_size: self.width, None
    Label:
        text: "First run: all logs. Later runs: last 30 days."
        color: 0.35, 0.35, 0.35, 1
        size_hint_y: None
        height: "28dp"
"""

class RootUI(BoxLayout):
    saved_ip = StringProperty("10.16.15.12")
    saved_port = StringProperty("4370")
    saved_branch = StringProperty("BNS")
    status_text = StringProperty("Ready. Save your settings, then test the connection.")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.settings_path = os.path.join(App.get_running_app().user_data_dir, "settings.json")
        self.last_sync_path = os.path.join(App.get_running_app().user_data_dir, "last_sync.txt")
        self.load_settings()

    def update_status(self, message):
        Clock.schedule_once(lambda dt: setattr(self, "status_text", message), 0)

    def popup(self, message):
        Clock.schedule_once(lambda dt: Popup(title="Attendance Sync",
            content=Label(text=message), size_hint=(0.85, 0.35)).open(), 0)

    def load_settings(self):
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.saved_ip = data.get("ip", self.saved_ip)
            self.saved_port = str(data.get("port", self.saved_port))
            self.saved_branch = data.get("branch", self.saved_branch)
        except Exception:
            pass

    def get_values(self):
        ip = self.ids.ip_input.text.strip()
        port_text = self.ids.port_input.text.strip()
        branch = self.ids.branch_input.text.strip().upper()
        if not ip or not port_text or not branch:
            raise ValueError("Please fill in IP, Port and Branch Code.")
        port = int(port_text)
        if not 1 <= port <= 65535:
            raise ValueError("Port must be between 1 and 65535.")
        return ip, port, branch

    def save_settings(self, show=True):
        try:
            ip, port, branch = self.get_values()
            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
            with open(self.settings_path, "w", encoding="utf-8") as f:
                json.dump({"ip": ip, "port": port, "branch": branch}, f)
            self.saved_ip, self.saved_port, self.saved_branch = ip, str(port), branch
            if show:
                self.popup("Settings saved on this phone.")
            return ip, port, branch
        except Exception as e:
            self.popup(str(e))
            return None

    def test_connection(self):
        vals = self.save_settings(show=False)
        if not vals:
            return
        threading.Thread(target=self._test_connection_worker, args=vals, daemon=True).start()

    def _test_connection_worker(self, ip, port, branch):
        self.update_status("Testing connection to fingerprint device...")
        conn = None
        try:
            zk = ZK(ip, port=port, timeout=10)
            conn = zk.connect()
            self.update_status("Connection successful. Device responded at %s:%s." % (ip, port))
            self.popup("Connection successful.")
        except Exception as e:
            self.update_status("Connection failed: %s" % str(e))
            self.popup("Connection failed:\n%s\n\nCheck that the phone can reach the device on the local network." % str(e))
        finally:
            if conn:
                try: conn.disconnect()
                except Exception: pass

    def start_sync(self):
        vals = self.save_settings(show=False)
        if not vals:
            return
        threading.Thread(target=self._sync_worker, args=vals, daemon=True).start()

    def _sync_worker(self, ip, port, branch):
        conn = None
        try:
            self.update_status("Connecting to device...")
            zk = ZK(ip, port=port, timeout=15)
            conn = zk.connect()
            try:
                conn.disable_device()
            except Exception:
                pass

            if os.path.exists(self.last_sync_path):
                start_date = datetime.now() - timedelta(days=30)
                self.update_status("Connected. Reading logs from the last 30 days...")
            else:
                start_date = None
                self.update_status("First run: reading all attendance logs...")

            logs = conn.get_attendance()
            logs_data = []
            for log in logs:
                if start_date and log.timestamp < start_date:
                    continue
                logs_data.append({
                    "AC-No.": str(log.user_id),
                    "No.": "",
                    "Name": "",
                    "Time": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "Branch": branch
                })

            total = len(logs_data)
            sent = inserted_total = failed = 0
            batch_count = (total + BATCH_SIZE - 1) // BATCH_SIZE
            for index in range(0, total, BATCH_SIZE):
                batch = logs_data[index:index + BATCH_SIZE]
                batch_no = index // BATCH_SIZE + 1
                self.update_status("Sending batch %s/%s — %s records..." % (batch_no, batch_count, len(batch)))
                try:
                    response = requests.post(API_URL, json={"data": batch},
                        headers={"Content-Type": "application/json"}, timeout=120)
                    result = response.json()
                    if response.status_code == 200 and result.get("status") == "success":
                        sent += len(batch)
                        inserted_total += int(result.get("inserted", 0))
                    else:
                        failed += len(batch)
                except Exception:
                    failed += len(batch)
                time.sleep(2)

            summary = "Sync finished.\nRead: %s\nSent successfully: %s\nAdded to Sheet: %s\nFailed: %s" % (
                total, sent, inserted_total, failed)
            if failed == 0 and sent == total:
                with open(self.last_sync_path, "w", encoding="utf-8") as f:
                    f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                summary += "\nSync timestamp saved."
                self.update_status(summary)
            else:
                summary += "\nTimestamp not saved because some records failed."
                self.update_status(summary)
            self.popup(summary)
        except Exception as e:
            self.update_status("Error: %s" % str(e))
            self.popup("Sync error:\n%s" % str(e))
        finally:
            if conn:
                try: conn.enable_device()
                except Exception: pass
                try: conn.disconnect()
                except Exception: pass

class AttendanceSyncApp(App):
    def build(self):
        Builder.load_string(KV)
        return RootUI()

if __name__ == "__main__":
    AttendanceSyncApp().run()
