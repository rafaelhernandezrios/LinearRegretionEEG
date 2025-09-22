import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import serial.tools.list_ports
import serial
import threading
import time
import numpy as np
import pandas as pd
import pickle
from pylsl import StreamInlet, resolve_byprop
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
import queue
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from tkinter import font

class VRehabGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🧠 VRehab EEG Rehabilitation System")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1a1a2e')
        self.root.minsize(1200, 800)
        
        # Modern color scheme
        self.colors = {
            'primary': '#16213e',
            'secondary': '#0f3460', 
            'accent': '#e94560',
            'success': '#00d4aa',
            'warning': '#ffa726',
            'error': '#f44336',
            'background': '#1a1a2e',
            'surface': '#2d2d44',
            'text': '#ffffff',
            'text_secondary': '#b0b0b0',
            'border': '#404060'
        }
        
        # Configure styles
        self.setup_styles()
        
        # Variables
        self.arduino = None
        self.brain_inlet = None
        self.lr_model = None
        self.sc_x = None
        self.is_training = False
        self.is_controlling = False
        self.training_data = {'rest': pd.DataFrame(), 'move': pd.DataFrame()}
        self.counter = 0
        self.sample_queue = queue.Queue()
        
        # Status variables
        self.arduino_connected = False
        self.eeg_connected = False
        
        self.setup_ui()
        self.update_com_ports()
        self.check_connections()
        
        # Welcome message
        self.log_message("🚀 VRehab EEG Rehabilitation System started")
        self.log_message("📡 Please connect Arduino and EEG devices to begin")
        
    def setup_styles(self):
        """Configure modern styles for the interface"""
        style = ttk.Style()
        
        # Set theme
        style.theme_use('clam')
        
        # Configure main styles
        style.configure('TFrame', 
                       background=self.colors['background'],
                       borderwidth=0)
        
        style.configure('TLabelFrame',
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       borderwidth=1,
                       relief='solid',
                       font=('Segoe UI', 10, 'bold'))
        
        style.configure('TLabelFrame.Label',
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 10, 'bold'))
        
        style.configure('TLabel',
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       font=('Segoe UI', 9))
        
        # Button styles
        style.configure('Primary.TButton',
                       background=self.colors['accent'],
                       foreground='white',
                       font=('Segoe UI', 9, 'bold'),
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Primary.TButton',
                 background=[('active', '#d63384'),
                           ('pressed', '#c2185b')])
        
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='white',
                       font=('Segoe UI', 9, 'bold'),
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Success.TButton',
                 background=[('active', '#00b894'),
                           ('pressed', '#00a085')])
        
        style.configure('Warning.TButton',
                       background=self.colors['warning'],
                       foreground='white',
                       font=('Segoe UI', 9, 'bold'),
                       borderwidth=0,
                       focuscolor='none')
        
        style.configure('Secondary.TButton',
                       background=self.colors['secondary'],
                       foreground='white',
                       font=('Segoe UI', 9),
                       borderwidth=0,
                       focuscolor='none')
        
        # Progress bar style
        style.configure('TProgressbar',
                       background=self.colors['accent'],
                       troughcolor=self.colors['border'],
                       borderwidth=0,
                       lightcolor=self.colors['accent'],
                       darkcolor=self.colors['accent'])
        
        # Combobox style
        style.configure('TCombobox',
                       fieldbackground=self.colors['surface'],
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       borderwidth=1,
                       relief='solid')
        
        # Configure root window
        self.root.configure(bg=self.colors['background'])
        
    def setup_ui(self):
        # Main frame with modern styling
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Header section
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 30))
        header_frame.columnconfigure(1, weight=1)
        
        # Title with icon
        title_label = ttk.Label(header_frame, text="🧠 VRehab EEG Rehabilitation System", 
                               font=('Segoe UI', 18, 'bold'),
                               foreground=self.colors['text'])
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, text="Advanced Brain-Computer Interface for Rehabilitation", 
                                  foreground=self.colors['text_secondary'])
        subtitle_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Connection settings card
        conn_frame = ttk.LabelFrame(main_frame, text="🔌 Connection Settings", 
                                   padding="20")
        conn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        conn_frame.columnconfigure(1, weight=1)
        
        # Arduino settings row
        arduino_frame = ttk.Frame(conn_frame)
        arduino_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        arduino_frame.columnconfigure(1, weight=1)
        
        ttk.Label(arduino_frame, text="🔌 Arduino Settings", 
                 font=('Segoe UI', 12, 'bold'),
                 foreground=self.colors['text']).grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 10))
        
        # COM Port selection
        ttk.Label(arduino_frame, text="COM Port:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10))
        self.com_var = tk.StringVar()
        self.com_combo = ttk.Combobox(arduino_frame, textvariable=self.com_var, width=15)
        self.com_combo.grid(row=1, column=1, sticky=tk.W, padx=(0, 15))
        
        # Refresh COM ports button
        ttk.Button(arduino_frame, text="🔄 Refresh", command=self.update_com_ports, 
                  style='Secondary.TButton').grid(row=1, column=2, padx=(0, 15))
        
        # Baudrate selection
        ttk.Label(arduino_frame, text="Baudrate:").grid(row=1, column=3, sticky=tk.W, padx=(0, 10))
        self.baudrate_var = tk.StringVar(value="38400")
        baudrate_combo = ttk.Combobox(arduino_frame, textvariable=self.baudrate_var, 
                                     values=["9600", "19200", "38400", "57600", "115200"], 
                                     width=10)
        baudrate_combo.grid(row=1, column=4, sticky=tk.W, padx=(0, 15))
        
        # Connect/Disconnect Arduino button
        self.arduino_btn = ttk.Button(arduino_frame, text="🔌 Connect Arduino", 
                                     command=self.toggle_arduino, style='Primary.TButton')
        self.arduino_btn.grid(row=1, column=5, padx=(10, 0))
        
        # EEG settings row
        eeg_frame = ttk.Frame(conn_frame)
        eeg_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 0))
        eeg_frame.columnconfigure(1, weight=1)
        
        ttk.Label(eeg_frame, text="🧠 EEG Settings", 
                 font=('Segoe UI', 12, 'bold'),
                 foreground=self.colors['text']).grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 10))
        
        # Connect/Disconnect EEG button
        self.eeg_btn = ttk.Button(eeg_frame, text="🧠 Connect EEG", 
                                 command=self.toggle_eeg, style='Success.TButton')
        self.eeg_btn.grid(row=1, column=0, padx=(0, 15))
        
        # Search EEG streams button
        ttk.Button(eeg_frame, text="🔍 Search Streams", command=self.search_eeg_streams, 
                  style='Warning.TButton').grid(row=1, column=1, padx=(0, 0))
        
        # Status indicators card
        status_frame = ttk.LabelFrame(main_frame, text="📊 Connection Status", 
                                     padding="20")
        status_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        status_frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(1, weight=1)
        
        # Arduino status
        arduino_status_frame = ttk.Frame(status_frame)
        arduino_status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 20))
        
        ttk.Label(arduino_status_frame, text="🔌 Arduino", 
                 font=('Segoe UI', 12, 'bold'),
                 foreground=self.colors['text']).grid(row=0, column=0, sticky=tk.W)
        self.arduino_status = tk.Label(arduino_status_frame, text="Disconnected", 
                                      fg=self.colors['error'], font=('Segoe UI', 12, 'bold'),
                                      bg=self.colors['surface'])
        self.arduino_status.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # EEG status
        eeg_status_frame = ttk.Frame(status_frame)
        eeg_status_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        ttk.Label(eeg_status_frame, text="🧠 EEG", 
                 font=('Segoe UI', 12, 'bold'),
                 foreground=self.colors['text']).grid(row=0, column=0, sticky=tk.W)
        self.eeg_status = tk.Label(eeg_status_frame, text="Disconnected", 
                                  fg=self.colors['error'], font=('Segoe UI', 12, 'bold'),
                                  bg=self.colors['surface'])
        self.eeg_status.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # Main control card
        control_frame = ttk.LabelFrame(main_frame, text="🎮 System Control", 
                                      padding="20")
        control_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        # Training section
        training_frame = ttk.Frame(control_frame)
        training_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        training_frame.columnconfigure(0, weight=1)
        
        ttk.Label(training_frame, text="🎯 Training Phase", 
                 font=('Segoe UI', 12, 'bold'),
                 foreground=self.colors['text']).grid(row=0, column=0, sticky=tk.W, pady=(0, 15))
        
        # Training buttons
        btn_frame = ttk.Frame(training_frame)
        btn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.start_training_btn = ttk.Button(btn_frame, text="🚀 Start Training", 
                                           command=self.start_training, state='disabled',
                                           style='Success.TButton')
        self.start_training_btn.grid(row=0, column=0, padx=(0, 15))
        
        self.stop_training_btn = ttk.Button(btn_frame, text="⏹️ Stop Training", 
                                          command=self.stop_training, state='disabled',
                                          style='Warning.TButton')
        self.stop_training_btn.grid(row=0, column=1, padx=(0, 0))
        
        # Training progress
        progress_frame = ttk.Frame(training_frame)
        progress_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.training_progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.training_progress.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        self.training_label = ttk.Label(progress_frame, text="Ready to start training")
        self.training_label.grid(row=1, column=0, sticky=tk.W)
        
        # Control section
        control_section_frame = ttk.Frame(control_frame)
        control_section_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(20, 0))
        control_section_frame.columnconfigure(0, weight=1)
        
        ttk.Label(control_section_frame, text="🎮 Control Phase", 
                 font=('Segoe UI', 12, 'bold'),
                 foreground=self.colors['text']).grid(row=0, column=0, sticky=tk.W, pady=(0, 15))
        
        # Control buttons
        control_btn_frame = ttk.Frame(control_section_frame)
        control_btn_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.start_control_btn = ttk.Button(control_btn_frame, text="▶️ Start Control", 
                                           command=self.start_control, state='disabled',
                                           style='Primary.TButton')
        self.start_control_btn.grid(row=0, column=0, padx=(0, 15))
        
        self.stop_control_btn = ttk.Button(control_btn_frame, text="⏹️ Stop Control", 
                                          command=self.stop_control, state='disabled',
                                          style='Warning.TButton')
        self.stop_control_btn.grid(row=0, column=1, padx=(0, 0))
        
        # Movement detection display
        detection_frame = ttk.LabelFrame(control_section_frame, text="📊 Movement Detection", 
                                        padding="15")
        detection_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 0))
        detection_frame.columnconfigure(1, weight=1)
        
        # Detection info
        detection_info_frame = ttk.Frame(detection_frame)
        detection_info_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        detection_info_frame.columnconfigure(1, weight=1)
        
        ttk.Label(detection_info_frame, text="Counter:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.movement_counter = ttk.Label(detection_info_frame, text="0", 
                                         font=('Segoe UI', 16, 'bold'),
                                         foreground=self.colors['accent'])
        self.movement_counter.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        # Status indicator
        status_frame = ttk.Frame(detection_info_frame)
        status_frame.grid(row=0, column=2, sticky=tk.E)
        
        ttk.Label(status_frame, text="Status:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.movement_indicator = tk.Label(status_frame, text="●", fg=self.colors['text_secondary'], 
                                          font=('Segoe UI', 24, 'bold'),
                                          bg=self.colors['surface'])
        self.movement_indicator.grid(row=0, column=1, sticky=tk.W)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="📝 System Log", 
                                  padding="15")
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(20, 0))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        # Configure text widget with modern styling
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=80,
                                                 bg=self.colors['surface'],
                                                 fg=self.colors['text'],
                                                 font=('Consolas', 9),
                                                 insertbackground=self.colors['text'],
                                                 selectbackground=self.colors['accent'],
                                                 selectforeground='white',
                                                 borderwidth=0,
                                                 relief='flat')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure main frame grid weights
        main_frame.rowconfigure(4, weight=1)
        
    def log_message(self, message):
        """Add message to log with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def update_com_ports(self):
        """Update COM port list"""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.com_combo['values'] = port_list
        if port_list and not self.com_var.get():
            self.com_var.set(port_list[0])
            
    def check_connections(self):
        """Check and update connection status"""
        # Check Arduino connection
        if self.arduino and self.arduino.is_open:
            self.arduino_connected = True
            self.arduino_status.config(text="Connected", fg=self.colors['success'])
        else:
            self.arduino_connected = False
            self.arduino_status.config(text="Disconnected", fg=self.colors['error'])
            
        # Check EEG connection
        try:
            if self.brain_inlet:
                self.eeg_connected = True
                self.eeg_status.config(text="Connected", fg=self.colors['success'])
                self.eeg_btn.config(text="🧠 Disconnect EEG")
            else:
                self.eeg_connected = False
                self.eeg_status.config(text="Disconnected", fg=self.colors['error'])
                self.eeg_btn.config(text="🧠 Connect EEG")
        except:
            self.eeg_connected = False
            self.eeg_status.config(text="Disconnected", fg=self.colors['error'])
            self.eeg_btn.config(text="🧠 Connect EEG")
            
        # Update button states
        if self.arduino_connected and self.eeg_connected:
            self.start_training_btn.config(state='normal')
        else:
            self.start_training_btn.config(state='disabled')
            
        # Schedule next check
        self.root.after(1000, self.check_connections)
        
    def toggle_arduino(self):
        """Connect or disconnect Arduino"""
        if not self.arduino_connected:
            try:
                port = self.com_var.get()
                baudrate = int(self.baudrate_var.get())
                self.arduino = serial.Serial(port=port, baudrate=baudrate, timeout=0.1)
                self.arduino_btn.config(text="🔌 Disconnect Arduino")
                self.log_message(f"🔌 Arduino connected to {port} at {baudrate} baud")
            except Exception as e:
                messagebox.showerror("Connection Error", f"Failed to connect to Arduino: {str(e)}")
                self.log_message(f"❌ Arduino connection failed: {str(e)}")
        else:
            try:
                if self.arduino:
                    self.arduino.close()
                self.arduino = None
                self.arduino_btn.config(text="🔌 Connect Arduino")
                self.log_message("🔌 Arduino disconnected")
            except Exception as e:
                self.log_message(f"Error disconnecting Arduino: {str(e)}")
                
    def toggle_eeg(self):
        """Connect or disconnect EEG stream"""
        if not self.eeg_connected:
            try:
                self.log_message("Looking for EEG stream...")
                brain_stream = resolve_byprop("name", "AURA_Power")
                if brain_stream:
                    self.brain_inlet = StreamInlet(brain_stream[0])
                    self.brain_inlet.open_stream()
                    self.eeg_btn.config(text="🧠 Disconnect EEG")
                    self.log_message("🧠 EEG stream connected successfully")
                else:
                    self.log_message("❌ No EEG stream found with name 'AURA_Power'")
                    messagebox.showwarning("EEG Stream Not Found", 
                                         "No EEG stream found with name 'AURA_Power'.\n"
                                         "Please make sure your EEG device is running and streaming data.")
            except Exception as e:
                self.log_message(f"❌ EEG connection failed: {str(e)}")
                messagebox.showerror("EEG Connection Error", f"Failed to connect to EEG: {str(e)}")
        else:
            try:
                if self.brain_inlet:
                    self.brain_inlet.close_stream()
                self.brain_inlet = None
                self.eeg_btn.config(text="🧠 Connect EEG")
                self.log_message("🧠 EEG stream disconnected")
            except Exception as e:
                self.log_message(f"Error disconnecting EEG: {str(e)}")
                
    def search_eeg_streams(self):
        """Search for available EEG streams"""
        try:
            self.log_message("Searching for available EEG streams...")
            streams = resolve_byprop("type", "EEG", timeout=2)
            
            if streams:
                self.log_message(f"Found {len(streams)} EEG stream(s):")
                for i, stream in enumerate(streams):
                    info = stream.info()
                    name = info.name()
                    type_name = info.type()
                    channel_count = info.channel_count()
                    self.log_message(f"  Stream {i+1}: Name='{name}', Type='{type_name}', Channels={channel_count}")
            else:
                self.log_message("No EEG streams found")
                messagebox.showinfo("No Streams Found", 
                                  "No EEG streams detected.\n"
                                  "Please make sure your EEG device is running and streaming data.")
        except Exception as e:
            self.log_message(f"Error searching for streams: {str(e)}")
            messagebox.showerror("Search Error", f"Error searching for streams: {str(e)}")
                
    def connect_eeg(self):
        """Connect to EEG stream (internal method)"""
        try:
            self.log_message("Looking for EEG stream...")
            brain_stream = resolve_byprop("name", "AURA_Power")
            if brain_stream:
                self.brain_inlet = StreamInlet(brain_stream[0])
                self.brain_inlet.open_stream()
                self.eeg_btn.config(text="Disconnect EEG")
                self.log_message("EEG stream connected successfully")
                return True
            else:
                self.log_message("No EEG stream found")
                return False
        except Exception as e:
            self.log_message(f"EEG connection failed: {str(e)}")
            return False
            
    def start_training(self):
        """Start training process"""
        if not self.eeg_connected:
            messagebox.showerror("Error", "Please connect to EEG stream first")
            return
            
        self.is_training = True
        self.start_training_btn.config(state='disabled')
        self.stop_training_btn.config(state='normal')
        
        # Start training in separate thread
        training_thread = threading.Thread(target=self.training_process)
        training_thread.daemon = True
        training_thread.start()
        
    def training_process(self):
        """Main training process"""
        try:
            # Rest training
            self.root.after(0, lambda: self.training_label.config(text="Relax Training - Stay still for 30 seconds"))
            self.root.after(0, lambda: self.training_progress.config(value=0))
            
            rest_data = self.collect_training_data(30, "rest")
            if not self.is_training:
                return
                
            # Movement training
            self.root.after(0, lambda: self.training_label.config(text="Movement Training - Think about moving for 30 seconds"))
            self.root.after(0, lambda: self.training_progress.config(value=50))
            
            move_data = self.collect_training_data(30, "move")
            if not self.is_training:
                return
                
            # Train model
            self.root.after(0, lambda: self.training_label.config(text="Training AI model..."))
            self.root.after(0, lambda: self.training_progress.config(value=75))
            
            self.train_model(rest_data, move_data)
            
            self.root.after(0, lambda: self.training_label.config(text="Training completed successfully!"))
            self.root.after(0, lambda: self.training_progress.config(value=100))
            self.root.after(0, lambda: self.start_control_btn.config(state='normal'))
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Training error: {str(e)}"))
        finally:
            self.root.after(0, lambda: self.stop_training_btn.config(state='disabled'))
            self.root.after(0, lambda: self.start_training_btn.config(state='normal'))
            self.is_training = False
            
    def collect_training_data(self, duration, data_type):
        """Collect training data for specified duration"""
        data = pd.DataFrame()
        start_time = time.time()
        
        while time.time() - start_time < duration and self.is_training:
            try:
                sample, timestamp = self.brain_inlet.pull_sample()
                if sample:
                    data = pd.concat([data, pd.DataFrame(sample).T])
                    
                # Update progress
                progress = ((time.time() - start_time) / duration) * 50
                if data_type == "move":
                    progress += 50
                self.root.after(0, lambda p=progress: self.training_progress.config(value=p))
                
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Data collection error: {str(e)}"))
                
        if data_type == "rest":
            data["Event"] = 0
        else:
            data["Event"] = 1
            
        return data
        
    def train_model(self, rest_data, move_data):
        """Train the machine learning model"""
        try:
            # Combine data
            selected_data = pd.concat([rest_data, move_data])
            selected_data.to_csv('full_data_personas_nuevas.csv')
            
            # Prepare features and labels
            X = selected_data.iloc[1:, :-1].values
            y = selected_data.iloc[1:, -1].values
            
            # Scale features
            self.sc_x = StandardScaler()
            X = self.sc_x.fit_transform(X)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)
            
            # Train model
            self.lr_model = LogisticRegression()
            self.lr_model.fit(X_train, y_train)
            
            # Test accuracy
            y_pred = self.lr_model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred) * 100
            
            self.root.after(0, lambda: self.log_message(f"Model trained successfully! Accuracy: {accuracy:.2f}%"))
            
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Model training error: {str(e)}"))
            raise
            
    def stop_training(self):
        """Stop training process"""
        self.is_training = False
        self.training_label.config(text="Training stopped")
        
    def start_control(self):
        """Start control process"""
        if not self.lr_model:
            messagebox.showerror("Error", "Please train the model first")
            return
            
        self.is_controlling = True
        self.start_control_btn.config(state='disabled')
        self.stop_control_btn.config(state='normal')
        
        # Start control in separate thread
        control_thread = threading.Thread(target=self.control_process)
        control_thread.daemon = True
        control_thread.start()
        
    def control_process(self):
        """Main control process"""
        self.counter = 0
        
        while self.is_controlling:
            try:
                sample, timestamp = self.brain_inlet.pull_sample()
                if sample:
                    # Predict intention
                    intention = self.lr_model.predict(self.sc_x.transform(pd.DataFrame(sample).values.T))
                    
                    if intention == 1:
                        self.counter += 1
                        self.root.after(0, lambda: self.movement_indicator.config(fg=self.colors['success']))
                    else:
                        if self.counter > 0:
                            self.counter -= 1
                        self.root.after(0, lambda: self.movement_indicator.config(fg=self.colors['text_secondary']))
                        
                    # Update display
                    self.root.after(0, lambda: self.movement_counter.config(text=f"Counter: {self.counter}"))
                    
                    # Send command to Arduino if threshold reached
                    if self.counter >= 700:
                        if self.arduino and self.arduino.is_open:
                            self.arduino.write(b"1")
                        self.counter = 0
                        self.root.after(0, lambda: self.log_message("Movement command sent to Arduino"))
                        
            except Exception as e:
                self.root.after(0, lambda: self.log_message(f"Control error: {str(e)}"))
                
    def stop_control(self):
        """Stop control process"""
        self.is_controlling = False
        self.start_control_btn.config(state='normal')
        self.stop_control_btn.config(state='disabled')
        self.movement_indicator.config(fg=self.colors['text_secondary'])
        self.log_message("⏹️ Control stopped")

def main():
    root = tk.Tk()
    app = VRehabGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
