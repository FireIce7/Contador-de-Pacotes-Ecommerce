# gui/main_app.py

import tkinter as tk
from tkinter import messagebox, filedialog, Toplevel
from tkinter import ttk
from tkcalendar import DateEntry
import csv
import datetime
import os
import sys
import threading
import logging

from config import TRANSPORTADORA_PADRAO, STATUS_PENDING, STATUS_COLLECTED, PACKAGE_CODE_REGEX
from utils import detect_transportadora, play_sound, center_window
from database import get_database_connection

# Agora importamos corretamente a janela de visualização de coletas anteriores
from gui.view_total_packages import ViewTotalPackagesWindow

class PackageCounterApp:
    """
    Classe principal da aplicação de contagem de pacotes.
    """
    def __init__(self, root, current_user, conn=None, title="Contador de Pacotes - Ponto 3D", override_role=None):
        self.root = root
        self.current_user = current_user

        if override_role is not None:
            self.current_user['role'] = override_role

        self.conn = conn or get_database_connection()[0]
        self.cursor = self.conn.cursor()
        self.root.title(title)

        # Definir o tamanho da janela para 80% da resolução do monitor
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = int(screen_width * 0.8)
        window_height = int(screen_height * 0.8)
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.root.geometry(f'{window_width}x{window_height}+{x}+{y}')

        # Lista de transportadoras disponíveis
        self.transportadoras = ["SHEIN", "Shopee", "Mercado Livre"]
        self.transportadora_colors = {
            "SHEIN": "#90EE90",         # Verde Claro
            "Shopee": "#FFA500",        # Laranja
            "Mercado Livre": "#FFFF99"  # Amarelo Claro
        }

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

    def create_admin_menu(self):
        """
        Cria o menu administrativo com opções de gerenciamento de usuários e modo de teste.
        """
        # Limpar qualquer conteúdo existente na janela
        for widget in self.root.winfo_children():
            widget.destroy()

        # Frame principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(expand=True)

        # Label com o nome da empresa (logo)
        logo_label = tk.Label(main_frame, text="Ponto 3D", font=("Helvetica", 24, "bold"))
        logo_label.pack(pady=10)

        # Título ou cabeçalho
        header_label = tk.Label(main_frame, text="Menu do Administrador", font=("Helvetica", 18, "bold"))
        header_label.pack(pady=10)

        # Botões para as opções
        button_font = ("Helvetica", 14)
        manage_users_button = tk.Button(main_frame, text="Gerenciar Usuários", command=self.manage_users, font=button_font, width=25)
        manage_users_button.pack(pady=10)

        test_scanning_button = tk.Button(main_frame, text="Menu de Bipagem de Testes", command=self.open_test_scanning, font=button_font, width=25)
        test_scanning_button.pack(pady=10)

    def create_user_interface(self):
        """
        Cria a interface de usuário para operações normais (não-admin).
        """
        # Limpar qualquer conteúdo existente na janela
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

        # Adicionar o nome da empresa no topo
        company_label = tk.Label(main_frame, text="Ponto 3D", font=("Helvetica", 24, "bold"), bg="#f0f0f0")
        company_label.pack(pady=10)

        # Frame superior para seleção de transportadora e entrada de código de barras
        top_frame = tk.Frame(main_frame, bg="#f0f0f0")
        top_frame.pack(fill=tk.X, pady=10)

        # Label e Combobox para seleção de transportadora
        transportadora_label = tk.Label(top_frame, text="Transportadora:", font=("Helvetica", 14, "bold"), bg="#f0f0f0")
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
        help_transportadora = tk.Button(top_frame, text="?", font=("Helvetica", 12), command=self.show_transportadora_help)
        help_transportadora.grid(row=0, column=2, padx=5)

        # Label e Entry para entrada do código de barras
        package_label = tk.Label(top_frame, text="Bipe o código de barras:", font=("Helvetica", 14, "bold"), bg="#f0f0f0")
        package_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.package_entry = tk.Entry(top_frame, width=40, font=("Helvetica", 12))
        self.package_entry.grid(row=1, column=1, padx=10, pady=10)
        self.package_entry.bind('<Return>', self.add_package)
        self.package_entry.bind("<Tab>", lambda e: self.export_button.focus_set())
        self.package_entry.focus_set()  # Focar automaticamente na entrada do código de barras

        # Botão de ajuda para código de barras
        help_package = tk.Button(top_frame, text="?", font=("Helvetica", 12), command=self.show_package_help)
        help_package.grid(row=1, column=2, padx=5)

        # Frame do Treeview e Total de Pacotes
        treeview_frame = tk.Frame(main_frame, bg="#f0f0f0")
        treeview_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Configuração do Treeview para exibir pacotes
        columns = ("codigo_pacote", "data", "hora", "coleta_number")
        self.package_treeview = ttk.Treeview(treeview_frame, columns=columns, show='headings')
        self.package_treeview.heading('codigo_pacote', text='Código de Pacote')
        self.package_treeview.heading('data', text='Data')
        self.package_treeview.heading('hora', text='Hora')
        self.package_treeview.heading('coleta_number', text='Coleta Número')
        self.package_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar para o Treeview
        scrollbar = ttk.Scrollbar(treeview_frame, orient=tk.VERTICAL, command=self.package_treeview.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.package_treeview.configure(yscroll=scrollbar.set)

        # Label para exibir o total de pacotes
        self.total_label = tk.Label(main_frame, text="", font=("Helvetica", 14, "bold"), bg="#f0f0f0")
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

    def add_package(self, event=None):
        transportadora = self.selected_transportadora.get()
        package_code = self.package_entry.get().strip()

        if not package_code:
            messagebox.showwarning("Aviso", "Por favor, bipar um código válido.")
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()
            return

        if transportadora == TRANSPORTADORA_PADRAO:
            messagebox.showerror("Erro", "Por favor, selecione uma transportadora antes de bipar o pacote.")
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()
            return

        if not PACKAGE_CODE_REGEX.match(package_code):
            play_sound('error')
            messagebox.showerror(
                "Erro",
                "Formato de código de pacote inválido.\n\n"
                "Por favor, verifique o código e tente novamente."
            )
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()
            return

        detected_transportadora = detect_transportadora(package_code)

        if detected_transportadora == "Nota Fiscal":
            play_sound('error')
            messagebox.showerror(
                "Erro",
                f"Você está tentando bipar um código de Nota Fiscal com a transportadora {transportadora} selecionada.\n\n"
                "Por favor, verifique o código de barras do pacote."
            )
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()
            return
        elif detected_transportadora and detected_transportadora != transportadora:
            play_sound('error')
            messagebox.showerror(
                "Erro",
                f"O código bipado pertence à transportadora {detected_transportadora}.\n\n"
                f"Por favor, selecione a transportadora correta ({detected_transportadora}) e tente novamente."
            )
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()
            return
        elif detected_transportadora is None:
            play_sound('error')
            messagebox.showerror(
                "Erro",
                "Código de barras inválido ou não reconhecido.\n\n"
                "Por favor, verifique o código e tente novamente."
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
                messagebox.showerror("Pacote Duplicado", "Este pacote já foi registrado hoje para esta transportadora.")
                self.package_entry.delete(0, tk.END)
                self.package_entry.focus_set()
                return

            self.save_package(transportadora, package_code)
            self.update_treeview()
            self.package_entry.delete(0, tk.END)
            self.package_entry.focus_set()

            # Destacar a última linha adicionada
            children = self.package_treeview.get_children()
            if children:
                last_item = children[-1]
                self.package_treeview.selection_set(last_item)
                self.package_treeview.focus(last_item)

        except Exception as e:
            logging.error("Erro ao adicionar pacote: %s", e)
            messagebox.showerror("Erro", f"Ocorreu um erro ao adicionar o pacote: {str(e)}")

    def save_package(self, transportadora, codigo_pacote):
        try:
            data_atual = datetime.date.today().isoformat()
            hora_atual = datetime.datetime.now().strftime("%H:%M:%S")
            status = STATUS_PENDING

            self.cursor.execute("""
                SELECT MAX(coleta_number) FROM packages 
                WHERE transportadora = ? AND data = ? AND status = ?
            """, (transportadora, data_atual, STATUS_COLLECTED))
            result = self.cursor.fetchone()
            max_collected_coleta_number = result[0] if result[0] is not None else 0

            coleta_number = max_collected_coleta_number + 1

            self.cursor.execute("""
                INSERT INTO packages (transportadora, codigo_pacote, data, hora, status, coleta_number) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (transportadora, codigo_pacote, data_atual, hora_atual, status, coleta_number))
            self.conn.commit()
        except Exception as e:
            logging.error("Erro ao salvar pacote: %s", e)
            messagebox.showerror("Erro", f"Ocorreu um erro ao salvar o pacote: {str(e)}")

    def close_collection(self):
        transportadora = self.selected_transportadora.get()
        if transportadora == TRANSPORTADORA_PADRAO:
            messagebox.showerror("Erro", "Por favor, selecione uma transportadora para fechar a coleta.")
            return

        confirmation = messagebox.askyesno("Confirmação", f"Tem certeza de que deseja fechar a coleta de hoje para {transportadora}?")
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
                    messagebox.showinfo("Sucesso", f"Coleta {coleta_number} de hoje para a transportadora {transportadora} foi fechada com sucesso. Pacotes atualizados: {rows_updated}")
                else:
                    messagebox.showwarning("Aviso", "Nenhum pacote foi atualizado. Verifique se havia pacotes pendentes.")
                
                self.update_treeview()
            except Exception as e:
                logging.error("Erro ao fechar a coleta: %s", e)
                messagebox.showerror("Erro", f"Ocorreu um erro ao fechar a coleta: {str(e)}")

    def reopen_collection(self):
        transportadora = self.selected_transportadora.get()
        if transportadora == TRANSPORTADORA_PADRAO:
            messagebox.showerror("Erro", "Por favor, selecione uma transportadora para reabrir a coleta.")
            return

        confirmation = messagebox.askyesno("Confirmação", f"Tem certeza de que deseja reabrir a coleta de hoje para {transportadora}?")
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
                    messagebox.showinfo("Sucesso", f"Coleta {coleta_number} de hoje para a transportadora {transportadora} foi reaberta com sucesso.")
                else:
                    messagebox.showwarning("Aviso", "Nenhum pacote foi atualizado ao tentar reabrir a coleta.")
                
                self.update_treeview()
            except Exception as e:
                logging.error("Erro ao reabrir a coleta: %s", e)
                messagebox.showerror("Erro", f"Ocorreu um erro ao reabrir a coleta: {str(e)}")

    def export_list(self):
        """
        Exporta a lista de pacotes com base nos parâmetros selecionados para um arquivo CSV.
        """
        from gui.export import ExportWindow  # Importação tardia para evitar dependências circulares
        ExportWindow(self)

    def update_treeview(self):
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
                SELECT codigo_pacote, data, hora, coleta_number 
                FROM packages 
                WHERE data = ? AND transportadora = ? AND status = ?
            """, (data_atual, selected_transportadora, STATUS_PENDING))
            packages = self.cursor.fetchall()
            for codigo_pacote, data, hora, coleta_number in packages:
                self.package_treeview.insert('', 'end', values=(codigo_pacote, data, hora, coleta_number))

            for item in self.package_treeview.get_children():
                self.package_treeview.item(item, tags=(selected_transportadora,))
            self.package_treeview.tag_configure(selected_transportadora, background=self.transportadora_colors.get(selected_transportadora, 'white'))

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
        self.update_treeview()
        if self.selected_transportadora.get() != TRANSPORTADORA_PADRAO:
            self.style.configure('TCombobox', fieldbackground='white')
        else:
            self.style.configure('TCombobox', fieldbackground='red')

    def view_total_packages(self):
        """
        Abre uma janela para consultar coletas anteriores com filtros de data e transportadora.
        """
        # Agora importamos do módulo correto
        ViewTotalPackagesWindow(self)

    def remove_package(self):
        selected_item = self.package_treeview.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Por favor, selecione um pacote para remover.")
            return

        item = self.package_treeview.item(selected_item)
        codigo_pacote = str(item['values'][0])
        transportadora = self.selected_transportadora.get()
        coleta_number = item['values'][3]

        try:
            data_atual = datetime.date.today().isoformat()
            self.cursor.execute("""
                DELETE FROM packages 
                WHERE transportadora = ? AND codigo_pacote = ? AND data = ? AND status = ? AND coleta_number = ?
            """, (transportadora, codigo_pacote, data_atual, STATUS_PENDING, coleta_number))
            self.conn.commit()
            self.update_treeview()
            messagebox.showinfo("Sucesso", "Pacote removido com sucesso.")
        except Exception as e:
            logging.error("Erro ao remover pacote: %s", e)
            messagebox.showerror("Erro", f"Ocorreu um erro ao remover o pacote: {str(e)}")

    def show_transportadora_help(self):
        messagebox.showinfo("Ajuda - Transportadora", "Selecione a transportadora correspondente aos pacotes que estão sendo coletados.")

    def show_package_help(self):
        messagebox.showinfo("Ajuda - Código de Barras", "Digite ou escaneie o código de barras do pacote para registrá-lo.")

    def on_closing(self):
        try:
            self.conn.close()
        except Exception as e:
            logging.error("Erro ao fechar a conexão com o banco de dados: %s", e)
        self.root.destroy()

    def manage_users(self):
        from gui.user_management import UserManagementWindow
        UserManagementWindow(self)

    def open_test_scanning(self):
        """
        Abre uma janela de teste para simular a contagem de pacotes.
        Antes usávamos from gui.main_app import PackageCounterApp, o que é desnecessário.
        Podemos instanciar diretamente a classe aqui, pois já está definida.
        """
        test_window = Toplevel(self.root)
        test_window.transient(self.root)
        test_window.grab_set()
        test_window.title("Contador de Pacotes - Ponto 3D - Teste")

        # Definir o tamanho da janela para 1920x1080 ou a resolução disponível
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        desired_width = 1920
        desired_height = 1080

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
            messagebox.showerror("Erro", "Erro ao conectar ao banco de dados de teste. Verifique os logs para mais detalhes.")
            test_window.destroy()
            return

        # Criar uma nova instância da aplicação para o modo de teste
        test_app = PackageCounterApp(
            test_window,
            self.current_user.copy(),
            conn=test_conn,
            title="Contador de Pacotes - Ponto 3D - Teste",
            override_role='user'
        )

        def on_closing_test():
            try:
                test_conn.close()
            except Exception as e:
                logging.error("Erro ao fechar a conexão de teste: %s", e)
            test_window.destroy()

        test_window.protocol("WM_DELETE_WINDOW", on_closing_test)
        center_window(test_window)
