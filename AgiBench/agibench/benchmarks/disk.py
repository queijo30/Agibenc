"""
disk.py - Testes de benchmark de armazenamento (SSD / HD / NVMe).
Mede velocidade sequencial de leitura/escrita e operações por segundo (IOPS 4K).
"""

import os
import random
import tempfile
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class DiskBenchmarkResult:
    seq_write_mb_s: float = 0.0
    seq_read_mb_s: float = 0.0
    random_4k_iops: float = 0.0
    random_4k_mb_s: float = 0.0
    disk_score: int = 0


def run_disk_benchmark(
    target_dir: Optional[str] = None,
    file_size_mb: int = 96,
    progress_callback: Optional[Callable[[float, str], None]] = None,
    cancel_event: Optional[threading.Event] = None
) -> DiskBenchmarkResult:
    """
    Executa testes de armazenamento:
    1. Escrita sequencial com descarga direta para o disco (fsync)
    2. Leitura sequencial
    3. Acesso aleatório em blocos de 4 KB (IOPS e taxa de transferência)
    """
    result = DiskBenchmarkResult()

    if target_dir is None:
        target_dir = tempfile.gettempdir()

    test_file_path = os.path.join(target_dir, f"agibench_benchmark_{os.getpid()}_{int(time.time())}.tmp")
    chunk_1mb = os.urandom(1024 * 1024)

    try:
        # --- 1. Teste de Escrita Sequencial ---
        if cancel_event and cancel_event.is_set():
            return result

        if progress_callback:
            progress_callback(0.10, f"Gravando arquivo temporário ({file_size_mb} MB) para testar escrita sequencial...")

        t0_write = time.perf_counter()
        with open(test_file_path, "wb") as f:
            for i in range(file_size_mb):
                if cancel_event and cancel_event.is_set():
                    return result
                f.write(chunk_1mb)
            f.flush()
            os.fsync(f.fileno())

        t_write = max(0.001, time.perf_counter() - t0_write)
        result.seq_write_mb_s = round(file_size_mb / t_write, 1)

        if cancel_event and cancel_event.is_set():
            return result

        if progress_callback:
            progress_callback(0.50, f"Escrita: {result.seq_write_mb_s} MB/s. Testando leitura sequencial...")

        # --- 2. Teste de Leitura Sequencial ---
        t0_read = time.perf_counter()
        with open(test_file_path, "rb") as f:
            bytes_read = 0
            while True:
                if cancel_event and cancel_event.is_set():
                    return result
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                bytes_read += len(chunk)

        t_read = max(0.001, time.perf_counter() - t0_read)
        result.seq_read_mb_s = round((bytes_read / (1024 * 1024)) / t_read, 1)

        if cancel_event and cancel_event.is_set():
            return result

        if progress_callback:
            progress_callback(0.75, f"Leitura: {result.seq_read_mb_s} MB/s. Testando operações aleatórias 4K (IOPS)...")

        # --- 3. Teste Aleatório 4K ---
        block_4k_size = 4096
        max_blocks = (file_size_mb * 1024 * 1024) // block_4k_size
        num_4k_ops = 800

        t0_4k = time.perf_counter()
        with open(test_file_path, "rb") as f:
            for _ in range(num_4k_ops):
                if cancel_event and cancel_event.is_set():
                    return result
                blk_idx = random.randint(0, max_blocks - 1)
                f.seek(blk_idx * block_4k_size)
                _ = f.read(block_4k_size)

        t_4k = max(0.001, time.perf_counter() - t0_4k)
        result.random_4k_iops = round(num_4k_ops / t_4k, 0)
        result.random_4k_mb_s = round(((num_4k_ops * block_4k_size) / (1024 * 1024)) / t_4k, 1)

        # --- Cálculo da Pontuação de Disco ---
        # Ponderação: 40% escrita, 40% leitura, 20% fator 4K
        seq_avg = (result.seq_write_mb_s + result.seq_read_mb_s) / 2.0
        bonus_4k = min(1500, result.random_4k_iops * 0.15)
        result.disk_score = max(100, int(seq_avg * 2.2 + bonus_4k))

        if progress_callback:
            progress_callback(1.0, f"Disco Concluído! {result.disk_score} pts (Leitura: {result.seq_read_mb_s} MB/s | Escrita: {result.seq_write_mb_s} MB/s | IOPS: {int(result.random_4k_iops)})")

    finally:
        # Limpeza obrigatória do arquivo de teste
        try:
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
        except Exception:
            pass

    return result
