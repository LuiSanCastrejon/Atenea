import sqlite3
import os
from datetime import datetime, timedelta

#________________________________________________________________________________
#Configuración
DIRECTORIO = os.path.dirname(os.path.abspath(__file__))
RUTA_BD = os.path.join(DIRECTORIO, "atenea.db")

#________________________________________________________________________________
#Utilidades

def conectar():
    if not os.path.exists(RUTA_BD):
        try:
            from Skills.crear_base_datos import crear_base_datos
        except ImportError:
            from crear_base_datos import crear_base_datos
        crear_base_datos(RUTA_BD)
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    return conexion

def normalizar_fecha(fecha):
    # Acepta "hoy", "mañana", "pasado mañana", AAAA-MM-DD o DD/MM/AAAA
    if fecha is None:
        return datetime.now().strftime("%Y-%m-%d")
    texto = str(fecha).strip().lower()
    hoy = datetime.now()
    if texto == "hoy":
        return hoy.strftime("%Y-%m-%d")
    if texto in ("mañana", "manana"):
        return (hoy + timedelta(days=1)).strftime("%Y-%m-%d")
    if texto in ("pasado mañana", "pasado manana"):
        return (hoy + timedelta(days=2)).strftime("%Y-%m-%d")
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(texto, formato).strftime("%Y-%m-%d")
        except ValueError:
            pass
    raise ValueError(f"Fecha no reconocida: {fecha}")

def describir(tarea):
    estado = "hecha" if tarea["completada"] else "pendiente"
    hora = f" a las {tarea['hora']}" if tarea["hora"] else ""
    return f"[{tarea['id']}] {tarea['titulo']} - {tarea['fecha']}{hora} ({estado})"

#________________________________________________________________________________
#Gestión de tareas

def agregar_tarea(titulo, fecha=None, hora=None, descripcion=None):
    try:
        fecha = normalizar_fecha(fecha)
    except ValueError as e:
        return str(e)

    conexion = conectar()
    cursor = conexion.execute(
        "INSERT INTO tareas (titulo, descripcion, fecha, hora) VALUES (?, ?, ?, ?)",
        (titulo, descripcion, fecha, hora)
    )
    conexion.commit()
    id_tarea = cursor.lastrowid
    conexion.close()
    return f"Tarea {id_tarea} agregada: {titulo} para el {fecha}"

def listar_tareas(pendientes=True):
    conexion = conectar()
    consulta = "SELECT * FROM tareas"
    if pendientes:
        consulta += " WHERE completada = 0"
    consulta += " ORDER BY fecha, hora"
    tareas = conexion.execute(consulta).fetchall()
    conexion.close()

    if not tareas:
        return "No hay tareas."
    return "\n".join(describir(t) for t in tareas)

def tareas_del_dia(fecha=None):
    try:
        fecha = normalizar_fecha(fecha)
    except ValueError as e:
        return str(e)

    conexion = conectar()
    tareas = conexion.execute(
        "SELECT * FROM tareas WHERE fecha = ? ORDER BY hora", (fecha,)
    ).fetchall()
    conexion.close()

    if not tareas:
        return f"No hay tareas para el {fecha}."
    return "\n".join(describir(t) for t in tareas)

def tareas_entre(fecha_inicio, fecha_fin):
    try:
        fecha_inicio = normalizar_fecha(fecha_inicio)
        fecha_fin = normalizar_fecha(fecha_fin)
    except ValueError as e:
        return str(e)

    conexion = conectar()
    tareas = conexion.execute(
        "SELECT * FROM tareas WHERE fecha BETWEEN ? AND ? ORDER BY fecha, hora",
        (fecha_inicio, fecha_fin)
    ).fetchall()
    conexion.close()

    if not tareas:
        return f"No hay tareas entre el {fecha_inicio} y el {fecha_fin}."
    return "\n".join(describir(t) for t in tareas)

def tareas_de_la_semana():
    hoy = datetime.now()
    return tareas_entre(hoy.strftime("%Y-%m-%d"), (hoy + timedelta(days=7)).strftime("%Y-%m-%d"))

def describir_tareas(titulo=None, fecha=None):
    # Busca por parte del título, por fecha o por ambos, y dice la descripción
    consulta = "SELECT * FROM tareas WHERE 1 = 1"
    valores = []
    if titulo:
        # Cada palabra debe aparecer en el título, así "soldar kyon" encuentra "Soldar placa de Kyon"
        for palabra in str(titulo).split():
            consulta += " AND titulo LIKE ?"
            valores.append(f"%{palabra}%")
    if fecha:
        try:
            valores.append(normalizar_fecha(fecha))
        except ValueError as e:
            return str(e)
        consulta += " AND fecha = ?"
    elif not titulo:
        consulta += " AND completada = 0"
    consulta += " ORDER BY fecha, hora"

    conexion = conectar()
    tareas = conexion.execute(consulta, valores).fetchall()
    conexion.close()

    if not tareas:
        return "No encontré tareas con esos datos."

    frases = []
    for t in tareas:
        hora = f" a las {t['hora']}" if t["hora"] else ""
        descripcion = t["descripcion"] or "no tiene descripción"
        frases.append(f"{t['titulo']}, el {t['fecha']}{hora}: {descripcion}.")
    return " ".join(frases)

def actualizar_tarea(id_tarea, titulo=None, fecha=None, hora=None, descripcion=None):
    cambios = {}
    if titulo is not None:
        cambios["titulo"] = titulo
    if fecha is not None:
        try:
            cambios["fecha"] = normalizar_fecha(fecha)
        except ValueError as e:
            return str(e)
    if hora is not None:
        cambios["hora"] = hora
    if descripcion is not None:
        cambios["descripcion"] = descripcion
    if not cambios:
        return "No indicaste nada que cambiar."

    columnas = ", ".join(f"{c} = ?" for c in cambios)
    conexion = conectar()
    cursor = conexion.execute(
        f"UPDATE tareas SET {columnas} WHERE id = ?", (*cambios.values(), id_tarea)
    )
    conexion.commit()
    conexion.close()

    if cursor.rowcount == 0:
        return f"No existe la tarea {id_tarea}."
    return f"Tarea {id_tarea} actualizada."

def buscar_por_titulo(conexion, titulo, solo_pendientes=False):
    # Cada palabra debe aparecer en el título
    consulta = "SELECT * FROM tareas WHERE 1 = 1"
    valores = []
    for palabra in str(titulo).split():
        consulta += " AND titulo LIKE ?"
        valores.append(f"%{palabra}%")
    if solo_pendientes:
        consulta += " AND completada = 0"
    return conexion.execute(consulta + " ORDER BY fecha, hora", valores).fetchall()

def completar_tarea(tarea):
    # Acepta el número de la tarea o su nombre ("soldar Kyon")
    conexion = conectar()
    texto = str(tarea).strip()
    if texto.isdigit():
        encontradas = conexion.execute("SELECT * FROM tareas WHERE id = ?", (int(texto),)).fetchall()
    else:
        encontradas = buscar_por_titulo(conexion, texto, solo_pendientes=True)

    if not encontradas:
        conexion.close()
        return f"No encontré una tarea pendiente llamada {texto}."
    if len(encontradas) > 1:
        conexion.close()
        nombres = ", ".join(f"{t['titulo']} (número {t['id']})" for t in encontradas)
        return f"Encontré varias tareas: {nombres}. ¿Cuál quieres marcar como hecha?"

    t = encontradas[0]
    conexion.execute("UPDATE tareas SET completada = 1 WHERE id = ?", (t["id"],))
    conexion.commit()
    conexion.close()
    return f"Listo, marqué como hecha la tarea {t['titulo']}."

def marcar_tarea(id_tarea, completada=True):
    # Marca (o desmarca) una tarea como hecha por su número; lo usa la checkbox de la web
    conexion = conectar()
    cursor = conexion.execute(
        "UPDATE tareas SET completada = ? WHERE id = ?", (1 if completada else 0, id_tarea)
    )
    conexion.commit()
    conexion.close()

    if cursor.rowcount == 0:
        return f"No existe la tarea {id_tarea}."
    estado = "hecha" if completada else "pendiente"
    return f"Tarea {id_tarea} marcada como {estado}."

def eliminar_tarea(id_tarea):
    conexion = conectar()
    cursor = conexion.execute("DELETE FROM tareas WHERE id = ?", (id_tarea,))
    conexion.commit()
    conexion.close()

    if cursor.rowcount == 0:
        return f"No existe la tarea {id_tarea}."
    return f"Tarea {id_tarea} eliminada."

#________________________________________________________________________________
#Prueba rápida

if __name__ == "__main__":
    print(agregar_tarea("Soldar placa del robot", "hoy", "16:00"))
    print(agregar_tarea("Revisar osciloscopio", "mañana"))
    print(tareas_del_dia("hoy"))
    print(tareas_de_la_semana())
