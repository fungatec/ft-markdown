"""Lanzador para PyInstaller.

PyInstaller necesita un script de entrada ejecutable; `ft_markdown/__main__.py` usa imports
relativos y no sirve directamente. Este archivo solo delega en main().
"""

from ft_markdown.__main__ import main

raise SystemExit(main())
