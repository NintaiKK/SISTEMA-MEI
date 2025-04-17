import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import messagebox, ttk, filedialog, scrolledtext
import os
from datetime import datetime
import webbrowser
from tkcalendar import DateEntry

# Configuração inicial
ARQUIVO_XML = 'log.xml'
HISTORICO_NFE = 'historico_nfe.xml'
NATUREZA_PADRAO_GERAL = '170201'  # Natureza padrão geral

# Funções para manipulação de XML
def criar_arquivos_base():
    if not os.path.exists(ARQUIVO_XML):
        root = ET.Element('banco_senhas')
        ET.ElementTree(root).write(ARQUIVO_XML, encoding='utf-8', xml_declaration=True)
    
    if not os.path.exists(HISTORICO_NFE):
        root = ET.Element('historico_nfe')
        ET.ElementTree(root).write(HISTORICO_NFE, encoding='utf-8', xml_declaration=True)

def carregar_contas():
    try:
        tree = ET.parse(ARQUIVO_XML)
        return tree.getroot()
    except (ET.ParseError, FileNotFoundError):
        return ET.Element('banco_senhas')

def salvar_contas(root):
    ET.ElementTree(root).write(ARQUIVO_XML, encoding='utf-8', xml_declaration=True)

def obter_natureza_padrao(conta):
    """Obtém a natureza padrão da conta ou retorna a geral se não existir"""
    natop = conta.find('natureza_padrao')
    return natop.text if natop is not None else NATUREZA_PADRAO_GERAL

# Classe principal da aplicação
class Application:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gerenciamento e Emissão NF-e")
        self.root.geometry("1200x800")
        
        criar_arquivos_base()
        
        # Configurar estilo
        self.style = ttk.Style()
        self.style.configure('TNotebook.Tab', font=('Arial', 10, 'bold'))
        self.style.configure('TFrame', background='#f0f0f0')
        
        # Criar abas principais
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Abas
        self.criar_aba_contas()
        self.criar_aba_nfe()
        self.criar_aba_historico()
        self.criar_aba_config()
        
        # Atualizar dados iniciais
        self.atualizar_treeview_contas()
        self.atualizar_combobox_contas()
        self.atualizar_historico()

    def editar_conta(self):
        selected_item = self.tree_contas.selection()
        if not selected_item:
            messagebox.showwarning("Aviso", "Selecione uma conta para editar!")
            return
        
        item = self.tree_contas.item(selected_item[0])
        cnpj = item['values'][1]  # O CNPJ está na segunda coluna
        
        root = carregar_contas()
        conta = None
        for c in root.findall('conta'):
            if c.find('cnpj').text == cnpj:
                conta = c
                break
        
        if not conta:
            messagebox.showerror("Erro", "Conta não encontrada!")
            return
        
        janela = tk.Toplevel(self.root)
        janela.title("Editar Conta")
        janela.geometry("450x400")
        
        # Campos do formulário
        campos = [
            ("Usuário:", ttk.Entry(janela)),
            ("CNPJ:", ttk.Entry(janela)),
            ("Senha:", ttk.Entry(janela, show="*")),
            ("Cidade:", ttk.Entry(janela)),
            ("Natureza Padrão:", ttk.Entry(janela))
        ]
        
        # Preencher com valores atuais
        campos[0][1].insert(0, conta.find('usuario').text if conta.find('usuario') is not None else '')
        campos[1][1].insert(0, conta.find('cnpj').text if conta.find('cnpj') is not None else '')
        campos[1][1].config(state='readonly')  # CNPJ não pode ser alterado
        campos[2][1].insert(0, conta.find('senha').text if conta.find('senha') is not None else '')
        campos[3][1].insert(0, conta.find('cidade').text if conta.find('cidade') is not None else '')
        campos[4][1].insert(0, obter_natureza_padrao(conta))
        
        for i, (label, entry) in enumerate(campos):
            ttk.Label(janela, text=label).grid(row=i, column=0, sticky=tk.W, pady=5, padx=5)
            entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Configurar redimensionamento
        janela.columnconfigure(1, weight=1)
        
        def salvar():
            # Verificar campos obrigatórios
            if not all(entry.get() for label, entry in campos):
                messagebox.showwarning("Aviso", "Todos os campos são obrigatórios!")
                return
            
            # Atualizar os dados da conta
            conta.find('usuario').text = campos[0][1].get()
            # CNPJ não é alterado (já que está como readonly)
            conta.find('senha').text = campos[2][1].get()
            conta.find('cidade').text = campos[3][1].get()
            
            # Atualizar natureza padrão (cria o nó se não existir)
            natop = conta.find('natureza_padrao')
            if natop is None:
                natop = ET.SubElement(conta, 'natureza_padrao')
            natop.text = campos[4][1].get()
            
            salvar_contas(root)
            messagebox.showinfo("Sucesso", "Conta atualizada com sucesso!")
            self.atualizar_treeview_contas()
            self.atualizar_combobox_contas()
            janela.destroy()
        
        ttk.Button(janela, text="Salvar", command=salvar).grid(row=len(campos), column=0, columnspan=2, pady=10)

    def criar_aba_contas(self):
        self.frame_contas = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_contas, text="Gerenciar Contas")
        
        # Treeview para contas
        self.tree_contas = ttk.Treeview(self.frame_contas, columns=('usuario', 'cnpj', 'cidade', 'natop'), show='headings')
        self.tree_contas.heading('usuario', text='Usuário')
        self.tree_contas.heading('cnpj', text='CNPJ')
        self.tree_contas.heading('cidade', text='Cidade')
        self.tree_contas.heading('natop', text='Natureza Padrão')
        self.tree_contas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Barra de rolagem
        scrollbar = ttk.Scrollbar(self.tree_contas, orient=tk.VERTICAL, command=self.tree_contas.yview)
        self.tree_contas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame de botões
        frame_botoes = ttk.Frame(self.frame_contas)
        frame_botoes.pack(fill=tk.X, pady=5)
        
        ttk.Button(frame_botoes, text="Adicionar", command=self.abrir_janela_adicionar).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botoes, text="Editar", command=self.editar_conta).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botoes, text="Atualizar", command=self.atualizar_treeview_contas).pack(side=tk.LEFT, padx=5)

    def criar_aba_nfe(self):
        self.frame_nfe = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_nfe, text="Emissão NF-e")
        
        # Frame de automação
        frame_automacao = ttk.LabelFrame(self.frame_nfe, text="Dados da Nota Fiscal", padding=15)
        frame_automacao.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Formulário de emissão
        ttk.Label(frame_automacao, text="Conta:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.combo_contas = ttk.Combobox(frame_automacao, state='readonly')
        self.combo_contas.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.combo_contas.bind('<<ComboboxSelected>>', self.atualizar_natureza_padrao)
        
        ttk.Label(frame_automacao, text="Valor:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.entry_valor = ttk.Entry(frame_automacao)
        self.entry_valor.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(frame_automacao, text="Data:").grid(row=2, column=0, sticky=tk.W, pady=5)
        frame_data = ttk.Frame(frame_automacao)
        frame_data.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        self.entry_data = DateEntry(frame_data, date_pattern='dd/mm/yyyy')
        self.entry_data.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.var_checkbox_hoje = tk.BooleanVar()
        ttk.Checkbutton(frame_data, text="Hoje", variable=self.var_checkbox_hoje,
                       command=lambda: self.entry_data.set_date(datetime.now())).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(frame_automacao, text="Natureza Operação:").grid(row=3, column=0, sticky=tk.W, pady=5)
        frame_natop = ttk.Frame(frame_automacao)
        frame_natop.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=5)
        self.entry_natop = ttk.Entry(frame_natop)
        self.entry_natop.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.var_checkbox_natpadrao = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame_natop, text="Usar padrão", variable=self.var_checkbox_natpadrao,
                       command=self.atualizar_natureza_padrao).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(frame_automacao, text="Descrição Serviço:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.entry_descricao = ttk.Entry(frame_automacao)
        self.entry_descricao.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=5)
        
        ttk.Label(frame_automacao, text="Observações:").grid(row=5, column=0, sticky=tk.NW, pady=5)
        self.text_observacoes = scrolledtext.ScrolledText(frame_automacao, height=4, wrap=tk.WORD)
        self.text_observacoes.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=5)
        
        # Botões
        frame_botoes = ttk.Frame(frame_automacao)
        frame_botoes.grid(row=6, column=0, columnspan=2, pady=15)
        ttk.Button(frame_botoes, text="Emitir NF-e", command=self.emitir_nfe).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame_botoes, text="Limpar Campos", command=self.limpar_campos_nfe).pack(side=tk.LEFT, padx=5)
        
        # Configurar redimensionamento
        frame_automacao.columnconfigure(1, weight=1)

    def criar_aba_config(self):
        self.frame_config = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_config, text="Configurações")
        
        ttk.Label(self.frame_config, text="Configurações do Sistema", font=('Arial', 12, 'bold')).pack(pady=10)
        
        frame_configs = ttk.Frame(self.frame_config)
        frame_configs.pack(pady=20)
        
        # Configuração de tema
        ttk.Label(frame_configs, text="Tema:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.combo_tema = ttk.Combobox(frame_configs, values=['clam', 'alt', 'default', 'classic'])
        self.combo_tema.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.combo_tema.set('clam')
        self.combo_tema.bind('<<ComboboxSelected>>', self.mudar_tema)
        
        # Botão sobre
        ttk.Button(self.frame_config, text="Sobre", command=self.mostrar_sobre).pack(pady=20)

    def mudar_tema(self, event=None):
        """Altera o tema visual da aplicação"""
        tema_selecionado = self.combo_tema.get()
        self.style.theme_use(tema_selecionado)
    
    def mostrar_sobre(self):
        messagebox.showinfo("Sobre", 
                          "Sistema de Gerenciamento e Emissão NF-e\n\n"
                          "Versão 1.0\n"
                          "Desenvolvido para controle de contas e automação fiscal")

    # Métodos para funcionalidades

    def criar_aba_historico(self):
        self.frame_historico = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_historico, text="Histórico NF-e")
        
        # Treeview para histórico
        self.tree_historico = ttk.Treeview(self.frame_historico, 
                                         columns=('data', 'conta', 'valor', 'natop', 'descricao'),
                                         show='headings')
        self.tree_historico.heading('data', text='Data')
        self.tree_historico.heading('conta', text='Conta')
        self.tree_historico.heading('valor', text='Valor')
        self.tree_historico.heading('natop', text='Natureza')
        self.tree_historico.heading('descricao', text='Descrição')
        self.tree_historico.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Barra de rolagem
        scrollbar = ttk.Scrollbar(self.tree_historico, orient=tk.VERTICAL, command=self.tree_historico.yview)
        self.tree_historico.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def atualizar_treeview_contas(self):
        for item in self.tree_contas.get_children():
            self.tree_contas.delete(item)
        
        root = carregar_contas()
        for conta in root.findall('conta'):
            usuario = conta.find('usuario').text if conta.find('usuario') is not None else ''
            cnpj = conta.find('cnpj').text if conta.find('cnpj') is not None else ''
            cidade = conta.find('cidade').text if conta.find('cidade') is not None else ''
            natop = obter_natureza_padrao(conta)
            
            self.tree_contas.insert('', tk.END, values=(usuario, cnpj, cidade, natop))

    def atualizar_combobox_contas(self):
        root = carregar_contas()
        contas = []
        
        for conta in root.findall('conta'):
            usuario = conta.find('usuario').text if conta.find('usuario') is not None else ''
            cnpj = conta.find('cnpj').text if conta.find('cnpj') is not None else ''
            contas.append(f"{usuario} - {cnpj}")
        
        self.combo_contas['values'] = contas
        if contas:
            self.combo_contas.current(0)

    def atualizar_natureza_padrao(self, event=None):
        """Atualiza o campo de natureza com o valor padrão da conta selecionada"""
        if self.var_checkbox_natpadrao.get():
            conta_selecionada = self.combo_contas.get()
            if conta_selecionada:
                cnpj = conta_selecionada.split(' - ')[-1]
                root = carregar_contas()
                for conta in root.findall('conta'):
                    if conta.find('cnpj').text == cnpj:
                        self.entry_natop.delete(0, tk.END)
                        self.entry_natop.insert(0, obter_natureza_padrao(conta))
                        break

    def abrir_janela_adicionar(self):
        janela = tk.Toplevel(self.root)
        janela.title("Adicionar Nova Conta")
        janela.geometry("450x400")
        
        # Campos do formulário
        campos = [
            ("Usuário:", ttk.Entry(janela)),
            ("CNPJ:", ttk.Entry(janela)),
            ("Senha:", ttk.Entry(janela, show="*")),
            ("Cidade:", ttk.Entry(janela)),
            ("Natureza Padrão:", ttk.Entry(janela))
        ]
        
        for i, (label, entry) in enumerate(campos):
            ttk.Label(janela, text=label).grid(row=i, column=0, sticky=tk.W, pady=5, padx=5)
            entry.grid(row=i, column=1, sticky=tk.EW, padx=5, pady=5)
            if label == "Natureza Padrão:":
                entry.insert(0, NATUREZA_PADRAO_GERAL)
        
        # Configurar redimensionamento
        janela.columnconfigure(1, weight=1)
        
        def salvar():
            valores = [entry.get() for label, entry in campos]
            if not all(valores):
                messagebox.showwarning("Aviso", "Todos os campos são obrigatórios!")
                return
            
            root = carregar_contas()
            
            # Verifica se CNPJ já existe
            for conta in root.findall('conta'):
                if conta.find('cnpj').text == valores[1]:
                    messagebox.showwarning("Aviso", "CNPJ já cadastrado!")
                    return
            
            # Adiciona nova conta
            nova_conta = ET.SubElement(root, 'conta')
            ET.SubElement(nova_conta, 'usuario').text = valores[0]
            ET.SubElement(nova_conta, 'cnpj').text = valores[1]
            ET.SubElement(nova_conta, 'senha').text = valores[2]
            ET.SubElement(nova_conta, 'cidade').text = valores[3]
            ET.SubElement(nova_conta, 'natureza_padrao').text = valores[4]
            
            salvar_contas(root)
            messagebox.showinfo("Sucesso", "Conta adicionada com sucesso!")
            self.atualizar_treeview_contas()
            self.atualizar_combobox_contas()
            janela.destroy()
        
        ttk.Button(janela, text="Salvar", command=salvar).grid(row=len(campos), column=0, columnspan=2, pady=10)

    def emitir_nfe(self):
        conta_selecionada = self.combo_contas.get()
        valor = self.entry_valor.get()
        data = self.entry_data.get()
        natop = self.entry_natop.get()
        descricao = self.entry_descricao.get()
        observacoes = self.text_observacoes.get("1.0", tk.END).strip()
        
        if not all([conta_selecionada, valor, data, natop, descricao]):
            messagebox.showwarning("Aviso", "Preencha todos os campos obrigatórios!")
            return
        
        # Simulação de emissão
        dados_nfe = {
            'data': data,
            'conta': conta_selecionada,
            'valor': valor,
            'natop': natop,
            'descricao': descricao,
            'observacoes': observacoes,
            'status': 'EMITIDA'
        }
        
        # Adiciona ao histórico (simulado)
        try:
            tree = ET.parse(HISTORICO_NFE)
            root = tree.getroot()
        except (ET.ParseError, FileNotFoundError):
            root = ET.Element('historico_nfe')
        
        nfe = ET.SubElement(root, 'nfe')
        for chave, valor in dados_nfe.items():
            ET.SubElement(nfe, chave).text = str(valor)
        
        ET.ElementTree(root).write(HISTORICO_NFE, encoding='utf-8', xml_declaration=True)
        
        messagebox.showinfo("Sucesso", "NF-e emitida com sucesso!")
        self.limpar_campos_nfe()
        self.atualizar_historico()

    def limpar_campos_nfe(self):
        self.entry_valor.delete(0, tk.END)
        self.entry_descricao.delete(0, tk.END)
        self.text_observacoes.delete("1.0", tk.END)
        self.var_checkbox_hoje.set(False)
        self.entry_data.set_date(datetime.now())
        self.atualizar_natureza_padrao()

    def atualizar_historico(self):
        for item in self.tree_historico.get_children():
            self.tree_historico.delete(item)
        
        try:
            tree = ET.parse(HISTORICO_NFE)
            root = tree.getroot()
            
            for nfe in root.findall('nfe'):
                data = nfe.find('data').text if nfe.find('data') is not None else ''
                conta = nfe.find('conta').text if nfe.find('conta') is not None else ''
                valor = nfe.find('valor').text if nfe.find('valor') is not None else ''
                natop = nfe.find('natop').text if nfe.find('natop') is not None else ''
                descricao = nfe.find('descricao').text if nfe.find('descricao') is not None else ''
                
                self.tree_historico.insert('', tk.END, values=(data, conta, valor, natop, descricao))
        
        except (ET.ParseError, FileNotFoundError):
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = Application(root)
    root.mainloop()
