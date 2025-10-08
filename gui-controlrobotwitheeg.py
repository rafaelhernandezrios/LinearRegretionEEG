import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import serial
import serial.tools.list_ports
import threading
import time
import queue
import pandas as pd
from pylsl import StreamInlet, resolve_byprop
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import typing
import pydobot


class VRehabGUI:
    """Refactored dark UI while preserving public methods and behavior.

    Visual-only refactor:
    - New dark theme and layout (header + sidebar + two main cards)
    - Helper style system and widget factory funcs
    - Chips, primary/ghost buttons, flat progress bar, threshold slider
    - All existing methods and behavior intact; long ops on threads; .after for UI
    - Logging preserved; ML workflow unchanged; serial write '1' unchanged
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("VRehab - Mind-Controlled Robot")
        self.root.minsize(1200, 800)

        # Color system (spec)
        self.colors = {
            "BG": "#0b0f19",
            "CARD": "#111827",
            "CARD_ALT": "#0f172a",
            "TEXT": "#e5e7eb",
            "MUTED": "#9ca3af",
            "ACCENT": "#8b5cf6",
            "ACCENT2": "#22d3ee",
            "OK": "#10b981",
            "WARN": "#f59e0b",
            "ERR": "#ef4444",
            "BORDER": "#1f2937",
            "CHIP": "#1e293b",
            "TRACK": "#0b1220",
        }

        # State
        self.robot = None
        self.brain_inlet = None
        self.lr_model = None
        self.sc_x = None
        self.is_training = False
        self.is_controlling = False
        self.threshold_var = tk.IntVar(value=700)

        # UI registry
        self.ui = {}

        # Set theme and global styles
        self.set_dark_theme()

        # Build UI
        self.build_layout()

        # Initial data
        self.update_com_ports()
        self.check_connections()

        # Welcome logs
        self.log_message("App started")
        self.log_message("Connect Robot and EEG to begin mind control")

    # =============== THEME AND FACTORIES ===============
    def set_dark_theme(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        self.root.configure(bg=self.colors["BG"]) 

        # Base
        style.configure("TFrame", background=self.colors["BG"]) 
        style.configure("TLabel", background=self.colors["BG"], foreground=self.colors["TEXT"], font=("Segoe UI", 11))
        style.configure("TLabelframe", background=self.colors["CARD"], foreground=self.colors["TEXT"], borderwidth=1, relief="solid")
        style.configure("TLabelframe.Label", background=self.colors["CARD"], foreground=self.colors["TEXT"], font=("Segoe UI", 12, "bold"))

        # Buttons
        style.configure("Primary.TButton", background=self.colors["ACCENT"], foreground="#ffffff", borderwidth=0, focusthickness=0, padding=(12, 8), font=("Segoe UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", self.colors["ACCENT"]), ("pressed", self.colors["ACCENT"])])
        style.configure("Ghost.TButton", background=self.colors["BG"], foreground=self.colors["ACCENT"], bordercolor=self.colors["ACCENT"], relief="solid", borderwidth=1, padding=(12, 8), font=("Segoe UI", 10))
        style.map("Ghost.TButton", background=[("active", self.colors["BG"])])

        # Inputs
        style.configure("TCombobox", fieldbackground=self.colors["CARD"], background=self.colors["CARD"], foreground=self.colors["TEXT"], arrowcolor=self.colors["TEXT"], bordercolor=self.colors["BORDER"], lightcolor=self.colors["CARD"], darkcolor=self.colors["CARD"], relief="solid")

        # Progressbar
        style.configure("TProgressbar", troughcolor=self.colors["TRACK"], background=self.colors["ACCENT"], bordercolor=self.colors["TRACK"], lightcolor=self.colors["ACCENT"], darkcolor=self.colors["ACCENT"], thickness=10)

    def make_card(self, parent: tk.Widget, title: str, subtitle: typing.Optional[str] = None) -> dict:
        """Create a card with rounded-looking feel via frame layering. Returns dict with frame and header labels."""
        outer = tk.Frame(parent, bg=self.colors["CARD"], highlightthickness=1, highlightbackground=self.colors["BORDER"])
        container = tk.Frame(outer, bg=self.colors["CARD"]) 
        container.pack(fill="both", expand=True, padx=16, pady=16)
        title_lbl = tk.Label(container, text=title, bg=self.colors["CARD"], fg=self.colors["TEXT"], font=("Segoe UI", 16, "bold"))
        title_lbl.grid(row=0, column=0, sticky="w")
        sub_lbl = None
        if subtitle:
            sub_lbl = tk.Label(container, text=subtitle, bg=self.colors["CARD"], fg=self.colors["MUTED"], font=("Segoe UI", 10))
            sub_lbl.grid(row=1, column=0, sticky="w", pady=(4, 0))
        return {"frame": outer, "container": container, "title": title_lbl, "subtitle": sub_lbl}

    def make_header(self, parent: tk.Widget) -> dict:
        hdr = tk.Frame(parent, bg=self.colors["CARD_ALT"], highlightthickness=1, highlightbackground=self.colors["BORDER"])
        inner = tk.Frame(hdr, bg=self.colors["CARD_ALT"]) 
        inner.pack(fill="x", expand=True, padx=16, pady=16)
        left = tk.Frame(inner, bg=self.colors["CARD_ALT"]) 
        right = tk.Frame(inner, bg=self.colors["CARD_ALT"]) 
        left.grid(row=0, column=0, sticky="w")
        right.grid(row=0, column=1, sticky="e")
        inner.columnconfigure(0, weight=1)
        inner.columnconfigure(1, weight=0)
        title = tk.Label(left, text="VRehab — Mind-Controlled Robot", bg=self.colors["CARD_ALT"], fg=self.colors["TEXT"], font=("Segoe UI", 18, "bold"))
        title.pack(anchor="w")
        subtitle = tk.Label(left, text="Brain-computer interface for robot control", bg=self.colors["CARD_ALT"], fg=self.colors["MUTED"], font=("Segoe UI", 10))
        subtitle.pack(anchor="w", pady=(4, 0))
        # Header chips
        chips_frame = tk.Frame(right, bg=self.colors["CARD_ALT"]) 
        chips_frame.pack(anchor="e")
        eeg_chip = self.make_chip(chips_frame, text="EEG: Disconnected")
        ar_chip = self.make_chip(chips_frame, text="Robot: Disconnected")
        eeg_chip["frame"].pack(side="left", padx=(0, 8))
        ar_chip["frame"].pack(side="left")
        return {"frame": hdr, "eeg_chip": eeg_chip, "arduino_chip": ar_chip}

    def make_chip(self, parent: tk.Widget, text: str) -> dict:
        chip = tk.Frame(parent, bg=self.colors["CHIP"], highlightthickness=1, highlightbackground=self.colors["BORDER"])
        dot = tk.Canvas(chip, width=10, height=10, bg=self.colors["CHIP"], highlightthickness=0)
        dot_id = dot.create_oval(2, 2, 10, 10, fill=self.colors["ERR"], outline=self.colors["ERR"])
        lbl = tk.Label(chip, text=text, bg=self.colors["CHIP"], fg=self.colors["TEXT"], font=("Segoe UI", 10))
        dot.pack(side="left", padx=(8, 6), pady=6)
        lbl.pack(side="left", padx=(0, 10))

        def set_status(ok: bool, text_value: typing.Optional[str] = None):
            color = self.colors["OK"] if ok else self.colors["ERR"]
            dot.itemconfig(dot_id, fill=color, outline=color)
            if text_value is not None:
                lbl.configure(text=text_value)

        return {"frame": chip, "dot": dot, "dot_id": dot_id, "label": lbl, "set_status": set_status}

    def make_button_primary(self, parent: tk.Widget, text: str, command) -> ttk.Button:
        return ttk.Button(parent, text=text, command=command, style="Primary.TButton")

    def make_button_ghost(self, parent: tk.Widget, text: str, command) -> ttk.Button:
        return ttk.Button(parent, text=text, command=command, style="Ghost.TButton")

    # =============== LAYOUT ===============
    def build_layout(self) -> None:
        root_wrap = tk.Frame(self.root, bg=self.colors["BG"]) 
        root_wrap.pack(fill="both", expand=True)
        root_wrap.grid_columnconfigure(0, weight=1)
        root_wrap.grid_rowconfigure(2, weight=1)

        # Header
        header = self.make_header(root_wrap)
        header["frame"].grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        self.ui["hdr_eeg_chip"] = header["eeg_chip"]
        self.ui["hdr_arduino_chip"] = header["arduino_chip"]

        # Main content area: two columns (sidebar + content)
        main = tk.Frame(root_wrap, bg=self.colors["BG"]) 
        main.grid(row=2, column=0, sticky="nsew", padx=16, pady=(8, 16))
        main.grid_columnconfigure(0, minsize=340)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        # Sidebar: Setup & Status
        sidebar_card = self.make_card(main, title="Setup & Status")
        sidebar_card["frame"].grid(row=0, column=0, sticky="nsw", padx=(0, 16))
        side = sidebar_card["container"]
        side.grid_columnconfigure(0, weight=1)

        # Robot section
        ar_frame = tk.Frame(side, bg=self.colors["CARD"]) 
        ar_frame.grid(row=0, column=0, sticky="ew", pady=(8, 8))
        tk.Label(ar_frame, text="Robot", bg=self.colors["CARD"], fg=self.colors["TEXT"], font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        grid = tk.Frame(ar_frame, bg=self.colors["CARD"]) 
        grid.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        grid.grid_columnconfigure(1, weight=1)
        tk.Label(grid, text="Port", bg=self.colors["CARD"], fg=self.colors["MUTED"], font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.com_var = tk.StringVar()
        self.ui["com_combo"] = ttk.Combobox(grid, textvariable=self.com_var, width=18)
        self.ui["com_combo"].grid(row=0, column=1, sticky="ew")
        tk.Label(grid, text="Baud", bg=self.colors["CARD"], fg=self.colors["MUTED"], font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.baudrate_var = tk.StringVar(value="115200")
        self.ui["baud_combo"] = ttk.Combobox(grid, textvariable=self.baudrate_var, width=18, values=["9600", "19200", "38400", "57600", "115200"]) 
        self.ui["baud_combo"].grid(row=1, column=1, sticky="ew", pady=(8, 0))
        btns = tk.Frame(ar_frame, bg=self.colors["CARD"]) 
        btns.grid(row=2, column=0, sticky="w", pady=(12, 0))
        self.ui["btn_connect_arduino"] = self.make_button_primary(btns, "Connect Robot", self.toggle_robot)
        self.ui["btn_connect_arduino"].grid(row=0, column=0, padx=(0, 8))
        self.ui["btn_refresh_ports"] = self.make_button_ghost(btns, "Refresh", self.update_com_ports)
        self.ui["btn_refresh_ports"].grid(row=0, column=1)

        # EEG section
        eeg_frame = tk.Frame(side, bg=self.colors["CARD"]) 
        eeg_frame.grid(row=1, column=0, sticky="ew", pady=(16, 8))
        tk.Label(eeg_frame, text="EEG via LSL", bg=self.colors["CARD"], fg=self.colors["TEXT"], font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        eeg_btns = tk.Frame(eeg_frame, bg=self.colors["CARD"]) 
        eeg_btns.grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.ui["btn_connect_eeg"] = self.make_button_primary(eeg_btns, "Connect EEG", self.toggle_eeg)
        self.ui["btn_connect_eeg"].grid(row=0, column=0, padx=(0, 8))
        self.ui["btn_search_streams"] = self.make_button_ghost(eeg_btns, "Search Streams", self.search_eeg_streams)
        self.ui["btn_search_streams"].grid(row=0, column=1)

        # Connection Status sub-card
        status_card = self.make_card(side, title="Connection Status")
        status_card["frame"].grid(row=2, column=0, sticky="ew", pady=(16, 8))
        stc = status_card["container"]
        row1 = tk.Frame(stc, bg=self.colors["CARD"]) 
        row2 = tk.Frame(stc, bg=self.colors["CARD"]) 
        row1.grid(row=0, column=0, sticky="w", pady=(8, 4))
        row2.grid(row=1, column=0, sticky="w", pady=(4, 8))
        self.ui["chip_arduino"] = self.make_chip(row1, "Robot: Disconnected")
        self.ui["chip_arduino"]["frame"].pack(side="left")
        self.ui["chip_eeg"] = self.make_chip(row2, "EEG: Disconnected")
        self.ui["chip_eeg"]["frame"].pack(side="left")

        # Quick tips sub-card
        tips_card = self.make_card(side, title="Quick Tips")
        tips_card["frame"].grid(row=3, column=0, sticky="ew", pady=(8, 8))
        tips = tips_card["container"]
        tk.Label(tips, text="- Start EEG software before connecting", bg=self.colors["CARD"], fg=self.colors["MUTED"], font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w")
        tk.Label(tips, text="- Choose correct COM port for robot", bg=self.colors["CARD"], fg=self.colors["MUTED"], font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", pady=(4, 0))
        tk.Label(tips, text="- Train: 30s relax, 30s imagine", bg=self.colors["CARD"], fg=self.colors["MUTED"], font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w", pady=(4, 0))

        # System log sub-card
        log_card = self.make_card(side, title="System Log")
        log_card["frame"].grid(row=4, column=0, sticky="nsew", pady=(8, 0))
        side.grid_rowconfigure(4, weight=1)
        log_container = log_card["container"]
        log_container.grid_columnconfigure(0, weight=1)
        log_container.grid_rowconfigure(0, weight=1)
        self.log_text = scrolledtext.ScrolledText(log_container, height=12, bg=self.colors["CARD"], fg=self.colors["TEXT"], insertbackground=self.colors["TEXT"], selectbackground=self.colors["ACCENT"], relief="flat", borderwidth=0, font=("Consolas", 10))
        self.log_text.grid(row=0, column=0, sticky="nsew")

        # Right column content (stacked cards)
        right = tk.Frame(main, bg=self.colors["BG"]) 
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(3, weight=1)

        # Training card
        training_card = self.make_card(right, title="Training", subtitle="Steps: 1) Relax 30s -> 2) Imagine 30s -> 3) Train model")
        training_card["frame"].grid(row=0, column=0, sticky="ew")
        tr = training_card["container"]
        tr.grid_columnconfigure(0, weight=1)

        # Buttons row
        tr_btns = tk.Frame(tr, bg=self.colors["CARD"]) 
        tr_btns.grid(row=2, column=0, sticky="w", pady=(12, 0))
        self.ui["btn_start_training"] = self.make_button_primary(tr_btns, "Start Training", self.start_training)
        self.ui["btn_start_training"].grid(row=0, column=0, padx=(0, 8))
        self.ui["btn_stop_training"] = self.make_button_ghost(tr_btns, "Stop", self.stop_training)
        self.ui["btn_stop_training"].grid(row=0, column=1)

        # Progress row
        pr = tk.Frame(tr, bg=self.colors["CARD"]) 
        pr.grid(row=3, column=0, sticky="ew", pady=(16, 0))
        tk.Label(pr, text="Progress", bg=self.colors["CARD"], fg=self.colors["MUTED"], font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.training_progress = ttk.Progressbar(pr, mode="determinate", length=300)
        self.training_progress.grid(row=0, column=1, sticky="ew")
        pr.grid_columnconfigure(1, weight=1)
        self.training_label = tk.Label(tr, text="Ready to start training", bg=self.colors["CARD"], fg=self.colors["TEXT"], font=("Segoe UI", 10))
        self.training_label.grid(row=4, column=0, sticky="w", pady=(8, 0))

        # Training metrics sub-row
        metrics = tk.Frame(tr, bg=self.colors["CARD"]) 
        metrics.grid(row=5, column=0, sticky="ew", pady=(16, 0))
        metrics.grid_columnconfigure(1, weight=1)
        tk.Label(metrics, text="Training Metrics", bg=self.colors["CARD"], fg=self.colors["TEXT"], font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", columnspan=2)
        self.ui["lbl_accuracy"] = tk.Label(metrics, text="Accuracy: —", bg=self.colors["CARD"], fg=self.colors["MUTED"], font=("Segoe UI", 10))
        self.ui["lbl_accuracy"].grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.ui["lbl_samples"] = tk.Label(metrics, text="Samples: —", bg=self.colors["CARD"], fg=self.colors["MUTED"], font=("Segoe UI", 10))
        self.ui["lbl_samples"].grid(row=1, column=1, sticky="w", pady=(6, 0))
        self.ui["metrics_placeholder"] = tk.Frame(metrics, bg=self.colors["CARD"], height=80, highlightthickness=1, highlightbackground=self.colors["BORDER"]) 
        self.ui["metrics_placeholder"].grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        # Control card
        control_card = self.make_card(right, title="Control")
        control_card["frame"].grid(row=2, column=0, sticky="nsew", pady=(16, 0))
        ctrl = control_card["container"]
        ctrl.grid_columnconfigure(0, weight=1)
        ctrl.grid_columnconfigure(1, weight=1)

        # Control buttons row (start/stop)
        ctrl_btns = tk.Frame(ctrl, bg=self.colors["CARD"])  
        ctrl_btns.grid(row=2, column=0, columnspan=2, sticky="w", pady=(8, 8))
        self.ui["btn_start_control"] = self.make_button_primary(ctrl_btns, "Start Control", self.start_control)
        self.ui["btn_start_control"].grid(row=0, column=0, padx=(0, 8))
        self.ui["btn_stop_control"] = self.make_button_ghost(ctrl_btns, "Stop", self.stop_control)
        self.ui["btn_stop_control"].grid(row=0, column=1)
        
        # Robot test button row
        robot_btns = tk.Frame(ctrl, bg=self.colors["CARD"])  
        robot_btns.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 8))
        self.ui["btn_test_robot"] = self.make_button_primary(robot_btns, "🤖 Test Robot Movement", self.test_robot_movement)
        self.ui["btn_test_robot"].grid(row=0, column=0, padx=(0, 8))
        self.ui["btn_robot_home"] = self.make_button_ghost(robot_btns, "🏠 Robot Home", self.robot_home)
        self.ui["btn_robot_home"].grid(row=0, column=1)

        # Left: Movement Detection
        md_card = self.make_card(ctrl, title="Movement Detection")
        md_card["frame"].grid(row=4, column=0, sticky="nsew", padx=(0, 8))
        md = md_card["container"]
        # Start content at row=2 to avoid overlapping the card title/subtitle
        tk.Label(md, text="Counter", bg=self.colors["CARD"], fg=self.colors["MUTED"], font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w")
        self.ui["counter_value"] = tk.Label(md, text="0", bg=self.colors["CARD"], fg=self.colors["TEXT"], font=("Segoe UI", 24, "bold"))
        self.ui["counter_value"].grid(row=3, column=0, sticky="w", pady=(4, 0))
        status_row = tk.Frame(md, bg=self.colors["CARD"]) 
        status_row.grid(row=4, column=0, sticky="w", pady=(10, 0))
        self.ui["status_light"] = tk.Canvas(status_row, width=14, height=14, bg=self.colors["CARD"], highlightthickness=0)
        self.ui["status_light_id"] = self.ui["status_light"].create_oval(2, 2, 12, 12, fill=self.colors["MUTED"], outline=self.colors["MUTED"])
        self.ui["status_light"].pack(side="left")
        self.ui["status_text"] = tk.Label(status_row, text="Idle", bg=self.colors["CARD"], fg=self.colors["MUTED"], font=("Segoe UI", 10))
        self.ui["status_text"].pack(side="left", padx=(6, 0))
        self.ui["md_placeholder"] = tk.Frame(md, bg=self.colors["CARD"], height=80, highlightthickness=1, highlightbackground=self.colors["BORDER"]) 
        self.ui["md_placeholder"].grid(row=5, column=0, sticky="ew", pady=(12, 0))

        # Right: Action & Threshold
        at_card = self.make_card(ctrl, title="Action & Threshold")
        at_card["frame"].grid(row=4, column=1, sticky="nsew", padx=(8, 0))
        at = at_card["container"]
        # Start content at row=2 to avoid overlapping the card title/subtitle
        tk.Label(at, text="Threshold", bg=self.colors["CARD"], fg=self.colors["MUTED"], font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w")
        self.ui["threshold_slider"] = ttk.Scale(at, from_=100, to=2000, orient="horizontal", command=lambda v: self.update_threshold_pill(int(float(v))))
        self.ui["threshold_slider"].set(self.threshold_var.get())
        self.ui["threshold_slider"].grid(row=3, column=0, sticky="ew", pady=(6, 0))
        at.grid_columnconfigure(0, weight=1)
        pill = tk.Frame(at, bg=self.colors["CHIP"], highlightthickness=1, highlightbackground=self.colors["BORDER"]) 
        pill.grid(row=3, column=1, sticky="w", padx=(8, 0))
        self.ui["threshold_pill"] = tk.Label(pill, text=str(self.threshold_var.get()), bg=self.colors["CHIP"], fg=self.colors["TEXT"], font=("Segoe UI", 10))
        self.ui["threshold_pill"].pack(padx=10, pady=4)
        actions = tk.Frame(at, bg=self.colors["CARD"]) 
        actions.grid(row=4, column=0, columnspan=2, sticky="w", pady=(12, 0))
        self.ui["chip_send"] = self.make_chip(actions, "Send Arduino: '1'")
        self.ui["chip_send"]["frame"].pack(side="left", padx=(0, 8))
        self.ui["chip_reset"] = self.make_chip(actions, "Reset counter & log action")
        self.ui["chip_reset"]["frame"].pack(side="left")

    # =============== UTILITIES ===============
    def log_message(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def update_threshold_pill(self, value: int) -> None:
        self.threshold_var.set(value)
        self.ui["threshold_pill"].configure(text=str(value))

    def update_com_ports(self) -> None:
        ports = serial.tools.list_ports.comports()
        values = [p.device for p in ports]
        self.ui["com_combo"]["values"] = values
        if values and not self.ui["com_combo"].get():
            self.ui["com_combo"].set(values[0])

    def check_connections(self) -> None:
        # Robot
        robot_connected = bool(self.robot)
        # EEG
        eeg_connected = bool(self.brain_inlet)

        # Sidebar chips
        self.ui["chip_arduino"]["set_status"](robot_connected, f"Robot: {'Connected' if robot_connected else 'Disconnected'}")
        self.ui["chip_eeg"]["set_status"](eeg_connected, f"EEG: {'Connected' if eeg_connected else 'Disconnected'}")
        # Header chips
        self.ui["hdr_arduino_chip"]["set_status"](robot_connected, f"Robot: {'Connected' if robot_connected else 'Disconnected'}")
        self.ui["hdr_eeg_chip"]["set_status"](eeg_connected, f"EEG: {'Connected' if eeg_connected else 'Disconnected'}")

        # Enable training only if both connected
        if robot_connected and eeg_connected:
            self.ui["btn_start_training"].configure(state="normal")
        else:
            self.ui["btn_start_training"].configure(state="disabled")

        # Enable control if model trained and EEG connected
        if self.lr_model and eeg_connected:
            self.ui["btn_start_control"].configure(state="normal")
        else:
            self.ui["btn_start_control"].configure(state="disabled")

        # Schedule next check
        self.root.after(1000, self.check_connections)

    # =============== PUBLIC METHODS (UNCHANGED NAMES) ===============
    def toggle_robot(self) -> None:
        if not self.robot:
            try:
                port = self.ui["com_combo"].get()
                self.robot = pydobot.Dobot(port=port, verbose=True)
                self.ui["btn_connect_arduino"].configure(text="Disconnect Robot")
                self.log_message(f"Robot connected to {port}")
            except Exception as e:
                messagebox.showerror("Connection Error", f"Failed to connect to Robot: {e}")
                self.log_message(f"Robot connection failed: {e}")
        else:
            try:
                self.robot.close()
                self.robot = None
                self.ui["btn_connect_arduino"].configure(text="Connect Robot")
                self.log_message("Robot disconnected")
            except Exception as e:
                self.log_message(f"Error disconnecting Robot: {e}")

    def execute_robot_movement(self) -> None:
        """Ejecuta una secuencia de movimientos del robot para control mental"""
        if not self.robot:
            self.log_message("Robot not connected")
            return
        
        try:
            # Obtener posición actual
            (x, y, z, r, j1, j2, j3, j4) = self.robot.pose()
            self.log_message(f"Robot position: x:{x:.1f} y:{y:.1f} z:{z:.1f}")
            
            # Guardar posición inicial
            start_x, start_y, start_z, start_r = x, y, z, r
            
            # Trayectoria SIMPLE y SEGURA
            self.log_message("🎯 Starting safe movement sequence...")
            
            # Secuencia de movimientos seguros
            movements = [
                ("Moving forward", start_x, start_y + 15, start_z, start_r),
                ("Moving right", start_x + 15, start_y + 15, start_z, start_r),
                ("Moving up", start_x + 15, start_y + 15, start_z + 10, start_r),
                ("Moving back", start_x, start_y + 15, start_z + 10, start_r),
                ("Moving left", start_x - 15, start_y + 15, start_z + 10, start_r),
                ("Moving down", start_x - 15, start_y + 15, start_z, start_r),
                ("Moving forward again", start_x - 15, start_y, start_z, start_r),
                ("Returning to start", start_x, start_y, start_z, start_r)
            ]
            
            # Ejecutar movimientos uno por uno
            for i, (description, new_x, new_y, new_z, new_r) in enumerate(movements):
                progress = ((i + 1) / len(movements)) * 100
                self.log_message(f"🔄 Movement {i+1}/{len(movements)} ({progress:.0f}%): {description}")
                
                # Usar move_to para movimientos seguros
                self.robot.move_to(new_x, new_y, new_z, new_r, wait=True)
                time.sleep(0.5)  # Pausa entre movimientos
            
            self.log_message("🎉 Movement sequence completed!")
            
        except Exception as e:
            self.log_message(f"❌ Robot movement error: {e}")
            # En caso de error, intentar regresar a posición segura
            try:
                self.log_message("🚨 Attempting to return to safe position...")
                self.robot.move_to(start_x, start_y, start_z + 20, start_r, wait=True)
            except:
                self.log_message("❌ Could not return to safe position")

    def test_robot_movement(self) -> None:
        """Ejecuta la rutina del robot manualmente para pruebas"""
        if not self.robot:
            messagebox.showerror("Error", "Please connect Robot first")
            return
        
        # Deshabilitar botón temporalmente
        self.ui["btn_test_robot"].configure(state="disabled", text="🤖 Testing...")
        
        try:
            # Ejecutar en hilo separado para no bloquear la UI
            test_thread = threading.Thread(target=self.execute_robot_movement)
            test_thread.daemon = True
            test_thread.start()
            
            # Rehabilitar botón después de un tiempo
            self.root.after(10000, lambda: self.ui["btn_test_robot"].configure(state="normal", text="🤖 Test Robot Movement"))
            
        except Exception as e:
            self.log_message(f"❌ Test robot error: {e}")
            self.ui["btn_test_robot"].configure(state="normal", text="🤖 Test Robot Movement")

    def robot_home(self) -> None:
        """Mueve el robot a posición home SEGURA"""
        if not self.robot:
            messagebox.showerror("Error", "Please connect Robot first")
            return
        
        try:
            self.log_message("🏠 Moving robot to safe home position...")
            # Obtener posición actual
            (x, y, z, r, j1, j2, j3, j4) = self.robot.pose()
            self.log_message(f"Current position: x:{x:.1f} y:{y:.1f} z:{z:.1f}")
            
            # Movimiento SEGURO paso a paso
            # 1. Primero subir para evitar choques
            safe_z = max(z + 20, 80)  # Subir al menos 20mm o llegar a 80mm
            self.log_message(f"🔼 Moving up to safe height: {safe_z:.1f}mm")
            self.robot.move_to(x, y, safe_z, r, wait=True)
            time.sleep(1)
            
            # 2. Luego mover horizontalmente (más seguro)
            self.log_message("↔️ Moving to center horizontally...")
            self.robot.move_to(0, 0, safe_z, r, wait=True)
            time.sleep(1)
            
            # 3. Finalmente bajar a altura home
            home_z = 60  # Altura home segura
            self.log_message(f"🔽 Moving to home height: {home_z:.1f}mm")
            self.robot.move_to(0, 0, home_z, 0, wait=True)
            
            self.log_message("✅ Robot safely at home position")
        except Exception as e:
            self.log_message(f"❌ Robot home error: {e}")
            # En caso de error, intentar posición de emergencia
            try:
                self.log_message("🚨 Attempting emergency safe position...")
                self.robot.move_to(0, 0, 100, 0, wait=True)  # Posición muy alta y segura
            except:
                self.log_message("❌ Emergency positioning also failed")

    def toggle_eeg(self) -> None:
        if not self.brain_inlet:
            try:
                self.log_message("Looking for EEG stream...")
                streams = resolve_byprop("name", "AURA_Power", timeout=2)
                if streams:
                    self.brain_inlet = StreamInlet(streams[0])
                    self.brain_inlet.open_stream()
                    self.ui["btn_connect_eeg"].configure(text="Disconnect EEG")
                    self.log_message("EEG connected")
                else:
                    self.log_message("EEG stream not found (AURA_Power)")
                    messagebox.showwarning("EEG Stream", "No EEG stream named 'AURA_Power' found.")
            except Exception as e:
                self.log_message(f"EEG connection failed: {e}")
                messagebox.showerror("EEG Connection Error", str(e))
        else:
            try:
                self.brain_inlet.close_stream()
                self.brain_inlet = None
                self.ui["btn_connect_eeg"].configure(text="Connect EEG")
                self.log_message("EEG disconnected")
            except Exception as e:
                self.log_message(f"Error disconnecting EEG: {e}")

    def search_eeg_streams(self) -> None:
        try:
            self.log_message("Searching for EEG streams...")
            streams = resolve_byprop("type", "EEG", timeout=2)
            if streams:
                self.log_message(f"Found {len(streams)} EEG stream(s)")
                for i, st in enumerate(streams):
                    info = st.info()
                    self.log_message(f"  {i+1}. {info.name()} ({info.type()}) ch={info.channel_count()}")
            else:
                self.log_message("No EEG streams found")
        except Exception as e:
            self.log_message(f"Search error: {e}")

    def start_training(self) -> None:
        if not self.brain_inlet:
            messagebox.showerror("Error", "Please connect to EEG stream first")
            return
        if not self.robot:
            messagebox.showerror("Error", "Please connect Robot first")
            return
        if self.is_training:
            return
        self.is_training = True
        self.ui["btn_start_training"].configure(state="disabled")
        self.ui["btn_stop_training"].configure(state="normal")
        t = threading.Thread(target=self.training_process, daemon=True)
        t.start()

    def stop_training(self) -> None:
        self.is_training = False
        self.training_label.configure(text="Training stopped")
        self.ui["btn_stop_training"].configure(state="disabled")
        self.ui["btn_start_training"].configure(state="normal")

    def training_process(self) -> None:
        try:
            self.root.after(0, lambda: self.training_label.configure(text="Relax 30s"))
            self.root.after(0, lambda: self.training_progress.configure(value=0))
            rest = self.collect_training_data(30, "rest")
            if not self.is_training:
                return
            self.root.after(0, lambda: self.training_label.configure(text="Imagine 30s"))
            self.root.after(0, lambda: self.training_progress.configure(value=50))
            move = self.collect_training_data(30, "move")
            if not self.is_training:
                return
            self.root.after(0, lambda: self.training_label.configure(text="Training model..."))
            self.root.after(0, lambda: self.training_progress.configure(value=75))
            self.train_model(rest, move)
            self.root.after(0, lambda: self.training_label.configure(text="Training completed"))
            self.root.after(0, lambda: self.training_progress.configure(value=100))
            self.root.after(0, lambda: self.ui["btn_start_training"].configure(state="normal"))
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Training error: {e}"))
        finally:
            self.is_training = False
            self.root.after(0, lambda: self.ui["btn_stop_training"].configure(state="disabled"))

    def collect_training_data(self, duration: int, data_type: str) -> pd.DataFrame:
        data = pd.DataFrame()
        start = time.time()
        while time.time() - start < duration and self.is_training:
            try:
                sample, ts = self.brain_inlet.pull_sample()
                if sample:
                    data = pd.concat([data, pd.DataFrame(sample).T])
                # Progress update
                elapsed = time.time() - start
                base = 0 if data_type == "rest" else 50
                prog = base + (elapsed / duration) * 50
                self.root.after(0, lambda v=prog: self.training_progress.configure(value=v))
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Collect error: {e}"))
        data["Event"] = 0 if data_type == "rest" else 1
        # Update samples label
        try:
            self.root.after(0, lambda: self.ui["lbl_samples"].configure(text=f"Samples: {len(data)}"))
        except Exception:
            pass
        return data

    def train_model(self, rest_df: pd.DataFrame, move_df: pd.DataFrame) -> None:
        try:
            selected = pd.concat([rest_df, move_df])
            selected.to_csv("full_data_personas_nuevas.csv", index=False)
            X = selected.iloc[1:, :-1].values
            y = selected.iloc[1:, -1].values
            self.sc_x = StandardScaler()
            Xs = self.sc_x.fit_transform(X)
            X_train, X_test, y_train, y_test = train_test_split(Xs, y, test_size=0.1)
            self.lr_model = LogisticRegression()
            self.lr_model.fit(X_train, y_train)
            pred = self.lr_model.predict(X_test)
            acc = accuracy_score(y_test, pred) * 100
            self.root.after(0, lambda: self.ui["lbl_accuracy"].configure(text=f"Accuracy: {acc:.2f}%"))
            self.root.after(0, lambda: self.log_message(f"Model trained. Accuracy {acc:.2f}%"))
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Model error: {e}"))
            raise

    def start_control(self) -> None:
        if not self.lr_model:
            messagebox.showerror("Error", "Train the model first")
            return
        if self.is_controlling:
            return
        self.is_controlling = True
        t = threading.Thread(target=self.control_process, daemon=True)
        t.start()

    def stop_control(self) -> None:
        self.is_controlling = False
        self.update_status_light(active=False)
        self.log_message("Control stopped")

    def update_status_light(self, active: bool) -> None:
        color = self.colors["OK"] if active else self.colors["MUTED"]
        self.ui["status_light"].itemconfig(self.ui["status_light_id"], fill=color, outline=color)

    def control_process(self) -> None:
        counter = 0
        while self.is_controlling:
            try:
                sample, ts = self.brain_inlet.pull_sample()
                if sample:
                    intention = self.lr_model.predict(self.sc_x.transform(pd.DataFrame(sample).values.T))
                    if intention == 1:
                        counter += 1
                        self.root.after(0, lambda: self.update_status_light(True))
                    else:
                        if counter > 0:
                            counter -= 1
                        self.root.after(0, lambda: self.update_status_light(False))
                    # Update counter label only integer
                    self.root.after(0, lambda c=counter: self.ui["counter_value"].configure(text=str(c)))
                    # Threshold action
                    if counter >= int(self.threshold_var.get()):
                        if self.robot:
                            try:
                                # Ejecutar movimientos del robot en un hilo separado
                                robot_thread = threading.Thread(target=self.execute_robot_movement)
                                robot_thread.daemon = True
                                robot_thread.start()
                                self.root.after(0, lambda: self.ui["chip_send"]["set_status"](True, "Robot movement started"))
                            except Exception as e:
                                self.root.after(0, lambda: self.log_message(f"Robot movement error: {e}"))
                        counter = 0
                        self.root.after(0, lambda: self.log_message("Robot movement command sent"))
                        self.root.after(0, lambda: self.ui["chip_reset"]["set_status"](True, "Reset counter & log action"))
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Control error: {e}"))


def main() -> None:
    root = tk.Tk()
    app = VRehabGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()


