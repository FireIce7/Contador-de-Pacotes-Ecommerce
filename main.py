# main.py

import tkinter as tk
from gui.login import LoginWindow
from gui.main_app import PackageCounterApp
import logging

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Esconder a janela principal até o login ser bem-sucedido
    login_window = LoginWindow(root)
    root.wait_window(login_window.top)
    if login_window.user:
        app = PackageCounterApp(root, login_window.user)
        root.mainloop()
    else:
        root.destroy()
