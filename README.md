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

---

## 🚀 Como usar

```bash
python wordcloud.py
```

## 📄 Licença

MIT License — sinta-se livre para usar, modificar e distribuir.
