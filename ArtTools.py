"""
The ArtTools ( Vers For Vietnamese )
=================
Download:
    pip install PyQt6 requests psutil gputil

Run:
    python ArtTools.py
"""

import sys, os, json, subprocess, tempfile, shutil, socket, random, math
import psutil
import requests

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QLineEdit, QFrame,
    QPlainTextEdit, QStackedWidget, QProgressBar, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread, QTimer, QProcess
from PyQt6.QtGui import QFont, QPainter, QColor, QPen, QBrush, QPainterPath

IS_WIN = os.name == "nt"

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
def cfg_path():
    base = os.environ.get("APPDATA", os.path.expanduser("~")) if IS_WIN else os.path.expanduser("~/.config")
    d = os.path.join(base, "ArtTools")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "config.json")

CFG_FILE = cfg_path()
DEFAULTS = {"claude_key": "", "model": "free", "language": "python", "effect": "none"}

def load_cfg():
    try:
        with open(CFG_FILE, encoding="utf-8") as f:
            c = json.load(f); m = DEFAULTS.copy(); m.update(c); return m
    except Exception:
        return DEFAULTS.copy()

def save_cfg(c):
    try:
        with open(CFG_FILE, "w", encoding="utf-8") as f: json.dump(c, f, indent=2)
        return True
    except Exception:
        return False

# ─────────────────────────────────────────────
#  AI WORKER
# ─────────────────────────────────────────────
class AIWorker(QObject):
    done   = pyqtSignal(str)
    fail   = pyqtSignal(str)

    def __init__(self, prompt, lang, model, cfg, mode="code"):
        super().__init__()
        self.prompt, self.lang, self.model, self.cfg, self.mode = prompt, lang, model, cfg, mode

    def run(self):
        try:
            sys_p, usr_p = self._build_prompts()
            if self.model == "claude":
                result = self._claude(sys_p, usr_p)
            elif self.model == "deepseek":
                result = self._deepseek(sys_p, usr_p)
            elif self.model == "chatgpt":
                result = self._chatgpt(sys_p, usr_p)
            else:
                result = self._free(sys_p, usr_p)
            self.done.emit(result)
        except Exception as e:
            self.fail.emit(str(e))

    def _build_prompts(self):
        if self.mode == "check":
            s = (f"Bạn là senior {self.lang} code reviewer. "
                 "Phân tích code sau: lỗi syntax, lỗi logic, edge case, hiệu năng. "
                 "Trả lời TIẾNG VIỆT, rõ ràng từng mục, kèm cách sửa và đoạn code sửa.")
            u = f"```{self.lang}\n{self.prompt}\n```"
        elif self.mode == "chat":
            s = "Bạn là trợ lý AI thân thiện tích hợp trong ArtTools. Trả lời tiếng Việt, ngắn gọn, rõ ràng, hữu ích."
            u = self.prompt
        else:
            s = (f"You are an expert {self.lang} programmer. "
                 "Reply ONLY with code in ONE code block, minimal comments, no explanation outside block.")
            u = f"[{self.lang}] {self.prompt}"
        return s, u

    def _free(self, sys_p, usr_p):
        msgs = [{"role":"system","content":sys_p},{"role":"user","content":usr_p}]
        try:
            r = requests.post(
                "https://chateverywhere.app/api/chat/",
                headers={"Content-Type":"application/json",
                         "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                json={"model":"gpt-4o-mini","messages":msgs}, timeout=25)
            if r.status_code == 200 and r.text.strip():
                return r.text.strip()
        except Exception:
            pass
        try:
            r2 = requests.post(
                "https://api.deepinfra.com/v1/openai/chat/completions",
                json={"model":"meta-llama/Meta-Llama-3-70B-Instruct","messages":msgs}, timeout=30)
            if r2.status_code == 200:
                d = r2.json()
                return d["choices"][0]["message"]["content"]
        except Exception:
            pass
        try:
            combined = f"{sys_p}\n\n{usr_p}"
            import urllib.parse
            enc = urllib.parse.quote(combined)
            r3 = requests.get(f"https://text.pollinations.ai/{enc}", timeout=30)
            if r3.status_code == 200:
                return r3.text.strip()
        except Exception:
            pass
        return "[Not Connecting All Server < Not Found 404 > Return now.]"

    def _claude(self, sys_p, usr_p):
        key = self.cfg.get("claude_key","").strip()
        if not key: return "[Chưa nhập Claude API Key trong Cài đặt]"
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"},
            json={"model":"claude-3-5-sonnet-20241022","max_tokens":2048,
                  "system":sys_p,"messages":[{"role":"user","content":usr_p}]}, timeout=60)
        if r.status_code != 200: return f"[Lỗi Claude {r.status_code}]: {r.text[:300]}"
        data = r.json()
        return "\n".join(b["text"] for b in data.get("content",[]) if b.get("type")=="text")

    def _deepseek(self, sys_p, usr_p):
        key = self.cfg.get("deepseek_key","").strip()
        if not key: return "[Chưa nhập DeepSeek API Key trong Cài đặt]"
        r = requests.post("https://api.deepseek.com/chat/completions",
            headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
            json={"model":"deepseek-chat","max_tokens":2048,
                  "messages":[{"role":"system","content":sys_p},{"role":"user","content":usr_p}]}, timeout=60)
        if r.status_code != 200: return f"[Lỗi DeepSeek {r.status_code}]: {r.text[:300]}"
        return r.json()["choices"][0]["message"]["content"]

    def _chatgpt(self, sys_p, usr_p):
        key = self.cfg.get("openai_key","").strip()
        if not key: return "[Chưa nhập OpenAI API Key trong Cài đặt]"
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},
            json={"model":"gpt-4o-mini","max_tokens":2048,
                  "messages":[{"role":"system","content":sys_p},{"role":"user","content":usr_p}]}, timeout=60)
        if r.status_code != 200: return f"[Lỗi OpenAI {r.status_code}]: {r.text[:300]}"
        return r.json()["choices"][0]["message"]["content"]

# ─────────────────────────────────────────────
#  PARTICLE EFFECT CANVAS
# ─────────────────────────────────────────────
class Particle:
    def __init__(self, kind, w, h):
        self.kind = kind
        self.reset(w, h, fresh=True)

    def reset(self, w, h, fresh=False):
        self.x = random.uniform(0, w)
        self.y = random.uniform(-h, 0) if not fresh else random.uniform(0, h)
        if self.kind == "snow":
            self.size  = random.uniform(4, 10)
            self.speed = random.uniform(1.5, 4)
            self.sway  = random.uniform(-0.5, 0.5)
            self.phase = random.uniform(0, math.pi*2)
            self.alpha = random.uniform(140, 230)
        elif self.kind == "rain":
            self.size  = random.uniform(8, 20)
            self.speed = random.uniform(10, 40)
            self.sway  = random.uniform(-0.3, 0.3)
            self.phase = 0
            self.alpha = random.uniform(80, 160)
        else:
            self.size  = random.uniform(8, 18)
            self.speed = random.uniform(1, 3)
            self.sway  = random.uniform(-1.5, 1.5)
            self.phase = random.uniform(0, math.pi*2)
            self.alpha = random.uniform(160, 240)
            self.rot   = random.uniform(0, 360)
            self.rot_s = random.uniform(-3, 3)

    def update(self, w, h):
        self.phase += 0.03
        if self.kind == "snow":
            self.x += math.sin(self.phase) * 0.8 + self.sway
            self.y += self.speed
        elif self.kind == "rain":
            self.x += self.sway
            self.y += self.speed
        else:
            self.x += math.sin(self.phase) * 1.5 + self.sway
            self.y += self.speed
            self.rot += self.rot_s
        if self.y > h + 20 or self.x < -20 or self.x > w + 20:
            self.reset(w, h)

class EffectCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.kind = "none"
        self.particles = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setStyleSheet("background: transparent;")

    def set_effect(self, kind):
        self.kind = kind
        self.particles = []
        if kind != "none":
            count = {"snow": 30, "rain": 60, "leaves": 25}[kind]
            w, h = max(self.width(), 800), max(self.height(), 600)
            for _ in range(count):
                self.particles.append(Particle(kind, w, h))
            self.timer.start(14)
        else:
            self.timer.stop()
            self.update()

    def _tick(self):
        w, h = self.width(), self.height()
        for p in self.particles:
            p.update(w, h)
        self.update()

    def paintEvent(self, event):
        if not self.particles: return
        painter = QPainter(self)
        LEAF_COLORS = [(125, 140, 225), (150, 165, 240), (100, 115, 205)]
        for p in self.particles:
            if self.kind == "snow":
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(125, 140, 225, int(p.alpha))))
                r = int(p.size / 2)
                painter.drawEllipse(int(p.x - r), int(p.y - r), r*2, r*2)
            elif self.kind == "rain":
                painter.setPen(QPen(QColor(125, 140, 225, int(p.alpha)), 1))
                painter.drawLine(int(p.x), int(p.y), int(p.x), int(p.y + p.size))
            else:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                painter.save()
                painter.translate(p.x, p.y)
                painter.rotate(p.rot)
                rgb = LEAF_COLORS[int(abs(p.x + p.y)) % len(LEAF_COLORS)]
                painter.setBrush(QBrush(QColor(*rgb, int(p.alpha))))
                painter.setPen(Qt.PenStyle.NoPen)
                s = p.size
                path = QPainterPath()
                path.moveTo(0, -s/2)
                path.cubicTo(s/2, -s/3, s/2, s/3, 0, s/2)
                path.cubicTo(-s/2, s/3, -s/2, -s/3, 0, -s/2)
                painter.drawPath(path)
                painter.restore()
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        painter.end()

# ─────────────────────────────────────────────
#  CODE RUNNER
# ─────────────────────────────────────────────
class RunnerWidget(QWidget):
    def __init__(self, get_code_cb):
        super().__init__()
        self.get_code = get_code_cb
        self.proc = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(6)

        bar = QHBoxLayout()
        self.run_btn = QPushButton("▶ Run")
        self.run_btn.setObjectName("primaryBtn")
        self.run_btn.clicked.connect(self.run_code)
        self.stop_btn = QPushButton("■ Stop")
        self.stop_btn.setObjectName("dangerBtn")
        self.stop_btn.clicked.connect(self.stop_code)
        self.stat = QLabel("Load")
        self.stat.setObjectName("status")
        bar.addWidget(self.run_btn); bar.addWidget(self.stop_btn)
        bar.addWidget(self.stat); bar.addStretch()

        self.term = QPlainTextEdit()
        self.term.setObjectName("panel")
        self.term.setFont(QFont("Cascadia Code",10))
        self.term.setPlaceholderText("The Output...")

        self.stdin = QLineEdit()
        self.stdin.setObjectName("lineEdit")
        self.stdin.setPlaceholderText("Send stdin and Enter To send program running...")
        self.stdin.returnPressed.connect(self.send_stdin)

        layout.addLayout(bar)
        layout.addWidget(self.term)
        layout.addWidget(self.stdin)

    def run_code(self):
        self.stop_code()
        info = self.get_code()
        lang = info["language"].lower(); code = info["text"].strip()
        if not code: self.term.appendPlainText("Not Found Code =)"); return
        self.term.clear(); self.stat.setText("Running...")
        td = tempfile.mkdtemp(prefix="art_")
        try:
            if lang == "python":
                fp = os.path.join(td,"s.py")
                open(fp,"w",encoding="utf-8").write(code)
                self._start(sys.executable,[fp])
            elif lang in ("cpp", "c++"):
                src = os.path.join(td,"m.cpp"); exe = os.path.join(td,"m.exe" if IS_WIN else "m")
                open(src,"w",encoding="utf-8").write(code)
                gpp = shutil.which("g++")
                if not gpp: self.term.appendPlainText("// Thiếu g++"); return
                cp = subprocess.run([gpp,src,"-o",exe,"-O2"],capture_output=True,text=True)
                if cp.returncode != 0: self.term.appendPlainText("// Lỗi biên dịch:\n"+cp.stderr); return
                self._start(exe,[])
            elif lang in ("lua","luau"):
                fp = os.path.join(td,"s.lua")
                open(fp,"w",encoding="utf-8").write(code)
                interp = shutil.which("luau") or shutil.which("lua")
                if not interp: self.term.appendPlainText("// Thiếu lua/luau interpreter"); return
                self._start(interp,[fp])
        except Exception as e:
            self.term.appendPlainText(f"// Error: {e}")

    def _start(self, prog, args):
        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardOutput.connect(self._out)
        self.proc.finished.connect(lambda: self.stat.setText("Ending"))
        self.proc.start(prog, args)

    def _out(self):
        if self.proc:
            data = self.proc.readAllStandardOutput().data().decode(errors="replace")
            self.term.moveCursor(self.term.textCursor().MoveOperation.End)
            self.term.insertPlainText(data)
            self.term.moveCursor(self.term.textCursor().MoveOperation.End)

    def send_stdin(self):
        t = self.stdin.text()
        if self.proc and self.proc.state()==QProcess.ProcessState.Running:
            self.proc.write((t+"\n").encode())
        self.stdin.clear()

    def stop_code(self):
        if self.proc and self.proc.state()==QProcess.ProcessState.Running:
            self.proc.kill(); self.proc.waitForFinished(1000)
        self.stat.setText("Đã dừng")

# ─────────────────────────────────────────────
#  MANAGER (Dual GPU Support & Corrected Monitoring)
# ─────────────────────────────────────────────
class TaskWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self); layout.setContentsMargins(0,0,0,0); layout.setSpacing(6)
        self.bars = {}
        
        for name in ("CPU", "RAM", "GPU 1 (Integrated)", "GPU 2 (dGPU)"):
            row = QHBoxLayout()
            lbl = QLabel(f"{name}: 0%"); lbl.setFixedWidth(155); lbl.setObjectName("status")
            bar = QProgressBar(); bar.setObjectName("bar"); bar.setRange(0,100)
            row.addWidget(lbl); row.addWidget(bar)
            layout.addLayout(row); self.bars[name] = (lbl, bar)
            
        self.batt = QLabel("Battery: N/A"); self.batt.setObjectName("status")
        layout.addWidget(self.batt)
        
        self.proc_view = QPlainTextEdit(); self.proc_view.setObjectName("panel")
        self.proc_view.setReadOnly(True); self.proc_view.setFont(QFont("Cascadia Code",9))
        layout.addWidget(QLabel("Top Processor CPU%:"))
        layout.addWidget(self.proc_view)
        
        t = QTimer(self); t.timeout.connect(self.refresh); t.start(1500); self.refresh()

    def refresh(self):
        cpu = psutil.cpu_percent()
        self.bars["CPU"][0].setText(f"CPU: {cpu:.0f}%"); self.bars["CPU"][1].setValue(int(cpu))
        
        ram = psutil.virtual_memory().percent
        self.bars["RAM"][0].setText(f"RAM: {ram:.0f}%"); self.bars["RAM"][1].setValue(int(ram))
        
        igpu_load = 0
        dgpu_load = 0
        
        # Đọc trực tiếp từ nvidia-smi cho card rời NVIDIA trên Linux/Windows
        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=1
            )
            if res.returncode == 0:
                lines = res.stdout.strip().split("\n")
                if lines and lines[0].strip().isdigit():
                    dgpu_load = float(lines[0].strip())
        except Exception:
            pass

        # Đọc GPU tích hợp trên Linux qua sysfs
        if not IS_WIN:
            try:
                i_path = "/sys/class/drm/card0/device/gpu_busy_percent"
                if os.path.exists(i_path):
                    with open(i_path, "r") as f:
                        igpu_load = float(f.read().strip())
            except Exception:
                pass

        self.bars["GPU 1 (Integrated)"][0].setText(f"GPU 1 (Int): {igpu_load:.0f}%")
        self.bars["GPU 1 (Integrated)"][1].setValue(int(igpu_load))
        
        self.bars["GPU 2 (dGPU)"][0].setText(f"GPU 2 (dGPU): {dgpu_load:.0f}%")
        self.bars["GPU 2 (dGPU)"][1].setValue(int(dgpu_load))

        b = psutil.sensors_battery()
        self.batt.setText(f"Battery: {b.percent:.0f}% ({'Plugged In' if b.power_plugged else 'Not Plugged'})" if b else "Battery: Không có")
        
        procs=[]
        for p in psutil.process_iter(["pid","name","cpu_percent","memory_percent"]):
            try: procs.append(p.info)
            except: pass
        procs.sort(key=lambda x: x.get("cpu_percent") or 0, reverse=True)
        lines=[f"{'PID':>7}  {'CPU%':>6}  {'MEM%':>6}  NAME"]
        for i in procs[:20]:
            lines.append(f"{i['pid']:>7}  {(i['cpu_percent'] or 0):>6.1f}  {(i['memory_percent'] or 0):>6.1f}  {i['name']}")
        self.proc_view.setPlainText("\n".join(lines))

# ─────────────────────────────────────────────
#  AI HELPER
# ─────────────────────────────────────────────
def run_ai(prompt, lang, model, cfg, mode, on_done, on_fail):
    thread = QThread()
    worker = AIWorker(prompt, lang, model, cfg, mode)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.done.connect(on_done); worker.fail.connect(on_fail)
    worker.done.connect(thread.quit); worker.fail.connect(thread.quit)
    thread.start()
    return thread, worker

# ─────────────────────────────────────────────
#  MAIN WINDOW
# ─────────────────────────────────────────────
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.cfg = load_cfg()
        self._ai_refs = []
        self.code_text = ""
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("ArtTools [Vers For Vietnamese]")
        screen = QApplication.primaryScreen().geometry()
        w,h = int(screen.width()*.75), int(screen.height()*.75)
        self.resize(w,h)
        self.move((screen.width()-w)//2,(screen.height()-h)//2)

        root = QHBoxLayout(self)
        root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        sidebar = QFrame(); sidebar.setObjectName("sidebar"); sidebar.setFixedWidth(195)
        sl = QVBoxLayout(sidebar); sl.setContentsMargins(10,16,10,16); sl.setSpacing(4)

        brand = QLabel("🎨 ArtTools"); brand.setObjectName("brand")
        sl.addWidget(brand); sl.addSpacing(11)

        pages = [("💬","Code AI"),("▶","Run / Test"),("🔍","Error Check"),
                 ("🗨","Chat Bot"),("📊","Manager"),("❄","Effect"),("🔑","Settings")]
        self._nav = []
        for icon, name in pages:
            b = QPushButton(f"  {icon}  {name}"); b.setObjectName("navBtn"); b.setCheckable(True)
            b.clicked.connect(lambda _,n=name: self._go(n))
            sl.addWidget(b); self._nav.append((name,b))

        sl.addStretch()

        sl.addWidget(QLabel("Type Coding:"))
        self.lang_combo = QComboBox(); self.lang_combo.setObjectName("combo")
        self.lang_combo.addItems(["Python","C++","Lua","Luau"])
        self.lang_combo.setCurrentText(self.cfg.get("language","python"))
        sl.addWidget(self.lang_combo)

        sl.addWidget(QLabel("AI Model:"))
        self.model_combo = QComboBox(); self.model_combo.setObjectName("combo")
        self.model_combo.addItems(["GPT 4 High","Claude","DeepSeek","ChatGPT"])
        saved = self.cfg.get("model","free")
        idx_map = {"free":0,"claude":1,"deepseek":2,"chatgpt":3}
        self.model_combo.setCurrentIndex(idx_map.get(saved,0))
        sl.addWidget(self.model_combo)

        content_frame = QFrame(); content_frame.setObjectName("contentFrame")
        content_frame.setMinimumWidth(0)
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0,0,0,0)

        self.stack = QStackedWidget(); self.stack.setObjectName("stack")

        self.p_code    = self._pg_code()
        self.p_run     = self._pg_run()
        self.p_check   = self._pg_check()
        self.p_chat    = self._pg_chat()
        self.p_task    = self._pg_task()
        self.p_effects = self._pg_effects()
        self.p_settings= self._pg_settings()

        for p in [self.p_code,self.p_run,self.p_check,self.p_chat,
                  self.p_task,self.p_effects,self.p_settings]:
            self.stack.addWidget(p)

        content_layout.addWidget(self.stack)

        root.addWidget(sidebar)
        root.addWidget(content_frame, 1)

        self.canvas = EffectCanvas(content_frame)
        self.canvas.setGeometry(0, 0, content_frame.width(), content_frame.height())
        self.canvas.raise_()
        self.canvas.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.canvas.set_effect(self.cfg.get("effect","none"))

        self.setStyleSheet(CSS)
        self._go("Code AI")

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "canvas"):
            cf = self.canvas.parent()
            if cf: self.canvas.setGeometry(0,0,cf.width(),cf.height())

    def _go(self, name):
        names = ["Code AI","Run / Test","Error Check","Chat Bot","Manager","Effect","Settings"]
        idx = names.index(name)
        self.stack.setCurrentIndex(idx)
        for n,b in self._nav: b.setChecked(n==name)

    def _model(self):
        t = self.model_combo.currentText().lower()
        if "claude" in t: return "claude"
        if "deepseek" in t: return "deepseek"
        if "chatgpt" in t or "openai" in t: return "chatgpt"
        return "free"
        
    def _lang(self):
        return self.lang_combo.currentText().lower()

    def _pg_code(self):
        page = QWidget()
        l = QVBoxLayout(page); l.setContentsMargins(20,20,20,20); l.setSpacing(8)
        l.addWidget(QLabel("💬 Native Coding Python | C++ | Lua | Luau"))
        self.code_out = QPlainTextEdit()
        self.code_out.setObjectName("panel"); self.code_out.setFont(QFont("Cascadia Code",10))
        self.code_out.setPlaceholderText("AI generated code will appear here...")
        row = QHBoxLayout()
        self.code_in = QLineEdit(); self.code_in.setObjectName("lineEdit")
        self.code_in.setPlaceholderText("Enter your prompt, press Enter to send...")
        self.code_in.returnPressed.connect(self._send_code)
        sb = QPushButton("Send"); sb.setObjectName("primaryBtn"); sb.clicked.connect(self._send_code)
        cb = QPushButton("Copy");   cb.setObjectName("secondaryBtn")
        cb.clicked.connect(lambda: (QApplication.clipboard().setText(self.code_out.toPlainText()),
                                     self.code_stat.setText("Copied")))
        row.addWidget(self.code_in); row.addWidget(sb); row.addWidget(cb)
        self.code_stat = QLabel("[Ready ✓]"); self.code_stat.setObjectName("status")
        l.addWidget(self.code_out); l.addLayout(row); l.addWidget(self.code_stat)
        return page

    def _pg_run(self):
        page = QWidget()
        l = QVBoxLayout(page); l.setContentsMargins(20,20,20,20); l.setSpacing(8)
        l.addWidget(QLabel("▶ Run / Test — Test code from the 'Code AI' tab"))
        self.runner = RunnerWidget(lambda: {"language":self._lang(),"text":self.code_out.toPlainText()})
        l.addWidget(self.runner)
        return page

    def _pg_check(self):
        page = QWidget()
        l = QVBoxLayout(page); l.setContentsMargins(20,20,20,20); l.setSpacing(8)
        l.addWidget(QLabel("🔍 Error Check — AI Review code from the 'Code AI' tab"))
        btn = QPushButton("🔍 Start Error Check"); btn.setObjectName("primaryBtn")
        btn.clicked.connect(self._do_check)
        self.check_out = QPlainTextEdit(); self.check_out.setObjectName("panel")
        self.check_out.setReadOnly(True)
        self.check_out.setPlaceholderText("// Error analysis output will appear here...")
        self.check_stat = QLabel("Ready"); self.check_stat.setObjectName("status")
        l.addWidget(btn); l.addWidget(self.check_out); l.addWidget(self.check_stat)
        return page

    def _pg_chat(self):
        page = QWidget()
        l = QVBoxLayout(page); l.setContentsMargins(20,20,20,20); l.setSpacing(8)
        l.addWidget(QLabel("🗨 Chat Bot — Chat with AI Assistant"))
        self.chat_hist = QPlainTextEdit(); self.chat_hist.setObjectName("panel")
        self.chat_hist.setReadOnly(True); self.chat_hist.setFont(QFont("Segoe UI",10))
        row = QHBoxLayout()
        self.chat_in = QLineEdit(); self.chat_in.setObjectName("lineEdit")
        self.chat_in.setPlaceholderText("Type a message, press Enter to send...")
        self.chat_in.returnPressed.connect(self._send_chat)
        sb = QPushButton("Send"); sb.setObjectName("primaryBtn"); sb.clicked.connect(self._send_chat)
        row.addWidget(self.chat_in); row.addWidget(sb)
        self.chat_stat = QLabel("Ready"); self.chat_stat.setObjectName("status")
        l.addWidget(self.chat_hist); l.addLayout(row); l.addWidget(self.chat_stat)
        return page

    def _pg_task(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(20,20,20,20)
        l.addWidget(QLabel("📊 System Manager"))
        l.addWidget(TaskWidget())
        return page

    def _pg_effects(self):
        page = QWidget(); l = QVBoxLayout(page); l.setContentsMargins(20,20,20,20); l.setSpacing(12)
        l.addWidget(QLabel("❄ Background Visual Effects"))
        row = QHBoxLayout(); row.setSpacing(10)
        self._eff_btns = {}
        for key,label in [("none","Off"),("snow","❄ Falling Snow"),("rain","🌧 Raining"),("leaves","🍃 Falling Leaves")]:
            b = QPushButton(label); b.setObjectName("effBtn"); b.setCheckable(True)
            b.clicked.connect(lambda _,k=key: self._set_eff(k))
            row.addWidget(b); self._eff_btns[key]=b
        cur = self.cfg.get("effect","none")
        if cur in self._eff_btns: self._eff_btns[cur].setChecked(True)
        l.addLayout(row); l.addStretch()
        return page

    def _pg_settings(self):
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)

        # Sử dụng QScrollArea để bọc toàn bộ nội dung trong trang cài đặt giúp cuộn được mượt mà
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

        scroll_content = QWidget()
        l = QVBoxLayout(scroll_content)
        l.setContentsMargins(20, 20, 20, 20)
        l.setSpacing(8)

        l.addWidget(QLabel("🔑 Settings — API Keys"))

        l.addWidget(QLabel("Claude API Key:"))
        self.key_in = QLineEdit(self.cfg.get("claude_key",""))
        self.key_in.setObjectName("lineEdit"); self.key_in.setEchoMode(QLineEdit.EchoMode.Password)
        l.addWidget(self.key_in)

        l.addWidget(QLabel("DeepSeek API Key:"))
        self.deepseek_key_in = QLineEdit(self.cfg.get("deepseek_key",""))
        self.deepseek_key_in.setObjectName("lineEdit"); self.deepseek_key_in.setEchoMode(QLineEdit.EchoMode.Password)
        l.addWidget(self.deepseek_key_in)

        l.addWidget(QLabel("OpenAI API Key (ChatGPT):"))
        self.openai_key_in = QLineEdit(self.cfg.get("openai_key",""))
        self.openai_key_in.setObjectName("lineEdit"); self.openai_key_in.setEchoMode(QLineEdit.EchoMode.Password)
        l.addWidget(self.openai_key_in)

        sv = QPushButton("💾 Save All"); sv.setObjectName("primaryBtn"); sv.clicked.connect(self._save_settings)
        self.cfg_stat = QLabel(""); self.cfg_stat.setObjectName("status"); self.cfg_stat.setWordWrap(True)
        
        self.note_box = QPlainTextEdit()
        self.note_box.setObjectName("note")
        self.note_box.setFont(QFont("Cascadia Code", 8))
        self.note_box.setReadOnly(True)
        self.note_box.setFixedHeight(320)  # Cố định chiều cao ô chứa mèo ở mức hợp lý (320px)
        self.note_box.setPlainText(
            "ArtTools - Vers For Vietnamese\n"
            "⠀⠀⠀⠀⢠⡶⠚⢷⣤⡀⠀⠀⠀⠀⠀⣲⡶⠛⠻⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
            "⠀⠀⠀⢠⡿⠁⠀⠀⠙⣷⣄⠀⢀⣴⡟⠁⠀⠀⢷⢹⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
            "⠀⠀⠀⣾⠃⠀⠠⠶⠚⠛⠛⠛⠛⠋⠀⠀⣀⡀⢸⠈⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
            "⠀⠀⢸⣏⡔⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠚⠉⠉⣿⠀⢹⠀⠀⠀⠀⠀⠀⠀⠀⠀\n"
            "⠀⠀⢾⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀\n"
            "⠀⢠⣿⢠⣶⡆⠀⠀⠀⠀⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀\n"
            "⢒⡾⠁⠘⠟⠁⠀⠀⠀⠀⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀\n"
            "⠉c⠀⠀⠀⠀⠃⠀⠀⠀⠈⠉⠠⣍⠀⠀⠀⠀⠀⠀⣸⡇⢀⣤⠶⠛⠛⠻⢦⣄\n"
            "⠀⠸⣧⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⡟⣴⠟⠁⠀⠀⠀⠀⠀⢻\n"
            "⠀⠀⠀⠛⣷⡦⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣤⡴⠞⠋⢠⡟⠀⠀⠀⠀⠀⠀⢀⡾\n"
            "⠀⠀⠀⢰⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠳⣤⡀⢸⠃⠀⠀⠀⠀⢠⡶⠟⠁\n"
            "⠀⠀⠀⣸⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢷⣹⡄⠀⠀⠀⠀⣼⠀⠀⠀\n"
            "⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠈⢿⣇⠀⠀⠀⠀⢹⡄⠀⠀\n"
            "⠀⠀⠀⢸⡀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⡄⠀⠀⠀⠈⣧⠀⠀\n"
            "⠀⠀⠀⢸⡇⠘⡇⠀⠀⠀⠀⠀⠀⠀⣀⠀⠀⠀⠀⠀⠀⢸⣿⠀⠀⠀⠀⢹⡇⠀\n"
            "⠀⠀⠀⢸⡇⠀⠙⠀⠀⠀⠀⠀⢠⠞⠁⠀⠀⠀⠀⠀⠀⠀⣿⠇⠀⠀⠀⢸⡇⠀\n"
            "⠀⠀⠀⢸⡇⠀⢸⡆⠀⠀⠀⠀⣟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠛⠀⠀⠀⠀⣸⠇⠀\n"
            "⠀⠀⠀⢸⣿⠀⠀⡇⠀⠀⠀⠀⣿⡀⠀⠀⠀⠀⠀⠀⠀⢀⡇⠀⠀⢀⣴⡟⠁⠀\n"
            "⠀⠀⠀⠘⠿⠶⢶⢧⣦⣦⡴⢾⣥⣽⣤⣤⣤⣤⣤⣤⡴⣯⡤⠴⠶⠛⠋⠀⠀⠀"
        )
        l.addWidget(sv)
        l.addWidget(self.cfg_stat)
        l.addWidget(self.note_box)
        l.addStretch()

        scroll_area.setWidget(scroll_content)
        page_layout.addWidget(scroll_area)
        return page

    def _send_code(self):
        prompt = self.code_in.text().strip()
        if not prompt: return
        self.code_stat.setText("Sending to AI...")
        self.code_out.setPlainText("Loading Data From Server.........🔃")
        t,w = run_ai(prompt,self._lang(),self._model(),self.cfg,"code",
                     self._on_code_done, lambda e: (self.code_out.setPlainText(f"// Error: {e}"),
                                                     self.code_stat.setText("Error")))
        self._ai_refs = [t,w]

    def _on_code_done(self, text):
        if "```" in text:
            parts = text.split("```")
            for p in parts:
                s = p.strip()
                if s and not s.split("\n")[0].lower() in ("Python","Cpp","C++","Lua ?","Luau ?",""):
                    text = s; break
                elif s:
                    lines = s.split("\n",1)
                    if len(lines)==2: text=lines[1]; break
        self.code_out.setPlainText(text.strip())
        self.code_stat.setText("Success ✓")

    def _do_check(self):
        code = self.code_out.toPlainText().strip()
        if not code: self.check_out.setPlainText("Error: No code found to check."); return
        self.check_stat.setText("Analyzing code...")
        self.check_out.setPlainText("Loading...")
        t,w = run_ai(code,self._lang(),self._model(),self.cfg,"check",
                     lambda r: (self.check_out.setPlainText(r), self.check_stat.setText("Success ✓")),
                     lambda e: (self.check_out.setPlainText(f"// Lỗi: {e}"), self.check_stat.setText("Error")))
        self._ai_refs = [t,w]

    def _send_chat(self):
        msg = self.chat_in.text().strip()
        if not msg: return
        self.chat_hist.appendPlainText(f"You: {msg}"); self.chat_in.clear()
        self.chat_stat.setText("Sending To AI...")
        t,w = run_ai(msg,self._lang(),self._model(),self.cfg,"chat",
                     lambda r: (self.chat_hist.appendPlainText(f"AI: {r}\n"), self.chat_stat.setText("Ready")),
                     lambda e: (self.chat_hist.appendPlainText(f"[Error]: {e}\n"), self.chat_stat.setText("Error")))
        self._ai_refs = [t,w]

    def _set_eff(self, key):
        for k,b in self._eff_btns.items(): b.setChecked(k==key)
        self.cfg["effect"] = key; save_cfg(self.cfg)
        self.canvas.set_effect(key)

    def _save_settings(self):
        self.cfg["claude_key"]   = self.key_in.text().strip()
        self.cfg["deepseek_key"] = self.deepseek_key_in.text().strip()
        self.cfg["openai_key"]   = self.openai_key_in.text().strip()
        ok = save_cfg(self.cfg)
        self.cfg_stat.setText(f"Save Success: {CFG_FILE}" if ok else "Save Error!")

# ─────────────────────────────────────────────
#  STYLESHEET
# ─────────────────────────────────────────────
CSS = """
QWidget          { background:#111113; color:#788cf0; font-size:13px; font-family:'Segoe UI',sans-serif; }
#sidebar         { background:#17171a; border-right:1.5px solid #232329; }
#brand           { color:#788cf0; font-size:16px; font-weight:700; padding:2px 4px; }
#navBtn          { background:transparent; color:#6b7280; border:none; border-radius:12px;
                   padding:10px 12px; text-align:left; font-size:13px; }
#navBtn:hover    { background:#1f1f24; color:#788cf0; }
#navBtn:checked  { background:#1f1f24; color:#788cf0; font-weight:600; border:1.5px solid #788cf0; }
#panel           { background:#17171a; color:#788cf0;
                   border:1.5px solid #272730; border-radius:14px; padding:10px; }
#lineEdit        { background:#17171a; color:#788cf0;
                   border:1.5px solid #272730; border-radius:12px; padding:8px 12px; }
#primaryBtn      { background:#17171a; color:#788cf0; border:1.5px solid #788cf0; border-radius:12px; padding:8px 16px; font-weight:600; }
#primaryBtn:hover{ background:#1f1f24; }
#secondaryBtn    { background:#17171a; color:#788cf0; border:1.5px solid #272730; border-radius:12px; padding:8px 14px; font-weight:600; }
#secondaryBtn:hover{ background:#1f1f24; }
#dangerBtn       { background:#17171a; color:#788cf0; border:1.5px solid #272730; border-radius:12px; padding:8px 14px; font-weight:600; }
#dangerBtn:hover { background:#1f1f24; }
#effBtn          { background:#17171a; color:#788cf0; border:1.5px solid #272730;
                   border-radius:14px; padding:10px 18px; font-size:14px; }
#effBtn:checked  { background:#1f1f24; color:#788cf0; border-color:#788cf0; }
#effBtn:hover    { background:#1f1f24; }
#combo           { background:#17171a; color:#788cf0;
                   border:1.5px solid #272730; border-radius:10px; padding:4px 10px; }
#status          { color:#6b7280; font-size:11px; }
#note            { color:#6b7280; font-size:11px; background:#17171a;
                   border:1.5px solid #272730; border-radius:12px; padding:10px; margin-top:6px; }
#bar             { background:#17171a; border:1.5px solid #272730; border-radius:10px; text-align: center; color: #788cf0; font-weight:600; }
#bar::chunk      { background:#788cf0; border-radius:8px; }
QScrollArea      { background: transparent; border: none; }
QScrollBar:vertical   { background:#111113; width:8px; border-radius:4px; }
QScrollBar::handle:vertical{ background:#17171a; border-radius:4px; border:1.5px solid #272730; }
"""

def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
