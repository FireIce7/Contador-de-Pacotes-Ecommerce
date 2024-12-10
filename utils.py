# utils.py

import os
import logging
import winsound
import threading
from config import ALERT_SOUND_PATH, PACKAGE_CODE_REGEX
from tkinter import messagebox

def detect_transportadora(codigo):
    """
    Detecta a transportadora com base no código fornecido.
    """
    codigo = codigo.strip()
    if PACKAGE_CODE_REGEX.match(codigo):
        if codigo.startswith(("GC", "AJ")) and len(codigo) == 18 and codigo[2:].isdigit():
            return "SHEIN"
        elif codigo.startswith("BR") and len(codigo) == 15 and codigo[2:].isalnum():
            return "Shopee"
        elif codigo.startswith("44") and len(codigo) == 11 and codigo.isdigit():
            return "Mercado Livre"
        elif codigo.isdigit() and len(codigo) >= 15:
            return "Nota Fiscal"
    return None

def play_sound(sound_type='error'):
    """
    Reproduz um som baseado no tipo especificado.
    """
    def _play():
        try:
            if sound_type == 'error':
                sound_path = ALERT_SOUND_PATH
                if os.path.exists(sound_path):
                    winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
            elif sound_type == 'alert':
                sound_path = ALERT_SOUND_PATH
                if os.path.exists(sound_path):
                    winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception as e:
            logging.error("Erro ao tocar o som (%s): %s", sound_type, e)

    threading.Thread(target=_play, daemon=True).start()

def center_window(window):
    """
    Centraliza a janela na tela.
    """
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')
