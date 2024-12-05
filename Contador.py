import tkinter as tk
from tkinter import messagebox, filedialog, Toplevel
from tkinter import ttk
import csv
import sqlite3
import datetime
from tkcalendar import DateEntry  # Certifique-se de que o tkcalendar está instalado
import os
import sys

# Obter o caminho da aplicação
if getattr(sys, 'frozen', False):
    # Quando executado como um executável
    application_path = os.path.dirname(sys.executable)
else:
    # Quando executado como um script Python
    application_path = os.path.dirname(os.path.abspath(__file__))

# Caminho do banco de dados
db_path = os.path.join(application_path, 'packages.db')

# Inicializando o banco de dados SQLite
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS packages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transportadora TEXT,
        codigo_pacote TEXT,
        data TEXT,
        hora TEXT,
        status TEXT,
        coleta_number INTEGER
    )
''')
conn.commit()

# Função para migrar o banco de dados
def migrate_database():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verificar se a tabela 'packages' existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='packages'")
    table_exists = cursor.fetchone()

    if table_exists:
        # Verificar se a coluna 'coleta_number' existe na tabela antiga
        cursor.execute('PRAGMA table_info(packages)')
        columns = [info[1] for info in cursor.fetchall()]

        if 'coleta_number' not in columns:
            cursor.execute('ALTER TABLE packages ADD COLUMN coleta_number INTEGER')
            conn.commit()

        # Alterar o tipo da coluna 'codigo_pacote' para TEXT
        cursor.execute('PRAGMA table_info(packages)')
        columns_info = cursor.fetchall()
        codigo_pacote_type = None
        for col in columns_info:
            if col[1] == 'codigo_pacote':
                codigo_pacote_type = col[2]
                break

        if codigo_pacote_type != 'TEXT':
            # Criar nova tabela com o esquema correto
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS packages_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transportadora TEXT,
                    codigo_pacote TEXT,
                    data TEXT,
                    hora TEXT,
                    status TEXT,
                    coleta_number INTEGER
                )
            ''')

            # Copiar os dados da tabela antiga para a nova tabela
            cursor.execute('''
                INSERT INTO packages_new (id, transportadora, codigo_pacote, data, hora, status, coleta_number)
                SELECT id, transportadora, CAST(codigo_pacote AS TEXT), data, hora, status, coleta_number
                FROM packages
            ''')

            # Remover a tabela antiga
            cursor.execute('DROP TABLE packages')

            # Renomear a nova tabela
            cursor.execute('ALTER TABLE packages_new RENAME TO packages')

            conn.commit()
    else:
        # Se a tabela não existe, não é necessário migrar
        pass

    conn.close()

# Executar a migração
migrate_database()

# Reabrir a conexão com o banco de dados
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

class PackageCounterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Contador de Pacotes - Ponto 3D")
        self.root.geometry('1200x800')  # Ajustado para melhor visibilidade
        self.root.eval('tk::PlaceWindow . center')  # Abrir no centro da tela

        self.transportadoras = ["SHEIN", "Shopee", "Mercado Livre"]
        self.transportadora_colors = {
            "SHEIN": "#90EE90",         # Verde Claro
            "Shopee": "#FFA500",        # Laranja
            "Mercado Livre": "#FFFF99"  # Amarelo Claro
        }
        self.selected_transportadora = tk.StringVar()
        self.selected_transportadora.set("Selecione a Transportadora")
        self.selected_transportadora.trace('w', self.update_treeview_on_selection)

        # Estilo para o Combobox
        self.style = ttk.Style()
        self.style.configure('TCombobox', font=("Helvetica", 12))

        self.create_widgets()
        self.update_treeview()

        # Fechar conexão com o banco de dados ao fechar a janela
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Frame principal
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Adicionar o nome da empresa no topo
        company_label = tk.Label(main_frame, text="Ponto 3D", font=("Helvetica", 24, "bold"), bg="#f0f0f0")
        company_label.pack(pady=10)

        # Frame superior para seleção de transportadora e entrada de código de barras
        top_frame = tk.Frame(main_frame, bg="#f0f0f0")
        top_frame.pack(fill=tk.X, pady=10)

        # Transportadora Dropdown
        transportadora_label = tk.Label(top_frame, text="Transportadora:", font=("Helvetica", 14, "bold"), bg="#f0f0f0")
        transportadora_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.transportadora_menu = ttk.Combobox(top_frame, textvariable=self.selected_transportadora, values=self.transportadoras, font=("Helvetica", 12), width=25, state="readonly")
        self.transportadora_menu.grid(row=0, column=1, padx=10, pady=10)
        self.transportadora_menu.bind("<Tab>", lambda e: self.package_entry.focus_set())
        self.transportadora_menu.bind("<Return>", lambda e: self.package_entry.focus_set())

        help_transportadora = tk.Button(top_frame, text="?", font=("Helvetica", 12), command=self.show_transportadora_help)
        help_transportadora.grid(row=0, column=2, padx=5)

        # Package Input
        package_label = tk.Label(top_frame, text="Bipe o código de barras:", font=("Helvetica", 14, "bold"), bg="#f0f0f0")
        package_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.package_entry = tk.Entry(top_frame, width=40, font=("Helvetica", 12))
        self.package_entry.grid(row=1, column=1, padx=10, pady=10)
        self.package_entry.bind('<Return>', self.add_package)
        self.package_entry.bind("<Tab>", lambda e: self.export_button.focus_set())
        self.package_entry.focus_set()  # Focar automaticamente na entrada do código de barras

        help_package = tk.Button(top_frame, text="?", font=("Helvetica", 12), command=self.show_package_help)
        help_package.grid(row=1, column=2, padx=5)

        # Frame do Treeview e Total de Pacotes
        treeview_frame = tk.Frame(main_frame, bg="#f0f0f0")
        treeview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        columns = ("codigo_pacote", "data", "hora", "coleta_number")
        self.package_treeview = ttk.Treeview(treeview_frame, columns=columns, show='headings')
        self.package_treeview.heading('codigo_pacote', text='Código de Pacote')
        self.package_treeview.heading('data', text='Data')
        self.package_treeview.heading('hora', text='Hora')
        self.package_treeview.heading('coleta_number', text='Coleta Número')
        self.package_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=self.package_treeview.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.package_treeview.configure(yscroll=scrollbar.set)

        # Label para total de pacotes
        self.total_label = tk.Label(main_frame, text="", font=("Helvetica", 14, "bold"), bg="#f0f0f0")
        self.total_label.pack(pady=10)

        # Frame dos botões
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(fill=tk.X, pady=20)

        # Export Button
        self.export_button = tk.Button(button_frame, text="Exportar Coleta", command=self.export_list, font=("Helvetica", 12), bg="#4CAF50", fg="white", width=25)
        self.export_button.grid(row=0, column=0, padx=10, pady=10)
        self.export_button.bind("<Tab>", lambda e: self.close_collection_button.focus_set())
        self.export_button.bind("<Return>", lambda e: self.export_list())

        # Close Collection Button
        self.close_collection_button = tk.Button(button_frame, text="Fechar Coleta para a Transportadora", command=self.close_collection, font=("Helvetica", 12), bg="#f44336", fg="white", width=30)
        self.close_collection_button.grid(row=0, column=1, padx=10, pady=10)
        self.close_collection_button.bind("<Tab>", lambda e: self.total_button.focus_set())
        self.close_collection_button.bind("<Return>", lambda e: self.close_collection())

        # View Total Packages Button
        self.total_button = tk.Button(button_frame, text="Consultar Coletas Anteriores", command=self.view_total_packages, font=("Helvetica", 12), bg="#2196F3", fg="white", width=25)
        self.total_button.grid(row=0, column=2, padx=10, pady=10)
        self.total_button.bind("<Tab>", lambda e: self.reopen_collection_button.focus_set())
        self.total_button.bind("<Return>", lambda e: self.view_total_packages())

        # Reopen Collection Button
        self.reopen_collection_button = tk.Button(button_frame, text="Reabrir Coleta para a Transportadora", command=self.reopen_collection, font=("Helvetica", 12), bg="#8B4513", fg="white", width=30)
        self.reopen_collection_button.grid(row=1, column=1, padx=10, pady=10)
        self.reopen_collection_button.bind("<Tab>", lambda e: self.remove_button.focus_set())
        self.reopen_collection_button.bind("<Return>", lambda e: self.reopen_collection())

        # Remove Package Button
        self.remove_button = tk.Button(button_frame, text="Remover Pacote Selecionado", command=self.remove_package, font=("Helvetica", 12), bg="#FF9800", fg="white", width=25)
        self.remove_button.grid(row=1, column=0, columnspan=1, padx=10, pady=10)
        self.remove_button.bind("<Tab>", lambda e: self.package_entry.focus_set())
        self.remove_button.bind("<Return>", lambda e: self.remove_package())

    def add_package(self, event=None):
        transportadora = self.selected_transportadora.get()
        package_code = self.package_entry.get().strip()

        if not package_code:
            messagebox.showwarning("Aviso", "Por favor, bipar um código válido.")
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()
            return

        if transportadora == "Selecione a Transportadora":
            messagebox.showerror("Erro", "Por favor, selecione uma transportadora antes de bipar o pacote.")
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()
            return

        try:
            # Verificar se o pacote já foi bipado hoje para a transportadora selecionada
            cursor.execute("SELECT * FROM packages WHERE codigo_pacote = ? AND data = ? AND transportadora = ?", (package_code, datetime.date.today().isoformat(), transportadora))
            if cursor.fetchone():
                messagebox.showwarning("Aviso", "Este pacote já foi registrado hoje para esta transportadora.")
                # Emitir um som de alerta
                self.root.bell()
                self.package_entry.delete(0, tk.END)
                self.package_entry.focus_set()
                return

            # Salvar o pacote se não for duplicado
            self.save_package(transportadora, package_code)
            self.update_treeview()
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()  # Focar novamente na entrada de código de barras

            # Feedback visual: destacar a última linha adicionada
            self.package_treeview.selection_set(self.package_treeview.get_children()[-1])
            self.package_treeview.focus(self.package_treeview.get_children()[-1])

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao adicionar o pacote: {str(e)}")

    def save_package(self, transportadora, codigo_pacote):
        try:
            data_atual = datetime.date.today().isoformat()
            hora_atual = datetime.datetime.now().strftime("%H:%M:%S")
            status = 'pending'

            # Obter o número máximo de coleta das coletas já fechadas
            cursor.execute("""
                SELECT MAX(coleta_number) FROM packages 
                WHERE transportadora = ? AND data = ? AND status = 'collected'
            """, (transportadora, data_atual))
            result = cursor.fetchone()
            max_collected_coleta_number = result[0] if result[0] is not None else 0

            # O número da coleta atual é o máximo das coletas fechadas + 1
            coleta_number = max_collected_coleta_number + 1

            cursor.execute("INSERT INTO packages (transportadora, codigo_pacote, data, hora, status, coleta_number) VALUES (?, ?, ?, ?, ?, ?)",
                           (transportadora, codigo_pacote, data_atual, hora_atual, status, coleta_number))
            conn.commit()
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar o pacote: {str(e)}")

    def close_collection(self):
        transportadora = self.selected_transportadora.get()
        if transportadora == "Selecione a Transportadora":
            messagebox.showerror("Erro", "Por favor, selecione uma transportadora para fechar a coleta.")
            return

        confirmation = messagebox.askyesno("Confirmação", f"Tem certeza de que deseja fechar a coleta de hoje para {transportadora}?")
        if confirmation:
            try:
                data_atual = datetime.date.today().isoformat()

                # Obter o número da coleta atual dos pacotes pendentes
                cursor.execute("""
                    SELECT coleta_number FROM packages
                    WHERE transportadora = ? AND data = ? AND status = 'pending'
                    LIMIT 1
                """, (transportadora, data_atual))
                result = cursor.fetchone()
                if result:
                    coleta_number = result[0]
                else:
                    messagebox.showwarning("Aviso", "Não há pacotes pendentes para fechar.")
                    return

                # Atualizar status para 'collected' para os pacotes com o número de coleta atual
                cursor.execute("""
                    UPDATE packages 
                    SET status = 'collected' 
                    WHERE transportadora = ? AND data = ? AND status = 'pending' AND coleta_number = ?
                """, (transportadora, data_atual, coleta_number))
                conn.commit()
                self.update_treeview()
                messagebox.showinfo("Sucesso", f"Coleta {coleta_number} de hoje para a transportadora {transportadora} foi fechada com sucesso.")
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao fechar a coleta: {str(e)}")

    def reopen_collection(self):
        transportadora = self.selected_transportadora.get()
        if transportadora == "Selecione a Transportadora":
            messagebox.showerror("Erro", "Por favor, selecione uma transportadora para reabrir a coleta.")
            return

        confirmation = messagebox.askyesno("Confirmação", f"Tem certeza de que deseja reabrir a coleta de hoje para {transportadora}?")
        if confirmation:
            try:
                data_atual = datetime.date.today().isoformat()

                # Obter o número da última coleta fechada
                cursor.execute("""
                    SELECT MAX(coleta_number) FROM packages
                    WHERE transportadora = ? AND data = ? AND status = 'collected'
                """, (transportadora, data_atual))
                result = cursor.fetchone()
                if result and result[0] is not None:
                    coleta_number = result[0]
                else:
                    messagebox.showwarning("Aviso", "Não há coletas fechadas para reabrir.")
                    return

                # Atualizar status para 'pending' para os pacotes da última coleta
                cursor.execute("""
                    UPDATE packages 
                    SET status = 'pending' 
                    WHERE transportadora = ? AND data = ? AND status = 'collected' AND coleta_number = ?
                """, (transportadora, data_atual, coleta_number))
                conn.commit()
                self.update_treeview()
                messagebox.showinfo("Sucesso", f"Coleta {coleta_number} de hoje para a transportadora {transportadora} foi reaberta com sucesso.")
            except Exception as e:
                messagebox.showerror("Erro", f"Ocorreu um erro ao reabrir a coleta: {str(e)}")

    def export_list(self):
        # Janela para selecionar parâmetros de exportação
        export_window = Toplevel(self.root)
        export_window.title("Exportar Coleta")
        export_window.geometry("400x450")

        label = tk.Label(export_window, text="Selecione os parâmetros de exportação:", font=("Helvetica", 12))
        label.pack(pady=10)

        # Selecionar transportadora
        transportadora_label = tk.Label(export_window, text="Transportadora:", font=("Helvetica", 12))
        transportadora_label.pack(pady=5)

        transportadora_var = tk.StringVar()
        transportadora_var.set("Todas")
        transportadora_options = ["Todas"] + self.transportadoras
        transportadora_menu = ttk.Combobox(export_window, textvariable=transportadora_var, values=transportadora_options, font=("Helvetica", 12), state="readonly")
        transportadora_menu.pack(pady=5)

        # Selecionar status
        status_label = tk.Label(export_window, text="Status:", font=("Helvetica", 12))
        status_label.pack(pady=5)

        status_var = tk.StringVar()
        status_var.set("Todos")
        status_options = ["Todos", "pending", "collected"]
        status_menu = ttk.Combobox(export_window, textvariable=status_var, values=status_options, font=("Helvetica", 12), state="readonly")
        status_menu.pack(pady=5)

        # Selecionar data inicial
        start_date_label = tk.Label(export_window, text="Data Inicial:", font=("Helvetica", 12))
        start_date_label.pack(pady=5)

        start_date_entry = DateEntry(export_window, width=20, background='darkblue', foreground='white', date_pattern='yyyy-MM-dd')
        start_date_entry.pack(pady=5)

        # Selecionar data final
        end_date_label = tk.Label(export_window, text="Data Final:", font=("Helvetica", 12))
        end_date_label.pack(pady=5)

        end_date_entry = DateEntry(export_window, width=20, background='darkblue', foreground='white', date_pattern='yyyy-MM-dd')
        end_date_entry.pack(pady=5)

        def confirm_export():
            selected_transportadora = transportadora_var.get()
            start_date = start_date_entry.get_date().isoformat()
            end_date = end_date_entry.get_date().isoformat()
            status = status_var.get()

            if start_date > end_date:
                messagebox.showwarning("Aviso", "A data inicial não pode ser maior que a data final.")
                return

            query = "SELECT * FROM packages WHERE data BETWEEN ? AND ?"
            params = [start_date, end_date]

            if selected_transportadora != "Todas":
                query += " AND transportadora = ?"
                params.append(selected_transportadora)

            if status != "Todos":
                query += " AND status = ?"
                params.append(status)

            try:
                cursor.execute(query, params)
                packages = cursor.fetchall()

                if not packages:
                    messagebox.showwarning("Aviso", "Nenhum pacote registrado para exportar neste período.")
                    return

                file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
                if file_path:
                    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                        writer = csv.writer(file)
                        writer.writerow(["Transportadora", "Código de Pacote", "Data", "Hora", "Status", "Coleta Número"])
                        for package in packages:
                            writer.writerow(package[1:])
                        messagebox.showinfo("Sucesso", "Lista exportada com sucesso!")
                        export_window.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar a lista: {str(e)}")

        export_button = tk.Button(export_window, text="Exportar", command=confirm_export, font=("Helvetica", 12), bg="#4CAF50", fg="white")
        export_button.pack(pady=20)

    def update_treeview(self):
        # Limpar o Treeview
        for item in self.package_treeview.get_children():
            self.package_treeview.delete(item)

        selected_transportadora = self.selected_transportadora.get()
        if selected_transportadora == "Selecione a Transportadora":
            self.total_label.config(text="Total de pacotes bipados hoje:\nNenhuma transportadora selecionada.")
            return

        try:
            data_atual = datetime.date.today().isoformat()
            cursor.execute("""
                SELECT codigo_pacote, data, hora, coleta_number 
                FROM packages 
                WHERE data = ? AND transportadora = ? AND status = 'pending'
            """, (data_atual, selected_transportadora))
            packages = cursor.fetchall()
            for codigo_pacote, data, hora, coleta_number in packages:
                self.package_treeview.insert('', 'end', values=(codigo_pacote, data, hora, coleta_number))

            # Aplicar a coloração somente às linhas dos pacotes
            for item in self.package_treeview.get_children():
                self.package_treeview.item(item, tags=(selected_transportadora,))
            self.package_treeview.tag_configure(selected_transportadora, background=self.transportadora_colors.get(selected_transportadora, 'white'))

            # Atualizar o total de pacotes
            cursor.execute("""
                SELECT COUNT(*) 
                FROM packages 
                WHERE data = ? AND transportadora = ? AND status = 'pending'
            """, (data_atual, selected_transportadora))
            count = cursor.fetchone()[0]
            total_text = f"Total de pacotes bipados hoje para {selected_transportadora}: {count}"
            self.total_label.config(text=total_text)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao atualizar a lista: {str(e)}")

        # Refocar na entrada de código de barras
        self.package_entry.focus_set()

    def update_treeview_on_selection(self, *args):
        self.update_treeview()
        # Destacar a transportadora selecionada
        if self.selected_transportadora.get() != "Selecione a Transportadora":
            self.style.configure('TCombobox', fieldbackground='white')
        else:
            self.style.configure('TCombobox', fieldbackground='red')

    def view_total_packages(self):
        view_window = Toplevel(self.root)
        view_window.title("Consultar Coletas Anteriores")
        view_window.geometry("800x600")

        # Frame principal da nova janela
        view_frame = tk.Frame(view_window, bg="#f0f0f0")
        view_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Seleção de data
        date_label = tk.Label(view_frame, text="Selecione a data:", font=("Helvetica", 14), bg="#f0f0f0")
        date_label.pack(pady=10)

        date_entry = DateEntry(view_frame, width=20, background='darkblue', foreground='white', date_pattern='yyyy-MM-dd')
        date_entry.pack(pady=5)

        # Seleção de transportadora
        transportadora_label = tk.Label(view_frame, text="Transportadora:", font=("Helvetica", 14), bg="#f0f0f0")
        transportadora_label.pack(pady=10)

        transportadora_var = tk.StringVar()
        transportadora_var.set("Todas")
        transportadora_options = ["Todas"] + self.transportadoras
        transportadora_menu = ttk.Combobox(view_frame, textvariable=transportadora_var, values=transportadora_options, font=("Helvetica", 12), state="readonly")
        transportadora_menu.pack(pady=5)

        filter_button = tk.Button(view_frame, text="Filtrar", command=lambda: self.filter_by_date_and_transportadora(date_entry.get_date().isoformat(), transportadora_var.get(), view_frame), font=("Helvetica", 12), bg="#2196F3", fg="white")
        filter_button.pack(pady=10)

        # Frame para resultados
        self.results_frame = tk.Frame(view_frame, bg="#f0f0f0")
        self.results_frame.pack(fill=tk.BOTH, expand=True)

    def filter_by_date_and_transportadora(self, date, transportadora, view_frame):
        # Limpar conteúdos anteriores
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        try:
            # Construir a consulta para contagem por coleta
            query = "SELECT coleta_number, COUNT(*) FROM packages WHERE data = ?"
            params = [date]

            if transportadora != "Todas":
                query += " AND transportadora = ?"
                params.append(transportadora)

            query += " GROUP BY coleta_number ORDER BY coleta_number ASC"

            cursor.execute(query, params)
            results = cursor.fetchall()
            if results:
                total_label = tk.Label(self.results_frame, text=f"Resultados para {date}:", font=("Helvetica", 14, "bold"), bg="#f0f0f0")
                total_label.pack(pady=10)

                for coleta_number, count in results:
                    count_label = tk.Label(self.results_frame, text=f"Coleta {coleta_number}: {count} pacotes", font=("Helvetica", 12), bg="#f0f0f0")
                    count_label.pack()

                # Detalhes dos pacotes
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

                # Buscar detalhes dos pacotes
                query = "SELECT transportadora, codigo_pacote, hora, coleta_number FROM packages WHERE data = ?"
                params = [date]
                if transportadora != "Todas":
                    query += " AND transportadora = ?"
                    params.append(transportadora)

                cursor.execute(query, params)
                package_details = cursor.fetchall()
                for transportadora_result, codigo_pacote, hora, coleta_number in package_details:
                    package_treeview.insert('', 'end', values=(transportadora_result, codigo_pacote, hora, coleta_number))
            else:
                no_data_label = tk.Label(self.results_frame, text="Nenhum pacote registrado para esta data.", font=("Helvetica", 12), bg="#f0f0f0")
                no_data_label.pack(pady=10)
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao filtrar os pacotes: {str(e)}")

    def remove_package(self):
        selected_item = self.package_treeview.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Por favor, selecione um pacote para remover.")
            return

        item = self.package_treeview.item(selected_item)
        codigo_pacote = str(item['values'][0])  # Converter para string
        transportadora = self.selected_transportadora.get()
        coleta_number = item['values'][3]
        try:
            data_atual = datetime.date.today().isoformat()
            cursor.execute("""
                DELETE FROM packages 
                WHERE transportadora = ? AND codigo_pacote = ? AND data = ? AND status = 'pending' AND coleta_number = ?
            """, (transportadora, codigo_pacote, data_atual, coleta_number))
            conn.commit()
            self.update_treeview()
            messagebox.showinfo("Sucesso", "Pacote removido com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro ao remover o pacote: {str(e)}")

    def show_transportadora_help(self):
        messagebox.showinfo("Ajuda - Transportadora", "Selecione a transportadora correspondente aos pacotes que estão sendo coletados.")

    def show_package_help(self):
        messagebox.showinfo("Ajuda - Código de Barras", "Digite ou escaneie o código de barras do pacote para registrá-lo.")

    def on_closing(self):
        # Fechar conexão com o banco de dados ao fechar a aplicação
        conn.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PackageCounterApp(root)
    root.mainloop() 
