import tkinter as tk
from tkinter import messagebox, Toplevel
from tkinter import ttk
import datetime
import logging

from config import TRANSPORTADORA_PADRAO, STATUS_PENDING, STATUS_COLLECTED, PACKAGE_CODE_REGEX
from utils import detect_transportadora, play_sound, center_window
from database import get_database_connection

# Importar janelas secundárias
from gui.view_total_packages import ViewTotalPackagesWindow
from gui.user_management import UserManagementWindow
from gui.export import ExportWindow
from gui.verify_package import VerifyPackageWindow

class PackageCounterApp:
    """
    Classe principal da aplicação de contagem de pacotes.
    """
    def __init__(self, root, current_user, conn=None, title="Contador de Pacotes - Ponto 3D", override_role=None, db_type='main'):
        self.root = root
        self.current_user = current_user
        self.db_type = db_type  # 'main' ou 'test'

        if override_role is not None:
            self.current_user['role'] = override_role

        self.conn = conn or get_database_connection(test=(self.db_type == 'test'))[0]
        self.cursor = self.conn.cursor()
        self.root.title(title)

        self.configure_main_window()

        self.transportadoras = ["SHEIN", "Shopee", "Mercado Livre"]
        self.transportadora_colors = {
            "SHEIN": "#90EE90",
            "Shopee": "#FFA500",
            "Mercado Livre": "#FFFF99"
        }

        self.selected_transportadora = tk.StringVar()
        self.selected_transportadora.set(TRANSPORTADORA_PADRAO)
        self.selected_transportadora.trace('w', self.update_treeview_on_selection)

        self.style = ttk.Style()
        self.style.configure('TCombobox', font=("Helvetica", 12))

        if self.current_user['role'] == 'admin' and override_role is None:
            self.create_admin_menu()
        else:
            self.create_user_interface()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def configure_main_window(self):
        """
        Configurações iniciais da janela principal.
        """
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f'{window_width}x{window_height}+{x}+{y}')

    def create_admin_menu(self):
        """
        Cria o menu administrativo com opções de gerenciamento de usuários e verificação de pedidos.
        """
        for widget in self.root.winfo_children():
            widget.destroy()

        main_frame = tk.Frame(self.root)
        main_frame.pack(expand=True)

        logo_label = tk.Label(main_frame, text="Ponto 3D", font=("Helvetica", 24, "bold"))
        logo_label.pack(pady=10)

        header_label = tk.Label(main_frame, text="Menu do Administrador", font=("Helvetica", 18, "bold"))
        header_label.pack(pady=10)

        button_font = ("Helvetica", 14)
        manage_users_button = tk.Button(
            main_frame,
            text="Gerenciar Usuários",
            command=self.manage_users,
            font=button_font,
            width=25
        )
        manage_users_button.pack(pady=10)

        verify_frame = tk.Frame(main_frame)
        verify_frame.pack(pady=10)

        verify_package_button = tk.Button(
            verify_frame,
            text="Verificar Pedido",
            command=self.open_verify_package,
            font=button_font,
            width=20
        )
        verify_package_button.grid(row=0, column=0, padx=5)

        help_button = tk.Button(
            verify_frame,
            text="?",
            font=("Helvetica", 12),
            command=self.show_verify_help
        )
        help_button.grid(row=0, column=1, padx=5)

        test_scanning_button = tk.Button(
            main_frame,
            text="Menu de Bipagem de Testes",
            command=self.open_test_scanning,
            font=button_font,
            width=25
        )
        test_scanning_button.pack(pady=10)

    def create_user_interface(self):
        """
        Cria a interface de usuário para operações normais (não-admin).
        """
        for widget in self.root.winfo_children():
            widget.destroy()

        self.create_widgets()
        self.update_treeview()

    def create_widgets(self):
        """
        Cria os widgets principais da interface de usuário.
        """
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Título ou logo
        company_label = tk.Label(
            main_frame,
            text="Ponto 3D",
            font=("Helvetica", 24, "bold"),
            bg="#f0f0f0"
        )
        company_label.pack(pady=10)

        # Frame superior para transportadora e código
        top_frame = tk.Frame(main_frame, bg="#f0f0f0")
        top_frame.pack(fill=tk.X, pady=10)

        transportadora_label = tk.Label(
            top_frame,
            text="Transportadora:",
            font=("Helvetica", 14, "bold"),
            bg="#f0f0f0"
        )
        transportadora_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.transportadora_menu = ttk.Combobox(
            top_frame,
            textvariable=self.selected_transportadora,
            values=self.transportadoras,
            font=("Helvetica", 12),
            width=25,
            state="readonly"
        )
        self.transportadora_menu.grid(row=0, column=1, padx=10, pady=10)
        self.transportadora_menu.bind("<Tab>", lambda e: self.package_entry.focus_set())
        self.transportadora_menu.bind("<Return>", lambda e: self.package_entry.focus_set())

        help_transportadora = tk.Button(
            top_frame,
            text="?",
            font=("Helvetica", 12),
            command=self.show_transportadora_help
        )
        help_transportadora.grid(row=0, column=2, padx=5)

        package_label = tk.Label(
            top_frame,
            text="Bipe o código de barras:",
            font=("Helvetica", 14, "bold"),
            bg="#f0f0f0"
        )
        package_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.package_entry = tk.Entry(
            top_frame,
            width=40,
            font=("Helvetica", 12)
        )
        self.package_entry.grid(row=1, column=1, padx=10, pady=10)
        self.package_entry.bind('<Return>', self.add_package)
        self.package_entry.bind("<Tab>", lambda e: self.export_button.focus_set())
        self.package_entry.focus_set()

        help_package = tk.Button(
            top_frame,
            text="?",
            font=("Helvetica", 12),
            command=self.show_package_help
        )
        help_package.grid(row=1, column=2, padx=5)

        # Frame do Treeview no meio
        treeview_frame = tk.Frame(main_frame, bg="#f0f0f0")
        treeview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        columns = ("codigo_pacote", "data", "hora", "coleta_number", "id")
        self.package_treeview = ttk.Treeview(treeview_frame, columns=columns, show='headings')
        self.package_treeview.heading('codigo_pacote', text='Código de Pacote')
        self.package_treeview.heading('data', text='Data')
        self.package_treeview.heading('hora', text='Hora')
        self.package_treeview.heading('coleta_number', text='Coleta Número')
        self.package_treeview.heading('id', text='ID')

        self.package_treeview.column('codigo_pacote', width=150)
        self.package_treeview.column('data', width=100)
        self.package_treeview.column('hora', width=100)
        self.package_treeview.column('coleta_number', width=100)
        self.package_treeview.column('id', width=50, anchor='center')

        self.package_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=self.package_treeview.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.package_treeview.configure(yscroll=scrollbar.set)

        # Frame inferior para botões em grid
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(fill=tk.X, pady=20)

        self.export_button = tk.Button(
            button_frame,
            text="Exportar Coleta",
            command=self.export_list,
            font=("Helvetica", 12),
            bg="#4CAF50",
            fg="white",
            width=20
        )
        self.export_button.grid(row=0, column=0, padx=10, pady=10)

        self.close_collection_button = tk.Button(
            button_frame,
            text="Fechar Coleta",
            command=self.close_collection,
            font=("Helvetica", 12),
            bg="#f44336",
            fg="white",
            width=20
        )
        self.close_collection_button.grid(row=0, column=1, padx=10, pady=10)

        self.total_button = tk.Button(
            button_frame,
            text="Consultar Coletas Anteriores",
            command=self.view_total_packages,
            font=("Helvetica", 12),
            bg="#2196F3",
            fg="white",
            width=25
        )
        self.total_button.grid(row=0, column=2, padx=10, pady=10)

        self.remove_button = tk.Button(
            button_frame,
            text="Remover",
            command=self.remove_package,
            font=("Helvetica", 12),
            bg="#FF9800",
            fg="white",
            width=15
        )
        self.remove_button.grid(row=1, column=0, padx=10, pady=10)

        self.reopen_collection_button = tk.Button(
            button_frame,
            text="Reabrir Coleta",
            command=self.reopen_collection,
            font=("Helvetica", 12),
            bg="#8B4513",
            fg="white",
            width=20
        )
        self.reopen_collection_button.grid(row=1, column=1, padx=10, pady=10)

        self.verify_button = tk.Button(
            button_frame,
            text="Verificar Pedido",
            command=self.open_verify_package,
            font=("Helvetica", 12),
            bg="#673AB7",
            fg="white",
            width=20
        )
        self.verify_button.grid(row=1, column=2, padx=10, pady=10)

        help_verify_user = tk.Button(
            button_frame,
            text="?",
            font=("Helvetica", 12),
            command=self.show_verify_help
        )
        help_verify_user.grid(row=1, column=3, padx=5)

        # NOVO: frame à direita (coluna 4) para a frase e total
        right_info_frame = tk.Frame(button_frame, bg="#f0f0f0")
        # rowspan=2 faz ocupar as duas linhas de botões
        right_info_frame.grid(row=0, column=4, rowspan=2, sticky="nsew", padx=(40, 0))

        self.total_text_label = tk.Label(
            right_info_frame,
            text="TOTAL DE PEDIDOS BIPADOS",
            font=("Helvetica", 18, "bold"),
            bg="#f0f0f0"
        )
        self.total_text_label.pack(anchor="center", pady=(0, 10))

        self.big_total_label = tk.Label(
            right_info_frame,
            text="0",
            font=("Helvetica", 72, "bold"),
            fg="#333333",
            bg="#f0f0f0"
        )
        self.big_total_label.pack(anchor="center")

        self.transportadora_label_big = tk.Label(
            right_info_frame,
            text="",  # Ex: (SHEIN)
            font=("Helvetica", 18),
            bg="#f0f0f0"
        )
        self.transportadora_label_big.pack(anchor="center", pady=(10, 0))

    def show_verify_help(self):
        """
        Exibe uma mensagem de ajuda sobre a verificação de pedidos baseada no tipo de banco de dados.
        """
        if self.db_type == 'main':
            message = "Verifica os pedidos no Banco de Dados Principal.\nUse para pedidos reais."
        elif self.db_type == 'test':
            message = "Verifica os pedidos no Banco de Dados de Teste.\nUse para testes sem afetar dados reais."
        else:
            message = "Opção de verificação de pedidos."
        messagebox.showinfo("Ajuda - Verificar Pedido", message)

    def open_verify_package(self):
        """
        Abre a janela de verificação de pedidos, ajustando o título conforme o banco de dados.
        """
        if self.db_type == 'main':
            title = "Verificar Pedido (DB Principal)"
        elif self.db_type == 'test':
            title = "Verificar Pedido (DB de Teste)"
        else:
            title = "Verificar Pedido"

        VerifyPackageWindow(self, self.conn, title)

    def add_package(self, event=None):
        """
        Adiciona um novo pacote ao banco de dados após verificar duplicatas e validar a transportadora.
        """
        transportadora = self.selected_transportadora.get()
        package_code = self.package_entry.get().strip()

        if not package_code:
            messagebox.showwarning("Aviso", "Por favor, insira um código válido.")
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()
            return

        if transportadora == TRANSPORTADORA_PADRAO:
            messagebox.showerror("Erro", "Selecione uma transportadora antes de bipar o pacote.")
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()
            return

        if not PACKAGE_CODE_REGEX.match(package_code):
            play_sound('error')
            messagebox.showerror(
                "Erro",
                "Código de pacote inválido.\nVerifique e tente novamente."
            )
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()
            return

        detected_transportadora = detect_transportadora(package_code)

        if detected_transportadora == "Nota Fiscal":
            play_sound('error')
            messagebox.showerror(
                "Erro",
                f"Você está tentando bipar um código de Nota Fiscal com a transportadora {transportadora}.\nVerifique o código."
            )
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()
            return
        elif detected_transportadora and detected_transportadora != transportadora:
            play_sound('error')
            messagebox.showerror(
                "Erro",
                f"O código pertence à transportadora {detected_transportadora}.\nSelecione a transportadora correta."
            )
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()
            return
        elif detected_transportadora is None:
            play_sound('error')
            messagebox.showerror(
                "Erro",
                "Código de barras não reconhecido.\nVerifique e tente novamente."
            )
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()
            return

        try:
            self.cursor.execute(
                "SELECT * FROM packages WHERE codigo_pacote = ? AND data = ? AND transportadora = ?",
                (package_code, datetime.date.today().isoformat(), transportadora)
            )
            if self.cursor.fetchone():
                play_sound('alert')
                messagebox.showerror("Duplicado", "Este pacote já foi registrado hoje para esta transportadora.")
                self.package_entry.delete(0, tk.END)
                self.package_entry.focus_set()
                return

            self.save_package(transportadora, package_code)
            play_sound('success')

            self.update_treeview()
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()

            children = self.package_treeview.get_children()
            if children:
                last_item = children[-1]
                self.package_treeview.selection_set(last_item)
                self.package_treeview.focus(last_item)

        except Exception as e:
            logging.error("Erro ao adicionar pacote: %s", e)
            messagebox.showerror("Erro", f"Ocorreu um erro ao adicionar o pacote: {str(e)}")

    def save_package(self, transportadora, codigo_pacote):
        """
        Salva um novo pacote no banco de dados.
        """
        try:
            data_atual = datetime.date.today().isoformat()
            hora_atual = datetime.datetime.now().strftime("%H:%M:%S")
            status = STATUS_PENDING

            self.cursor.execute("""
                SELECT MAX(coleta_number) FROM packages 
                WHERE transportadora = ? AND data = ? AND status = ?
            """, (transportadora, data_atual, STATUS_COLLECTED))
            result = self.cursor.fetchone()
            max_collected_coleta_number = result[0] if result and result[0] else 0
            coleta_number = max_collected_coleta_number + 1

            # Registrar quem bipou
            bipped_by = self.current_user['username']

            self.cursor.execute("""
                INSERT INTO packages (transportadora, codigo_pacote, data, hora, status, coleta_number, bipped_by) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (transportadora, codigo_pacote, data_atual, hora_atual, status, coleta_number, bipped_by))
            self.conn.commit()
        except Exception as e:
            logging.error("Erro ao salvar pacote: %s", e)
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar o pacote: {str(e)}")

    def close_collection(self):
        """
        Fecha a coleta atual, atualizando o status dos pacotes para 'collected'.
        """
        transportadora = self.selected_transportadora.get()
        if transportadora == TRANSPORTADORA_PADRAO:
            messagebox.showerror("Erro", "Selecione uma transportadora para fechar a coleta.")
            return

        confirmation = messagebox.askyesno("Confirmação", f"Fechar coleta de hoje para {transportadora}?")
        if confirmation:
            try:
                data_atual = datetime.date.today().isoformat()
                self.cursor.execute("""
                    SELECT coleta_number FROM packages
                    WHERE transportadora = ? AND data = ? AND status = ?
                    LIMIT 1
                """, (transportadora, data_atual, STATUS_PENDING))
                result = self.cursor.fetchone()
                if result:
                    coleta_number = result[0]
                else:
                    messagebox.showwarning("Aviso", "Não há pacotes pendentes para fechar.")
                    return

                self.cursor.execute("""
                    UPDATE packages 
                    SET status = ? 
                    WHERE transportadora = ? AND data = ? AND status = ? AND coleta_number = ?
                """, (STATUS_COLLECTED, transportadora, data_atual, STATUS_PENDING, coleta_number))

                rows_updated = self.cursor.rowcount
                self.conn.commit()

                if rows_updated > 0:
                    messagebox.showinfo("Sucesso", f"Coleta {coleta_number} fechada com sucesso.\nPacotes atualizados: {rows_updated}")
                else:
                    messagebox.showwarning("Aviso", "Nenhum pacote foi atualizado.")

                self.update_treeview()
            except Exception as e:
                logging.error("Erro ao fechar a coleta: %s", e)
                messagebox.showerror("Erro", f"Ocorreu um erro ao fechar a coleta: {str(e)}")

    def reopen_collection(self):
        """
        Reabre a última coleta fechada, atualizando o status dos pacotes para 'pending'.
        """
        transportadora = self.selected_transportadora.get()
        if transportadora == TRANSPORTADORA_PADRAO:
            messagebox.showerror("Erro", "Selecione uma transportadora para reabrir a coleta.")
            return

        confirmation = messagebox.askyesno("Confirmação", f"Reabrir coleta de hoje para {transportadora}?")
        if confirmation:
            try:
                data_atual = datetime.date.today().isoformat()
                self.cursor.execute("""
                    SELECT MAX(coleta_number) FROM packages
                    WHERE transportadora = ? AND data = ? AND status = ?
                """, (transportadora, data_atual, STATUS_COLLECTED))
                result = self.cursor.fetchone()
                if result and result[0] is not None:
                    coleta_number = result[0]
                else:
                    messagebox.showwarning("Aviso", "Não há coletas fechadas para reabrir.")
                    return

                self.cursor.execute("""
                    UPDATE packages 
                    SET status = ? 
                    WHERE transportadora = ? AND data = ? AND status = ? AND coleta_number = ?
                """, (STATUS_PENDING, transportadora, data_atual, STATUS_COLLECTED, coleta_number))
                rows_updated = self.cursor.rowcount
                self.conn.commit()

                if rows_updated > 0:
                    messagebox.showinfo("Sucesso", f"Coleta {coleta_number} reaberta com sucesso.")
                else:
                    messagebox.showwarning("Aviso", "Nenhum pacote foi atualizado.")

                self.update_treeview()
            except Exception as e:
                logging.error("Erro ao reabrir a coleta: %s", e)
                messagebox.showerror("Erro", f"Ocorreu um erro ao reabrir a coleta: {str(e)}")

    def export_list(self):
        """
        Exporta a lista de pacotes para um arquivo CSV.
        """
        ExportWindow(self)

    def update_treeview(self):
        """
        Atualiza o Treeview com os pacotes registrados para a transportadora selecionada no dia atual.
        """
        for item in self.package_treeview.get_children():
            self.package_treeview.delete(item)

        selected_transportadora = self.selected_transportadora.get()
        if selected_transportadora == TRANSPORTADORA_PADRAO:
            self.big_total_label.config(text="0")
            self.transportadora_label_big.config(text="")
            return

        try:
            data_atual = datetime.date.today().isoformat()
            self.cursor.execute("""
                SELECT codigo_pacote, data, hora, coleta_number, id 
                FROM packages 
                WHERE data = ? AND transportadora = ? AND status = ?
            """, (data_atual, selected_transportadora, STATUS_PENDING))
            packages = self.cursor.fetchall()
            for pacote in packages:
                self.package_treeview.insert('', 'end', values=(pacote[0], pacote[1], pacote[2], pacote[3], pacote[4]))

            # Colorir pela transportadora
            for item in self.package_treeview.get_children():
                self.package_treeview.item(item, tags=(selected_transportadora,))
            self.package_treeview.tag_configure(selected_transportadora, background=self.transportadora_colors.get(selected_transportadora, 'white'))

            self.cursor.execute("""
                SELECT COUNT(*) 
                FROM packages 
                WHERE data = ? AND transportadora = ? AND status = ?
            """, (data_atual, selected_transportadora, STATUS_PENDING))
            count = self.cursor.fetchone()[0]
            self.big_total_label.config(text=str(count))
            self.transportadora_label_big.config(text=f"({selected_transportadora})")
        except Exception as e:
            logging.error("Erro ao atualizar a lista: %s", e)
            messagebox.showerror("Erro", f"Ocorreu um erro ao atualizar a lista: {str(e)}")

        self.package_entry.focus_set()

    def update_treeview_on_selection(self, *args):
        """
        Atualiza o Treeview quando a transportadora selecionada muda.
        """
        self.update_treeview()
        if self.selected_transportadora.get() != TRANSPORTADORA_PADRAO:
            self.style.configure('TCombobox', fieldbackground='white')
        else:
            self.style.configure('TCombobox', fieldbackground='red')

    def view_total_packages(self):
        """
        Abre uma janela para consultar coletas anteriores com filtros de data e transportadora.
        """
        ViewTotalPackagesWindow(self)

    def remove_package(self):
        """
        Remove um pacote selecionado do banco de dados.
        """
        selected_item = self.package_treeview.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione um pacote para remover.")
            return

        item = self.package_treeview.item(selected_item)
        codigo_pacote = str(item['values'][0])
        transportadora = self.selected_transportadora.get()
        coleta_number = item['values'][3]
        package_id = item['values'][4]

        try:
            data_atual = datetime.date.today().isoformat()
            self.cursor.execute("""
                DELETE FROM packages 
                WHERE id = ? AND transportadora = ? AND codigo_pacote = ? AND data = ? AND status = ? AND coleta_number = ?
            """, (package_id, transportadora, codigo_pacote, data_atual, STATUS_PENDING, coleta_number))
            self.conn.commit()
            self.update_treeview()
            messagebox.showinfo("Sucesso", "Pacote removido com sucesso.")
        except Exception as e:
            logging.error("Erro ao remover pacote: %s", e)
            messagebox.showerror("Erro", f"Ocorreu um erro ao remover o pacote: {str(e)}")

    def show_transportadora_help(self):
        """
        Exibe uma mensagem de ajuda sobre a seleção de transportadora.
        """
        messagebox.showinfo("Ajuda - Transportadora", "Selecione a transportadora correspondente aos pacotes.")

    def show_package_help(self):
        """
        Exibe uma mensagem de ajuda sobre a entrada do código de barras.
        """
        messagebox.showinfo("Ajuda - Código de Barras", "Insira ou escaneie o código de barras do pacote.")

    def on_closing(self):
        """
        Fecha a conexão com o banco de dados e destrói a janela principal.
        """
        try:
            self.conn.close()
        except Exception as e:
            logging.error("Erro ao fechar a conexão com o banco de dados: %s", e)
        self.root.destroy()

    def manage_users(self):
        """
        Abre a janela de gerenciamento de usuários.
        """
        UserManagementWindow(self)

    def open_test_scanning(self):
        """
        Abre uma janela de teste para simular a contagem de pacotes.
        """
        test_window = Toplevel(self.root)
        test_window.transient(self.root)
        test_window.grab_set()
        test_window.title("Contador de Pacotes - Ponto 3D - Teste")

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        desired_width = 800
        desired_height = 600

        if screen_width >= desired_width and screen_height >= desired_height:
            window_width = desired_width
            window_height = desired_height
        else:
            window_width = screen_width
            window_height = screen_height

        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        test_window.geometry(f'{window_width}x{window_height}+{x}+{y}')
        test_window.state('normal')

        try:
            test_conn, test_cursor = get_database_connection(test=True)
        except Exception as e:
            logging.error("Erro ao conectar ao banco de dados de teste: %s", e)
            messagebox.showerror("Erro", "Erro ao conectar ao banco de dados de teste. Verifique os logs.")
            test_window.destroy()
            return

        test_app = PackageCounterApp(
            test_window,
            self.current_user.copy(),
            conn=test_conn,
            title="Contador de Pacotes - Ponto 3D - Teste",
            override_role='user',
            db_type='test'
        )

        def on_closing_test():
            try:
                test_conn.close()
            except Exception as e:
                logging.error("Erro ao fechar a conexão de teste: %s", e)
            test_window.destroy()

        test_window.protocol("WM_DELETE_WINDOW", on_closing_test)
        center_window(test_window)
