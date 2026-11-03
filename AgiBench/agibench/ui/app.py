"""
app.py - Janela principal do aplicativo AgiBench.
"""

import threading
import time
import tkinter as tk
from typing import Optional

import customtkinter as ctk

from agibench.benchmarks.cpu import CPUBenchmarkResult, run_cpu_benchmark
from agibench.benchmarks.disk import DiskBenchmarkResult, run_disk_benchmark
from agibench.benchmarks.graphics import (
    GraphicsBenchmarkResult,
    run_graphics_benchmark,
)
from agibench.benchmarks.ram import RAMBenchmarkResult, run_ram_benchmark
from agibench.hardware import SystemInfo, get_system_info
from agibench.scoring import (
    BenchmarkReport,
    generate_benchmark_report,
)
from agibench.ui.components import HardwareBadge, MetricCard
from agibench.ui.report_view import ReportModal


class AgiBenchApp(ctk.CTk):
    """Aplicativo principal de benchmark universal com interface gráfica moderna."""

    def __init__(self):
        super().__init__()

        # Configurações da Janela
        self.title("AgiBench - Benchmark Universal de Desempenho")
        self.geometry("1020x760")
        self.minsize(920, 680)

        # Tema Escuro Moderno
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color="#0b0f19")

        # Estado da Aplicação
        self.sys_info: SystemInfo = get_system_info()
        self.cpu_res: Optional[CPUBenchmarkResult] = None
        self.ram_res: Optional[RAMBenchmarkResult] = None
        self.disk_res: Optional[DiskBenchmarkResult] = None
        self.gpu_res: Optional[GraphicsBenchmarkResult] = None
        self.current_report: Optional[BenchmarkReport] = None

        self.worker_thread: Optional[threading.Thread] = None
        self.cancel_event = threading.Event()
        self.is_running = False

        self._build_ui()

    def _build_ui(self):
        # 1. Topo: Cabeçalho do Aplicativo
        header_frame = ctk.CTkFrame(self, fg_color="#111827", corner_radius=14, border_width=1, border_color="#1f2937")
        header_frame.pack(fill="x", padx=20, pady=(16, 12))

        title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_container.pack(fill="x", padx=16, pady=(12, 6))

        app_title = ctk.CTkLabel(
            title_container,
            text="⚡ AgiBench",
            font=("Segoe UI", 20, "bold"),
            text_color="#38bdf8"
        )
        app_title.pack(side="left")

        app_ver = ctk.CTkLabel(
            title_container,
            text="v1.0 • Universal PC Benchmark",
            font=("Segoe UI", 11),
            text_color="#64748b"
        )
        app_ver.pack(side="left", padx=(8, 0), pady=(3, 0))

        # Badges de Especificações de Hardware
        badges_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        badges_container.pack(fill="x", padx=16, pady=(0, 12))

        cpu_val = f"{self.sys_info.cpu_model} ({self.sys_info.cpu_cores_logical}T)"
        if len(cpu_val) > 42:
            cpu_val = cpu_val[:39] + "..."
        b_cpu = HardwareBadge(badges_container, "🧠", "Processador", cpu_val)
        b_cpu.pack(side="left", fill="x", expand=True, padx=(0, 6))

        b_ram = HardwareBadge(badges_container, "💾", "Memória RAM", f"{self.sys_info.ram_total_gb} GB")
        b_ram.pack(side="left", fill="x", expand=True, padx=(0, 6))

        gpu_val = self.sys_info.gpus[0] if self.sys_info.gpus else "Integrada"
        if len(gpu_val) > 28:
            gpu_val = gpu_val[:25] + "..."
        b_gpu = HardwareBadge(badges_container, "🎮", "Gráficos", gpu_val)
        b_gpu.pack(side="left", fill="x", expand=True, padx=(0, 6))

        disk_val = f"{self.sys_info.storage_primary} ({self.sys_info.storage_free_gb} GB livres)"
        b_disk = HardwareBadge(badges_container, "💽", "Disco", disk_val)
        b_disk.pack(side="left", fill="x", expand=True)

        # 2. Área Central (Cards à Esquerda, Canvas de Renderização à Direita)
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.pack(fill="both", expand=True, padx=20, pady=(0, 12))

        # Coluna da Esquerda: Cards de Métricas em Grade (2 colunas)
        cards_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        cards_frame.pack(side="left", fill="both", expand=True, padx=(0, 12))
        cards_frame.columnconfigure((0, 1), weight=1)

        self.card_cpu_single = MetricCard(cards_frame, "CPU Single-Core", "⚡", accent_color="#38bdf8")
        self.card_cpu_single.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")

        self.card_cpu_multi = MetricCard(cards_frame, "CPU Multi-Core", "🚀", accent_color="#818cf8")
        self.card_cpu_multi.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")

        self.card_ram = MetricCard(cards_frame, "Memória RAM", "💾", accent_color="#34d399")
        self.card_ram.grid(row=1, column=0, padx=6, pady=6, sticky="nsew")

        self.card_disk = MetricCard(cards_frame, "Armazenamento", "💽", accent_color="#fbbf24")
        self.card_disk.grid(row=1, column=1, padx=6, pady=6, sticky="nsew")

        self.card_gpu = MetricCard(cards_frame, "Gráficos / GPU", "🎮", accent_color="#f43f5e")
        self.card_gpu.grid(row=2, column=0, padx=6, pady=6, sticky="nsew")

        self.card_global = MetricCard(cards_frame, "Pontuação Global", "🏆", accent_color="#a855f7")
        self.card_global.grid(row=2, column=1, padx=6, pady=6, sticky="nsew")

        # Coluna da Direita: Viewport Visual em Tempo Real (Canvas)
        viewport_frame = ctk.CTkFrame(center_frame, fg_color="#0f172a", corner_radius=14, border_width=1, border_color="#1e293b")
        viewport_frame.pack(side="right", fill="both", expand=True)

        viewport_header = ctk.CTkFrame(viewport_frame, fg_color="transparent")
        viewport_header.pack(fill="x", padx=14, pady=(10, 6))

        viewport_title = ctk.CTkLabel(viewport_header, text="📺 Monitor Visual em Tempo Real", font=("Segoe UI", 12, "bold"), text_color="#cbd5e1")
        viewport_title.pack(side="left")

        self.viewport_canvas = tk.Canvas(
            viewport_frame,
            bg="#020617",
            highlightthickness=0,
            bd=0
        )
        self.viewport_canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self._draw_idle_viewport()

        # 3. Rodapé: Status, Barra de Progresso e Botões de Controle
        footer_frame = ctk.CTkFrame(self, fg_color="#111827", corner_radius=14, border_width=1, border_color="#1f2937")
        footer_frame.pack(fill="x", padx=20, pady=(0, 20))

        # Status e Progresso
        status_bar = ctk.CTkFrame(footer_frame, fg_color="transparent")
        status_bar.pack(fill="x", padx=16, pady=(12, 8))

        self.status_label = ctk.CTkLabel(
            status_bar,
            text="Pronto para iniciar. Clique em 'Executar Benchmark Completo' ou escolha um teste individual.",
            font=("Segoe UI", 11),
            text_color="#94a3b8"
        )
        self.status_label.pack(side="left")

        self.progress_bar = ctk.CTkProgressBar(
            footer_frame,
            orientation="horizontal",
            height=10,
            corner_radius=5,
            progress_color="#0284c7"
        )
        self.progress_bar.pack(fill="x", padx=16, pady=(0, 12))
        self.progress_bar.set(0.0)

        # Botões de Ação
        controls_bar = ctk.CTkFrame(footer_frame, fg_color="transparent")
        controls_bar.pack(fill="x", padx=16, pady=(0, 14))

        self.run_full_btn = ctk.CTkButton(
            controls_bar,
            text="⚡ Executar Benchmark Completo",
            font=("Segoe UI", 13, "bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=38,
            command=self._start_full_benchmark
        )
        self.run_full_btn.pack(side="left", padx=(0, 10))

        self.test_selector = ctk.CTkOptionMenu(
            controls_bar,
            values=["Apenas CPU", "Apenas Memória", "Apenas Armazenamento", "Apenas Gráficos"],
            command=self._start_single_test,
            width=160,
            height=38,
            fg_color="#334155",
            button_color="#475569"
        )
        self.test_selector.set("Testes Individuais ▾")
        self.test_selector.pack(side="left", padx=(0, 10))

        self.cancel_btn = ctk.CTkButton(
            controls_bar,
            text="Cancelar",
            font=("Segoe UI", 11),
            fg_color="#ef4444",
            hover_color="#dc2626",
            height=38,
            width=90,
            state="disabled",
            command=self._cancel_benchmark
        )
        self.cancel_btn.pack(side="left", padx=(0, 10))

        self.report_btn = ctk.CTkButton(
            controls_bar,
            text="📊 Ver Relatório",
            font=("Segoe UI", 11, "bold"),
            fg_color="#4f46e5",
            hover_color="#4338ca",
            height=38,
            width=120,
            state="disabled",
            command=self._open_report_modal
        )
        self.report_btn.pack(side="right")

    def _draw_idle_viewport(self):
        """Desenha uma tela elegante em espera no Canvas."""
        self.viewport_canvas.delete("all")
        w = max(200, self.viewport_canvas.winfo_width() or 400)
        h = max(150, self.viewport_canvas.winfo_height() or 260)
        cx, cy = w / 2, h / 2

        # Círculos concêntricos de radar estático
        for r in (30, 60, 90, 120):
            self.viewport_canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#1e293b", width=1)

        self.viewport_canvas.create_text(
            cx, cy - 10,
            text="⚡ AgiBench Engine",
            fill="#38bdf8",
            font=("Segoe UI", 14, "bold")
        )
        self.viewport_canvas.create_text(
            cx, cy + 18,
            text="Aguardando início do teste...",
            fill="#64748b",
            font=("Segoe UI", 10)
        )

    def _update_status(self, progress: float, message: str):
        """Atualiza a barra de status e progresso de forma thread-safe."""
        self.after(0, lambda: self._apply_status(progress, message))

    def _apply_status(self, progress: float, message: str):
        self.progress_bar.set(max(0.0, min(1.0, progress)))
        self.status_label.configure(text=message)

    def _set_ui_running(self, running: bool):
        """Habilita ou desabilita botões durante a execução."""
        self.is_running = running
        if running:
            self.run_full_btn.configure(state="disabled")
            self.test_selector.configure(state="disabled")
            self.cancel_btn.configure(state="normal")
            self.report_btn.configure(state="disabled")
        else:
            self.run_full_btn.configure(state="normal")
            self.test_selector.configure(state="normal")
            self.cancel_btn.configure(state="disabled")
            if self.current_report:
                self.report_btn.configure(state="normal")

    def _start_full_benchmark(self):
        """Inicia a bateria completa de benchmarks."""
        if self.is_running:
            return

        self.cancel_event.clear()
        self._set_ui_running(True)

        # Reseta os cards
        self.card_cpu_single.reset()
        self.card_cpu_multi.reset()
        self.card_ram.reset()
        self.card_disk.reset()
        self.card_gpu.reset()
        self.card_global.reset()

        self.worker_thread = threading.Thread(target=self._run_full_sequence, daemon=True)
        self.worker_thread.start()

    def _run_full_sequence(self):
        """Thread trabalhadora para a sequência completa de testes."""
        try:
            # 1. CPU
            self.after(0, lambda: self.card_cpu_single.set_running("Testando Single-Core..."))
            self.after(0, lambda: self.card_cpu_multi.set_running("Aguardando..."))
            self.cpu_res = run_cpu_benchmark(
                duration_per_stage=3.5,
                progress_callback=lambda p, msg: self._update_status(p * 0.30, msg),
                cancel_event=self.cancel_event
            )
            if self.cancel_event.is_set():
                self._handle_cancel()
                return

            self.after(0, lambda: self.card_cpu_single.update_score(
                self.cpu_res.single_core_score,
                f"{self.cpu_res.single_core_ops_per_sec:,.0f} ops/s"
            ))
            self.after(0, lambda: self.card_cpu_multi.update_score(
                self.cpu_res.multi_core_score,
                f"{self.cpu_res.threads_used} Threads ({self.cpu_res.multicore_ratio}x)"
            ))

            # 2. RAM
            self.after(0, lambda: self.card_ram.set_running("Testando leitura e escrita..."))
            self.ram_res = run_ram_benchmark(
                progress_callback=lambda p, msg: self._update_status(0.30 + p * 0.25, msg),
                cancel_event=self.cancel_event
            )
            if self.cancel_event.is_set():
                self._handle_cancel()
                return

            self.after(0, lambda: self.card_ram.update_score(
                self.ram_res.ram_score,
                f"Gravação: {self.ram_res.write_speed_mb_s} MB/s\nLeitura: {self.ram_res.read_speed_mb_s} MB/s"
            ))

            # 3. Armazenamento
            self.after(0, lambda: self.card_disk.set_running("Testando SSD/HD..."))
            self.disk_res = run_disk_benchmark(
                progress_callback=lambda p, msg: self._update_status(0.55 + p * 0.20, msg),
                cancel_event=self.cancel_event
            )
            if self.cancel_event.is_set():
                self._handle_cancel()
                return

            self.after(0, lambda: self.card_disk.update_score(
                self.disk_res.disk_score,
                f"Leitura: {self.disk_res.seq_read_mb_s} MB/s\nEscrita: {self.disk_res.seq_write_mb_s} MB/s"
            ))

            # 4. Gráficos (Executado no loop principal de forma síncrona controlada)
            self.after(0, lambda: self.card_gpu.set_running("Renderizando cena 3D..."))
            self._update_status(0.75, "Iniciando teste de estresse gráfico 3D...")

            gpu_done_event = threading.Event()

            def _run_gpu_on_main():
                self.gpu_res = run_graphics_benchmark(
                    self.viewport_canvas,
                    self,
                    duration=5.0,
                    progress_callback=lambda p, msg: self._update_status(0.75 + p * 0.25, msg),
                    cancel_event=self.cancel_event
                )
                gpu_done_event.set()

            self.after(0, _run_gpu_on_main)
            gpu_done_event.wait()

            if self.cancel_event.is_set():
                self._handle_cancel()
                return

            self.after(0, lambda: self.card_gpu.update_score(
                self.gpu_res.graphics_score,
                f"FPS Médio: {self.gpu_res.avg_fps} (Min: {self.gpu_res.min_fps})"
            ))

            # 5. Cálculo Final e Apresentação
            self.current_report = generate_benchmark_report(
                self.sys_info,
                self.cpu_res,
                self.ram_res,
                self.disk_res,
                self.gpu_res
            )

            self.after(0, lambda: self.card_global.update_score(
                self.current_report.total_score,
                f"{self.current_report.tier_badge} {self.current_report.tier_title}",
                active=True
            ))

            self._update_status(
                1.0,
                f"Benchmark Concluído! Pontuação Global: {self.current_report.total_score} pts ({self.current_report.tier_title})"
            )

        except Exception as e:
            self._update_status(0.0, f"Erro durante benchmark: {e}")
        finally:
            self.after(0, lambda: self._set_ui_running(False))

    def _start_single_test(self, selection: str):
        """Inicia apenas o teste selecionado pelo usuário."""
        if self.is_running:
            return

        self.cancel_event.clear()
        self._set_ui_running(True)

        def worker():
            try:
                if selection == "Apenas CPU":
                    self.after(0, lambda: self.card_cpu_single.set_running("Testando Single-Core..."))
                    self.after(0, lambda: self.card_cpu_multi.set_running("Aguardando..."))
                    self.cpu_res = run_cpu_benchmark(
                        duration_per_stage=3.5,
                        progress_callback=self._update_status,
                        cancel_event=self.cancel_event
                    )
                    if not self.cancel_event.is_set():
                        self.after(0, lambda: self.card_cpu_single.update_score(
                            self.cpu_res.single_core_score,
                            f"{self.cpu_res.single_core_ops_per_sec:,.0f} ops/s"
                        ))
                        self.after(0, lambda: self.card_cpu_multi.update_score(
                            self.cpu_res.multi_core_score,
                            f"{self.cpu_res.threads_used} Threads ({self.cpu_res.multicore_ratio}x)"
                        ))

                elif selection == "Apenas Memória":
                    self.after(0, lambda: self.card_ram.set_running("Testando RAM..."))
                    self.ram_res = run_ram_benchmark(
                        progress_callback=self._update_status,
                        cancel_event=self.cancel_event
                    )
                    if not self.cancel_event.is_set():
                        self.after(0, lambda: self.card_ram.update_score(
                            self.ram_res.ram_score,
                            f"Gravação: {self.ram_res.write_speed_mb_s} MB/s\nLeitura: {self.ram_res.read_speed_mb_s} MB/s"
                        ))

                elif selection == "Apenas Armazenamento":
                    self.after(0, lambda: self.card_disk.set_running("Testando SSD/HD..."))
                    self.disk_res = run_disk_benchmark(
                        progress_callback=self._update_status,
                        cancel_event=self.cancel_event
                    )
                    if not self.cancel_event.is_set():
                        self.after(0, lambda: self.card_disk.update_score(
                            self.disk_res.disk_score,
                            f"Leitura: {self.disk_res.seq_read_mb_s} MB/s\nEscrita: {self.disk_res.seq_write_mb_s} MB/s"
                        ))

                elif selection == "Apenas Gráficos":
                    self.after(0, lambda: self.card_gpu.set_running("Renderizando 3D..."))
                    gpu_done = threading.Event()

                    def _run_gpu():
                        self.gpu_res = run_graphics_benchmark(
                            self.viewport_canvas,
                            self,
                            duration=5.0,
                            progress_callback=self._update_status,
                            cancel_event=self.cancel_event
                        )
                        gpu_done.set()

                    self.after(0, _run_gpu)
                    gpu_done.wait()

                    if not self.cancel_event.is_set():
                        self.after(0, lambda: self.card_gpu.update_score(
                            self.gpu_res.graphics_score,
                            f"FPS Médio: {self.gpu_res.avg_fps} (Min: {self.gpu_res.min_fps})"
                        ))

                # Atualiza relatório e pontuação parcial
                self.current_report = generate_benchmark_report(
                    self.sys_info,
                    self.cpu_res,
                    self.ram_res,
                    self.disk_res,
                    self.gpu_res
                )
                self.after(0, lambda: self.card_global.update_score(
                    self.current_report.total_score,
                    f"{self.current_report.tier_badge} {self.current_report.tier_title}",
                    active=True
                ))

            except Exception as e:
                self._update_status(0.0, f"Erro: {e}")
            finally:
                self.after(0, lambda: self._set_ui_running(False))
                self.after(0, lambda: self.test_selector.set("Testes Individuais ▾"))

        self.worker_thread = threading.Thread(target=worker, daemon=True)
        self.worker_thread.start()

    def _cancel_benchmark(self):
        """Interrompe a execução atual imediatamente."""
        self.cancel_event.set()
        self._update_status(0.0, "Cancelamento solicitado... Finalizando tarefas pendentes.")

    def _handle_cancel(self):
        self._update_status(0.0, "Benchmark cancelado pelo usuário.")
        self.after(0, self._draw_idle_viewport)

    def _open_report_modal(self):
        """Abre a janela flutuante com o relatório completo."""
        if self.current_report:
            ReportModal(self, self.current_report)
