# VRehab - Mind-Controlled Robot 🤖🧠

Control a Dobot Magic robot using your thoughts through EEG signals.

## 🚀 Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Connect hardware**
   - Connect Dobot Magic robot via USB
   - Start EEG device with LSL stream

3. **Run the application**
   ```bash
   python gui-controlrobotwitheeg.py
   ```

## 🎮 How to Use

1. **Connect Robot**: Select COM port and connect
2. **Connect EEG**: Connect to LSL stream
3. **Train Model**: Click "Start Training" and follow protocol
4. **Mind Control**: Click "Start Control" and think about moving!

## 🤖 Robot Controls

- **🤖 Test Robot Movement**: Manual movement sequence
- **🏠 Robot Home**: Return to safe position
- **🎯 Mind Control**: Automatic movement when EEG threshold reached

## 🛡️ Safety

- Clear workspace around robot
- Keep hands away during operation
- Use "Robot Home" button to reset position

## 📁 Files

- **`gui-controlrobotwitheeg.py`** - Main GUI for robot control with EEG
- **`eegwitharduino.py`** - Arduino EEG integration (legacy version)
- **`requirements.txt`** - Python dependencies
- **`README.md`** - This documentation

## 📋 Requirements

- Python 3.8+
- Dobot Magic robot
- EEG device with LSL support
- pydobot, pylsl, scikit-learn

## ⚠️ Warning

This system is for research and educational purposes. Always ensure workspace is clear and keep hands away during operation.