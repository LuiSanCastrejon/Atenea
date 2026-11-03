# Muestra los micrófonos y altavoces que ve Python.
# Copia el número del que quieras usar en DISPOSITIVO_ENTRADA / DISPOSITIVO_SALIDA de Atenea.py
import sounddevice as sd

print(sd.query_devices())
entrada, salida = sd.default.device
print(f"\nPredeterminados: entrada = {entrada}, salida = {salida}")
print("En Windows cada aparato sale repetido (MME, DirectSound, WASAPI). Usa el de MME si dudas.")
