# gui/main_app.py

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

        # Override de função caso necessário
        if override_role is not None:
            self.current_user['role'] = override_role

        # Conexão com o banco de dados
        self.conn = conn or get_database_connection(test=(self.db_type == 'test'))[0]
        self.cursor = self.conn.cursor()
        self.root.title(title)

        # Configuração da janela principal
        self.configure_main_window()

        # Lista de transportadoras disponíveis
        self.transportadoras = ["SHEIN", "Shopee", "Mercado Livre"]
        self.transportadora_colors = {
            "SHEIN": "#90EE90",         # Verde Claro
            "Shopee": "#FFA500",        # Laranja
            "Mercado Livre": "#FFFF99"  # Amarelo Claro
        }

        # Variável para a transportadora selecionada
        self.selected_transportadora = tk.StringVar()
        self.selected_transportadora.set(TRANSPORTADORA_PADRAO)
        self.selected_transportadora.trace('w', self.update_treeview_on_selection)

        # Configuração do estilo para o Combobox
        self.style = ttk.Style()
        self.style.configure('TCombobox', font=("Helvetica", 12))

        # Criar a interface baseada no papel do usuário
        if self.current_user['role'] == 'admin' and override_role is None:
            self.create_admin_menu()
        else:
            self.create_user_interface()

        # Fechar conexão com o banco de dados ao fechar a janela
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def configure_main_window(self):
        """
        Configurações iniciais da janela principal.
        """
        # Definir o tamanho da janela para 80% da resolução do monitor
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
        # Limpar a janela
        for widget in self.root.winfo_children():
            widget.destroy()

        # Frame principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(expand=True)

        # Nome da empresa (logo)
        logo_label = tk.Label(main_frame, text="Ponto 3D", font=("Helvetica", 24, "bold"))
        logo_label.pack(pady=10)

        # Título do menu admin
        header_label = tk.Label(main_frame, text="Menu do Administrador", font=("Helvetica", 18, "bold"))
        header_label.pack(pady=10)

        # Botão para gerenciar usuários
        button_font = ("Helvetica", 14)
        manage_users_button = tk.Button(
            main_frame,
            text="Gerenciar Usuários",
            command=self.manage_users,
            font=button_font,
            width=25
        )
        manage_users_button.pack(pady=10)

        # Frame para verificar pedido e ajuda
        verify_frame = tk.Frame(main_frame)
        verify_frame.pack(pady=10)

        # Botão para verificar pedido
        verify_package_button = tk.Button(
            verify_frame,
            text="Verificar Pedido",
            command=self.open_verify_package,
            font=button_font,
            width=20
        )
        verify_package_button.grid(row=0, column=0, padx=5)

        # Botão de ajuda único que depende do tipo de banco de dados
        help_button = tk.Button(
            verify_frame,
            text="?",
            font=("Helvetica", 12),
            command=self.show_verify_help
        )
        help_button.grid(row=0, column=1, padx=5)

        # Botão para acessar o menu de bipagem de testes
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
        # Limpar a janela
        for widget in self.root.winfo_children():
            widget.destroy()

        self.create_widgets()
        self.update_treeview()

    def create_widgets(self):
        """
        Cria os widgets principais da interface de usuário.
        """
        # Frame principal
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Nome da empresa no topo
        company_label = tk.Label(
            main_frame,
            text="Ponto 3D",
            font=("Helvetica", 24, "bold"),
            bg="#f0f0f0"
        )
        company_label.pack(pady=10)

        # Frame superior para seleção de transportadora e entrada de código de barras
        top_frame = tk.Frame(main_frame, bg="#f0f0f0")
        top_frame.pack(fill=tk.X, pady=10)

        # Label e Combobox para seleção de transportadora
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

        # Botão de ajuda para transportadora
        help_transportadora = tk.Button(
            top_frame,
            text="?",
            font=("Helvetica", 12),
            command=self.show_transportadora_help
        )
        help_transportadora.grid(row=0, column=2, padx=5)

        # Label e Entry para entrada do código de barras
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
        self.package_entry.focus_set()  # Focar automaticamente na entrada do código de barras

        # Botão de ajuda para código de barras
        help_package = tk.Button(
            top_frame,
            text="?",
            font=("Helvetica", 12),
            command=self.show_package_help
        )
        help_package.grid(row=1, column=2, padx=5)

        # Frame do Treeview e Total de Pacotes
        treeview_frame = tk.Frame(main_frame, bg="#f0f0f0")
        treeview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Configuração do Treeview para exibir pacotes
        columns = ("codigo_pacote", "data", "hora", "coleta_number", "id")
        self.package_treeview = ttk.Treeview(treeview_frame, columns=columns, show='headings')
        self.package_treeview.heading('codigo_pacote', text='Código de Pacote')
        self.package_treeview.heading('data', text='Data')
        self.package_treeview.heading('hora', text='Hora')
        self.package_treeview.heading('coleta_number', text='Coleta Número')
        self.package_treeview.heading('id', text='ID')  # Adiciona o ID

        # Configuração das colunas
        self.package_treeview.column('codigo_pacote', width=150)
        self.package_treeview.column('data', width=100)
        self.package_treeview.column('hora', width=100)
        self.package_treeview.column('coleta_number', width=100)
        self.package_treeview.column('id', width=50, anchor='center')  # Centraliza o ID

        self.package_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar para o Treeview
        scrollbar = ttk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=self.package_treeview.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.package_treeview.configure(yscroll=scrollbar.set)

        # Label para exibir o total de pacotes
        self.total_label = tk.Label(
            main_frame,
            text="",
            font=("Helvetica", 14, "bold"),
            bg="#f0f0f0"
        )
        self.total_label.pack(pady=10)

        # Frame para os botões de ação
        button_frame = tk.Frame(main_frame, bg="#f0f0f0")
        button_frame.pack(fill=tk.X, pady=20)

        # Botão para exportar a coleta
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
        self.export_button.bind("<Tab>", lambda e: self.close_collection_button.focus_set())
        self.export_button.bind("<Return>", lambda e: self.export_list())

        # Botão para fechar a coleta
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
        self.close_collection_button.bind("<Tab>", lambda e: self.total_button.focus_set())
        self.close_collection_button.bind("<Return>", lambda e: self.close_collection())

        # Botão para consultar coletas anteriores
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
        self.total_button.bind("<Tab>", lambda e: self.reopen_collection_button.focus_set())
        self.total_button.bind("<Return>", lambda e: self.view_total_packages())

        # Botão para reabrir uma coleta
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
        self.reopen_collection_button.bind("<Tab>", lambda e: self.remove_button.focus_set())
        self.reopen_collection_button.bind("<Return>", lambda e: self.reopen_collection())

        # Botão para remover um pacote
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
        self.remove_button.bind("<Tab>", lambda e: self.package_entry.focus_set())
        self.remove_button.bind("<Return>", lambda e: self.remove_package())

        # Botão para verificar pedido
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
        self.verify_button.bind("<Tab>", lambda e: self.export_button.focus_set())
        self.verify_button.bind("<Return>", lambda e: self.open_verify_package())

        # Botão de ajuda para verificar pedidos no usuário
        help_verify_user = tk.Button(
            button_frame,
            text="?",
            font=("Helvetica", 12),
            command=self.show_verify_help
        )
        help_verify_user.grid(row=1, column=3, padx=5)

        # Bind para a tecla Enter na entrada do pacote
        self.package_entry.bind('<Return>', self.add_package)

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
            self.update_treeview()
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()

            # Selecionar a última linha adicionada
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

            # Determinar o próximo número de coleta
            self.cursor.execute("""
                SELECT MAX(coleta_number) FROM packages 
                WHERE transportadora = ? AND data = ? AND status = ?
            """, (transportadora, data_atual, STATUS_COLLECTED))
            result = self.cursor.fetchone()
            max_collected_coleta_number = result[0] if result[0] is not None else 0

            coleta_number = max_collected_coleta_number + 1

            # Inserir o pacote no banco de dados
            self.cursor.execute("""
                INSERT INTO packages (transportadora, codigo_pacote, data, hora, status, coleta_number) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (transportadora, codigo_pacote, data_atual, hora_atual, status, coleta_number))
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

                # Verificar se há pacotes pendentes
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

                # Atualizar o status dos pacotes
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

                # Obter o último número de coleta fechada
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

                # Atualizar o status dos pacotes
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
        # Limpar o Treeview
        for item in self.package_treeview.get_children():
            self.package_treeview.delete(item)

        selected_transportadora = self.selected_transportadora.get()
        if selected_transportadora == TRANSPORTADORA_PADRAO:
            self.total_label.config(text="Total de pacotes bipados hoje:\nNenhuma transportadora selecionada.")
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

            # Aplicar a coloração às linhas dos pacotes com base na transportadora
            for item in self.package_treeview.get_children():
                self.package_treeview.item(item, tags=(selected_transportadora,))
            self.package_treeview.tag_configure(selected_transportadora, background=self.transportadora_colors.get(selected_transportadora, 'white'))

            # Atualizar o total de pacotes
            self.cursor.execute("""
                SELECT COUNT(*) 
                FROM packages 
                WHERE data = ? AND transportadora = ? AND status = ?
            """, (data_atual, selected_transportadora, STATUS_PENDING))
            count = self.cursor.fetchone()[0]
            total_text = f"Total de pacotes bipados hoje para {selected_transportadora}: {count}"
            self.total_label.config(text=total_text)
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
        package_id = item['values'][4]  # ID do pacote

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

        # Definir o tamanho da janela para 800x600 ou a resolução disponível
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        desired_width = 800  # Reduzir o tamanho para evitar problemas em telas menores
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

        # Conectar ao banco de dados de teste
        try:
            test_conn, test_cursor = get_database_connection(test=True)
        except Exception as e:
            logging.error("Erro ao conectar ao banco de dados de teste: %s", e)
            messagebox.showerror("Erro", "Erro ao conectar ao banco de dados de teste. Verifique os logs.")
            test_window.destroy()
            return

        # Criar uma nova instância da aplicação para o modo de teste
        test_app = PackageCounterApp(
            test_window,
            self.current_user.copy(),
            conn=test_conn,
            title="Contador de Pacotes - Ponto 3D - Teste",
            override_role='user',
            db_type='test'  # Define o tipo de DB para 'test'
        )

        # Função para fechar a janela de teste e a conexão
        def on_closing_test():
            try:
                test_conn.close()
            except Exception as e:
                logging.error("Erro ao fechar a conexão de teste: %s", e)
            test_window.destroy()

        test_window.protocol("WM_DELETE_WINDOW", on_closing_test)
        center_window(test_window)
