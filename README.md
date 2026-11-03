# Atenea

Asistente de voz en español que corre 100 % en local (sin nube) para un laboratorio de electrónica: gestiona tareas, proyectos e inventario de materiales por voz o desde una interfaz web.

![demo](docs/demo.gif)

## Características
- Pipeline de voz offline en CPU: wake word → VAD → ASR → LLM → TTS
- Router de intenciones con LLM que devuelve JSON estructurado para ejecutar herramientas
- Skills definidas en `skills.json`: añadir una no requiere tocar el código principal
- Gestión de tareas, proyectos e inventario de laboratorio (SQLite)
- Integración con Wikipedia y Spotify
- Interfaz web (voz y texto) con API REST en Flask

## Arquitectura
```
Micrófono → openWakeWord → WebRTC VAD → faster-whisper
                                              ↓
                                   Router (Qwen3-4B, T=0)
                                   ↙                    ↘
                          Skill (SQLite, APIs)     Conversación libre
                                   ↘                    ↙
                                        Piper TTS → Altavoz
```

## Resultados
| Métrica | Valor | Condiciones |
|---|---|---|
| Latencia fin de frase → inicio de voz | X s | CPU / RAM |
| Precisión del router | X/Y órdenes | N frases de prueba |
| RAM del sistema completo | X GB | |

## Instalación rápida
Requiere Python 3.11 de 64 bits.
```
instalar.bat
iniciar.bat        # modo voz
iniciar_web.bat    # interfaz web en http://localhost:5000
```
Guía completa en [LEEME.md](LEEME.md).

## Cómo añadir una skill
1. Escribe la función en `Skills/`.
2. Decláresela en `skills.json` con descripción, parámetros y ejemplos.
3. El prompt del router se genera solo.

## Decisiones técnicas
- **Qwen3-4B Q4_K_M:** equilibrio entre calidad en español y consumo en CPU.
- **Router con temperatura 0:** salidas deterministas y fáciles de validar.
- **Piper:** TTS neuronal ligero que corre offline.
- **ONNX en Windows:** `tflite-runtime` no está disponible.

## Limitaciones
- El LLM atiende una petición a la vez.
- La precisión del router depende de las descripciones de las skills.
- (Añade aquí las que hayas observado.)

## Trabajo futuro
- Evaluación sistemática del router
- (Tus ideas)

## Stack
Python · llama.cpp · faster-whisper · Piper · openWakeWord · Flask · SQLite
