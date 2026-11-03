"""
ram.py - Testes de benchmark de memória RAM (Leitura, Escrita e Acesso Aleatório).
Projetado para ser seguro e leve mesmo em computadores com 2GB ou 4GB de RAM.
"""

import random
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class RAMBenchmarkResult:
    write_speed_mb_s: float = 0.0
    read_speed_mb_s: float = 0.0
    access_latency_ns: float = 0.0
    ram_score: int = 0


def run_ram_benchmark(
    progress_callback: Optional[Callable[[float, str], None]] = None,
    cancel_event: Optional[threading.Event] = None
) -> RAMBenchmarkResult:
    """
    Executa testes de memória:
    1. Escrita sequencial em blocos de memória
    2. Leitura sequencial e agregação
    3. Teste de latência com saltos aleatórios de memória
    """
    result = RAMBenchmarkResult()

    # Bloco seguro de 64 MB (não sobrecarrega PCs com pouca RAM)
    block_size_mb = 64
    block_bytes = block_size_mb * 1024 * 1024
    pattern_size = 1024 * 1024  # 1 MB por fatia
    pattern = b"\xAA" * pattern_size

    if cancel_event and cancel_event.is_set():
        return result

    if progress_callback:
        progress_callback(0.10, "Alocando e testando taxa de escrita na memória RAM...")

    # --- 1. Teste de Escrita ---
    try:
        buffer = bytearray(block_bytes)
    except MemoryError:
        # Fallback para máquinas com memória extremamente baixa (32 MB)
        block_size_mb = 32
        block_bytes = block_size_mb * 1024 * 1024
        buffer = bytearray(block_bytes)

    iterations_write = 4
    total_written_mb = block_size_mb * iterations_write

    t0_write = time.perf_counter()
    for _ in range(iterations_write):
        if cancel_event and cancel_event.is_set():
            del buffer
            return result
        for offset in range(0, block_bytes, pattern_size):
            buffer[offset:offset + pattern_size] = pattern

    t_write = max(0.0001, time.perf_counter() - t0_write)
    result.write_speed_mb_s = round(total_written_mb / t_write, 1)

    if cancel_event and cancel_event.is_set():
        del buffer
        return result

    if progress_callback:
        progress_callback(0.45, f"Escrita concluída ({result.write_speed_mb_s} MB/s). Testando taxa de leitura...")

    # --- 2. Teste de Leitura Sequencial ---
    iterations_read = 6
    total_read_mb = block_size_mb * iterations_read

    t0_read = time.perf_counter()
    for _ in range(iterations_read):
        if cancel_event and cancel_event.is_set():
            del buffer
            return result
        # Varredura por blocos com cálculo de checksum rápido
        for offset in range(0, block_bytes, pattern_size):
            _ = buffer[offset:offset + pattern_size]

    t_read = max(0.0001, time.perf_counter() - t0_read)
    result.read_speed_mb_s = round(total_read_mb / t_read, 1)

    if cancel_event and cancel_event.is_set():
        del buffer
        return result

    if progress_callback:
        progress_callback(0.75, "Testando latência de acesso e saltos aleatórios...")

    # --- 3. Teste de Latência / Acesso Aleatório ---
    num_probes = 500_000
    stride_mask = block_bytes - 1
    # Cria lista de índices aleatórios para saltos
    random_offsets = [random.randint(0, block_bytes - 1) for _ in range(1000)]

    t0_lat = time.perf_counter()
    accum = 0
    for i in range(num_probes):
        idx = random_offsets[i % 1000]
        accum += buffer[idx]
    t_lat = max(0.0001, time.perf_counter() - t0_lat)

    # Latência em nanossegundos por leitura
    result.access_latency_ns = round((t_lat / num_probes) * 1e9, 1)

    # Libera memória imediatamente
    del buffer

    # --- Cálculo da Pontuação de Memória ---
    # Fórmula normalizada combinando largura de banda de escrita, leitura e penalidade de latência
    bandwidth_score = (result.write_speed_mb_s * 0.4) + (result.read_speed_mb_s * 0.6)
    latency_factor = max(0.5, min(2.0, 100.0 / max(1.0, result.access_latency_ns)))
    result.ram_score = max(100, int((bandwidth_score * 0.5) * latency_factor))

    if progress_callback:
        progress_callback(1.0, f"RAM Concluída! {result.ram_score} pts (Escrita: {result.write_speed_mb_s} MB/s | Leitura: {result.read_speed_mb_s} MB/s)")

    return result
