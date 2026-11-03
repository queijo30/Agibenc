"""
cpu.py - Testes de benchmark de processador (Single-Core e Multi-Core).
Compatível com todos os processadores (x86, x64, ARM, Intel, AMD, Apple Silicon).
"""

import concurrent.futures
import hashlib
import math
import multiprocessing
import os
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class CPUBenchmarkResult:
    single_core_ops_per_sec: float = 0.0
    single_core_score: int = 0
    multi_core_ops_per_sec: float = 0.0
    multi_core_score: int = 0
    multicore_ratio: float = 1.0
    threads_used: int = 1


def _cpu_worker_task(duration: float, check_interval: int = 1000) -> int:
    """
    Executa uma carga de trabalho intensiva combinando:
    1. Operações de ponto flutuante e funções trigonométricas (ALU / FPU)
    2. Criptografia SHA-256 e operações com buffers binários
    3. Cálculos de raiz quadrada e aproximações matemáticas
    """
    end_time = time.perf_counter() + duration
    total_ops = 0
    payload = b"AgiBench-Universal-CPU-Benchmark-Vector-2026-Stress-Engine"

    while time.perf_counter() < end_time:
        acc = 0.0
        h = hashlib.sha256()
        for i in range(check_interval):
            x = (i + 1) * 0.000314159
            acc += math.sin(x) * math.cos(x) + math.sqrt(i + 1.0)
            h.update(payload)
        total_ops += check_interval

    return total_ops


def run_cpu_benchmark(
    duration_per_stage: float = 3.5,
    progress_callback: Optional[Callable[[float, str], None]] = None,
    cancel_event: Optional[threading.Event] = None
) -> CPUBenchmarkResult:
    """
    Executa a bateria de testes de CPU:
    1. Single-Core: Mede a velocidade de um único núcleo.
    2. Multi-Core: Mede a capacidade em paralelo utilizando todos os threads lógicos.
    """
    result = CPUBenchmarkResult()
    cores_logical = os.cpu_count() or 1
    result.threads_used = cores_logical

    # --- 1. Teste Single-Core ---
    if cancel_event and cancel_event.is_set():
        return result

    if progress_callback:
        progress_callback(0.05, "Iniciando teste Single-Core (Cálculo FPU + Criptografia)...")

    t0 = time.perf_counter()
    single_ops = _cpu_worker_task(duration_per_stage)
    t_elapsed_single = max(0.001, time.perf_counter() - t0)

    result.single_core_ops_per_sec = single_ops / t_elapsed_single
    # Fórmula calibrada: ~3.000.000 ops/s = ~1000 pontos
    result.single_core_score = max(50, int(result.single_core_ops_per_sec / 3000))

    if cancel_event and cancel_event.is_set():
        return result

    if progress_callback:
        progress_callback(0.50, f"Single-Core finalizado ({result.single_core_score} pts). Iniciando Multi-Core ({cores_logical} threads)...")

    # --- 2. Teste Multi-Core ---
    t0_multi = time.perf_counter()
    total_multi_ops = 0

    try:
        # Usa ProcessPoolExecutor para contornar o GIL e usar 100% de todos os núcleos
        with concurrent.futures.ProcessPoolExecutor(max_workers=cores_logical) as executor:
            futures = [executor.submit(_cpu_worker_task, duration_per_stage) for _ in range(cores_logical)]
            
            for f in concurrent.futures.as_completed(futures):
                if cancel_event and cancel_event.is_set():
                    executor.shutdown(wait=False, cancel_futures=True)
                    return result
                total_multi_ops += f.result()
    except Exception:
        # Fallback para ThreadPoolExecutor caso processos paralelos falhem
        with concurrent.futures.ThreadPoolExecutor(max_workers=cores_logical) as executor:
            futures = [executor.submit(_cpu_worker_task, duration_per_stage) for _ in range(cores_logical)]
            for f in concurrent.futures.as_completed(futures):
                if cancel_event and cancel_event.is_set():
                    return result
                total_multi_ops += f.result()

    t_elapsed_multi = max(0.001, time.perf_counter() - t0_multi)
    result.multi_core_ops_per_sec = total_multi_ops / t_elapsed_multi
    result.multi_core_score = max(result.single_core_score, int(result.multi_core_ops_per_sec / 3000))

    if result.single_core_score > 0:
        result.multicore_ratio = round(result.multi_core_score / result.single_core_score, 2)

    if progress_callback:
        progress_callback(1.0, f"CPU Concluído! Single: {result.single_core_score} pts | Multi: {result.multi_core_score} pts ({result.multicore_ratio}x)")

    return result
