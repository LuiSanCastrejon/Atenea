# Servidor web local para Atenea
# Uso:  python servidor_web.py  (o doble clic en iniciar_web.bat)  y abrir http://localhost:5000 en el navegador
# Requiere: pip install flask
import io
import os
import re
import wave
import base64
import threading

import flask.cli
from flask import Flask, request, jsonify, send_from_directory

# Importar Atenea carga los modelos (Whisper, Piper, LLM, skills) pero no arranca
# el bucle de la wakeword, que solo corre al ejecutar Atenea.py directamente
import Atenea
# Base de datos de tareas (Skills/gestor_tareas.py)
from Skills import gestor_tareas
# Base de datos de proyectos (Skills/gestor_proyectos.py), en el mismo atenea.db
from Skills import gestor_proyectos
# Inventario de materiales del laboratorio (Skills/gestor_materiales.py), también en atenea.db
from Skills import gestor_materiales

#________________________________________________________________________________
#Configuración
HOST = "127.0.0.1"   # Solo accesible desde esta computadora
PUERTO = 5000

app = Flask(__name__, static_folder=None)
# En Windows el banner de Flask (que usa click) falla con "OSError: Windows error 6"
# porque llama_cpp toca los manejadores de la consola al cargar el modelo.
# Se desactiva; la dirección ya se muestra con print al arrancar
flask.cli.show_server_banner = lambda *args, **kwargs: None
# El LLM no admite varias peticiones a la vez: se atienden de una en una
candado = threading.Lock()

#________________________________________________________________________________
#Funciones

def sintetizar(mensaje):
    """Convierte el texto a voz con Piper y devuelve el WAV en base64."""
    mensaje = re.sub(r"[*#`]", "", mensaje).replace("_", " ")
    if not mensaje.strip():
        return None
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        Atenea.voice.synthesize_wav(mensaje, wav_file)
    return base64.b64encode(buffer.getvalue()).decode("ascii")

def responder(texto_usuario):
    print("Usuario (web):", texto_usuario)
    respuesta = Atenea.procesar_orden(texto_usuario)
    print("Asistente (web):", respuesta)
    try:
        audio = sintetizar(respuesta)
    except Exception as e:
        print("Error al generar la voz:", e)
        audio = None
    return {"usuario": texto_usuario, "respuesta": respuesta, "audio": audio}

#________________________________________________________________________________
#Rutas

@app.route("/")
def inicio():
    # os.path.join usa la barra correcta en Windows (\) y en Linux (/)
    return send_from_directory(os.path.join(Atenea.DIRECTORIO, "web"), "index.html")

@app.route("/texto", methods=["POST"])
def texto():
    texto_usuario = (request.get_json(silent=True) or {}).get("texto", "").strip()
    if not texto_usuario:
        return jsonify({"error": "No escribiste nada."}), 400
    with candado:
        return jsonify(responder(texto_usuario))

@app.route("/audio", methods=["POST"])
def audio():
    archivo = request.files.get("audio")
    if archivo is None:
        return jsonify({"error": "No llegó el audio."}), 400
    with candado:
        # faster-whisper decodifica el audio del navegador (webm/ogg) por sí mismo
        try:
            segmentos, _ = Atenea.model_whisper.transcribe(
                io.BytesIO(archivo.read()), language="es"
            )
            texto_usuario = "".join(s.text for s in segmentos).strip()
        except Exception as e:
            print("Error al transcribir:", e)
            return jsonify({"error": "No pude leer el audio."}), 400
        if not texto_usuario:
            return jsonify({"error": "No entendí lo que dijiste."}), 400
        return jsonify(responder(texto_usuario))

@app.route("/tareas", methods=["GET"])
def ver_tareas():
    # Devuelve todas las tareas con todas sus columnas; ?todas=0 deja solo las pendientes
    consulta = "SELECT * FROM tareas"
    if request.args.get("todas", "1") == "0":
        consulta += " WHERE completada = 0"
    consulta += " ORDER BY completada, fecha, hora IS NULL, hora, id"
    conexion = gestor_tareas.conectar()
    tareas = [dict(t) for t in conexion.execute(consulta).fetchall()]
    conexion.close()
    return jsonify({"tareas": tareas})

@app.route("/tareas", methods=["POST"])
def nueva_tarea():
    datos = request.get_json(silent=True) or {}
    # Los campos vacíos se mandan como None para que la base use sus valores por defecto
    campos = {c: (str(datos.get(c) or "").strip() or None)
              for c in ("titulo", "descripcion", "fecha", "hora")}
    if not campos["titulo"]:
        return jsonify({"error": "La tarea necesita un título."}), 400
    resultado = gestor_tareas.agregar_tarea(**campos)
    return jsonify({"resultado": resultado})

@app.route("/tareas/<int:id_tarea>/completada", methods=["POST"])
def marcar_tarea(id_tarea):
    # La checkbox de la web manda {"completada": true} o {"completada": false}
    completada = bool((request.get_json(silent=True) or {}).get("completada"))
    resultado = gestor_tareas.marcar_tarea(id_tarea, completada)
    if resultado.startswith("No existe"):
        return jsonify({"error": resultado}), 404
    return jsonify({"resultado": resultado})

@app.route("/proyectos", methods=["GET"])
def ver_proyectos():
    # Por defecto solo los abiertos; ?todos=1 incluye también los cerrados
    solo_abiertos = request.args.get("todos", "0") != "1"
    return jsonify({"proyectos": gestor_proyectos.listar_proyectos(solo_abiertos)})

@app.route("/proyectos", methods=["POST"])
def nuevo_proyecto():
    datos = request.get_json(silent=True) or {}
    campos = {c: (str(datos.get(c) or "").strip() or None)
              for c in ("nombre", "descripcion", "fecha_inicio", "objetivos")}
    if not campos["nombre"]:
        return jsonify({"error": "El proyecto necesita un nombre."}), 400
    resultado = gestor_proyectos.agregar_proyecto(**campos)
    return jsonify({"resultado": resultado})

@app.route("/proyectos/<int:id_proyecto>/abierto", methods=["POST"])
def marcar_proyecto(id_proyecto):
    # El botón de la web manda {"abierto": false} para cerrar o {"abierto": true} para reabrir
    abierto = bool((request.get_json(silent=True) or {}).get("abierto"))
    resultado = gestor_proyectos.marcar_proyecto(id_proyecto, abierto)
    if resultado.startswith("No existe"):
        return jsonify({"error": resultado}), 404
    return jsonify({"resultado": resultado})

@app.route("/materiales", methods=["GET"])
def ver_materiales():
    # ?buscar=texto filtra por nombre, categoría o ubicación; ?disponibles=1 oculta los agotados
    busqueda = request.args.get("buscar", "").strip() or None
    solo_disponibles = request.args.get("disponibles", "0") == "1"
    return jsonify({"materiales": gestor_materiales.listar_materiales(busqueda, solo_disponibles)})

@app.route("/materiales", methods=["POST"])
def nuevo_material():
    datos = request.get_json(silent=True) or {}
    campos = {c: (str(datos.get(c) or "").strip() or None)
              for c in ("nombre", "categoria", "ubicacion", "notas")}
    if not campos["nombre"]:
        return jsonify({"error": "El material necesita un nombre."}), 400
    resultado = gestor_materiales.agregar_material(cantidad=datos.get("cantidad"), **campos)
    if resultado.startswith("La cantidad"):
        return jsonify({"error": resultado}), 400
    return jsonify({"resultado": resultado})

@app.route("/materiales/<int:id_material>/cantidad", methods=["POST"])
def cambiar_material(id_material):
    # Los botones + y − de la web mandan {"cambio": 1} o {"cambio": -1}
    try:
        cambio = int((request.get_json(silent=True) or {}).get("cambio", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "El cambio debe ser un número entero."}), 400
    resultado = gestor_materiales.cambiar_cantidad(id_material, cambio)
    if resultado.startswith("No existe"):
        return jsonify({"error": resultado}), 404
    return jsonify({"resultado": resultado})

#________________________________________________________________________________
if __name__ == "__main__":
    print(f"Atenea web en http://localhost:{PUERTO}")
    app.run(host=HOST, port=PUERTO, threaded=True)
