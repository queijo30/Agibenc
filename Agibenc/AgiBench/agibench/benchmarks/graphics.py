"""
graphics.py - Teste de benchmark gráfico 2D/3D em tempo real.
Executa renderização vetorial 3D com projeção em perspectiva, sombreamento
e simulação de física de partículas diretamente no canvas da interface.
"""

import math
import random
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional, Tuple


@dataclass
class GraphicsBenchmarkResult:
    avg_fps: float = 0.0
    min_fps: float = 0.0
    total_frames: int = 0
    test_duration: float = 0.0
    graphics_score: int = 0


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "color", "radius")

    def __init__(self, w: int, h: int):
        self.x = random.uniform(20, w - 20)
        self.y = random.uniform(20, h - 20)
        self.vx = random.uniform(-4.0, 4.0)
        self.vy = random.uniform(-4.0, 4.0)
        self.radius = random.choice([2, 3, 4])
        self.color = random.choice(["#38bdf8", "#818cf8", "#c084fc", "#f43f5e", "#34d399", "#fbbf24"])

    def update(self, w: int, h: int):
        self.x += self.vx
        self.y += self.vy
        if self.x <= self.radius or self.x >= w - self.radius:
            self.vx *= -1
        if self.y <= self.radius or self.y >= h - self.radius:
            self.vy *= -1


def generate_torus_mesh(r_major: float = 90.0, r_minor: float = 35.0, seg_u: int = 24, seg_v: int = 12):
    """Gera vértices e arestas de um toroide 3D para teste de geometria vetorial."""
    vertices = []
    edges = []

    for i in range(seg_u):
        u = (i / seg_u) * (2 * math.pi)
        for j in range(seg_v):
            v = (j / seg_v) * (2 * math.pi)
            x = (r_major + r_minor * math.cos(v)) * math.cos(u)
            y = (r_major + r_minor * math.cos(v)) * math.sin(u)
            z = r_minor * math.sin(v)
            vertices.append((x, y, z))

            # Arestas
            curr = i * seg_v + j
            next_v = i * seg_v + ((j + 1) % seg_v)
            next_u = ((i + 1) % seg_u) * seg_v + j
            edges.append((curr, next_v))
            edges.append((curr, next_u))

    return vertices, edges


def run_graphics_benchmark(
    canvas,
    root,
    duration: float = 5.0,
    progress_callback: Optional[Callable[[float, str], None]] = None,
    cancel_event: Optional[threading.Event] = None
) -> GraphicsBenchmarkResult:
    """
    Executa o teste de estresse gráfico em tempo real no Canvas do Tkinter.
    Mede taxa de quadros (FPS médio e 1% lows) com projeção 3D contínua.
    """
    result = GraphicsBenchmarkResult()

    w = max(300, canvas.winfo_width() or 500)
    h = max(200, canvas.winfo_height() or 300)
    cx, cy = w / 2.0, h / 2.0

    vertices, edges = generate_torus_mesh()
    num_particles = 250
    particles = [Particle(w, h) for _ in range(num_particles)]

    frame_times = []
    total_frames = 0
    t_start = time.perf_counter()
    last_frame_t = t_start
    rot_x, rot_y, rot_z = 0.0, 0.0, 0.0

    if progress_callback:
        progress_callback(0.10, "Renderizando malha 3D e simulação física de partículas...")

    while True:
        if cancel_event and cancel_event.is_set():
            break

        now = time.perf_counter()
        elapsed = now - t_start
        if elapsed >= duration:
            break

        dt = max(0.0001, now - last_frame_t)
        frame_times.append(dt)
        last_frame_t = now
        total_frames += 1

        # Rotação 3D
        rot_x += 0.03
        rot_y += 0.05
        rot_z += 0.02

        cx_val, sx_val = math.cos(rot_x), math.sin(rot_x)
        cy_val, sy_val = math.cos(rot_y), math.sin(rot_y)
        cz_val, sz_val = math.cos(rot_z), math.sin(rot_z)

        # Projeção de vértices 3D -> 2D
        proj_pts = []
        d = 350.0  # distância focal
        for vx, vy, vz in vertices:
            # Rot Y
            x1 = vx * cy_val + vz * sy_val
            z1 = -vx * sy_val + vz * cy_val
            # Rot X
            y2 = vy * cx_val - z1 * sx_val
            z2 = vy * sx_val + z1 * cx_val
            # Rot Z
            x3 = x1 * cz_val - y2 * sz_val
            y3 = x1 * sz_val + y2 * cz_val

            scale = d / (z2 + d + 120.0)
            px = cx + x3 * scale
            py = cy + y3 * scale
            proj_pts.append((px, py, scale))

        # Limpa o canvas para o novo quadro
        canvas.delete("all")

        # Desenha partículas do fundo
        for p in particles:
            p.update(w, h)
            canvas.create_oval(p.x - p.radius, p.y - p.radius, p.x + p.radius, p.y + p.radius, fill=p.color, outline="")

        # Desenha arestas do toroide com gradiente de profundidade
        for idx1, idx2 in edges:
            x1, y1, s1 = proj_pts[idx1]
            x2, y2, s2 = proj_pts[idx2]
            # Cor baseada na profundidade (escala)
            line_color = "#38bdf8" if s1 > 0.8 else "#1e40af"
            width = 1.8 if s1 > 0.8 else 1.0
            canvas.create_line(x1, y1, x2, y2, fill=line_color, width=width)

        # Medidor de FPS no canto da tela
        current_fps = int(1.0 / dt) if dt > 0 else 0
        canvas.create_text(
            50, 20,
            text=f"FPS: {current_fps}",
            fill="#22c55e",
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        )
        canvas.create_text(
            50, 40,
            text=f"Partículas: {num_particles} | Vértices: {len(vertices)}",
            fill="#94a3b8",
            font=("Segoe UI", 9),
            anchor="w"
        )

        # Atualiza a UI do Tkinter sem bloquear
        root.update()

        # Atualiza o callback de progresso a cada fração de tempo
        if progress_callback and total_frames % 20 == 0:
            fraction = min(0.95, elapsed / duration)
            progress_callback(fraction, f"Teste Gráfico em andamento... FPS Atual: {current_fps}")

    # Processamento dos resultados
    total_elapsed = max(0.001, time.perf_counter() - t_start)
    result.total_frames = total_frames
    result.test_duration = round(total_elapsed, 2)
    result.avg_fps = round(total_frames / total_elapsed, 1)

    if frame_times:
        sorted_times = sorted(frame_times, reverse=True)
        # 1% low (as 1% piores quedas de quadro)
        low_idx = max(1, int(len(sorted_times) * 0.01))
        result.min_fps = round(1.0 / sorted_times[low_idx - 1], 1)
    else:
        result.min_fps = result.avg_fps

    # Cálculo da pontuação gráfica (60 FPS = ~1500 pts, 120 FPS = ~3000 pts, 250+ FPS = ~6500+ pts)
    result.graphics_score = max(100, int((result.avg_fps * 22.0) + (result.min_fps * 8.0)))

    # Limpa o canvas após finalizar
    canvas.delete("all")
    canvas.create_text(
        cx, cy,
        text=f"Teste Gráfico Concluído!\nFPS Médio: {result.avg_fps} | Score: {result.graphics_score} pts",
        fill="#38bdf8",
        font=("Segoe UI", 14, "bold"),
        justify="center"
    )

    if progress_callback:
        progress_callback(1.0, f"Gráficos Concluído! FPS Médio: {result.avg_fps} (Min: {result.min_fps}) | {result.graphics_score} pts")

    return result
