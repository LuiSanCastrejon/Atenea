import sqlite3
import os

#________________________________________________________________________________
#Configuración
DIRECTORIO = os.path.dirname(os.path.abspath(__file__))
RUTA_BD = os.path.join(DIRECTORIO, "atenea.db")

#________________________________________________________________________________
#Creación de la base de datos

def crear_tablas(conexion):
    # Solo crea lo que falta (IF NOT EXISTS): se puede llamar sobre una base que ya
    # tiene datos sin perder nada, así las bases antiguas ganan las tablas de proyectos y materiales
    cursor = conexion.cursor()

    # fecha en formato AAAA-MM-DD y hora en HH:MM (la hora es opcional)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo      TEXT NOT NULL,
            descripcion TEXT,
            fecha       TEXT NOT NULL,
            hora        TEXT,
            completada  INTEGER NOT NULL DEFAULT 0,
            creada      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tareas_fecha ON tareas (fecha)")

    # fecha_inicio en formato AAAA-MM-DD; abierto = 1 mientras el proyecto sigue en curso
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre       TEXT NOT NULL,
            descripcion  TEXT,
            fecha_inicio TEXT NOT NULL,
            objetivos    TEXT,
            abierto      INTEGER NOT NULL DEFAULT 1,
            creado       TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Inventario del laboratorio: cantidad = unidades disponibles (0 = agotado)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materiales (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre      TEXT NOT NULL,
            cantidad    INTEGER NOT NULL DEFAULT 0,
            categoria   TEXT,
            ubicacion   TEXT,
            notas       TEXT,
            creado      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    """)
    conexion.commit()

def crear_base_datos(ruta=RUTA_BD):
    conexion = sqlite3.connect(ruta)
    crear_tablas(conexion)
    conexion.close()
    print(f"Base de datos lista en {ruta}")

if __name__ == "__main__":
    crear_base_datos()
