"""
main.py - Ponto de entrada principal do AgiBench.
"""

import multiprocessing
import os
import sys

# Garante que o diretório raiz esteja no sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from agibench.ui.app import AgiBenchApp


def main():
    # Suporte para multiprocessing em executáveis e Windows
    multiprocessing.freeze_support()

    app = AgiBenchApp()
    app.mainloop()


if __name__ == "__main__":
    main()
