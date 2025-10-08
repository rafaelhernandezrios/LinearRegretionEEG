# VRehab - Mind-Controlled Robot System 🤖🧠

A revolutionary brain-computer interface system that allows users to control a Dobot Magic robot using only their thoughts through EEG signals.

## 🌟 Features

- **🧠 EEG-Based Control**: Real-time brain signal processing using Lab Streaming Layer (LSL)
- **🤖 Robot Control**: Direct control of Dobot Magic robot via serial communication
- **🎯 Machine Learning**: Logistic Regression model for movement intention detection
- **📊 Real-time Visualization**: Live EEG data monitoring and movement detection
- **🛡️ Safety First**: Safe movement sequences with collision avoidance
- **🎨 Modern GUI**: Dark-themed interface with intuitive controls

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Dobot Magic robot
- EEG device compatible with LSL
- Windows/Linux/Mac

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/vrehab-mind-controlled-robot.git
   cd vrehab-mind-controlled-robot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Connect your hardware**
   - Connect Dobot Magic robot via USB/Serial
   - Connect EEG device and start LSL stream

4. **Run the application**
   ```bash
   python vrehab_gui_refactored.py
   ```

## 🎮 Usage

### Basic Workflow

1. **Connect Hardware**
   - Select COM port for Dobot robot
   - Connect to EEG stream
   - Verify both connections show "Connected" status

2. **Train the Model**
   - Click "Start Training"
   - Follow the training protocol
   - Train for both "Move" and "Rest" states
   - Save the trained model

3. **Mind Control**
   - Click "Start Control"
   - Think about moving your hand
   - Watch the robot respond to your thoughts!

### Robot Controls

- **🤖 Test Robot Movement**: Execute safe movement sequence manually
- **🏠 Robot Home**: Return robot to safe home position
- **🎯 Mind Control**: Automatic robot movement when EEG threshold is reached

## 🔧 Hardware Setup

### Dobot Magic Robot

1. **Connection**
   - Connect robot via USB cable
   - Note the COM port (e.g., COM5)
   - Ensure robot is powered and calibrated

2. **Safety**
   - Clear workspace around robot
   - Ensure robot has adequate movement space
   - Keep hands away during operation

### EEG Device

1. **LSL Stream**
   - Start your EEG software
   - Ensure LSL stream is active
   - Stream should contain EEG channels

2. **Electrode Placement**
   - Follow standard EEG electrode placement
   - Focus on motor cortex areas
   - Ensure good signal quality

## 📁 Project Structure

```
vrehab-mind-controlled-robot/
├── vrehab_gui_refactored.py    # Main GUI application
├── requirements.txt            # Python dependencies
├── README.md                  # This file
├── dobot/                     # Dobot SDK files
│   └── dobot-python/
└── examples/                  # Example scripts
```

## 🧠 How It Works

### EEG Signal Processing

1. **Data Acquisition**: Real-time EEG data via LSL
2. **Feature Extraction**: Signal processing and feature calculation
3. **Classification**: Machine learning model predicts movement intention
4. **Robot Control**: Commands sent to Dobot robot based on predictions

### Machine Learning Pipeline

1. **Training Phase**
   - Collect EEG data during "Move" and "Rest" states
   - Extract features from EEG signals
   - Train Logistic Regression classifier
   - Save model for real-time use

2. **Control Phase**
   - Real-time EEG data processing
   - Feature extraction and normalization
   - Movement intention prediction
   - Robot movement execution

## 🛡️ Safety Features

- **Safe Movement Sequences**: Pre-programmed safe robot movements
- **Collision Avoidance**: Step-by-step movement with height checks
- **Emergency Stop**: Manual stop controls
- **Home Position**: Safe return to home position
- **Error Handling**: Graceful error recovery

## 🎯 Robot Movement Sequences

### Test Movement
- Forward → Right → Up → Back → Left → Down → Forward → Home
- Small, safe increments (15mm movements)
- Moderate height changes (10mm)
- Returns to starting position

### Mind Control Movement
- Same safe sequence triggered by EEG threshold
- Automatic execution when movement intention detected
- Real-time progress logging

## 🔧 Configuration

### COM Port Settings
- Default baudrate: 115200
- Auto-detect available ports
- Manual port selection

### EEG Settings
- Auto-detect LSL streams
- Real-time signal monitoring
- Threshold adjustment (100-2000)

## 🐛 Troubleshooting

### Common Issues

1. **Robot Connection Failed**
   - Check COM port selection
   - Verify robot is powered on
   - Try different USB cable

2. **EEG Stream Not Found**
   - Ensure EEG software is running
   - Check LSL stream is active
   - Verify electrode connections

3. **Robot Movement Errors**
   - Check workspace is clear
   - Verify robot calibration
   - Use "Robot Home" button to reset

### Debug Mode

Enable verbose logging in the GUI to see detailed information about:
- EEG data processing
- Robot communication
- Movement execution
- Error messages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Dobot Technology** for the Magic robot platform
- **Lab Streaming Layer** for EEG data streaming
- **scikit-learn** for machine learning capabilities
- **pydobot** for robot control interface

## 📞 Support

For issues and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review the documentation

## 🔮 Future Enhancements

- [ ] Multiple robot support
- [ ] Advanced movement patterns
- [ ] Real-time EEG visualization
- [ ] Mobile app interface
- [ ] Cloud-based training data
- [ ] Multi-user support

---

**⚠️ Safety Warning**: Always ensure the robot workspace is clear and keep hands away during operation. This system is for research and educational purposes.

**🎉 Enjoy controlling robots with your mind!**