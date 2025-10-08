#!/usr/bin/env python3
"""
VRehab System Check
Verifies all dependencies and hardware connections
"""

import sys
import os
import importlib
import serial.tools.list_ports
from pylsl import resolve_streams

def check_python_version():
    """Check Python version"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.8+")
        return False

def check_dependencies():
    """Check required Python packages"""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        'numpy', 'pandas', 'sklearn', 'pylsl', 
        'pydobot', 'serial', 'matplotlib', 'tkinter'
    ]
    
    all_ok = True
    for package in required_packages:
        try:
            if package == 'sklearn':
                importlib.import_module('sklearn')
            elif package == 'serial':
                importlib.import_module('serial')
            else:
                importlib.import_module(package)
            print(f"✅ {package} - OK")
        except ImportError:
            print(f"❌ {package} - Missing")
            all_ok = False
    
    return all_ok

def check_serial_ports():
    """Check available serial ports"""
    print("\n🔌 Checking serial ports...")
    
    ports = serial.tools.list_ports.comports()
    if ports:
        print("Available COM ports:")
        for port in ports:
            print(f"  📍 {port.device} - {port.description}")
        return True
    else:
        print("❌ No COM ports found")
        return False

def check_lsl_streams():
    """Check for LSL streams"""
    print("\n🧠 Checking LSL streams...")
    
    try:
        streams = resolve_streams()
        if streams:
            print("Available LSL streams:")
            for stream in streams:
                print(f"  📡 {stream.name()} - {stream.type()} ({stream.channel_count()} channels)")
            return True
        else:
            print("⚠️  No LSL streams found (EEG device may not be connected)")
            return False
    except Exception as e:
        print(f"❌ Error checking LSL streams: {e}")
        return False

def check_robot_connection():
    """Check robot connection"""
    print("\n🤖 Checking robot connection...")
    
    try:
        import pydobot
        print("✅ pydobot library available")
        
        # Try to find a robot (this might fail if no robot connected)
        ports = serial.tools.list_ports.comports()
        robot_found = False
        
        for port in ports:
            try:
                device = pydobot.Dobot(port=port.device, verbose=False)
                pose = device.pose()
                print(f"✅ Robot found on {port.device} - Position: {pose[:3]}")
                device.close()
                robot_found = True
                break
            except:
                continue
        
        if not robot_found:
            print("⚠️  No robot found (make sure Dobot Magic is connected)")
        
        return robot_found
        
    except Exception as e:
        print(f"❌ Error checking robot: {e}")
        return False

def main():
    """Main system check"""
    print("=" * 50)
    print("VRehab System Check")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Serial Ports", check_serial_ports),
        ("LSL Streams", check_lsl_streams),
        ("Robot Connection", check_robot_connection)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ Error in {name}: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("System Check Summary")
    print("=" * 50)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All checks passed! System is ready.")
        print("\nTo start VRehab:")
        print("  python vrehab_gui_refactored.py")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("\nCommon solutions:")
        print("  - Install missing packages: pip install -r requirements.txt")
        print("  - Connect your Dobot Magic robot")
        print("  - Start your EEG device with LSL stream")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
