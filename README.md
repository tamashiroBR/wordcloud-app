# ☁ Nuvem de Palavras

Aplicação para geração de **nuvem de palavras** e **resumo automático** de documentos PDF, DOCX e TXT — disponível em três versões: desktop com ttkbootstrap (BERT ou LangChain) e web com Streamlit.

\---

## 📋 Funcionalidades

|Funcionalidade|Bootstrap + BERT|Bootstrap + LangChain|Streamlit|
|-|:-:|:-:|:-:|
|Leitura de PDF, DOCX, TXT|✅|✅|✅|
|Nuvem de palavras circular/quadrada|✅|✅|✅|
|16 paletas de cores|✅|✅|✅|
|Fundo transparente|✅|✅|✅|
|Salvar imagem PNG|✅|✅|✅ (download)|
|Resumo automático|BERT + MMR|LangChain map\_reduce|BERT + MMR|
|LLM local (Ollama)|❌|✅|❌|
|LLM nuvem (OpenAI)|❌|✅|❌|
|Salvar resumo TXT|✅|✅|✅ (download)|

\---

## 🗂 Estrutura do projeto

```
wordcloud-app/
├── wordcloud\_app\_bootstrap.py   # Desktop — ttkbootstrap + BERT + MMR
├── wordcloud\_langchain.py       # Desktop — ttkbootstrap + LangChain
├── streamlit\_app.py             # Web     — Streamlit + BERT + MMR
├── requirements.txt             # Dependências Python
├── .gitignore
└── README.md
```

\---

## ⚙️ Instalação

### 1\. Clone o repositório

```bash
git clone https://github.com/tamashiroBR/wordcloud-app.git
cd wordcloud-app
```

### 2\. Crie um ambiente virtual (recomendado)

```bash
python -m venv .venv

# Windows
.venv\\Scripts\\activate

# Linux / macOS
source .venv/bin/activate
```

### 3\. Instale as dependências

```bash
pip install -r requirements.txt
```

> \*\*Nota:\*\* O modelo BERT (`neuralmind/bert-base-portuguese-cased`, \~440 MB) é baixado automaticamente do HuggingFace na primeira execução do resumo.

\---

## 🚀 Como usar

### Versão Desktop — BERT

```bash
python wordcloud\_app.py
```

### Versão Desktop — LangChain

```bash
python wordcloud\_langchain.py
```

Para usar com **Ollama** (LLM local, gratuito):

```bash
# 1. Instale o Ollama: https://ollama.com
# 2. Baixe um modelo
ollama pull llama3

# 3. Inicie o servidor (em outro terminal)
ollama serve

# 4. Execute o app e selecione Ollama na sidebar
python wordcloud\_langchain.py
```

Para usar com **OpenAI**, crie um arquivo `.env` na raiz do projeto:

```env
OPENAI\_API\_KEY=sk-...
```

### Versão Web — Streamlit

```bash
streamlit run streamlit\_app.py
```

Acesse em `http://localhost:8501`

\---

## 🧠 Algoritmos de resumo

### BERT + MMR (`wordcloud\_app\_bootstrap.py` e `streamlit\_app.py`)

Pipeline 100% local sem API externa:

1. **Encoding BERT** — cada frase é transformada em um vetor de 768 dimensões capturando significado semântico real (modelo PT-BR: `neuralmind/bert-base-portuguese-cased`)
2. **Similaridade cosseno** — matriz de similaridade entre todas as frases
3. **MMR (Maximal Marginal Relevance)** — seleciona frases que maximizam relevância e minimizam redundância

O slider **Relevância MMR** controla o balanço:

* `0.3` → máxima diversidade de tópicos
* `1.0` → ranking puro por relevância

### LangChain map\_reduce (`wordcloud\_langchain.py`)

Pipeline com LLM configurável:

1. **Split** — texto dividido em chunks com `RecursiveCharacterTextSplitter`
2. **Map** — cada chunk resumido individualmente pelo LLM com prompt em PT-BR
3. **Reduce** — resumos parciais combinados em um resumo final coeso

Suporta **Ollama** (local, gratuito) e **OpenAI** (nuvem).

\---

## 📦 Dependências principais

|Pacote|Uso|
|-|-|
|`wordcloud`|Geração da nuvem de palavras|
|`matplotlib`|Renderização da imagem|
|`Pillow`|Composição e exibição da imagem|
|`PyPDF2`|Extração de texto de PDFs|
|`python-docx`|Extração de texto de arquivos Word|
|`nltk`|Stopwords em português|
|`ttkbootstrap`|Interface desktop com tema moderno|
|`sentence-transformers`|Modelo BERT para resumo semântico|
|`langchain` + `langchain-community`|Pipeline de sumarização com LLM|
|`streamlit`|Interface web|

\---

## 🖼 Screenshots

### Desktop — ttkbootstrap

> Interface com sidebar de controles, aba de nuvem e aba de resumo.

### Web — Streamlit

> Interface responsiva com upload, métricas e abas de resultado.

\---

## 📄 Licença

MIT License — sinta-se livre para usar, modificar e distribuir.

\---

## 👤 Autor

**tamashiroBR** · [github.com/tamashiroBR](https://github.com/tamashiroBR)

