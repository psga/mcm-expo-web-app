"""Wrapper de desarrollo para el Preview tool: lee el puerto asignado
dinámicamente (env var PORT) y arranca streamlit con --server.port en vez
de un puerto fijo hardcodeado. No es parte de la app en sí.
"""

import os
import subprocess
import sys

APP_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.py")


def main() -> int:
    port = os.environ.get("PORT", "8501")
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        APP_PATH,
        "--server.headless",
        "true",
        "--server.port",
        port,
    ]
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    sys.exit(main())
