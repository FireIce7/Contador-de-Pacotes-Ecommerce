# gui/view_total_packages.py

import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import logging

from utils import center_window

class ViewTotalPackagesWindow:
    """
    Classe para a janela de consulta de coletas anteriores.
    """
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.app = parent_app  # Referência correta para acessar atributos de PackageCounterApp

        view_window = tk.Toplevel(self.app.root)
        view_window.transient(self.app.root)
        view_window.grab_set()
        view_window.title("Consultar Coletas Anteriores")
        view_window.geometry("800x600")

        # Frame principal da nova janela
        view_frame = tk.Frame(view_window, bg="#f0f0f0")
        view_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Seleção de data
        tk.Label(view_frame, text="Selecione a data:", font=("Helvetica", 18), bg="#f0f0f0").pack(pady=10)
        date_entry = DateEntry(
            view_frame,
            width=20,
            background='darkblue',
            foreground='white',
            date_pattern='yyyy-MM-dd',
            font=("Helvetica", 16)
        )
        date_entry.pack(pady=5)

        # Seleção de transportadora
        tk.Label(view_frame, text="Transportadora:", font=("Helvetica", 18), bg="#f0f0f0").pack(pady=10)
        transportadora_var = tk.StringVar()
        transportadora_var.set("Todas")
        transportadora_options = ["Todas"] + self.app.transportadoras
        transportadora_menu = ttk.Combobox(
            view_frame,
            textvariable=transportadora_var,
            values=transportadora_options,
            state="readonly",
            font=("Helvetica", 16)
        )
        transportadora_menu.pack(pady=5)

        # Botão para filtrar os dados
        filter_button = tk.Button(
            view_frame,
            text="Filtrar",
            command=lambda: self.filter_by_date_and_transportadora(
                date_entry.get_date().isoformat(),
                transportadora_var.get()
            ),
            font=("Helvetica", 16),
            bg="#2196F3",
            fg="white"
        )
        filter_button.pack(pady=10)

        # Frame para exibir os resultados
        self.results_frame = tk.Frame(view_frame, bg="#f0f0f0")
        self.results_frame.pack(fill=tk.BOTH, expand=True)

        # Centralizar a janela de visualização
        center_window(view_window)

    def filter_by_date_and_transportadora(self, date, transportadora):
        """
        Filtra os pacotes com base na data e transportadora selecionadas e exibe os resultados.
        """
        # Limpar conteúdos anteriores
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        try:
            query = "SELECT coleta_number, COUNT(*) FROM packages WHERE data = ?"
            params = [date]

            if transportadora != "Todas":
                query += " AND transportadora = ?"
                params.append(transportadora)

            query += " GROUP BY coleta_number ORDER BY coleta_number ASC"

            self.app.cursor.execute(query, params)
            results = self.app.cursor.fetchall()
            if results:
                tk.Label(
                    self.results_frame,
                    text=f"Resultados para {date}:",
                    font=("Helvetica", 18, "bold"),
                    bg="#f0f0f0"
                ).pack(pady=10)

                for coleta_number, count in results:
                    tk.Label(
                        self.results_frame,
                        text=f"Coleta {coleta_number}: {count} pacotes",
                        font=("Helvetica", 16),
                        bg="#f0f0f0"
                    ).pack()

                columns = ("transportadora", "codigo_pacote", "hora", "coleta_number")
                package_treeview = ttk.Treeview(self.results_frame, columns=columns, show='headings')
                package_treeview.heading('transportadora', text='Transportadora')
                package_treeview.heading('codigo_pacote', text='Código de Pacote')
                package_treeview.heading('hora', text='Hora')
                package_treeview.heading('coleta_number', text='Coleta Número')
                package_treeview.pack(fill=tk.BOTH, expand=True, pady=10)

                scrollbar = ttk.Scrollbar(package_treeview, orient=tk.VERTICAL, command=package_treeview.yview)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                package_treeview.configure(yscroll=scrollbar.set)

                query = "SELECT transportadora, codigo_pacote, hora, coleta_number FROM packages WHERE data = ?"
                params = [date]
                if transportadora != "Todas":
                    query += " AND transportadora = ?"
                    params.append(transportadora)

                self.app.cursor.execute(query, params)
                package_details = self.app.cursor.fetchall()
                for transportadora_result, codigo_pacote, hora, coleta_number in package_details:
                    package_treeview.insert('', 'end', values=(transportadora_result, codigo_pacote, hora, coleta_number))
            else:
                tk.Label(
                    self.results_frame,
                    text="Nenhum pacote registrado para esta data.",
                    font=("Helvetica", 16),
                    bg="#f0f0f0"
                ).pack(pady=10)
        except Exception as e:
            logging.error("Erro ao filtrar os pacotes: %s", e)
            messagebox.showerror("Erro", f"Ocorreu um erro ao filtrar os pacotes: {str(e)}")
