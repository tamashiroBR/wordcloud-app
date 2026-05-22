"""
Nuvem de Palavras — Desktop (ttkbootstrap · tema flatly / visual clean)
  • Upload de PDF, DOCX e TXT
  • Paleta de cores, fundo, formato circular/quadrado
  • Resumo BERT + MMR (sentence-transformers) — 100 % local
  • Salvar imagem e resumo
"""

import io
import os
import re
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.widgets.scrolled import ScrolledText

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageTk

from wordcloud import WordCloud, STOPWORDS
import PyPDF2
import docx
import nltk
from nltk.corpus import stopwords

# ── NLTK ──────────────────────────────────────────────────────────────────────
for _pkg in ("stopwords",):
    try:
        nltk.data.find(f"corpora/{_pkg}")
    except LookupError:
        nltk.download(_pkg, quiet=True)

# ── Constantes ────────────────────────────────────────────────────────────────
COLORMAPS = [
    "viridis","plasma","magma","inferno","cividis",
    "cool","hot","spring","summer","autumn","winter",
    "Blues","Greens","Purples","Oranges","RdYlGn",
]
BG_COLORS  = ["white","black","transparente","#f0f4f8","#1a1a2e"]
BERT_PRIMARY  = "neuralmind/bert-base-portuguese-cased"
BERT_FALLBACK = "paraphrase-multilingual-MiniLM-L12-v2"
EXTRA_SW = {
    "http","https","dado","ser","ter","ir","sobre","pode","cada",
    "outros","sendo","neste","então","além","ainda","assim","também",
    "mais","para",
}

# ── Cache do modelo ────────────────────────────────────────────────────────────
_BERT_MODEL      = None
_BERT_MODEL_NAME = ""


# ══════════════════════════════════════════════════════════════════════════════
#  BERT + MMR
# ══════════════════════════════════════════════════════════════════════════════
def _get_model(status_cb=None):
    global _BERT_MODEL, _BERT_MODEL_NAME
    if _BERT_MODEL:
        return _BERT_MODEL
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise RuntimeError(
            "Instale: pip install sentence-transformers")
    for name in (BERT_PRIMARY, BERT_FALLBACK):
        try:
            if status_cb:
                status_cb(f"Baixando modelo BERT…\n{name}")
            _BERT_MODEL = SentenceTransformer(name)
            _BERT_MODEL_NAME = name
            return _BERT_MODEL
        except Exception:
            continue
    raise RuntimeError("Não foi possível carregar modelo BERT.")


def _split_sentences(text):
    text = re.sub(r"\s+", " ", text).strip()
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text)
            if len(s.split()) >= 5]


def _cosine_matrix(emb):
    n = np.linalg.norm(emb, axis=1, keepdims=True)
    n = np.where(n == 0, 1e-9, n)
    e = emb / n
    return e @ e.T


def _mmr(sentences, embeddings, n, lmb=0.65):
    sim      = _cosine_matrix(embeddings)
    relevance = sim.mean(axis=1)
    selected  = []
    remaining = list(range(len(sentences)))
    for _ in range(min(n, len(sentences))):
        if not selected:
            best = int(np.argmax(relevance))
        else:
            sel_sim = sim[remaining][:, selected].max(axis=1)
            scores  = lmb * relevance[remaining] - (1 - lmb) * sel_sim
            best    = remaining[int(np.argmax(scores))]
        selected.append(best)
        remaining = [i for i in remaining if i != best]
    return [sentences[i] for i in sorted(selected)]


def bert_summarize(text, n=5, lmb=0.65, status_cb=None):
    sents = _split_sentences(text)
    if not sents:
        return ["Texto insuficiente."], ""
    if len(sents) <= n:
        return sents, ""
    model = _get_model(status_cb)
    if status_cb:
        status_cb(f"Encoding BERT ({len(sents)} frases)…")
    emb = model.encode(sents, batch_size=32,
                       show_progress_bar=False, convert_to_numpy=True)
    if status_cb:
        status_cb("Seleção MMR…")
    return _mmr(sents, emb, n, lmb), _BERT_MODEL_NAME


# ══════════════════════════════════════════════════════════════════════════════
#  APP
# ══════════════════════════════════════════════════════════════════════════════
class App(ttk.Window):

    def __init__(self):
        super().__init__(themename="litera")   # tema claro e clean
        self.title("Nuvem de Palavras")
        self.geometry("1280x760")
        self.minsize(1000, 620)
        self.resizable(True, True)

        # state
        self._text          = ""
        self._img_bytes     = None
        self._tk_image      = None
        self._canvas_img_id = None
        self._ph_id         = None

        # vars
        self._v_file     = tk.StringVar(value="Nenhum arquivo")
        self._v_words    = tk.StringVar(value="—")
        self._v_chars    = tk.StringVar(value="—")
        self._v_cmap     = tk.StringVar(value="viridis")
        self._v_bg       = tk.StringVar(value="white")
        self._v_shape    = tk.StringVar(value="Circular")
        self._v_maxw     = tk.IntVar(value=30)
        self._v_minl     = tk.IntVar(value=4)
        self._v_nsent    = tk.IntVar(value=5)
        self._v_lmb      = tk.DoubleVar(value=0.65)
        self._v_status   = tk.StringVar(value="Pronto.")
        self._v_model    = tk.StringVar(value="")
        self._v_suminfo  = tk.StringVar(value="")

        self._build()

    # ── build ─────────────────────────────────────────────────────────────────
    def _build(self):
        # ── topbar ──
        bar = ttk.Frame(self, bootstyle="primary", padding=(20, 10))
        bar.pack(fill=X)
        ttk.Label(bar, text="☁  Nuvem de Palavras",
                  font=("Segoe UI", 15, "bold"),
                  bootstyle="inverse-primary").pack(side=LEFT)
        ttk.Label(bar, text="PDF · DOCX · TXT",
                  font=("Segoe UI", 9),
                  bootstyle="inverse-primary").pack(side=RIGHT)

        # ── body ──
        body = ttk.Frame(self)
        body.pack(fill=BOTH, expand=True)

        # sidebar
        self._sidebar = ttk.Frame(body, width=290, padding=(0, 0))
        self._sidebar.pack(side=LEFT, fill=Y)
        self._sidebar.pack_propagate(False)
        self._build_sidebar(self._sidebar)

        # separator
        ttk.Separator(body, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=0)

        # main
        main = ttk.Frame(body, padding=(18, 14))
        main.pack(side=LEFT, fill=BOTH, expand=True)
        self._build_main(main)

    # ── sidebar ───────────────────────────────────────────────────────────────
    def _build_sidebar(self, p):
        # scrollable interior
        canvas = tk.Canvas(p, highlightthickness=0, bd=0)
        vsb    = ttk.Scrollbar(p, orient=VERTICAL, command=canvas.yview,
                               bootstyle="round-light")
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=RIGHT, fill=Y)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)

        inner = ttk.Frame(canvas, padding=(18, 12))
        win   = canvas.create_window((0, 0), window=inner, anchor=NW)

        def _on_frame(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(win, width=e.width)

        inner.bind("<Configure>", _on_frame)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))

        # mousewheel
        def _scroll(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _scroll)

        f = inner   # alias curto

        def sec(txt):
            ttk.Separator(f).pack(fill=X, pady=(14, 6))
            tk.Label(f, text=txt.upper(),
                     font=("Segoe UI", 7, "bold"),
                     fg="#1a252f").pack(anchor=W)

        # ── Arquivo ──
        tk.Label(f, text="ARQUIVO", font=("Segoe UI", 7, "bold"),
                  fg="#1a252f").pack(anchor=W, pady=(4, 4))

        file_card = ttk.Frame(f, bootstyle="light", padding=(10, 6))
        file_card.pack(fill=X, pady=(0, 8))
        tk.Label(file_card, textvariable=self._v_file,
                  font=("Segoe UI", 8), fg="#2c3e50",
                  wraplength=220).pack(anchor=W)

        ttk.Button(f, text="📂  Abrir Arquivo",
                   command=self._open_file,
                   bootstyle="primary-outline",
                   width=28).pack(fill=X, pady=(0, 4))

        # ── Aparência ──
        sec("🎨  Aparência")
        self._mk_label(f, "Paleta de Cores")
        ttk.Combobox(f, textvariable=self._v_cmap,
                     values=COLORMAPS, state="readonly",
                     font=("Segoe UI", 9)).pack(fill=X, pady=(2, 8))

        self._mk_label(f, "Cor de Fundo")
        ttk.Combobox(f, textvariable=self._v_bg,
                     values=BG_COLORS, state="readonly",
                     font=("Segoe UI", 9)).pack(fill=X, pady=(2, 8))

        self._mk_label(f, "Formato")
        ttk.Combobox(f, textvariable=self._v_shape,
                     values=["Circular", "Quadrado"], state="readonly",
                     font=("Segoe UI", 9)).pack(fill=X, pady=(2, 8))

        # ── Nuvem ──
        sec("⚙️  Nuvem")
        self._mk_slider(f, "Máx. palavras", self._v_maxw, 5, 150)
        self._mk_slider(f, "Mín. letras",   self._v_minl, 2,  10)

        # ── Resumo BERT ──
        sec("🧠  Resumo BERT")
        self._mk_slider(f, "Frases",       self._v_nsent, 3, 20)
        self._mk_slider_float(f, "Relevância MMR",
                              self._v_lmb, 0.3, 1.0)
        tk.Label(f, text="0.3 = diverso  ·  1.0 = relevante",
                 font=("Segoe UI", 7), fg="#5d6d7e").pack(anchor=E)

        ttk.Separator(f).pack(fill=X, pady=14)

        # ── Botões ──
        btns = [
            ("✨  Gerar Nuvem",   self._gen_cloud,   "primary"),
            ("🧠  Gerar Resumo",  self._gen_summary,  "info"),
            ("💾  Salvar Imagem", self._save_image,   "success"),
            ("📋  Salvar Resumo", self._save_summary, "success-outline"),
        ]
        for label, cmd, style in btns:
            ttk.Button(f, text=label, command=cmd,
                       bootstyle=style, width=28).pack(fill=X, pady=3)

        ttk.Separator(f).pack(fill=X, pady=10)

        # ── Progresso ──
        self._pb = ttk.Progressbar(f, mode="indeterminate",
                                   bootstyle="info-striped", length=230)
        tk.Label(f, textvariable=self._v_status,
                 font=("Segoe UI", 8), fg="#34495e",
                 wraplength=238, justify=LEFT).pack(anchor=W, pady=(4, 0))

    # ── main ──────────────────────────────────────────────────────────────────
    def _build_main(self, p):
        # ── métricas ──
        mf = ttk.Frame(p)
        mf.pack(fill=X, pady=(0, 14))
        for col in range(3):
            mf.columnconfigure(col, weight=1)

        metrics = [
            ("📄  Arquivo",    self._v_file,  "primary"),
            ("📝  Palavras",   self._v_words, "info"),
            ("🔤  Caracteres", self._v_chars, "success"),
        ]
        for col, (lbl, var, style) in enumerate(metrics):
            card = ttk.Frame(mf, bootstyle="light",
                             padding=(14, 10))
            card.grid(row=0, column=col, sticky=EW,
                      padx=(0 if col == 0 else 10, 0))
            tk.Label(card, text=lbl,
                     font=("Segoe UI", 8, "bold"),
                     fg="#2c3e50").pack(anchor=W)
            ttk.Label(card, textvariable=var,
                      font=("Segoe UI", 13, "bold"),
                      bootstyle=style).pack(anchor=W)

        # ── notebook ──
        nb = ttk.Notebook(p, bootstyle="light")
        nb.pack(fill=BOTH, expand=True)
        self._nb = nb

        # aba nuvem
        tab1 = ttk.Frame(nb, padding=2)
        nb.add(tab1, text="  ☁  Nuvem de Palavras  ")
        self._build_cloud_tab(tab1)

        # aba resumo
        tab2 = ttk.Frame(nb, padding=2)
        nb.add(tab2, text="  🧠  Resumo BERT  ")
        self._build_summary_tab(tab2)

    def _build_cloud_tab(self, parent):
        border = ttk.Frame(parent, bootstyle="light", padding=2)
        border.pack(fill=BOTH, expand=True)
        self._canvas = tk.Canvas(border, bg="#eef0f2",
                                 highlightthickness=0)
        self._canvas.pack(fill=BOTH, expand=True)
        self._ph_id = self._canvas.create_text(
            0, 0,
            text="☁\n\nAbra um arquivo e clique em\n✨ Gerar Nuvem",
            font=("Segoe UI", 13), fill="#7f8c8d", justify=CENTER,
        )
        self._canvas.bind("<Configure>", self._on_resize)

    def _build_summary_tab(self, parent):
        # header
        hdr = ttk.Frame(parent, bootstyle="light", padding=(12, 6))
        hdr.pack(fill=X)
        tk.Label(hdr, text="Sumarização Extrativa — BERT + MMR",
                  font=("Segoe UI", 9, "bold"),
                  fg="#1a252f").pack(side=LEFT)
        ttk.Label(hdr, textvariable=self._v_model,
                  font=("Segoe UI", 8),
                  bootstyle="warning").pack(side=LEFT, padx=10)
        ttk.Label(hdr, textvariable=self._v_suminfo,
                  font=("Segoe UI", 8, "bold"),
                  bootstyle="success").pack(side=RIGHT)

        ttk.Separator(parent).pack(fill=X)

        # área de texto
        self._sum_text = ScrolledText(
            parent,
            padding=3,
            height=20,
            font=("Segoe UI", 11),
            autohide=True,
            bootstyle="round",
        )
        self._sum_text.pack(fill=BOTH, expand=True, padx=8, pady=8)
        self._sum_text.text.config(
            bg="#ffffff",
            fg="#212529",
            relief="flat",
            bd=0,
            wrap=WORD,
            padx=14,
            pady=12,
            spacing3=8,
            state="disabled",
        )
        self._sum_text.text.tag_configure(
            "num", foreground="#0d6efd", font=("Segoe UI", 11, "bold"))
        self._sum_text.text.tag_configure(
            "sentence", foreground="#212529", font=("Segoe UI", 11))
        self._sum_text.text.tag_configure(
            "note", foreground="#adb5bd", font=("Segoe UI", 8),
            justify="right")
        self._sum_text.text.tag_configure(
            "ph", foreground="#6c7a89", font=("Segoe UI", 12),
            justify="center")
        self._set_sum_placeholder()

    # ── helpers ───────────────────────────────────────────────────────────────
    def _mk_label(self, parent, text):
        tk.Label(parent, text=text,
                 font=("Segoe UI", 8, "bold"),
                 fg="#2c3e50"
                 ).pack(anchor=W, pady=(6, 0))

    def _mk_slider(self, parent, label, var, from_, to):
        row = ttk.Frame(parent)
        row.pack(fill=X, pady=(4, 0))
        tk.Label(row, text=label,
                 font=("Segoe UI", 8), fg="#2c3e50").pack(side=LEFT)
        ttk.Label(row, textvariable=var,
                  font=("Segoe UI", 8, "bold"),
                  bootstyle="primary", width=4).pack(side=RIGHT)
        ttk.Scale(parent, variable=var, from_=from_, to=to,
                  orient=HORIZONTAL,
                  bootstyle="primary",
                  command=lambda v: var.set(int(float(v)))
                  ).pack(fill=X, pady=(0, 4))

    def _mk_slider_float(self, parent, label, var, from_, to):
        row = ttk.Frame(parent)
        row.pack(fill=X, pady=(4, 0))
        tk.Label(row, text=label,
                 font=("Segoe UI", 8), fg="#2c3e50").pack(side=LEFT)
        lbl = ttk.Label(row, text=f"{var.get():.2f}",
                        font=("Segoe UI", 8, "bold"),
                        bootstyle="primary", width=5)
        lbl.pack(side=RIGHT)

        def _upd(v):
            val = round(float(v) / 0.05) * 0.05
            var.set(round(val, 2))
            lbl.config(text=f"{val:.2f}")

        ttk.Scale(parent, variable=var, from_=from_, to=to,
                  orient=HORIZONTAL, bootstyle="primary",
                  command=_upd).pack(fill=X, pady=(0, 2))

    def _set_sum_placeholder(self):
        t = self._sum_text.text
        t.config(state="normal")
        t.delete("1.0", END)
        t.insert(END,
            "\n\n\n        🧠\n\n"
            "        Abra um arquivo e clique em\n"
            "        🧠 Gerar Resumo.\n\n"
            "        Na primeira execução o modelo BERT\n"
            "        (~400 MB) será baixado automaticamente.",
            "ph")
        t.config(state="disabled")

    def _set_status(self, msg, boost="secondary"):
        self._v_status.set(msg)

    def _progress_start(self):
        self._pb.pack(fill=X, pady=4)
        self._pb.start(10)

    def _progress_stop(self):
        self._pb.stop()
        self._pb.pack_forget()

    # ── arquivo ───────────────────────────────────────────────────────────────
    def _open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Documentos", "*.pdf *.docx *.txt"),
                       ("PDF","*.pdf"),("Word","*.docx"),
                       ("Texto","*.txt"),("Todos","*.*")])
        if not path:
            return
        self._set_status("Lendo arquivo…")
        try:
            text = self._read(path)
        except Exception as e:
            messagebox.showerror("Erro", str(e))
            return
        if not text or not text.strip():
            messagebox.showwarning("Atenção", "Nenhum texto encontrado.")
            return
        self._text = text
        nome = os.path.basename(path)
        self._v_file.set(nome[:32] + ("…" if len(nome) > 32 else ""))
        self._v_words.set(f"{len(text.split()):,}")
        self._v_chars.set(f"{len(text):,}")
        self._v_model.set("")
        self._v_suminfo.set("")
        self._set_sum_placeholder()
        self._set_status(f"✓ {len(text.split()):,} palavras carregadas")

    @staticmethod
    def _read(path):
        with open(path, "rb") as f:
            c = f.read()
        if path.endswith(".pdf"):
            r = PyPDF2.PdfReader(io.BytesIO(c))
            return "".join(p.extract_text() or "" for p in r.pages)
        if path.endswith(".docx"):
            d = docx.Document(io.BytesIO(c))
            return "\n".join(p.text for p in d.paragraphs)
        if path.endswith(".doc"):
            raise ValueError("Use .docx em vez de .doc.")
        return c.decode("utf-8", errors="ignore")

    # ── nuvem ─────────────────────────────────────────────────────────────────
    def _gen_cloud(self):
        if not self._text:
            messagebox.showinfo("Atenção", "Abra um arquivo primeiro.")
            return
        self._progress_start()
        self._set_status("Gerando nuvem…")
        threading.Thread(target=self._do_cloud, daemon=True).start()

    def _do_cloud(self):
        try:
            img = self._make_cloud()
            self.after(0, lambda: self._show_cloud(img))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally:
            self.after(0, self._progress_stop)

    def _make_cloud(self):
        sw  = STOPWORDS | set(stopwords.words("portuguese")) | EXTRA_SW
        bg  = self._v_bg.get()
        trp = bg == "transparente"
        mask = None
        if self._v_shape.get() == "Circular":
            x, y = np.ogrid[:1000, :1000]
            m = (x-500)**2 + (y-500)**2 > 400**2
            mask = (255*m).astype(np.uint8)
        wc = WordCloud(
            width=1000, height=1000,
            background_color=None if trp else bg,
            mode="RGBA" if trp else "RGB",
            stopwords=sw,
            max_words=self._v_maxw.get(),
            min_word_length=self._v_minl.get(),
            mask=mask,
            colormap=self._v_cmap.get(),
            prefer_horizontal=0.8,
            min_font_size=10,
        ).generate(self._text)
        fig, ax = plt.subplots(figsize=(8,8), dpi=120)
        fig.patch.set_alpha(0)
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        ax.set_position([0,0,1,1])
        fig.subplots_adjust(0,0,1,1)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150,
                    bbox_inches="tight", transparent=True, pad_inches=0)
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    def _show_cloud(self, img_bytes):
        self._img_bytes = img_bytes
        self._canvas.delete("all")
        self._ph_id = None
        self._redraw()
        self._nb.select(0)
        self._set_status(f"✓ Nuvem gerada · {len(self._text.split()):,} palavras")

    def _redraw(self):
        if not self._img_bytes:
            return
        cw, ch = self._canvas.winfo_width(), self._canvas.winfo_height()
        if cw < 2 or ch < 2:
            return
        img  = Image.open(io.BytesIO(self._img_bytes)).convert("RGBA")
        bg   = Image.new("RGBA", img.size, (248, 249, 250, 255))
        comp = Image.alpha_composite(bg, img)
        comp.thumbnail((cw, ch), Image.LANCZOS)
        self._tk_image = ImageTk.PhotoImage(comp)
        if self._canvas_img_id:
            self._canvas.delete(self._canvas_img_id)
        self._canvas_img_id = self._canvas.create_image(
            cw//2, ch//2, anchor=CENTER, image=self._tk_image)

    def _on_resize(self, e):
        if self._ph_id:
            self._canvas.coords(self._ph_id, e.width//2, e.height//2)
        if self._img_bytes:
            self._redraw()

    # ── resumo ────────────────────────────────────────────────────────────────
    def _gen_summary(self):
        if not self._text:
            messagebox.showinfo("Atenção", "Abra um arquivo primeiro.")
            return
        self._progress_start()
        n, lmb = self._v_nsent.get(), self._v_lmb.get()
        threading.Thread(
            target=self._do_summary, args=(n, lmb), daemon=True).start()

    def _do_summary(self, n, lmb):
        try:
            def cb(msg):
                self.after(0, lambda m=msg: self._set_status(m))
            frases, model = bert_summarize(self._text, n, lmb, cb)
            self.after(0, lambda: self._show_summary(frases, model))
        except RuntimeError as e:
            self.after(0, lambda: messagebox.showerror(
                "sentence-transformers", str(e)))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally:
            self.after(0, self._progress_stop)

    def _show_summary(self, frases, model):
        t = self._sum_text.text
        t.config(state="normal")
        t.delete("1.0", END)
        for i, s in enumerate(frases, 1):
            t.insert(END, f"  {i:02d}.  ", "num")
            t.insert(END, s.strip() + "\n\n", "sentence")
        if model:
            t.insert(END, f"\n  modelo: {model}\n", "note")
        t.config(state="disabled")
        t.yview_moveto(0)

        total = len(_split_sentences(self._text))
        pct   = round(len(frases)/total*100) if total else 0
        self._v_suminfo.set(f"{len(frases)} frases · {pct}% do doc")
        short = model.split("/")[-1] if model else "—"
        self._v_model.set(f"modelo: {short}")
        self._nb.select(1)
        self._set_status(f"✓ Resumo BERT · {len(frases)} frases")

    # ── salvar ────────────────────────────────────────────────────────────────
    def _save_image(self):
        if not self._img_bytes:
            messagebox.showinfo("Atenção", "Gere a nuvem primeiro.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG","*.png"),("JPG","*.jpg")])
        if path:
            with open(path, "wb") as f:
                f.write(self._img_bytes)
            self._set_status(f"✓ Imagem salva: {os.path.basename(path)}")

    def _save_summary(self):
        t = self._sum_text.text.get("1.0", END).strip()
        if not t or "Abra um arquivo" in t:
            messagebox.showinfo("Atenção", "Gere o resumo primeiro.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Texto","*.txt"),("Markdown","*.md")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(t)
            self._set_status(f"✓ Resumo salvo: {os.path.basename(path)}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
