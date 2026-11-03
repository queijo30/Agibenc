"""
report_view.py - Janela modal de visualização e exportação do relatório de benchmark.
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

from agibench.scoring import (
    BenchmarkReport,
    export_report_to_json,
    export_report_to_text,
)


class ReportModal(ctk.CTkToplevel):
    """Janela flutuante moderna para apresentar os resultados finais e opções de exportação."""

    def __init__(self, master, report: BenchmarkReport):
        super().__init__(master)
        self.report = report

        self.title("AgiBench - Resultado do Benchmark")
        self.geometry("640x700")
        self.minsize(580, 600)
        self.configure(fg_color="#0b0f19")

        # Torna a janela modal
        self.transient(master)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        # Header com pontuação global
        header_card = ctk.CTkFrame(self, fg_color="#111827", corner_radius=14, border_width=1, border_color="#1f2937")
        header_card.pack(fill="x", padx=20, pady=(20, 10))

        score_title = ctk.CTkLabel(
            header_card,
            text="PONTUAÇÃO GLOBAL",
            font=("Segoe UI", 11, "bold"),
            text_color="#9ca3af"
        )
        score_title.pack(pady=(15, 0))

        big_score = ctk.CTkLabel(
            header_card,
            text=f"{self.report.total_score:,}".replace(",", "."),
            font=("Segoe UI", 42, "bold"),
            text_color="#38bdf8"
        )
        big_score.pack()

        tier_lbl = ctk.CTkLabel(
            header_card,
            text=f"{self.report.tier_badge}  {self.report.tier_title}",
            font=("Segoe UI", 16, "bold"),
            text_color="#f3f4f6"
        )
        tier_lbl.pack(pady=(2, 4))

        desc_lbl = ctk.CTkLabel(
            header_card,
            text=self.report.tier_description,
            font=("Segoe UI", 11),
            text_color="#94a3b8",
            wraplength=520
        )
        desc_lbl.pack(pady=(0, 15), padx=20)

        # Caixa com o texto detalhado do relatório
        report_frame = ctk.CTkFrame(self, fg_color="#1e293b", corner_radius=12)
        report_frame.pack(fill="both", expand=True, padx=20, pady=10)

        report_txt = export_report_to_text(self.report)
        self.textbox = ctk.CTkTextbox(
            report_frame,
            fg_color="transparent",
            font=("Consolas", 11),
            text_color="#e2e8f0"
        )
        self.textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.textbox.insert("1.0", report_txt)
        self.textbox.configure(state="disabled")

        # Barra de Ações (Copiar, Salvar TXT, Salvar JSON, Fechar)
        actions_bar = ctk.CTkFrame(self, fg_color="transparent")
        actions_bar.pack(fill="x", padx=20, pady=(5, 20))

        copy_btn = ctk.CTkButton(
            actions_bar,
            text="📋 Copiar",
            fg_color="#334155",
            hover_color="#475569",
            command=self._copy_to_clipboard,
            width=100
        )
        copy_btn.pack(side="left", padx=(0, 8))

        save_txt_btn = ctk.CTkButton(
            actions_bar,
            text="💾 Salvar .TXT",
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self._save_txt,
            width=110
        )
        save_txt_btn.pack(side="left", padx=(0, 8))

        save_json_btn = ctk.CTkButton(
            actions_bar,
            text="📊 Salvar .JSON",
            fg_color="#6366f1",
            hover_color="#4f46e5",
            command=self._save_json,
            width=110
        )
        save_json_btn.pack(side="left")

        close_btn = ctk.CTkButton(
            actions_bar,
            text="Fechar",
            fg_color="#dc2626",
            hover_color="#b91c1c",
            command=self.destroy,
            width=90
        )
        close_btn.pack(side="right")

    def _copy_to_clipboard(self):
        text = export_report_to_text(self.report)
        self.clipboard_clear()
        self.clipboard_append(text)
        messagebox.showinfo("Copiado!", "Relatório copiado com sucesso para a área de transferência!")

    def _save_txt(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivos de Texto", "*.txt")],
            initialfile=f"AgiBench_Relatorio_{self.report.total_score}pts.txt"
        )
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(export_report_to_text(self.report))
            messagebox.showinfo("Salvo!", f"Relatório salvo em:\n{filepath}")

    def _save_json(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Arquivos JSON", "*.json")],
            initialfile=f"AgiBench_Dados_{self.report.total_score}pts.json"
        )
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(export_report_to_json(self.report))
            messagebox.showinfo("Salvo!", f"Dados exportados em:\n{filepath}")
