# Atenea para Windows

Esta carpeta es Atenea lista para Windows 10/11. Junta el código del repo (Atenea.py, Skills de hora, Wikipedia y Spotify) con las versiones más nuevas de la web y de la base de datos de tareas.

## 1. Requisitos

- **Python 3.11 de 64 bits** desde python.org. Al instalarlo marca "Add python.exe to PATH". Se usa 3.11 porque es la versión con ruedas precompiladas para todo (llama-cpp, webrtcvad, piper).
- Unos 3 GB libres para los modelos.

## 2. Instalar

Descomprime el zip donde quieras y haz doble clic en `instalar.bat`. El script crea un entorno virtual `.venv`, instala las dependencias, descarga los modelos y crea la base de datos de tareas. Necesita internet y tarda un rato la primera vez.

Si algo falla, estas son las causas habituales:

| Paquete | Problema en Windows | Qué hace esta versión |
|---|---|---|
| `webrtcvad` | Necesita compilador C++ | Se instala `webrtcvad-wheels`, que trae el binario listo y se importa igual (`import webrtcvad`) |
| `llama-cpp-python` | Compilarlo exige Visual Studio Build Tools y CMake | Se baja la rueda precompilada de CPU desde `abetlen.github.io/llama-cpp-python/whl/cpu`. Si aun así intenta compilar, instala "Desktop development with C++" de [Visual Studio Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) y repite |
| `openwakeword` | `tflite-runtime` no existe en Windows | Atenea carga el modelo con `inference_framework="onnx"` (usa `onnxruntime`) y descarga los modelos sola la primera vez |
| `faster-whisper` | Nada especial | El modelo "small" se descarga solo la primera vez |

## 3. Modelos

`instalar.bat` ejecuta `descargar_modelos.py`, que baja de Hugging Face el LLM Qwen3-4B (Q4_K_M, unos 2.5 GB) y la voz de Piper. Si ya los tienes en Linux, puedes copiarlos aquí antes de instalar y se saltará la descarga:

```
Atenea\
  models\qwen3-4b-q4_k_m.gguf
  voices\es_ES-carlfm-x_low.onnx
  voices\es_ES-carlfm-x_low.onnx.json
```

Ya no hay rutas `/home/luis/...`. Todo se busca dentro de la carpeta de Atenea, así que funciona desde cualquier ubicación. Si falta un archivo, Atenea te dice cuál al arrancar.

## 4. Audio

En Linux la salida estaba fija en el dispositivo 11. Aquí `DISPOSITIVO_ENTRADA` y `DISPOSITIVO_SALIDA` valen `None`, así que se usan el micrófono y los altavoces predeterminados de Windows. Si quieres usar otros:

1. Abre una terminal en la carpeta, ejecuta `.venv\Scripts\activate` y luego `python listar_dispositivos.py`.
2. Pon el número que quieras en `Atenea.py` (sección Configuración). Cada aparato sale varias veces (MME, DirectSound, WASAPI). Si no sabes cuál elegir, usa el de MME, que acepta 16 kHz sin problema.

Si Windows no deja usar el micrófono, revisa Configuración > Privacidad > Micrófono > "Permitir que las aplicaciones de escritorio accedan al micrófono".

## 5. Spotify (opcional)

Guarda las claves una sola vez en una terminal:

```
setx SPOTIPY_CLIENT_ID "tu_client_id"
setx SPOTIPY_CLIENT_SECRET "tu_client_secret"
```

Cierra la terminal y abre otra para que se lean. Si no las pones, solo se desactivan las skills de Spotify y lo demás funciona.

## 6. Usar

- `iniciar.bat` arranca Atenea por voz (wake word "alexa").
- `iniciar_web.bat` arranca la página. Espera a que cargue los modelos y abre http://localhost:5000.

## Otros cambios respecto a la versión de Linux

- La consola se pone en UTF-8 para que los acentos y la ñ no rompan los `print`.
- `n_threads` del LLM se calcula según los núcleos del equipo en vez de estar fijo en 8.
- `Respuesta_modelo.wav` se guarda en la carpeta de Atenea, no donde se ejecute el comando.
- La web usa `os.path.join` para encontrar `web\index.html`.
- La carpeta del proyecto se añade a `sys.path`, así las skills cargan aunque abras Atenea con doble clic.
- Spotify da un mensaje claro si faltan las variables de entorno.

El código sigue funcionando en Linux sin cambios.
