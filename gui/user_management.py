# gui/user_management.py

import tkinter as tk
from tkinter import messagebox, Toplevel
from tkinter import ttk
import bcrypt
import sqlite3
import threading
import logging

from utils import play_sound, center_window
from config import STATUS_PENDING, STATUS_COLLECTED

class UserManagementWindow:
    """
    Classe para a janela de gerenciamento de usuários.
    """
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.app = parent_app

        manage_window = Toplevel(self.app.root)
        manage_window.transient(self.app.root)
        manage_window.grab_set()
        manage_window.title("Gerenciamento de Usuários")
        manage_window.geometry("900x600")

        # Frame principal
        main_frame = tk.Frame(manage_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Label com o nome da empresa (logo)
        logo_label = tk.Label(main_frame, text="Ponto 3D", font=("Helvetica", 24, "bold"))
        logo_label.pack(pady=10)

        # Label de título
        title_label = tk.Label(main_frame, text="Gerenciamento de Usuários", font=("Helvetica", 18, "bold"))
        title_label.pack(pady=10)

        # Frame para o Treeview
        treeview_frame = tk.Frame(main_frame)
        treeview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Configuração do Treeview para exibir usuários
        columns = ("username", "role")
        self.user_treeview = ttk.Treeview(treeview_frame, columns=columns, show='headings', height=15)
        self.user_treeview.heading('username', text='Usuário')
        self.user_treeview.heading('role', text='Cargo')
        self.user_treeview.column('username', width=400)
        self.user_treeview.column('role', width=200)
        self.user_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar para o Treeview
        scrollbar = ttk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=self.user_treeview.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.user_treeview.configure(yscroll=scrollbar.set)

        # Frame para os botões de ação
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=20)

        # Botões para adicionar, editar e remover usuários
        tk.Button(button_frame, text="Adicionar", command=self.add_user, font=("Helvetica", 12), width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Editar", command=self.edit_user, font=("Helvetica", 12), width=15).pack(side=tk.LEFT, padx=10)
        tk.Button(button_frame, text="Remover", command=self.delete_user, font=("Helvetica", 12), width=15).pack(side=tk.LEFT, padx=10)

        # Carregar usuários no Treeview
        self.load_users()

        # Centralizar a janela de gerenciamento de usuários
        center_window(manage_window)

    def load_users(self):
        """
        Carrega os usuários do banco de dados no Treeview.
        """
        # Limpar o Treeview
        for item in self.user_treeview.get_children():
            self.user_treeview.delete(item)

        try:
            # Buscar usuários no banco de dados
            self.app.cursor.execute("SELECT username, role FROM users")
            users = self.app.cursor.fetchall()
            for username, role in users:
                self.user_treeview.insert('', 'end', values=(username, role))
        except Exception as e:
            logging.error("Erro ao carregar usuários: %s", e)
            messagebox.showerror("Erro", f"Ocorreu um erro ao carregar os usuários: {str(e)}")

    def add_user(self):
        """
        Abre a janela para adicionar um novo usuário.
        """
        add_user_window = Toplevel(self.app.root)
        add_user_window.transient(self.app.root)
        add_user_window.grab_set()
        add_user_window.title("Adicionar Usuário")
        add_user_window.geometry("400x400")

        # Campos de entrada para nome de usuário, senha e cargo
        tk.Label(add_user_window, text="Nome de Usuário:", font=("Helvetica", 12)).pack(pady=10)
        username_entry = tk.Entry(add_user_window, font=("Helvetica", 12))
        username_entry.pack(pady=5)
        username_entry.focus_set()

        tk.Label(add_user_window, text="Senha:", font=("Helvetica", 12)).pack(pady=10)
        password_entry = tk.Entry(add_user_window, show="*", font=("Helvetica", 12))
        password_entry.pack(pady=5)

        tk.Label(add_user_window, text="Cargo:", font=("Helvetica", 12)).pack(pady=10)
        role_var = tk.StringVar()
        role_var.set("Selecione o Cargo")
        role_menu = ttk.Combobox(
            add_user_window,
            textvariable=role_var,
            values=["admin", "user"],
            state="readonly",
            font=("Helvetica", 12)
        )
        role_menu.pack(pady=5)

        def save_new_user():
            """
            Salva o novo usuário no banco de dados após validação.
            """
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            role = role_var.get()

            # Verificar se todos os campos estão preenchidos
            if not username or not password or role == "Selecione o Cargo":
                messagebox.showwarning("Aviso", "Por favor, preencha todos os campos.")
                return

            try:
                # Hash da senha antes de salvar
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                self.app.cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                    (username, hashed_password.decode('utf-8'), role)
                )
                self.app.conn.commit()
                messagebox.showinfo("Sucesso", "Usuário adicionado com sucesso.")
                self.load_users()
                add_user_window.destroy()
            except sqlite3.IntegrityError:
                # Tocar um som de erro de forma assíncrona
                play_sound('error')
                messagebox.showerror("Erro", "O nome de usuário já existe.")
            except Exception as e:
                logging.error("Erro ao adicionar usuário: %s", e)
                messagebox.showerror("Erro", f"Ocorreu um erro ao adicionar o usuário: {str(e)}")

        # Botão para salvar o novo usuário
        tk.Button(add_user_window, text="Salvar", command=save_new_user, font=("Helvetica", 12)).pack(pady=20)

        # Centralizar a janela de adicionar usuário
        center_window(add_user_window)

    def edit_user(self):
        """
        Abre a janela para editar um usuário selecionado.
        """
        selected_item = self.user_treeview.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Por favor, selecione um usuário para editar.")
            return

        item = self.user_treeview.item(selected_item)
        username = item['values'][0]

        edit_user_window = Toplevel(self.app.root)
        edit_user_window.transient(self.app.root)
        edit_user_window.grab_set()
        edit_user_window.title("Editar Usuário")
        edit_user_window.geometry("400x400")

        # Campos de entrada para nome de usuário, nova senha e cargo
        tk.Label(edit_user_window, text="Nome de Usuário:", font=("Helvetica", 12)).pack(pady=10)
        username_entry = tk.Entry(edit_user_window, font=("Helvetica", 12))
        username_entry.insert(0, username)
        username_entry.pack(pady=5)
        username_entry.focus_set()

        tk.Label(edit_user_window, text="Nova Senha (opcional):", font=("Helvetica", 12)).pack(pady=10)
        password_entry = tk.Entry(edit_user_window, show="*", font=("Helvetica", 12))
        password_entry.pack(pady=5)

        tk.Label(edit_user_window, text="Cargo:", font=("Helvetica", 12)).pack(pady=10)
        role_var = tk.StringVar()
        role_var.set(item['values'][1])
        role_menu = ttk.Combobox(
            edit_user_window,
            textvariable=role_var,
            values=["admin", "user"],
            state="readonly",
            font=("Helvetica", 12)
        )
        role_menu.pack(pady=5)

        def save_edited_user():
            """
            Salva as alterações do usuário no banco de dados após validação.
            """
            new_username = username_entry.get().strip()
            new_password = password_entry.get().strip()
            new_role = role_var.get()

            # Verificar se os campos obrigatórios estão preenchidos
            if not new_username or new_role == "Selecione o Cargo":
                messagebox.showwarning("Aviso", "Por favor, preencha todos os campos.")
                return

            try:
                if new_password:
                    # Hash da nova senha
                    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
                    self.app.cursor.execute(
                        "UPDATE users SET username = ?, password = ?, role = ? WHERE username = ?",
                        (new_username, hashed_password.decode('utf-8'), new_role, username)
                    )
                else:
                    self.app.cursor.execute(
                        "UPDATE users SET username = ?, role = ? WHERE username = ?",
                        (new_username, new_role, username)
                    )
                self.app.conn.commit()
                messagebox.showinfo("Sucesso", "Usuário atualizado com sucesso.")
                self.load_users()
                edit_user_window.destroy()
            except sqlite3.IntegrityError:
                # Tocar um som de erro de forma assíncrona
                play_sound('error')
                messagebox.showerror("Erro", "O nome de usuário já existe.")
            except Exception as e:
                logging.error("Erro ao editar usuário: %s", e)
                messagebox.showerror("Erro", f"Ocorreu um erro ao editar o usuário: {str(e)}")

        # Botão para salvar as alterações
        tk.Button(edit_user_window, text="Salvar", command=save_edited_user, font=("Helvetica", 12)).pack(pady=20)

        # Centralizar a janela de editar usuário
        center_window(edit_user_window)

    def delete_user(self):
        """
        Remove um usuário selecionado do banco de dados.
        """
        selected_item = self.user_treeview.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Por favor, selecione um usuário para remover.")
            return

        item = self.user_treeview.item(selected_item)
        username = item['values'][0]

        # Impedir que o usuário atualmente logado seja removido
        if username == self.app.current_user['username']:
            messagebox.showerror("Erro", "Você não pode remover o usuário atualmente logado.")
            return

        confirmation = messagebox.askyesno("Confirmação", f"Tem certeza de que deseja remover o usuário '{username}'?")
        if confirmation:
            try:
                self.app.cursor.execute("DELETE FROM users WHERE username = ?", (username,))
                self.app.conn.commit()
                messagebox.showinfo("Sucesso", "Usuário removido com sucesso.")
                self.load_users()
            except Exception as e:
                logging.error("Erro ao remover usuário: %s", e)
                messagebox.showerror("Erro", f"Ocorreu um erro ao remover o usuário: {str(e)}")
