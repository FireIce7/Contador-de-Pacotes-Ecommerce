# gui/view_total_packages.py

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import logging
from tkcalendar import DateEntry  # Certifique-se de instalar o tkcalendar com 'pip install tkcalendar'

from utils import center_window
from config import logging

class ViewTotalPackagesWindow:
    """
    Classe para a janela de consulta de coletas anteriores.
    """
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.conn = parent_app.conn
        self.cursor = self.conn.cursor()

        # Configuração da janela
        self.window = tk.Toplevel(self.parent_app.root)
        self.window.title("Consultar Coletas Anteriores")
        self.window.geometry("900x700")  # Aumentar o tamanho da janela para melhor acomodação
        self.window.resizable(True, True)  # Permitir redimensionamento
        center_window(self.window)  # Centralizar a janela

        # Frame principal
        main_frame = tk.Frame(self.window, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título da janela
        tk.Label(
            main_frame,
            text="Consultar Coletas Anteriores",
            font=("Helvetica", 18, "bold"),
            bg="#f0f0f0"
        ).pack(pady=10)

        # Frame para filtros de pesquisa
        filter_frame = tk.Frame(main_frame, bg="#f0f0f0")
        filter_frame.pack(fill=tk.X, pady=10)

        # Filtro por Data Inicial
        tk.Label(
            filter_frame,
            text="Data Inicial:",
            font=("Helvetica", 12, "bold"),
            bg="#f0f0f0"
        ).grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.start_date_entry = DateEntry(
            filter_frame,
            font=("Helvetica", 12),
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd'
        )
        self.start_date_entry.grid(row=0, column=1, padx=5, pady=5)

        # Filtro por Data Final
        tk.Label(
            filter_frame,
            text="Data Final:",
            font=("Helvetica", 12, "bold"),
            bg="#f0f0f0"
        ).grid(row=0, column=2, padx=5, pady=5, sticky="w")

        self.end_date_entry = DateEntry(
            filter_frame,
            font=("Helvetica", 12),
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            date_pattern='yyyy-mm-dd'
        )
        self.end_date_entry.grid(row=0, column=3, padx=5, pady=5)

        # Filtro por Transportadora
        tk.Label(
            filter_frame,
            text="Transportadora:",
            font=("Helvetica", 12, "bold"),
            bg="#f0f0f0"
        ).grid(row=1, column=0, padx=5, pady=5, sticky="w")

        self.transportadoras = ["Todas", "SHEIN", "Shopee", "Mercado Livre"]
        self.selected_transportadora = tk.StringVar(value="Todas")
        self.transportadora_menu = ttk.Combobox(
            filter_frame,
            textvariable=self.selected_transportadora,
            values=self.transportadoras,
            font=("Helvetica", 12),
            state="readonly",
            width=13
        )
        self.transportadora_menu.grid(row=1, column=1, padx=5, pady=5)
        self.transportadora_menu.current(0)  # Selecionar "Todas" por padrão

        # Botão de Pesquisa
        search_button = tk.Button(
            filter_frame,
            text="Pesquisar",
            command=self.search_packages,
            font=("Helvetica", 12, "bold"),
            bg="#2196F3",
            fg="white",
            width=12
        )
        search_button.grid(row=1, column=3, padx=5, pady=5)

        # Frame para Treeview e Scrollbar
        treeview_frame = tk.Frame(main_frame, bg="#f0f0f0")
        treeview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Configuração do Treeview para exibir coletas
        columns = ("codigo_pacote", "transportadora", "data", "hora", "status", "coleta_number")
        self.tree = ttk.Treeview(treeview_frame, columns=columns, show='headings')

        # Definir cabeçalhos
        self.tree.heading("codigo_pacote", text="Código do Pacote")
        self.tree.heading("transportadora", text="Transportadora")
        self.tree.heading("data", text="Data")
        self.tree.heading("hora", text="Hora")
        self.tree.heading("status", text="Status")
        self.tree.heading("coleta_number", text="Número da Coleta")

        # Definir largura das colunas
        self.tree.column("codigo_pacote", width=200, anchor='center')
        self.tree.column("transportadora", width=150, anchor='center')
        self.tree.column("data", width=100, anchor='center')
        self.tree.column("hora", width=80, anchor='center')
        self.tree.column("status", width=150, anchor='center')
        self.tree.column("coleta_number", width=150, anchor='center')

        # Adicionar a Treeview
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar vertical
        scrollbar = ttk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscroll=scrollbar.set)

        # Carregar todas as coletas inicialmente
        self.load_all_packages()

    def load_all_packages(self):
        """
        Carrega todas as coletas da transportadora selecionada sem filtros.
        """
        try:
            self.cursor.execute("""
                SELECT codigo_pacote, transportadora, data, hora, status, coleta_number 
                FROM packages 
                ORDER BY data DESC, hora DESC
            """)
            records = self.cursor.fetchall()

            # Limpar a Treeview
            for row in self.tree.get_children():
                self.tree.delete(row)

            # Inserir registros na Treeview
            for row in records:
                self.tree.insert('', tk.END, values=row)
        except Exception as e:
            logging.error("Erro ao carregar todas as coletas: %s", e)
            messagebox.showerror("Erro", f"Ocorreu um erro ao carregar as coletas: {str(e)}")

    def search_packages(self):
        """
        Pesquisa coletas com base nos filtros fornecidos.
        """
        start_date = self.start_date_entry.get_date().strftime('%Y-%m-%d')
        end_date = self.end_date_entry.get_date().strftime('%Y-%m-%d')
        transportadora = self.selected_transportadora.get()

        query = """
            SELECT codigo_pacote, transportadora, data, hora, status, coleta_number 
            FROM packages 
            WHERE data BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if transportadora != "Todas":
            query += " AND transportadora = ?"
            params.append(transportadora)

        query += " ORDER BY data DESC, hora DESC"

        try:
            self.cursor.execute(query, tuple(params))
            records = self.cursor.fetchall()

            # Limpar a Treeview
            for row in self.tree.get_children():
                self.tree.delete(row)

            # Inserir registros na Treeview
            for row in records:
                self.tree.insert('', tk.END, values=row)

            if not records:
                messagebox.showinfo("Informação", "Nenhuma coleta encontrada com os critérios selecionados.")
        except Exception as e:
            logging.error("Erro ao pesquisar coletas: %s", e)
            messagebox.showerror("Erro", f"Ocorreu um erro ao pesquisar as coletas: {str(e)}")
