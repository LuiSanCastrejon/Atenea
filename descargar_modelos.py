# Descarga el LLM y la voz de Piper en models\ y voices\ (unos 2.5 GB en total).
# Uso:  python descargar_modelos.py   (o se ejecuta solo desde instalar.bat)
import os
import sys
import urllib.request

DIRECTORIO = os.path.dirname(os.path.abspath(__file__))
VOZ = "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/carlfm/x_low/es_ES-carlfm-x_low.onnx"

ARCHIVOS = [
    ("https://huggingface.co/Qwen/Qwen3-4B-GGUF/resolve/main/Qwen3-4B-Q4_K_M.gguf",
     os.path.join(DIRECTORIO, "models", "qwen3-4b-q4_k_m.gguf")),
    (VOZ, os.path.join(DIRECTORIO, "voices", "es_ES-carlfm-x_low.onnx")),
    (VOZ + ".json", os.path.join(DIRECTORIO, "voices", "es_ES-carlfm-x_low.onnx.json")),
]

def progreso(bloques, tam_bloque, total):
    if total > 0:
        hecho = min(bloques * tam_bloque, total)
        print(f"\r  {hecho / 1e6:8.1f} / {total / 1e6:.1f} MB", end="", flush=True)

for url, destino in ARCHIVOS:
    if os.path.exists(destino):
        print(f"Ya existe {os.path.basename(destino)}")
        continue
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    print(f"Descargando {os.path.basename(destino)}...")
    temporal = destino + ".part"
    try:
        urllib.request.urlretrieve(url, temporal, progreso)
    except Exception as e:
        print(f"\nNo se pudo descargar {url}: {e}")
        sys.exit(1)
    os.replace(temporal, destino)
    print()

print("Modelos listos.")
