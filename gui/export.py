# gui/export.py

import tkinter as tk
from tkinter import messagebox, filedialog, Toplevel
from tkinter import ttk
from tkcalendar import DateEntry
import csv
import datetime
import logging

from utils import center_window

from config import STATUS_PENDING, STATUS_COLLECTED, TRANSPORTADORA_PADRAO

class ExportWindow:
    """
    Classe para a janela de exportação de coleta.
    """
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.app = parent_app  # Referência para acessar atributos de PackageCounterApp

        export_window = tk.Toplevel(self.app.root)
        export_window.transient(self.app.root)
        export_window.grab_set()
        export_window.title("Exportar Coleta")
        export_window.geometry("600x500")  # Aumentar o tamanho da janela para acomodar melhor os widgets

        # Frame principal
        main_frame = tk.Frame(export_window, bg="#f0f0f0", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        tk.Label(main_frame, text="Exportar Coleta", font=("Helvetica", 18, "bold"), bg="#f0f0f0").pack(pady=10)

        # Seleção de transportadora
        tk.Label(main_frame, text="Transportadora:", font=("Helvetica", 14), bg="#f0f0f0").pack(pady=5)
        transportadora_var = tk.StringVar()
        transportadora_var.set("Todas")
        transportadora_options = ["Todas"] + self.app.transportadoras
        transportadora_menu = ttk.Combobox(
            main_frame,
            textvariable=transportadora_var,
            values=transportadora_options,
            font=("Helvetica", 12),
            state="readonly"
        )
        transportadora_menu.pack(pady=5, fill=tk.X)

        # Seleção de status
        tk.Label(main_frame, text="Status:", font=("Helvetica", 14), bg="#f0f0f0").pack(pady=5)
        status_var = tk.StringVar()
        status_var.set("Todos")
        status_options = ["Todos", STATUS_PENDING, STATUS_COLLECTED]
        status_menu = ttk.Combobox(
            main_frame,
            textvariable=status_var,
            values=status_options,
            font=("Helvetica", 12),
            state="readonly"
        )
        status_menu.pack(pady=5, fill=tk.X)

        # Seleção de data inicial
        tk.Label(main_frame, text="Data Inicial:", font=("Helvetica", 14), bg="#f0f0f0").pack(pady=5)
        start_date_entry = DateEntry(
            main_frame,
            width=20,
            background='darkblue',
            foreground='white',
            date_pattern='yyyy-MM-dd',
            font=("Helvetica", 12)
        )
        start_date_entry.pack(pady=5, fill=tk.X)

        # Seleção de data final
        tk.Label(main_frame, text="Data Final:", font=("Helvetica", 14), bg="#f0f0f0").pack(pady=5)
        end_date_entry = DateEntry(
            main_frame,
            width=20,
            background='darkblue',
            foreground='white',
            date_pattern='yyyy-MM-dd',
            font=("Helvetica", 12)
        )
        end_date_entry.pack(pady=5, fill=tk.X)

        # Botão para confirmar a exportação
        export_button = tk.Button(
            main_frame,
            text="Exportar",
            command=lambda: self.confirm_export(
                transportadora_var.get(),
                status_var.get(),
                start_date_entry.get_date().isoformat(),
                end_date_entry.get_date().isoformat()
            ),
            font=("Helvetica", 14, "bold"),
            bg="#4CAF50",
            fg="white",
            activebackground="#45a049",
            activeforeground="white",
            padx=20,
            pady=10,
            width=20  # Aumentar a largura do botão
        )
        export_button.pack(pady=20)

        # Centralizar a janela de exportação
        center_window(export_window)

    def confirm_export(self, selected_transportadora, selected_status, start_date, end_date):
        """
        Confirma e realiza a exportação dos dados com base nos parâmetros selecionados.
        """
        # Verificar se a data inicial não é maior que a data final
        if start_date > end_date:
            messagebox.showwarning("Aviso", "A data inicial não pode ser maior que a data final.")
            return

        # Construir a consulta SQL com base nos parâmetros
        query = "SELECT transportadora, codigo_pacote, data, hora, status, coleta_number FROM packages WHERE data BETWEEN ? AND ?"
        params = [start_date, end_date]

        if selected_transportadora != "Todas":
            query += " AND transportadora = ?"
            params.append(selected_transportadora)

        if selected_status != "Todos":
            query += " AND status = ?"  # Comparação exata
            params.append(selected_status)

        # Log para depuração
        logging.debug(f"Export Query: {query}")
        logging.debug(f"Export Params: {params}")

        try:
            self.app.cursor.execute(query, params)
            packages = self.app.cursor.fetchall()

            if not packages:
                messagebox.showwarning("Aviso", "Nenhum pacote registrado para exportar neste período.")
                return

            # Melhorar o nome do arquivo CSV com timestamp e transportadora
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            transportadora_suffix = selected_transportadora.replace(" ", "_") if selected_transportadora != "Todas" else "Todas_Transportadoras"
            file_name = f"coleta_{transportadora_suffix}_{start_date}_a_{end_date}_{timestamp}.csv"

            # Solicitar o local para salvar o arquivo CSV
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=file_name
            )
            if file_path:
                with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    # Melhorar os cabeçalhos do CSV
                    writer.writerow(["Transportadora", "Código do Pacote", "Data", "Hora", "Status", "Número da Coleta"])
                    for package in packages:
                        writer.writerow(package)
                messagebox.showinfo("Sucesso", f"Lista exportada com sucesso!\nLocal: {file_path}")
                self.parent_app.update_treeview()  # Atualizar a view se necessário
                self.parent_app.package_entry.focus_set()
                self.parent_app.package_entry.selection_range(0, tk.END)
        except Exception as e:
            logging.error("Erro ao exportar a lista: %s", e)
            messagebox.showerror("Erro", f"Erro ao exportar a lista: {str(e)}")
