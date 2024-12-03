# Contador de Pacotes - Ponto 3D

Este repositório contém o código-fonte de uma aplicação em Python para gerenciamento e controle de pacotes de diferentes transportadoras, desenvolvida para auxiliar no processo logístico da empresa Ponto 3D.

## Índice

- [Descrição Geral](#descrição-geral)
- [Funcionalidades](#funcionalidades)
- [Como Executar](#como-executar)
  - [Pré-requisitos](#pré-requisitos)
  - [Instalação](#instalação)
  - [Execução](#execução)
- [Gerando o Executável (.exe)](#gerando-o-executável-exe)
  - [Passos para Gerar o Executável](#passos-para-gerar-o-executável)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Contribuição](#contribuição)
- [Licença](#licença)

---

## Descrição Geral

O **Contador de Pacotes - Ponto 3D** é uma aplicação que permite:

- Registrar pacotes escaneando códigos de barras.
- Selecionar transportadoras.
- Fechar e reabrir coletas.
- Exportar listas de pacotes.
- Consultar coletas anteriores.

A interface gráfica é desenvolvida com **Tkinter**, e o armazenamento é feito em um banco de dados **SQLite**.

---

## Funcionalidades

### Registro de Pacotes

- Seleção de transportadora (SHEIN, Shopee, Mercado Livre).
- Registro de pacotes através do escaneamento do código de barras.
- Evita duplicidade de pacotes registrados no mesmo dia para a mesma transportadora.

### Fechamento e Reabertura de Coletas

- **Fechar Coleta**: Marca todos os pacotes pendentes como 'coletados' para a transportadora selecionada.
- **Reabrir Coleta**: Reabre a última coleta fechada para adicionar ou remover pacotes.

### Exportação de Dados

- Exporta listas de pacotes para arquivos **CSV**.
- Filtros por:
  - Data inicial e final.
  - Transportadora.
  - Status (pendente ou coletado).

### Consulta de Coletas Anteriores

- Visualiza o histórico de coletas por data e transportadora.
- Exibe detalhes dos pacotes em cada coleta.

---

## Como Executar

### Pré-requisitos

- **Python 3.11** ou superior.
- Bibliotecas Python:
  - `tkinter`
  - `tkcalendar`

### Instalação

1. Clone o repositório:
   ```bash
   git clone https://github.com/seu-usuario/seu-repositorio.git


Navegue até o diretório do projeto:

```bash
cd seu-repositorio
```

Crie um ambiente virtual (opcional, mas recomendado):

```bash
python -m venv venv
```

Ative o ambiente virtual:

No Windows:
```bash
venv\Scripts\activate
```

No Linux/macOS:
```bash
source venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Caso o arquivo `requirements.txt` não exista, instale manualmente:

```bash
pip install tkcalendar
```

### Execução

Execute a aplicação com o seguinte comando:

```bash
python contador.py
```

---

## Gerando o Executável (.exe)

### Passos para Gerar o Executável

Certifique-se de que o PyInstaller está instalado:

```bash
pip install pyinstaller
```

Crie o arquivo `packages.db` (se ainda não existir):

Execute o script uma vez para que o banco de dados seja criado automaticamente:

```bash
python contador.py
```

Gere o executável:

```bash
pyinstaller --onefile --windowed --add-data "packages.db;." --hidden-import "tkcalendar" contador.py
```

**Explicação dos parâmetros**:

- `--onefile`: Cria um único arquivo executável.
- `--windowed`: Oculta o terminal ao executar o executável.
- `--add-data "packages.db;."`: Inclui o arquivo `packages.db` no executável.
- `--hidden-import "tkcalendar"`: Inclui a biblioteca `tkcalendar`.

Localize o executável:

Após a execução do comando, o executável estará disponível na pasta `dist`:

```
dist/
  contador.exe
```

Execute o programa:

Basta executar o arquivo `contador.exe` para iniciar a aplicação sem instalar o Python ou dependências.

---

## Estrutura do Projeto

```
contador_de_pacotes/
├── contador.py          # Arquivo principal da aplicação
├── packages.db          # Banco de dados SQLite (criado automaticamente)
├── README.md            # Este arquivo
└── requirements.txt     # Lista de dependências (opcional)
```

---

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir **issues** e **pull requests**.
