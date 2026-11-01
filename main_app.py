"""JustPressDownload (JPD) - Standalone Desktop Application Entry Point."""

import sys
import os

# Ensure src is on python path when running from source or frozen
src_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if os.path.exists(src_dir) and src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from idm_gui.app import main

if __name__ == "__main__":
    main()
