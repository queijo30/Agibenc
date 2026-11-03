"""
components.py - Componentes visuais reutilizáveis para a interface do AgiBench.
"""

import customtkinter as ctk


class MetricCard(ctk.CTkFrame):
    """Card visual moderno para exibir os resultados de cada teste individual."""

    def __init__(self, master, title: str, icon: str, accent_color: str = "#38bdf8", **kwargs):
        super().__init__(master, corner_radius=12, fg_color="#1e293b", border_width=1, border_color="#334155", **kwargs)
        self.accent_color = accent_color

        # Cabeçalho com ícone e título
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=14, pady=(10, 2))

        self.icon_label = ctk.CTkLabel(
            self.header_frame,
            text=icon,
            font=("Segoe UI Emoji", 16)
        )
        self.icon_label.pack(side="left", padx=(0, 6))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text=title,
            font=("Segoe UI", 12, "bold"),
            text_color="#94a3b8"
        )
        self.title_label.pack(side="left")

        # Valor da Pontuação
        self.score_label = ctk.CTkLabel(
            self,
            text="---",
            font=("Segoe UI", 22, "bold"),
            text_color="#f8fafc"
        )
        self.score_label.pack(padx=14, pady=(2, 0), anchor="w")

        # Subtítulo com detalhes técnicos
        self.detail_label = ctk.CTkLabel(
            self,
            text="Aguardando teste...",
            font=("Segoe UI", 10),
            text_color="#64748b",
            wraplength=180,
            justify="left"
        )
        self.detail_label.pack(padx=14, pady=(0, 10), anchor="w")

    def update_score(self, score: int, details: str, active: bool = False):
        """Atualiza os valores exibidos no card."""
        self.score_label.configure(
            text=f"{score:,} pts".replace(",", "."),
            text_color=self.accent_color if score > 0 else "#f8fafc"
        )
        self.detail_label.configure(text=details)
        if active:
            self.configure(border_color=self.accent_color, border_width=2)
        else:
            self.configure(border_color="#334155", border_width=1)

    def set_running(self, status: str = "Testando..."):
        """Define o estado do card como em execução."""
        self.score_label.configure(text="...", text_color=self.accent_color)
        self.detail_label.configure(text=status)
        self.configure(border_color=self.accent_color, border_width=2)

    def reset(self):
        """Reseta o card para o estado inicial."""
        self.score_label.configure(text="---", text_color="#f8fafc")
        self.detail_label.configure(text="Aguardando teste...")
        self.configure(border_color="#334155", border_width=1)


class HardwareBadge(ctk.CTkFrame):
    """Badge elegante para exibir especificações do PC no cabeçalho."""

    def __init__(self, master, icon: str, title: str, value: str, **kwargs):
        super().__init__(master, corner_radius=8, fg_color="#0f172a", border_width=1, border_color="#1e293b", **kwargs)

        icon_lbl = ctk.CTkLabel(self, text=icon, font=("Segoe UI Emoji", 14))
        icon_lbl.pack(side="left", padx=(10, 6), pady=6)

        text_frame = ctk.CTkFrame(self, fg_color="transparent")
        text_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=4)

        title_lbl = ctk.CTkLabel(text_frame, text=title, font=("Segoe UI", 9, "bold"), text_color="#64748b")
        title_lbl.pack(anchor="w")

        val_lbl = ctk.CTkLabel(text_frame, text=value, font=("Segoe UI", 11, "bold"), text_color="#e2e8f0")
        val_lbl.pack(anchor="w")
