# Control del Robot Magic Dobot

Este proyecto incluye scripts de Python para controlar el robot Magic Dobot a través del puerto COM.

## Archivos Incluidos

### 1. `test_dobot_magic.py` - Script de Prueba Básico
- **Propósito**: Prueba básica de conexión y movimientos simples
- **Características**:
  - Verificación de conexión
  - Movimientos básicos (adelante, lateral, vertical, rotación)
  - Regreso a posición home
  - Manejo de errores

### 2. `dobot_safe_movements.py` - Controlador Seguro
- **Propósito**: Control seguro con validaciones y límites
- **Características**:
  - Validación de límites de movimiento
  - Funciones de seguridad
  - Parada de emergencia
  - Movimientos relativos seguros

### 3. `dobot_advanced_demo.py` - Demostraciones Avanzadas
- **Propósito**: Patrones de movimiento complejos
- **Características**:
  - Dibujo de formas (cuadrado, círculo)
  - Patrón espiral
  - Simulación pick and place
  - Patrón de onda

## Configuración Inicial

### 1. Verificar Puerto COM
```python
# En Windows, el puerto suele ser:
port = "COM3"  # o COM4, COM5, etc.

# En Linux/Mac:
port = "/dev/ttyUSB0"  # o /dev/ttyACM0
```

### 2. Instalar Dependencias
```bash
pip install pyserial
```

### 3. Verificar Conexión
- Asegúrate de que el robot esté encendido
- Conecta el cable USB
- Verifica que no haya otros programas usando el puerto

## Uso de los Scripts

### Prueba Básica
```bash
python test_dobot_magic.py
```

### Control Seguro
```bash
python dobot_safe_movements.py
```

### Demostraciones Avanzadas
```bash
python dobot_advanced_demo.py
```

## Funciones Principales del SDK

### Movimientos Básicos
- `robot.home()` - Ir a posición home
- `robot.move_to(x, y, z, r)` - Movimiento absoluto
- `robot.move_to_relative(dx, dy, dz, dr)` - Movimiento relativo
- `robot.slide_to(x, y, z, r)` - Deslizamiento directo

### Información del Robot
- `robot.get_pose()` - Obtener posición actual
- `robot.connected()` - Verificar conexión

### Control de Cola
- `robot.wait()` - Esperar a que termine el movimiento
- `robot.interface.stop_queue()` - Detener movimientos

## Límites de Seguridad

El controlador seguro incluye límites por defecto:
- **X**: -200 a 200 mm
- **Y**: -200 a 200 mm  
- **Z**: -50 a 150 mm
- **R**: -180 a 180 grados

## Solución de Problemas

### Error de Conexión
1. Verifica que el puerto COM sea correcto
2. Asegúrate de que el robot esté encendido
3. Cierra otros programas que usen el puerto
4. Verifica la conexión USB

### Movimientos No Deseados
1. Usa el controlador seguro (`dobot_safe_movements.py`)
2. Verifica los límites de movimiento
3. Usa la función de parada de emergencia

### Errores de Comunicación
1. Reinicia el robot
2. Desconecta y reconecta el USB
3. Verifica que el baudrate sea 115200

## Ejemplos de Uso

### Movimiento Simple
```python
from dobot.dobot_python.lib.dobot import Dobot

robot = Dobot("COM3")
robot.home()  # Ir a home
robot.move_to(50, 50, 50, 0)  # Mover a posición específica
```

### Movimiento Seguro
```python
from dobot_safe_movements import SafeDobotController

controller = SafeDobotController("COM3")
controller.safe_move_to(50, 50, 50, 0)  # Movimiento con validación
```

### Patrón Complejo
```python
from dobot_advanced_demo import AdvancedDobotDemo

demo = AdvancedDobotDemo("COM3")
demo.draw_square(40)  # Dibujar cuadrado de 40mm
```

## Notas Importantes

⚠️ **Seguridad**:
- Siempre verifica el espacio de trabajo
- Usa límites de seguridad
- Mantén las manos alejadas durante el movimiento
- Ten listo el botón de parada de emergencia

🔧 **Mantenimiento**:
- Calibra el robot regularmente
- Verifica las conexiones
- Limpia el área de trabajo

📚 **Documentación**:
- Consulta el manual del Magic Dobot
- Revisa los ejemplos del SDK oficial
- Prueba movimientos pequeños primero
