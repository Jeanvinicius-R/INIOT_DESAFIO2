"""
Análise e visualização de dados IIoT — Desafio 2
Interface gráfica com importação de CSV via botão.
Uso: python analise_iiot.py
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

import pandas as pd
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.patches import FancyBboxPatch, Patch
from datetime import datetime

# ── Paleta ────────────────────────────────────────────────────────────────────
AZUL      = "#0ea5e9"
LARANJA   = "#f97316"
VERDE     = "#22c55e"
ROXO      = "#a855f7"
CINZA_BG  = "#0f172a"
CINZA_PAI = "#1e293b"
CINZA_TX  = "#94a3b8"
BRANCO    = "#f1f5f9"
BORDA     = "#334155"

UI_BG     = "#0f172a"
UI_PAI    = "#1e293b"
UI_BTN    = "#0ea5e9"
UI_BTN_HV = "#38bdf8"
UI_TEXT   = "#f1f5f9"
UI_MUTED  = "#64748b"

plt.rcParams.update({
    "figure.facecolor":  CINZA_BG,
    "axes.facecolor":    CINZA_PAI,
    "axes.edgecolor":    BORDA,
    "axes.labelcolor":   CINZA_TX,
    "text.color":        BRANCO,
    "xtick.color":       CINZA_TX,
    "ytick.color":       CINZA_TX,
    "grid.color":        BORDA,
    "grid.linestyle":    "--",
    "grid.alpha":        0.6,
    "legend.facecolor":  CINZA_PAI,
    "legend.edgecolor":  BORDA,
    "font.family":       "DejaVu Sans",
})


# ── Lógica de dados ───────────────────────────────────────────────────────────
def carregar(caminho: str) -> pd.DataFrame:
    df = pd.read_csv(caminho)
    df.columns = df.columns.str.strip()
    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if "temp" in cl:
            col_map[c] = "temperatura"
        elif "umid" in cl or "humid" in cl:
            col_map[c] = "umidade"
        elif "timestamp" in cl and "iso" in cl:
            col_map[c] = "timestamp"
        elif "data" in cl or "hora" in cl or "datetime" in cl:
            col_map[c] = "datetime_str"
        elif cl == "id":
            col_map[c] = "id"
    df.rename(columns=col_map, inplace=True)

    if "timestamp" in df.columns:
        df["tempo"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
        df["tempo"] = df["tempo"].dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None)
    elif "datetime_str" in df.columns:
        df["tempo"] = pd.to_datetime(df["datetime_str"], dayfirst=True, errors="coerce")
    else:
        df["tempo"] = pd.date_range(start="now", periods=len(df), freq="2s")

    df.sort_values("tempo", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def estatisticas(df: pd.DataFrame) -> dict:
    s = {}
    for col, label in [("temperatura", "temp"), ("umidade", "hum")]:
        if col not in df.columns:
            continue
        serie = df[col].dropna()
        if len(serie) == 0:
            continue
        s[label] = {
            "min":     serie.min(),
            "max":     serie.max(),
            "media":   serie.mean(),
            "mediana": serie.median(),
            "std":     serie.std(ddof=1) if len(serie) > 1 else 0.0,
            "p25":     serie.quantile(0.25),
            "p75":     serie.quantile(0.75),
            "n":       len(serie),
        }
    return s


# ── Helpers de plot ───────────────────────────────────────────────────────────
def _kpi(ax, titulo, valor, unidade, cor, subtitulo=""):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.05, 0.05), 0.90, 0.90,
                                boxstyle="round,pad=0.02",
                                linewidth=1.5, edgecolor=cor,
                                facecolor=CINZA_PAI, zorder=1))
    ax.text(0.5, 0.76, titulo,  ha="center", va="center",
            fontsize=9,  color=CINZA_TX, fontweight="bold", zorder=2)
    ax.text(0.5, 0.44, f"{valor:.2f}", ha="center", va="center",
            fontsize=20, color=cor, fontweight="bold", zorder=2)
    ax.text(0.5, 0.24, unidade, ha="center", va="center",
            fontsize=10, color=cor, alpha=0.85, zorder=2)
    if subtitulo:
        ax.text(0.5, 0.09, subtitulo, ha="center", va="center",
                fontsize=7.5, color=CINZA_TX, zorder=2)


def _serie_sigma(ax, tempo, serie, st, cor, label, unidade):
    mu, sigma = st["media"], st["std"]
    ax.plot(tempo, serie, color=cor, linewidth=1.6, zorder=4, label=label)
    ax.axhspan(mu - 2*sigma, mu + 2*sigma, alpha=0.07, color=VERDE, label="±2σ")
    ax.axhspan(mu -   sigma, mu +   sigma, alpha=0.17, color=VERDE, label="±1σ")
    ax.axhline(mu, color=VERDE, ls="--", lw=1.3, label="Média")
    for m in [-2, -1, 1, 2]:
        ax.axhline(mu + m*sigma,
                   color=CINZA_TX if abs(m) == 1 else ROXO, ls=":", lw=0.8)
        if sigma > 0:
            ax.annotate(f"{'+' if m > 0 else ''}{m}σ",
                        xy=(tempo.max(), mu + m*sigma),
                        xytext=(3, 0), textcoords="offset points",
                        color=CINZA_TX, fontsize=7, va="center")
    ax.set_title(f"{label} — Faixas de Desvio Padrão", color=BRANCO, fontsize=10, pad=6)
    ax.set_ylabel(unidade, color=CINZA_TX)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right", fontsize=7)
    ax.legend(fontsize=7, loc="upper right", ncol=2)
    ax.grid(True, axis="y")


def _rolling_sigma(ax, tempo, serie, sigma_global, janela, cor, label, unidade):
    roll = serie.rolling(window=janela, min_periods=1).std().fillna(0)
    ax.plot(tempo, roll, color=cor, linewidth=1.5,
            label=f"σ móvel (janela={janela})")
    ax.fill_between(tempo, roll, alpha=0.20, color=cor)
    ax.axhline(sigma_global, color=VERDE, ls="--", lw=1.2,
               label=f"σ global = {sigma_global:.4f}")
    ax.set_title(f"Desvio Padrão Móvel — {label}", color=BRANCO, fontsize=10, pad=6)
    ax.set_ylabel(f"σ ({unidade})", color=CINZA_TX)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right", fontsize=7)
    ax.legend(fontsize=8)
    ax.grid(True, axis="y")


# ── Geração da figura ─────────────────────────────────────────────────────────
def gerar_figura(df: pd.DataFrame, stats: dict, nome_arquivo: str) -> plt.Figure:
    tem_temp = "temperatura" in df.columns and "temp" in stats
    tem_hum  = "umidade"     in df.columns and "hum"  in stats

    fig = plt.figure(figsize=(16, 11), facecolor=CINZA_BG)
    fig.suptitle(
        f"Dashboard IIoT — Sensor DHT   |   {os.path.basename(nome_arquivo)}"
        f"   |   {stats.get('temp', stats.get('hum', {})).get('n', len(df))} registros"
        f"   |   {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        color=BRANCO, fontsize=11, fontweight="bold", y=0.985,
    )

    gs = gridspec.GridSpec(4, 4, figure=fig,
                           hspace=0.60, wspace=0.35,
                           top=0.96, bottom=0.06, left=0.06, right=0.97)

    if tem_temp:
        st = stats["temp"]
        cv = (st["std"] / st["media"] * 100) if st["media"] != 0 else 0
        kpis = [
            ("Média Temp",    st["media"], "°C",   AZUL,   f"Mediana {st['mediana']:.1f} °C"),
            ("Mín / Máx",     st["min"],   "°C",   ROXO,   f"Máx: {st['max']:.1f} °C"),
            ("Desvio Padrão", st["std"],   "σ °C", VERDE,  f"IQR: {st['p75']-st['p25']:.2f} °C"),
            ("Coef. Variação",cv,          "% CV", LARANJA,"σ / média × 100"),
        ]
        for i, (tit, val, uni, cor, sub) in enumerate(kpis):
            _kpi(fig.add_subplot(gs[0, i]), tit, val, uni, cor, sub)

    if tem_temp:
        _serie_sigma(fig.add_subplot(gs[1, :2]),
                     df["tempo"], df["temperatura"], stats["temp"], AZUL, "Temperatura", "°C")

    if tem_hum:
        _serie_sigma(fig.add_subplot(gs[1, 2:]),
                     df["tempo"], df["umidade"], stats["hum"], LARANJA, "Umidade", "%")

    janela = max(3, len(df) // 8)
    if tem_temp:
        _rolling_sigma(fig.add_subplot(gs[2, :2]),
                       df["tempo"], df["temperatura"],
                       stats["temp"]["std"], janela, AZUL, "Temperatura", "°C")
    if tem_hum:
        _rolling_sigma(fig.add_subplot(gs[2, 2:]),
                       df["tempo"], df["umidade"],
                       stats["hum"]["std"], janela, LARANJA, "Umidade", "%")

    ax_box = fig.add_subplot(gs[3, :2])
    dados, labels, cores = [], [], []
    if tem_temp:
        dados.append(df["temperatura"].dropna().values)
        labels.append("Temperatura (°C)"); cores.append(AZUL)
    if tem_hum:
        dados.append(df["umidade"].dropna().values)
        labels.append("Umidade (%)"); cores.append(LARANJA)
    if dados:
        bp = ax_box.boxplot(dados, patch_artist=True,
                            medianprops=dict(color=VERDE, linewidth=2),
                            whiskerprops=dict(color=CINZA_TX),
                            capprops=dict(color=CINZA_TX),
                            flierprops=dict(marker="o", color=ROXO, markersize=5))
        for patch, cor in zip(bp["boxes"], cores):
            patch.set_facecolor(cor); patch.set_alpha(0.4)
        ax_box.set_xticklabels(labels, fontsize=9)
    ax_box.set_title("Boxplot — Distribuição / IQR / Outliers",
                     color=BRANCO, fontsize=10, pad=6)
    ax_box.grid(True, axis="y")

    ax_hist = fig.add_subplot(gs[3, 2:])
    if tem_temp:
        bins_t = max(5, len(df["temperatura"].unique()))
        ax_hist.hist(df["temperatura"], bins=bins_t, color=AZUL,
                     alpha=0.65, edgecolor=CINZA_BG)
    if tem_hum:
        ax2 = ax_hist.twiny()
        bins_h = max(5, len(df["umidade"].unique()))
        ax2.hist(df["umidade"], bins=bins_h, color=LARANJA,
                 alpha=0.5, edgecolor=CINZA_BG)
        ax2.tick_params(colors=CINZA_TX, labelsize=7)
    ax_hist.set_ylabel("Frequência", color=CINZA_TX)
    ax_hist.set_title("Histograma de Frequências", color=BRANCO, fontsize=10, pad=6)
    ax_hist.grid(True, axis="y")
    ax_hist.legend(handles=[
        Patch(facecolor=AZUL,    alpha=0.7, label="Temperatura"),
        Patch(facecolor=LARANJA, alpha=0.7, label="Umidade"),
    ], fontsize=8, loc="upper right")

    return fig


# ── Relatório texto ───────────────────────────────────────────────────────────
def relatorio_texto(df: pd.DataFrame, stats: dict) -> str:
    linhas = []
    linhas.append("═" * 54)
    linhas.append("  RELATÓRIO DE ANÁLISE — IIoT Desafio 2")
    linhas.append("═" * 54)
    linhas.append(f"  Total de registros : {len(df)}")
    if "tempo" in df.columns and not df["tempo"].isna().all():
        dur = df["tempo"].max() - df["tempo"].min()
        linhas.append(f"  Duração            : {dur}")
        linhas.append(f"  Início             : {df['tempo'].min().strftime('%d/%m/%Y %H:%M:%S')}")
        linhas.append(f"  Fim                : {df['tempo'].max().strftime('%d/%m/%Y %H:%M:%S')}")

    for chave, label, unidade in [("temp", "TEMPERATURA", "°C"), ("hum", "UMIDADE", "%")]:
        if chave not in stats:
            continue
        s   = stats[chave]
        col = {"temp": "temperatura", "hum": "umidade"}[chave]
        cv  = (s["std"] / s["media"] * 100) if s["media"] != 0 else 0
        iqr = s["p75"] - s["p25"]
        out_low  = int((df[col] < s["p25"] - 1.5*iqr).sum())
        out_high = int((df[col] > s["p75"] + 1.5*iqr).sum())
        linhas += [
            f"\n  ── {label} ({unidade}) ──",
            f"  Mínima            : {s['min']:.2f}",
            f"  Máxima            : {s['max']:.2f}",
            f"  Amplitude         : {s['max']-s['min']:.2f}",
            f"  Média (μ)         : {s['media']:.4f}",
            f"  Mediana           : {s['mediana']:.4f}",
            f"  Desvio Padrão (σ) : {s['std']:.4f}",
            f"  Coef. Variação    : {cv:.2f} %",
            f"  μ − 1σ / μ + 1σ  : {s['media']-s['std']:.4f}  /  {s['media']+s['std']:.4f}",
            f"  μ − 2σ / μ + 2σ  : {s['media']-2*s['std']:.4f}  /  {s['media']+2*s['std']:.4f}",
            f"  Q1 / Q3 / IQR     : {s['p25']:.2f}  /  {s['p75']:.2f}  /  {iqr:.2f}",
            f"  Outliers (1.5×IQR): {out_low+out_high}  (↓{out_low}  ↑{out_high})",
        ]
    linhas.append("\n" + "═" * 54)
    return "\n".join(linhas)


# ── Widget botão customizado ──────────────────────────────────────────────────
class _Botao(tk.Label):
    def __init__(self, parent, texto, comando, bg, hover,
                 state="normal", font_size=9):
        super().__init__(parent, text=texto, bg=bg, fg=BRANCO,
                         font=("DejaVu Sans", font_size, "bold"),
                         cursor="hand2" if state == "normal" else "arrow",
                         padx=14, pady=6, relief="flat")
        self._bg    = bg
        self._hover = hover
        self._cmd   = comando
        self._ativo = (state == "normal")
        if self._ativo:
            self._registrar_eventos()

    def _registrar_eventos(self):
        self.bind("<Enter>",    lambda _: self.config(bg=self._hover))
        self.bind("<Leave>",    lambda _: self.config(bg=self._bg))
        self.bind("<Button-1>", lambda _: self._cmd())

    def habilitar(self):
        if not self._ativo:
            self._ativo = True
            self.config(cursor="hand2")
            self._registrar_eventos()


# ── App principal ─────────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("IIoT Dashboard — Análise de Sensor DHT")
        self.configure(bg=UI_BG)
        try:
            self.state("zoomed")
        except Exception:
            self.attributes("-zoomed", True)

        self._df      = None
        self._stats   = None
        self._arquivo = None
        self._fig     = None
        self._canvas  = None
        self._toolbar = None
        self._ph      = None

        self._build()

    def _build(self):
        # ── Topbar ────────────────────────────────────────────────────────────
        topbar = tk.Frame(self, bg=UI_PAI, pady=10)
        topbar.pack(fill="x", side="top")

        tk.Label(topbar, text="⚙  IIoT Dashboard", bg=UI_PAI, fg=BRANCO,
                 font=("DejaVu Sans", 13, "bold")).pack(side="left", padx=18)

        self._btn_import = _Botao(topbar, "📂  Importar CSV",
                                  self._importar, bg=UI_BTN, hover=UI_BTN_HV)
        self._btn_import.pack(side="left", padx=8)

        self._btn_save = _Botao(topbar, "💾  Salvar PNG",
                                self._salvar_png,
                                bg="#334155", hover="#475569", state="disabled")
        self._btn_save.pack(side="left", padx=4)

        self._lbl_arq = tk.Label(topbar, text="Nenhum arquivo carregado",
                                 bg=UI_PAI, fg=UI_MUTED,
                                 font=("DejaVu Sans", 9))
        self._lbl_arq.pack(side="left", padx=16)

        # ── Notebook ──────────────────────────────────────────────────────────
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("D.TNotebook",     background=UI_BG, borderwidth=0)
        style.configure("D.TNotebook.Tab", background=UI_PAI, foreground=CINZA_TX,
                        padding=[14, 6], font=("DejaVu Sans", 9))
        style.map("D.TNotebook.Tab",
                  background=[("selected", UI_BTN)],
                  foreground=[("selected", BRANCO)])

        self._nb = ttk.Notebook(self, style="D.TNotebook")
        self._nb.pack(fill="both", expand=True)

        self._tab_dash = tk.Frame(self._nb, bg=UI_BG)
        self._nb.add(self._tab_dash, text="  📊  Dashboard  ")

        self._tab_rel = tk.Frame(self._nb, bg=UI_BG)
        self._nb.add(self._tab_rel, text="  📋  Relatório  ")

        self._mostrar_placeholder()

        # Área de texto do relatório
        self._txt = tk.Text(self._tab_rel, bg=UI_PAI, fg=BRANCO,
                            font=("Courier New", 10), relief="flat",
                            state="disabled", padx=16, pady=12,
                            insertbackground=BRANCO)
        sb = ttk.Scrollbar(self._tab_rel, orient="vertical",
                           command=self._txt.yview)
        self._txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._txt.pack(fill="both", expand=True)

        # ── Status bar ────────────────────────────────────────────────────────
        self._status = tk.Label(self, text="  Pronto.", bg="#020617",
                                fg=UI_MUTED, font=("DejaVu Sans", 8), anchor="w")
        self._status.pack(fill="x", side="bottom")

    def _mostrar_placeholder(self):
        self._ph = tk.Frame(self._tab_dash, bg=UI_BG)
        self._ph.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(self._ph, text="📂", bg=UI_BG, fg=UI_MUTED,
                 font=("DejaVu Sans", 52)).pack()
        tk.Label(self._ph,
                 text="Importe um arquivo CSV para visualizar o dashboard",
                 bg=UI_BG, fg=UI_MUTED,
                 font=("DejaVu Sans", 11)).pack(pady=10)
        _Botao(self._ph, "  Selecionar arquivo CSV  ", self._importar,
               bg=UI_BTN, hover=UI_BTN_HV, font_size=11).pack(pady=4)

    # ── Importar ──────────────────────────────────────────────────────────────
    def _importar(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar arquivo CSV",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
        )
        if not caminho:
            return
        self._set_status("Carregando arquivo…")
        threading.Thread(target=self._processar, args=(caminho,), daemon=True).start()

    def _processar(self, caminho):
        try:
            df    = carregar(caminho)
            stats = estatisticas(df)
            if not stats:
                raise ValueError("Nenhuma coluna de temperatura ou umidade encontrada.")
            self._df      = df
            self._stats   = stats
            self._arquivo = caminho
            self.after(0, self._renderizar)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro ao carregar", str(e)))
            self.after(0, lambda: self._set_status(f"Erro: {e}"))

    # ── Renderizar ────────────────────────────────────────────────────────────
    def _renderizar(self):
        self._set_status("Gerando gráficos…")

        # limpa anterior
        if self._canvas:
            self._canvas.get_tk_widget().destroy()
        if self._toolbar:
            self._toolbar.destroy()
        if self._ph and self._ph.winfo_exists():
            self._ph.destroy()
        if self._fig:
            plt.close(self._fig)

        # gera nova figura
        self._fig = gerar_figura(self._df, self._stats, self._arquivo)

        frame = tk.Frame(self._tab_dash, bg=UI_BG)
        frame.pack(fill="both", expand=True)

        self._canvas = FigureCanvasTkAgg(self._fig, master=frame)
        self._canvas.draw()

        self._toolbar = NavigationToolbar2Tk(self._canvas, frame, pack_toolbar=False)
        self._toolbar.config(bg=UI_PAI)
        self._toolbar.pack(side="bottom", fill="x")
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        # relatório
        rel = relatorio_texto(self._df, self._stats)
        self._txt.config(state="normal")
        self._txt.delete("1.0", "end")
        self._txt.insert("end", rel)
        self._txt.config(state="disabled")

        nome = os.path.basename(self._arquivo)
        self._lbl_arq.config(text=f"✔  {nome}", fg=VERDE)
        self._btn_save.habilitar()
        n = self._stats.get("temp", self._stats.get("hum", {})).get("n", len(self._df))
        self._set_status(f"✔  {nome} — {n} registros carregados.")

    # ── Salvar PNG ────────────────────────────────────────────────────────────
    def _salvar_png(self):
        if not self._fig:
            return
        base     = os.path.splitext(os.path.basename(self._arquivo))[0]
        destino  = filedialog.asksaveasfilename(
            title="Salvar dashboard como PNG",
            initialfile=base + "_dashboard.png",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("Todos", "*.*")],
        )
        if not destino:
            return
        self._fig.savefig(destino, dpi=150, bbox_inches="tight", facecolor=CINZA_BG)
        self._set_status(f"✔  Salvo em: {destino}")
        messagebox.showinfo("Salvo com sucesso", f"Dashboard salvo em:\n{destino}")

    def _set_status(self, msg: str):
        self._status.config(text=f"  {msg}")


# ── Entrada ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    App().mainloop()