# gui/verify_package.py

import tkinter as tk
from tkinter import messagebox
from config import STATUS_PENDING, STATUS_COLLECTED, logging
from utils import center_window

class VerifyPackageWindow:
    """
    Classe para a janela de verificação de pedidos.
    """
    def __init__(self, parent_app, conn, title="Verificar Pedido"):
        self.parent_app = parent_app
        self.conn = conn
        self.cursor = self.conn.cursor()

        # Configuração da janela de verificação
        self.window = tk.Toplevel(self.parent_app.root)
        self.window.title(title)
        self.window.geometry("500x450")  # Ajustar o tamanho para melhor estética
        self.window.resizable(False, False)
        center_window(self.window)  # Centraliza a janela

        # Frame principal
        main_frame = tk.Frame(self.window, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título da janela de verificação
        tk.Label(
            main_frame,
            text="Verificar Pedido",
            font=("Helvetica", 16, "bold"),
            bg="#f0f0f0"
        ).pack(pady=10)

        # Entrada para Código do Pacote
        tk.Label(
            main_frame,
            text="Código do Pacote:",
            font=("Helvetica", 12),
            bg="#f0f0f0"
        ).pack(pady=5)
        self.package_code_entry = tk.Entry(
            main_frame,
            font=("Helvetica", 12),
            width=30
        )
        self.package_code_entry.pack(pady=5)
        self.package_code_entry.focus_set()

        # Botão de Verificar
        verify_button = tk.Button(
            main_frame,
            text="Verificar",
            command=self.verify_package,
            font=("Helvetica", 12, "bold"),
            bg="#2196F3",
            fg="white",
            width=10
        )
        verify_button.pack(pady=20)

        # Bind para a tecla Enter na janela
        self.window.bind('<Return>', self.verify_package)

    def verify_package(self, event=None):
        """
        Verifica se o pedido foi registrado e exibe os detalhes.
        """
        package_code = self.package_code_entry.get().strip()

        if not package_code:
            messagebox.showwarning("Aviso", "Por favor, insira o Código do Pacote.")
            self.package_code_entry.focus_set()
            return

        try:
            # Consultar o banco de dados pelo código do pacote
            self.cursor.execute("""
                SELECT codigo_pacote, transportadora, data, hora, status, coleta_number 
                FROM packages 
                WHERE codigo_pacote = ?
            """, (package_code,))
            result = self.cursor.fetchone()

            if result:
                codigo_pacote, transportadora, data, hora, status, coleta_number = result
                status_text = "Bipado" if status == STATUS_PENDING else "Coleta Fechada"
                coleta_status = "Fechada" if status == STATUS_COLLECTED else "Aberta"

                # Detalhes do pedido organizados em lista de tuplas
                detalhes = [
                    ("Código do Pacote", codigo_pacote),
                    ("Transportadora", transportadora),
                    ("Data do Bip", data),
                    ("Hora do Bip", hora),
                    ("Status do Pedido", status_text),
                    ("Número da Coleta", coleta_number),
                    ("Status da Coleta", coleta_status)
                ]

                # Criação da janela de detalhes do pedido
                details_window = tk.Toplevel(self.window)
                details_window.title("Detalhes do Pedido")
                details_window.geometry("500x450")
                details_window.resizable(False, False)
                center_window(details_window)

                # Frame principal dos detalhes
                details_frame = tk.Frame(details_window, bg="#f0f0f0")
                details_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

                # Título dos detalhes
                tk.Label(
                    details_frame,
                    text="Detalhes do Pedido",
                    font=("Helvetica", 14, "bold"),
                    bg="#f0f0f0"
                ).pack(pady=10)

                # Exibição dos detalhes com layout organizado
                for key, value in detalhes:
                    line_frame = tk.Frame(details_frame, bg="#f0f0f0")
                    line_frame.pack(fill='x', pady=2)

                    # Chave em negrito
                    tk.Label(
                        line_frame,
                        text=f"{key}:",
                        font=("Helvetica", 12, "bold"),
                        bg="#f0f0f0",
                        anchor="w"
                    ).pack(side=tk.LEFT)

                    # Valor em fonte normal
                    tk.Label(
                        line_frame,
                        text=value,
                        font=("Helvetica", 12),
                        bg="#f0f0f0",
                        anchor="w"
                    ).pack(side=tk.LEFT, padx=(5, 0))
            else:
                # Pedido não encontrado
                messagebox.showerror("Erro", f"Nenhum pedido encontrado com o Código {package_code}.")
        except Exception as e:
            logging.error("Erro ao verificar pedido: %s", e)
            messagebox.showerror("Erro", f"Ocorreu um erro ao verificar o pedido: {str(e)}")
            self.conn.rollback()
