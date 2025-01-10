# Contador de Pacotes - Ponto 3D

Este repositório contém um sistema de contagem de pacotes desenvolvido em Python, projetado para gerenciar fluxos logísticos de transportadoras como SHEIN, Shopee e Mercado Livre. Ele evita pedidos duplicados, possibilita a conferência de quantos pedidos foram embalados e a verificação de pedidos caso algum esteja faltando.

## Índice
- [Descrição Geral](#descrição-geral)
- [Funcionalidades](#funcionalidades)
  - [Registro de Pacotes](#registro-de-pacotes)
  - [Fechamento e Reabertura de Coletas](#fechamento-e-reabertura-de-coletas)
  - [Exportação de Dados](#exportação-de-dados)
  - [Consulta de Coletas Anteriores](#consulta-de-coletas-anteriores)
  - [Verificação de Pedidos](#verificação-de-pedidos)
  - [Gerenciamento de Usuários](#gerenciamento-de-usuários)
- [Arquitetura e Tecnologias](#arquitetura-e-tecnologias)
- [Como Executar](#como-executar)
  - [Pré-requisitos](#pré-requisitos)
  - [Instalação do Ambiente](#instalação-do-ambiente)
  - [Execução da Aplicação](#execução-da-aplicação)
  - [Modo de Teste](#modo-de-teste)
- [Gerando um Executável (.exe)](#gerando-um-executável-exe)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Contribuições](#contribuições)
- [Licença](#licença)

---

## Descrição Geral

O **Contador de Pacotes - Ponto 3D** é uma solução eficiente e modularizada para registro, controle e exportação de pacotes. Ele oferece recursos como autenticação segura, gerenciamento de usuários, exportação de dados em CSV, consulta de histórico de coletas e verificação de pacotes.

## Funcionalidades

### Registro de Pacotes
- Registro por código de barras com validação para evitar duplicidades.
- Identificação automática da transportadora usando regras específicas.

### Fechamento e Reabertura de Coletas
- Marcar pacotes como "collected" e reabri-los para ajustes.

### Exportação de Dados
- Exportar coletas filtradas por data, transportadora e status para CSV.

### Consulta de Coletas Anteriores
- Filtros avançados por data e transportadora com exibição de relatórios detalhados.
- Interface melhorada para maior clareza e usabilidade.

### Verificação de Pedidos
- Verifica informações detalhadas de pacotes registrados, como status, transportadora e data do bip.

### Gerenciamento de Usuários
- Adicionar, editar e remover contas de usuários com controle de permissões.

---

## Arquitetura e Tecnologias

- **Linguagem**: Python 3.11 ou superior.
- **Interface Gráfica**: Tkinter.
- **Banco de Dados**: SQLite.
- **Autenticação**: Senhas criptografadas com bcrypt.
- **Bibliotecas Externas**:
  - `tkcalendar` para seleção de datas.
  - `bcrypt` para hashing de senhas.

O projeto segue um padrão modularizado:
- **gui/**: Interfaces gráficas como login, gerenciamento de usuários, consulta e exportação.
- **database.py**: Inicialização e conexão com o banco de dados.
- **utils.py**: Funções auxiliares como sons e validação de pacotes.

---

## Como Executar

### Pré-requisitos
1. Python 3.11 ou superior instalado.
2. Bibliotecas listadas em `requirements.txt`.

### Instalação do Ambiente

1. Clone este repositório:
   ```bash
   git clone https://github.com/FireIce7/Contador-de-Pacotes-Ecommerce.git
   cd Contador-de-Pacotes-Ecommerce
   ```

2. Crie e ative um ambiente virtual (opcional):
   ```bash
   python -m venv venv
   ```
   Ative o ambiente virtual:

   - **Windows**: `venv\Scripts\activate`

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

### Execução da Aplicação

1. Inicie a aplicação:
   ```bash
   python main.py
   ```

2. Credenciais padrão para o primeiro login:
   - Usuário: admin
   - Senha: admin123

### Modo de Teste
- Use o banco de dados `packagestest.db` para testar funcionalidades sem impactar os dados reais.

---

## Gerando um Executável (.exe)

1. Instale o PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Gere o executável:
   ```bash
   pyinstaller --onefile --windowed --add-data "sounds;sounds" main.py
   ```

O executável estará disponível na pasta `dist/`.

---

## Estrutura do Projeto

A estrutura do projeto está organizada de forma modular, facilitando manutenção e expansão:

```
Contador_Pacotes/
├── data/
│   ├── db/
│   │   ├── packages.db        # Banco de dados principal para armazenar pacotes e status.
│   │   └── packagestest.db    # Banco de dados separado para testes, usado no modo de bipagem de testes.
│   └── logs/
│       └── app.log            # Registro de eventos e erros para depuração.
├── gui/
│   ├── login.py               # Tela de login, com autenticação de usuários usando bcrypt.
│   ├── main_app.py            # Interface principal, incluindo registro de pacotes, exportação e verificação.
│   ├── export.py              # Tela para exportação de coletas filtradas em formato CSV.
│   ├── user_management.py     # Tela para gerenciamento de usuários (adicionar, editar, remover).
│   ├── verify_package.py      # Tela para verificar pedidos registrados com detalhes.
│   └── view_total_packages.py # Tela para consultar coletas anteriores com filtros avançados.
├── sounds/
│   ├── alert.wav              # Som emitido ao bipar um pedido duplicado ou quando há algum erro.
│   └── correct.wav            # Som emitido ao bipar um pedido corretamente. 
├── main.py                    # Ponto de entrada da aplicação.
├── utils.py                   # Funções utilitárias para sons, validação de códigos e centralização de janelas.
├── config.py                  # Configurações globais do projeto, como constantes e diretórios.
├── requirements.txt           # Lista de bibliotecas necessárias para a execução.
├── database.py                # Inicialização e conexão com o banco de dados SQLite.
└── requirements.txt           # Bibliotecas necessárias do programa.
```

---

## Contribuições

Contribuições são bem-vindas! Envie sugestões ou melhorias via **issues** e **pull requests**.

---

## Licença

Este projeto possui restrições para uso comercial. Entre em contato para mais informações.
