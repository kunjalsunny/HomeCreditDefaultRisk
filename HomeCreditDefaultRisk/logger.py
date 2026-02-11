import logging as _logging
import os
import sys
from datetime import datetime

def setup_logging():
    # Always write logs under project directory where this logger.py lives
    project_root = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(project_root, "Logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    log_path = os.path.join(log_dir, log_file)

    root = _logging.getLogger()
    root.setLevel(_logging.INFO)

    fmt = _logging.Formatter("[%(asctime)s] %(lineno)d %(name)s - %(levelname)s - %(message)s")

    # --- Ensure console handler exists ---
    has_console = any(
        isinstance(h, _logging.StreamHandler) and getattr(h, "stream", None) in (sys.stdout, sys.stderr)
        for h in root.handlers
    )
    if not has_console:
        ch = _logging.StreamHandler(sys.stdout)
        ch.setLevel(_logging.INFO)
        ch.setFormatter(fmt)
        root.addHandler(ch)

    # --- Ensure file handler exists ---
    has_file = any(isinstance(h, _logging.FileHandler) for h in root.handlers)
    if not has_file:
        fh = _logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(_logging.INFO)
        fh.setFormatter(fmt)
        root.addHandler(fh)

    # IMPORTANT: flush immediately (helps in some IDEs)
    root.info("Logger initialized. log_dir=%s log_file=%s", log_dir, log_path)
    for h in root.handlers:
        try:
            h.flush()
        except Exception:
            pass

    return root

logging = setup_logging()
