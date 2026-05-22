# ☁ Nuvem de Palavras

Aplicação para geração de **nuvem de palavras** e **resumo automático** de documentos PDF, DOCX e TXT.

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

```bash
python wordcloud.py
```

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

## 📄 Licença

MIT License — sinta-se livre para usar, modificar e distribuir.

\---
