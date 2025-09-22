# VRehab EEG Rehabilitation System / Sistema de Rehabilitación EEG VRehab

## Description / Descripción

This project implements an EEG-based rehabilitation system that uses machine learning to detect movement intentions from brain signals. The system connects to an EEG device via Lab Streaming Layer (LSL) and controls an Arduino for rehabilitation purposes.

Este proyecto implementa un sistema de rehabilitación basado en EEG que utiliza machine learning para detectar intenciones de movimiento a partir de señales cerebrales. El sistema se conecta a un dispositivo EEG a través de Lab Streaming Layer (LSL) y controla un Arduino con fines de rehabilitación.

## Requirements / Requisitos

### Hardware / Hardware
- EEG device compatible with LSL (e.g., AURA_Power)
- Arduino connected to COM3 port
- Dispositivo EEG compatible con LSL (ej. AURA_Power)
- Arduino conectado al puerto COM3

### Software Dependencies / Dependencias de Software

Install the required Python packages using:

Instala los paquetes de Python requeridos usando:

```bash
pip install -r requirements.txt
```

## Setup Instructions / Instrucciones de Configuración

1. **Install Python packages / Instalar paquetes de Python:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Connect your EEG device / Conectar tu dispositivo EEG:**
   - Ensure your EEG device is running and streaming data via LSL
   - The code looks for a stream named "AURA_Power"
   - Asegúrate de que tu dispositivo EEG esté funcionando y transmitiendo datos vía LSL
   - El código busca un stream llamado "AURA_Power"

3. **Connect Arduino / Conectar Arduino:**
   - Connect Arduino to COM3 port (modify port in code if different)
   - Set baudrate to 38400
   - Conectar Arduino al puerto COM3 (modificar puerto en el código si es diferente)
   - Configurar baudrate a 38400

## Usage / Uso

Run the main script:

Ejecuta el script principal:

```bash
python VRehab_2.py
```

### Training Process / Proceso de Entrenamiento

1. **Relax Training (30 seconds) / Entrenamiento de Relajación (30 segundos):**
   - Stay relaxed and still
   - Permanece relajado y quieto

2. **Movement Intention Training (30 seconds) / Entrenamiento de Intención de Movimiento (30 segundos):**
   - Think about moving or imagine movement
   - Piensa en moverte o imagina movimiento

3. **AI Training / Entrenamiento de IA:**
   - The system trains a logistic regression model
   - El sistema entrena un modelo de regresión logística

4. **Control Phase / Fase de Control:**
   - The system monitors your brain signals in real-time
   - When movement intention is detected, it sends commands to Arduino
   - El sistema monitorea tus señales cerebrales en tiempo real
   - Cuando se detecta intención de movimiento, envía comandos al Arduino

## Important Notes / Notas Importantes

- Make sure your EEG device is properly calibrated before running
- The system requires a stable LSL stream connection
- Arduino must be connected and responsive
- Asegúrate de que tu dispositivo EEG esté calibrado correctamente antes de ejecutar
- El sistema requiere una conexión estable de stream LSL
- El Arduino debe estar conectado y responder

## Troubleshooting / Solución de Problemas

- If LSL stream is not found, check that your EEG software is running
- If Arduino communication fails, verify the COM port and baudrate
- Si no se encuentra el stream LSL, verifica que tu software EEG esté ejecutándose
- Si falla la comunicación con Arduino, verifica el puerto COM y baudrate
