"""
spekgen_paths.py — Resolución portable de paths SPEKGEN cross-platform.

USO:
    from spekgen_paths import drive_root, client_dir, find_xlsx

    # Raíz del Drive sincronizado (01. CLIENTS OFFICIAL)
    root = drive_root()

    # Carpeta de un cliente
    f24 = client_dir("F24")           # → .../F24- FERRE24
    hc  = client_dir("HC")            # → .../HC - HEALTHY CHUCHOS

CÓMO RESUELVE:
    1. Si SPEKGEN_ROOT (env var) está seteada → la usa.
    2. Sino, walk-up desde __file__ buscando el anchor "01. CLIENTS OFFICIAL".
    3. Si tampoco → busca en candidatos comunes por OS:
        - Mac: ~/Library/CloudStorage/GoogleDrive-*/My Drive*/01. CLIENTS OFFICIAL
        - Windows: G:/My Drive/01. CLIENTS OFFICIAL, G:/Shared drives/.../01. CLIENTS OFFICIAL
        - Linux: ~/google-drive/01. CLIENTS OFFICIAL
    4. RuntimeError con mensaje claro si nada funciona.

Esto SIEMPRE debe funcionar igual en máquina de Gibran (Mac) y Pedro (Windows)
sin tocar el código. NO hardcodear /Users/gibranalonzo/ en ningún script.
"""
import os
import sys
from pathlib import Path
from typing import Optional

ANCHOR = "01. CLIENTS OFFICIAL"

# Mapeo: client_code → folder name en Drive
CLIENT_FOLDERS = {
    "HC": "HC - HEALTHY CHUCHOS",
    "LF": "LF - LO FITNESS",
    "GR": "GR - GREENRAY",
    "MG": "MG - METAGREEN",
    "F24": "F24- FERRE24",
    "SPK": "SPK - SPEKGEN AGENCY",
    "CMI": "CMI - PERSONAL (MAMÁ GIBRAN)",  # ajusta si el nombre real difiere
}


def _candidate_roots() -> list[Path]:
    """Genera candidatos típicos donde podría estar '01. CLIENTS OFFICIAL' según OS."""
    home = Path.home()
    candidates: list[Path] = []

    if sys.platform == "darwin":  # macOS
        cloud = home / "Library" / "CloudStorage"
        if cloud.exists():
            for gd in cloud.glob("GoogleDrive-*"):
                # Drive típicamente monta como "My Drive" o "My Drive 2" o "Mi unidad"
                for my_drive in gd.iterdir():
                    if my_drive.is_dir() and (my_drive / ANCHOR).exists():
                        candidates.append(my_drive / ANCHOR)
                # Shared drives también
                shared = gd / "Shared drives"
                if shared.exists():
                    for sd in shared.iterdir():
                        if (sd / ANCHOR).exists():
                            candidates.append(sd / ANCHOR)
    elif sys.platform == "win32":  # Windows
        # Google Drive Desktop suele mapear a una letra (G:, H:, etc.)
        for letter in "GHIJKLMNOPQRSTUVWXYZ":
            for sub in ("My Drive", "Mi unidad", "Shared drives"):
                p = Path(f"{letter}:/") / sub
                if p.exists():
                    direct = p / ANCHOR
                    if direct.exists():
                        candidates.append(direct)
                    # Shared drives son contenedores → un nivel más
                    if sub == "Shared drives":
                        for sd in p.iterdir():
                            if (sd / ANCHOR).exists():
                                candidates.append(sd / ANCHOR)
        # Mirror mode (Drive sincroniza a carpeta del user profile)
        for sub in ("My Drive", "Mi unidad", "Google Drive"):
            p = home / sub / ANCHOR
            if p.exists():
                candidates.append(p)
    else:  # linux y otros
        for sub in ("google-drive", "GoogleDrive", "Google Drive"):
            p = home / sub / ANCHOR
            if p.exists():
                candidates.append(p)

    return candidates


def drive_root() -> Path:
    """Resuelve la ruta absoluta a '01. CLIENTS OFFICIAL'."""
    # 1. Env var explícita
    env = os.environ.get("SPEKGEN_ROOT") or os.environ.get("F24_PRODUCTS_DIR")
    if env:
        p = Path(env)
        # Si apuntan a F24-PRODUCTOS por compatibilidad legacy, sube al root
        if p.name == "F24 - 02. PRODUCTOS":
            p = p.parent.parent
        if p.name == ANCHOR:
            return p
        # Acepta que apunten al root real
        if (p / ANCHOR).exists():
            return p / ANCHOR
        if p.exists():
            return p

    # 2. Walk up desde __file__
    here = Path(__file__).resolve()
    for parent in here.parents:
        if parent.name == ANCHOR:
            return parent

    # 3. Candidatos por OS
    for c in _candidate_roots():
        return c

    # 4. Fallar con mensaje útil
    raise RuntimeError(
        f"No pude localizar '{ANCHOR}'. Opciones:\n"
        f"  - Set SPEKGEN_ROOT=/ruta/absoluta\n"
        f"  - Mueve este script dentro del Drive sincronizado\n"
        f"  - Verifica que Google Drive Desktop tenga '{ANCHOR}' sincronizado\n"
        f"OS detectado: {sys.platform}"
    )


def client_dir(code: str) -> Path:
    """Devuelve la carpeta de un cliente por su código (HC/LF/GR/MG/F24/SPK)."""
    code = code.upper()
    if code not in CLIENT_FOLDERS:
        raise ValueError(f"Cliente desconocido '{code}'. Conocidos: {list(CLIENT_FOLDERS)}")
    p = drive_root() / CLIENT_FOLDERS[code]
    if not p.exists():
        raise FileNotFoundError(f"Carpeta del cliente {code} no existe en disco: {p}")
    return p


def find_xlsx(client_code: str, filename_pattern: str) -> Optional[Path]:
    """Busca un xlsx por patrón dentro de la carpeta del cliente. Ej: find_xlsx('F24', '*PRIORITARIOS*.xlsx')."""
    matches = list(client_dir(client_code).rglob(filename_pattern))
    return matches[0] if matches else None


if __name__ == "__main__":
    import json
    print(json.dumps({
        "platform": sys.platform,
        "drive_root": str(drive_root()),
        "clients": {code: str(client_dir(code)) for code in CLIENT_FOLDERS if (drive_root() / CLIENT_FOLDERS[code]).exists()},
    }, indent=2, ensure_ascii=False))
