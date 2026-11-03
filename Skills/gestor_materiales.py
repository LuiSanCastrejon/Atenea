import sqlite3
import unicodedata

try:
    from Skills.gestor_tareas import RUTA_BD
    from Skills.crear_base_datos import crear_tablas
except ImportError:
    from gestor_tareas import RUTA_BD
    from crear_base_datos import crear_tablas

#________________________________________________________________________________
#Utilidades

def conectar():
    # Usa la misma base que las tareas (atenea.db). crear_tablas añade la tabla de
    # materiales si la base es de antes y aún no la tiene, sin tocar lo demás
    conexion = sqlite3.connect(RUTA_BD)
    crear_tablas(conexion)
    conexion.row_factory = sqlite3.Row
    return conexion

def simplificar(texto):
    # Minúsculas y sin acentos, para que "capacitor" encuentre "Capacitór" y viceversa
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")

def coincide(material, palabras):
    # Todas las palabras buscadas deben aparecer en el nombre, la categoría o la ubicación
    texto = simplificar(" ".join(str(material[c] or "") for c in ("nombre", "categoria", "ubicacion")))
    return all(p in texto for p in palabras)

#________________________________________________________________________________
#Gestión de materiales

def agregar_material(nombre, cantidad=0, categoria=None, ubicacion=None, notas=None):
    try:
        cantidad = int(cantidad or 0)
    except (TypeError, ValueError):
        return "La cantidad debe ser un número entero."
    if cantidad < 0:
        return "La cantidad no puede ser negativa."

    conexion = conectar()
    # Si ya hay un material con el mismo nombre, se suman las unidades en vez de duplicarlo
    for m in conexion.execute("SELECT id, nombre, cantidad FROM materiales").fetchall():
        if simplificar(m["nombre"]).strip() == simplificar(nombre).strip():
            total = m["cantidad"] + cantidad
            conexion.execute("UPDATE materiales SET cantidad = ? WHERE id = ?", (total, m["id"]))
            conexion.commit()
            conexion.close()
            return f"{m['nombre']} ya estaba en el inventario; ahora hay {total}."

    cursor = conexion.execute(
        "INSERT INTO materiales (nombre, cantidad, categoria, ubicacion, notas) VALUES (?, ?, ?, ?, ?)",
        (nombre, cantidad, categoria, ubicacion, notas)
    )
    conexion.commit()
    id_material = cursor.lastrowid
    conexion.close()
    unidades = "1 disponible" if cantidad == 1 else f"{cantidad} disponibles"
    return f"Material {id_material} agregado: {nombre}, {unidades}."

def listar_materiales(busqueda=None, solo_disponibles=False):
    conexion = conectar()
    consulta = "SELECT * FROM materiales"
    if solo_disponibles:
        consulta += " WHERE cantidad > 0"
    consulta += " ORDER BY nombre COLLATE NOCASE, id"
    materiales = [dict(m) for m in conexion.execute(consulta).fetchall()]
    conexion.close()

    palabras = simplificar(busqueda).split()
    if palabras:
        materiales = [m for m in materiales if coincide(m, palabras)]
    return materiales

def cambiar_cantidad(id_material, cambio):
    # Suma o resta unidades (los botones + y − de la web); nunca baja de cero
    conexion = conectar()
    material = conexion.execute("SELECT * FROM materiales WHERE id = ?", (id_material,)).fetchone()
    if material is None:
        conexion.close()
        return f"No existe el material {id_material}."
    total = max(0, material["cantidad"] + int(cambio))
    conexion.execute("UPDATE materiales SET cantidad = ? WHERE id = ?", (total, id_material))
    conexion.commit()
    conexion.close()
    return f"{material['nombre']}: quedan {total}."

def buscar_material(material):
    # Versión en texto para que Atenea responda en voz alta si hay un material
    encontrados = listar_materiales(material)
    if not encontrados:
        return f"No tengo registrado {material} en el inventario."
    frases = []
    for m in encontrados[:5]:
        ubicacion = f", en {m['ubicacion']}" if m["ubicacion"] else ""
        if m["cantidad"] > 0:
            frases.append(f"hay {m['cantidad']} de {m['nombre']}{ubicacion}.")
        else:
            frases.append(f"{m['nombre']} está agotado.")
    if len(encontrados) > 5:
        frases.append(f"Y {len(encontrados) - 5} más; búscalos en la página.")
    disponibles = any(m["cantidad"] > 0 for m in encontrados)
    inicio = "Sí, " if disponibles else "No hay disponible: "
    return inicio + " ".join(frases)

#________________________________________________________________________________
#Órdenes por voz o chat (skills.json)

def encontrar_material(material):
    # Busca un material por nombre: primero exacto y, si no, el único que coincida.
    # Devuelve (fila, None) o (None, mensaje para el usuario)
    nombre = simplificar(material).strip()
    encontrados = listar_materiales(material)
    exactos = [m for m in encontrados if simplificar(m["nombre"]).strip() == nombre]
    if exactos:
        return exactos[0], None
    if len(encontrados) == 1:
        return encontrados[0], None
    if not encontrados:
        return None, f"No tengo registrado {material} en el inventario."
    nombres = ", ".join(m["nombre"] for m in encontrados[:5])
    return None, f"Hay varios materiales que coinciden con {material}: {nombres}. ¿Cuál de ellos?"

def guardar_material(material, cantidad=1, categoria=None, ubicacion=None):
    # Agregar o reponer por voz: si no se dice cuántos, se cuenta una unidad.
    # agregar_material ya suma las unidades si el material existe
    if int(cantidad) <= 0:
        return "La cantidad para agregar debe ser mayor que cero."
    # Por voz llega en minúsculas ("capacitor"); se guarda con la primera en mayúscula
    material = material.strip()
    return agregar_material(material[:1].upper() + material[1:], cantidad, categoria, ubicacion)

def usar_material(material, cantidad=1):
    # Descuenta unidades del inventario cuando se usan o se gastan
    m, mensaje = encontrar_material(material)
    if m is None:
        return mensaje
    if int(cantidad) <= 0:
        return "La cantidad que usaste debe ser mayor que cero."
    if m["cantidad"] == 0:
        return f"{m['nombre']} ya está agotado."
    if m["cantidad"] < int(cantidad):
        return f"Solo hay {m['cantidad']} de {m['nombre']}; no puedo descontar {cantidad}."
    return cambiar_cantidad(m["id"], -int(cantidad))

#________________________________________________________________________________
#Prueba rápida

if __name__ == "__main__":
    print(agregar_material("Resistencia 10k", 50, "Resistencias", "Cajón A1"))
    print(agregar_material("Arduino Nano", 3, "Microcontroladores", "Estante 2"))
    print(buscar_material("arduino"))
    print(buscar_material("osciloscopio"))
    