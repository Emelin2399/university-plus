#!/usr/bin/env python3
"""Smoke test end-to-end contra el backend en marcha.

Ejecuta el flujo del MVP: crear asignatura -> subir PDF -> preguntar al tutor
-> generar cuestionario -> enviar intento. Reporta cada paso.

Uso:
    1. Arranca el backend en otra terminal:  uvicorn app.main:app --reload
    2. cd backend && source .venv/bin/activate
    3. python scripts/smoke_test.py [--url http://localhost:8000] [--token <JWT>]

Autenticación:
    - En modo desarrollo (sin Supabase) el backend acepta cualquier token;
      por defecto se usa "dev-token".
    - Con Supabase, pasa un access_token real de un usuario con --token.
"""
from __future__ import annotations

import argparse
import io
import sys

import httpx

GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"


def step_ok(msg: str) -> None:
    print(f"{GREEN}✓{RESET} {msg}")


def step_fail(msg: str) -> None:
    print(f"{RED}✗{RESET} {msg}")


def _minimal_pdf() -> bytes:
    """Genera un PDF mínimo válido con algo de texto para el procesamiento."""
    try:
        from pypdf import PdfWriter
    except ImportError:
        # PDF crudo mínimo (una página con texto) como fallback.
        return (
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]"
            b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
            b"4 0 obj<</Length 70>>stream\nBT /F1 12 Tf 20 100 Td "
            b"(UNIVERSITY PLUS smoke test content) Tj ET\nendstream endobj\n"
            b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
            b"trailer<</Root 1 0 R>>\n%%EOF"
        )
    buf = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=144)
    writer.write(buf)
    return buf.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--token", default="dev-token")
    args = parser.parse_args()

    base = args.url.rstrip("/")
    headers = {"Authorization": f"Bearer {args.token}"}
    failures = 0

    print(f"\n=== Smoke test contra {base} ===\n")

    with httpx.Client(timeout=60) as client:
        # 0. Health
        try:
            r = client.get(f"{base}/health")
            r.raise_for_status()
            info = r.json()
            step_ok(f"/health OK — provider={info.get('ai_provider')}, "
                    f"supabase={info.get('supabase_configured')}")
        except Exception as exc:
            step_fail(f"/health falló: {exc}. ¿Está el backend arrancado?")
            return 1

        # 1. Crear asignatura
        try:
            r = client.post(
                f"{base}/subjects",
                headers=headers,
                json={"name": "Smoke Test 101", "term": "2026-1"},
            )
            r.raise_for_status()
            subject = r.json()
            step_ok(f"Asignatura creada: {subject['id']}")
        except Exception as exc:
            step_fail(f"Crear asignatura falló: {exc}")
            return 1

        # 2. Subir documento
        try:
            files = {"file": ("prueba.pdf", _minimal_pdf(), "application/pdf")}
            r = client.post(
                f"{base}/documents",
                headers=headers,
                data={"subject_id": subject["id"]},
                files=files,
            )
            r.raise_for_status()
            doc = r.json()
            step_ok(f"Documento subido: {doc['id']} (status={doc['status']})")
        except Exception as exc:
            step_fail(f"Subir documento falló: {exc}")
            failures += 1

        # 2b. Agregar documento desde una URL (página web)
        try:
            r = client.post(
                f"{base}/documents/from-url",
                headers=headers,
                json={
                    "subject_id": subject["id"],
                    "url": "https://example.com/",
                },
            )
            if r.status_code == 201:
                link_doc = r.json()
                step_ok(f"Documento desde URL agregado: {link_doc['id']} "
                        f"(source={link_doc.get('source_type')})")
            else:
                # Puede fallar si el entorno no tiene salida a internet.
                print(f"  (omitido: /documents/from-url devolvió {r.status_code})")
        except Exception as exc:
            print(f"  (omitido: /documents/from-url no disponible: {exc})")

        # 3. Preguntar al tutor
        try:
            r = client.post(
                f"{base}/tutor/ask",
                headers=headers,
                json={"question": "¿De qué trata el material?",
                      "subject_id": subject["id"]},
            )
            r.raise_for_status()
            answer = r.json()
            step_ok(f"Tutor respondió ({len(answer['answer'])} chars, "
                    f"{len(answer['sources'])} fuentes)")
        except Exception as exc:
            step_fail(f"Tutor falló: {exc}")
            failures += 1

        # 4. Generar cuestionario
        try:
            r = client.post(
                f"{base}/quizzes",
                headers=headers,
                json={"subject_id": subject["id"], "title": "Quiz smoke",
                      "num_questions": 3, "difficulty": "easy"},
            )
            r.raise_for_status()
            quiz = r.json()
            step_ok(f"Cuestionario generado: {len(quiz['questions'])} preguntas")
        except Exception as exc:
            step_fail(f"Generar cuestionario falló: {exc}")
            return 1 if failures else 1

        # 5. Enviar intento
        try:
            answers = [
                {"question_id": q["id"],
                 "given_answer": (q.get("options") or ["Verdadero"])[0]}
                for q in quiz["questions"]
            ]
            r = client.post(
                f"{base}/quizzes/attempts",
                headers=headers,
                json={"quiz_id": quiz["id"], "answers": answers},
            )
            r.raise_for_status()
            result = r.json()
            step_ok(f"Intento enviado: {result['score']}% "
                    f"({result['correct']}/{result['total']})")
        except Exception as exc:
            step_fail(f"Enviar intento falló: {exc}")
            failures += 1

    print("\n" + "=" * 50)
    if failures == 0:
        step_ok("Smoke test completo: todos los pasos pasaron 🎉")
        return 0
    step_fail(f"{failures} paso(s) con error.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
