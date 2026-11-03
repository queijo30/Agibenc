"""
scoring.py - Sistema de cálculo de pontuação global, classificação de categorias (tiers)
e exportação de relatórios estruturados.
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from agibench.benchmarks.cpu import CPUBenchmarkResult
from agibench.benchmarks.disk import DiskBenchmarkResult
from agibench.benchmarks.graphics import GraphicsBenchmarkResult
from agibench.benchmarks.ram import RAMBenchmarkResult
from agibench.hardware import SystemInfo


@dataclass
class BenchmarkReport:
    timestamp: str = ""
    system_info: Optional[SystemInfo] = None
    cpu_result: Optional[CPUBenchmarkResult] = None
    ram_result: Optional[RAMBenchmarkResult] = None
    disk_result: Optional[DiskBenchmarkResult] = None
    graphics_result: Optional[GraphicsBenchmarkResult] = None
    total_score: int = 0
    tier_title: str = ""
    tier_badge: str = ""
    tier_description: str = ""


def calculate_tier(total_score: int) -> tuple[str, str, str]:
    """Retorna (título, emoji/badge, descrição recomendada de uso)."""
    if total_score < 2000:
        return (
            "Básico / Escritório",
            "🥉",
            "Ideal para navegação na internet, documentos, planilhas e reprodução de vídeos."
        )
    elif total_score < 4500:
        return (
            "Intermediário / Multitarefas",
            "🥈",
            "Ótimo para estudos, trabalho de escritório intenso, multitarefa e ferramentas corporativas."
        )
    elif total_score < 8000:
        return (
            "Avançado / Produtividade & Jogos Leves",
            "🥇",
            "Perfeito para programação, edição de fotos/vídeos leves, multitarefa pesada e jogos eSports."
        )
    elif total_score < 13000:
        return (
            "Alto Desempenho / Gamer & Criação",
            "🚀",
            "Desempenho de sobra para jogos AAA em alta qualidade, modelagem 3D e edição 4K fluida."
        )
    else:
        return (
            "Extremo / Workstation & Entusiasta",
            "⚡",
            "Poder de ponta para modelos de IA locais, renderização pesada, simulações e servidores."
        )


def generate_benchmark_report(
    sys_info: SystemInfo,
    cpu_res: Optional[CPUBenchmarkResult] = None,
    ram_res: Optional[RAMBenchmarkResult] = None,
    disk_res: Optional[DiskBenchmarkResult] = None,
    gpu_res: Optional[GraphicsBenchmarkResult] = None
) -> BenchmarkReport:
    """Calcula a pontuação global ponderada e compila o relatório final."""
    report = BenchmarkReport()
    report.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report.system_info = sys_info
    report.cpu_result = cpu_res
    report.ram_result = ram_res
    report.disk_result = disk_res
    report.graphics_result = gpu_res

    # Pesos balanceados:
    # CPU Single: 15% | CPU Multi: 35% | RAM: 20% | Disco: 15% | GPU: 15%
    weights_sum = 0.0
    weighted_total = 0.0

    if cpu_res and cpu_res.single_core_score > 0:
        weighted_total += cpu_res.single_core_score * 0.15
        weighted_total += cpu_res.multi_core_score * 0.35
        weights_sum += 0.50

    if ram_res and ram_res.ram_score > 0:
        weighted_total += ram_res.ram_score * 0.20
        weights_sum += 0.20

    if disk_res and disk_res.disk_score > 0:
        weighted_total += disk_res.disk_score * 0.15
        weights_sum += 0.15

    if gpu_res and gpu_res.graphics_score > 0:
        weighted_total += gpu_res.graphics_score * 0.15
        weights_sum += 0.15

    if weights_sum > 0:
        # Normaliza caso o usuário tenha executado apenas testes parciais
        report.total_score = int(weighted_total / weights_sum)
    else:
        report.total_score = 0

    title, badge, desc = calculate_tier(report.total_score)
    report.tier_title = title
    report.tier_badge = badge
    report.tier_description = desc

    return report


def export_report_to_text(report: BenchmarkReport) -> str:
    """Exporta o relatório em formato de texto limpo e legível."""
    lines = [
        "=" * 60,
        "              AGIBENCH - RELATÓRIO DE DESEMPENHO             ",
        "=" * 60,
        f"Data/Hora: {report.timestamp}",
        "",
        "--- ESPECIFICAÇÕES DO COMPUTADOR ---",
        f"• Sistema: {report.system_info.os_name} {report.system_info.os_version} ({report.system_info.os_arch})",
        f"• Processador: {report.system_info.cpu_model}",
        f"• Núcleos: {report.system_info.cpu_cores_physical} Físicos / {report.system_info.cpu_cores_logical} Threads",
        f"• Memória RAM: {report.system_info.ram_total_gb} GB Total",
        f"• Placa de Vídeo: {', '.join(report.system_info.gpus)}",
        f"• Armazenamento Principal: {report.system_info.storage_primary} ({report.system_info.storage_free_gb} GB livres de {report.system_info.storage_total_gb} GB)",
        "",
        "--- PONTUAÇÃO DOS TESTES ---",
    ]

    if report.cpu_result:
        lines.append(f"• CPU Single-Core: {report.cpu_result.single_core_score} pts ({report.cpu_result.single_core_ops_per_sec:,.0f} ops/s)")
        lines.append(f"• CPU Multi-Core:  {report.cpu_result.multi_core_score} pts (Escala de {report.cpu_result.multicore_ratio}x)")

    if report.ram_result:
        lines.append(f"• Memória RAM:     {report.ram_result.ram_score} pts (Gravação: {report.ram_result.write_speed_mb_s} MB/s | Leitura: {report.ram_result.read_speed_mb_s} MB/s | Latência: {report.ram_result.access_latency_ns} ns)")

    if report.disk_result:
        lines.append(f"• Armazenamento:   {report.disk_result.disk_score} pts (Leitura: {report.disk_result.seq_read_mb_s} MB/s | Escrita: {report.disk_result.seq_write_mb_s} MB/s | IOPS 4K: {int(report.disk_result.random_4k_iops)})")

    if report.graphics_result:
        lines.append(f"• Gráficos / GPU:  {report.graphics_result.graphics_score} pts (FPS Médio: {report.graphics_result.avg_fps} | Min FPS: {report.graphics_result.min_fps})")

    lines.extend([
        "",
        "=" * 60,
        f" PONTUAÇÃO GLOBAL: {report.total_score} PONTOS",
        f" CATEGORIA: {report.tier_badge} {report.tier_title}",
        f" PERFIL: {report.tier_description}",
        "=" * 60,
    ])

    return "\n".join(lines)


def export_report_to_json(report: BenchmarkReport) -> str:
    """Converte o relatório em JSON formatado."""
    data: Dict[str, Any] = {
        "timestamp": report.timestamp,
        "total_score": report.total_score,
        "tier": {
            "title": report.tier_title,
            "badge": report.tier_badge,
            "description": report.tier_description
        },
        "system": asdict(report.system_info) if report.system_info else {},
        "cpu": asdict(report.cpu_result) if report.cpu_result else {},
        "ram": asdict(report.ram_result) if report.ram_result else {},
        "disk": asdict(report.disk_result) if report.disk_result else {},
        "graphics": asdict(report.graphics_result) if report.graphics_result else {}
    }
    return json.dumps(data, indent=2, ensure_ascii=False)
