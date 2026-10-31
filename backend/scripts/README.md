# Scripts de utilidad

Scripts para verificar el entorno y probar el backend. Ejecútalos desde la
carpeta `backend/` con el entorno virtual activado.

## `check_setup.py`

Verifica (sin modificar nada) que el entorno esté listo:

```bash
python scripts/check_setup.py
```

Comprueba:
- Que exista `.env` y la configuración cargue.
- Que las variables de Supabase estén presentes y válidas.
- Que la **conexión a Supabase** funcione y la tabla `profiles` sea accesible.
- Que la función RPC `match_document_chunks` (RAG) exista.
- El estado del proveedor de IA (mock u openai).

## `smoke_test.py`

Prueba el flujo completo del MVP contra el backend en marcha:

```bash
# Backend arrancado en otra terminal
python scripts/smoke_test.py
# Con Supabase real:
python scripts/smoke_test.py --url http://localhost:8000 --token <ACCESS_TOKEN>
```

Ejecuta en orden: salud → crear asignatura → subir PDF → preguntar al tutor →
generar cuestionario → enviar intento, e informa el resultado de cada paso.
