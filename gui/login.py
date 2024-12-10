# gui/login.py

import tkinter as tk
from tkinter import messagebox
import bcrypt
from database import get_database_connection
from utils import play_sound, center_window
from config import ALERT_SOUND_PATH

class LoginWindow:
    """
    Classe responsável pela janela de login da aplicação.
    """
    def __init__(self, parent):
        self.parent = parent
        self.top = tk.Toplevel(parent)
        self.top.title("Login")
        self.top.geometry("400x300")
        self.top.grab_set()
        self.parent.withdraw()  # Esconder a janela principal até o login ser bem-sucedido

        # Configuração de fontes
        label_font = ("Helvetica", 14)
        entry_font = ("Helvetica", 14)
        button_font = ("Helvetica", 14)

        # Label com o nome da empresa (logo)
        logo_label = tk.Label(self.top, text="Ponto 3D", font=("Helvetica", 24, "bold"))
        logo_label.pack(pady=10)

        # Frame para centralizar os campos de login
        login_frame = tk.Frame(self.top)
        login_frame.pack(pady=10)

        # Campo de entrada para usuário
        tk.Label(login_frame, text="Usuário:", font=label_font).grid(row=0, column=0, pady=10, sticky='e')
        self.username_entry = tk.Entry(login_frame, font=entry_font)
        self.username_entry.grid(row=0, column=1, pady=10)
        self.username_entry.focus_set()

        # Campo de entrada para senha
        tk.Label(login_frame, text="Senha:", font=label_font).grid(row=1, column=0, pady=10, sticky='e')
        self.password_entry = tk.Entry(login_frame, show="*", font=entry_font)
        self.password_entry.grid(row=1, column=1, pady=10)

        # Botão de login
        tk.Button(self.top, text="Login", command=self.authenticate, font=button_font, width=10).pack(pady=20)

        self.user = None

        # Centralizar a janela de login
        center_window(self.top)

    def authenticate(self):
        """
        Autentica o usuário com base no banco de dados.
        """
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("Aviso", "Por favor, preencha todos os campos.")
            return

        try:
            conn, cursor = get_database_connection()
            cursor.execute("SELECT id, username, password, role FROM users WHERE username=?", (username,))
            user = cursor.fetchone()

            if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
                self.user = {'id': user[0], 'username': user[1], 'role': user[3]}
                self.top.destroy()
                self.parent.deiconify()  # Mostrar a janela principal
            else:
                # Tocar um som de erro de forma assíncrona
                play_sound('error')
                # Mostrar mensagem de erro mais chamativa
                messagebox.showerror("Erro", "Usuário ou senha inválidos")
        except Exception as e:
            logging.error("Erro durante autenticação: %s", e)
            messagebox.showerror("Erro", "Ocorreu um erro durante a autenticação. Verifique os logs para mais detalhes.")
