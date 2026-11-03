import sqlite3
import os

try:
    from Skills.gestor_tareas import RUTA_BD, normalizar_fecha
    from Skills.crear_base_datos import crear_tablas
except ImportError:
    from gestor_tareas import RUTA_BD, normalizar_fecha
    from crear_base_datos import crear_tablas

#________________________________________________________________________________
#Utilidades

def conectar():
    # Usa la misma base que las tareas (atenea.db). crear_tablas añade la tabla de
    # proyectos si la base es de antes y aún no la tiene, sin tocar las tareas
    conexion = sqlite3.connect(RUTA_BD)
    crear_tablas(conexion)
    conexion.row_factory = sqlite3.Row
    return conexion

#________________________________________________________________________________
#Gestión de proyectos

def agregar_proyecto(nombre, descripcion=None, fecha_inicio=None, objetivos=None):
    try:
        fecha_inicio = normalizar_fecha(fecha_inicio)
    except ValueError as e:
        return str(e)

    conexion = conectar()
    cursor = conexion.execute(
        "INSERT INTO proyectos (nombre, descripcion, fecha_inicio, objetivos) VALUES (?, ?, ?, ?)",
        (nombre, descripcion, fecha_inicio, objetivos)
    )
    conexion.commit()
    id_proyecto = cursor.lastrowid
    conexion.close()
    return f"Proyecto {id_proyecto} agregado: {nombre}, iniciado el {fecha_inicio}"

def listar_proyectos(solo_abiertos=True):
    conexion = conectar()
    consulta = "SELECT * FROM proyectos"
    if solo_abiertos:
        consulta += " WHERE abierto = 1"
    consulta += " ORDER BY abierto DESC, fecha_inicio, id"
    proyectos = [dict(p) for p in conexion.execute(consulta).fetchall()]
    conexion.close()
    return proyectos

def proyectos_abiertos():
    # Versión en texto para que Atenea la diga en voz alta
    proyectos = listar_proyectos()
    if not proyectos:
        return "No tienes proyectos abiertos."
    frases = []
    for p in proyectos:
        descripcion = f": {p['descripcion']}" if p["descripcion"] else ""
        frases.append(f"{p['nombre']}, iniciado el {p['fecha_inicio']}{descripcion}.")
    cuantos = "un proyecto abierto" if len(proyectos) == 1 else f"{len(proyectos)} proyectos abiertos"
    return f"Tienes {cuantos}. " + " ".join(frases)

def marcar_proyecto(id_proyecto, abierto=True):
    # Abre o cierra un proyecto por su número; lo usa el botón de la web
    conexion = conectar()
    cursor = conexion.execute(
        "UPDATE proyectos SET abierto = ? WHERE id = ?", (1 if abierto else 0, id_proyecto)
    )
    conexion.commit()
    conexion.close()

    if cursor.rowcount == 0:
        return f"No existe el proyecto {id_proyecto}."
    estado = "abierto" if abierto else "cerrado"
    return f"Proyecto {id_proyecto} marcado como {estado}."

#________________________________________________________________________________
#Prueba rápida

if __name__ == "__main__":
    print(agregar_proyecto("Robot seguidor de línea", "Chasis con dos motores", "hoy", "Seguir una línea negra"))
    print(proyectos_abiertos())
