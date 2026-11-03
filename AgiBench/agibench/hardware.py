"""
hardware.py - Módulo de detecção e diagnóstico de hardware para todos os tipos de PC.
Funciona em Windows, Linux e macOS com fallbacks seguros.
"""

import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from typing import List, Optional

try:
    import psutil
except ImportError:
    psutil = None


@dataclass
class SystemInfo:
    os_name: str = ""
    os_version: str = ""
    os_arch: str = ""
    cpu_model: str = ""
    cpu_cores_physical: int = 1
    cpu_cores_logical: int = 1
    cpu_frequency_ghz: float = 0.0
    ram_total_gb: float = 0.0
    ram_available_gb: float = 0.0
    gpus: List[str] = field(default_factory=list)
    storage_primary: str = ""
    storage_total_gb: float = 0.0
    storage_free_gb: float = 0.0


def _get_cpu_model() -> str:
    """Obtém o nome amigável do modelo de CPU de forma rápida e segura."""
    system = platform.system()
    try:
        if system == "Windows":
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            )
            name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            return name.strip()
        elif system == "Linux":
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "model name" in line:
                        return line.split(":", 1)[1].strip()
        elif system == "Darwin":
            cmd = ["sysctl", "-n", "machdep.cpu.brand_string"]
            return subprocess.check_output(cmd).decode().strip()
    except Exception:
        pass
    return platform.processor() or "Processador Desconhecido"


def _get_gpus() -> List[str]:
    """Obtém os adaptadores de vídeo / GPUs detectados no sistema."""
    system = platform.system()
    gpus = []
    if system == "Windows":
        try:
            import winreg
            base_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base_path)
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    i += 1
                    if subkey_name.isdigit():
                        sub_key = winreg.OpenKey(key, subkey_name)
                        try:
                            driver_desc, _ = winreg.QueryValueEx(sub_key, "DriverDesc")
                            if driver_desc and driver_desc not in gpus:
                                gpus.append(driver_desc.strip())
                        except FileNotFoundError:
                            pass
                except OSError:
                    break
        except Exception:
            pass

        # Fallback via PowerShell se o registro não tiver retornado nada
        if not gpus:
            try:
                cmd = ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"]
                out = subprocess.check_output(cmd, timeout=3).decode().strip()
                for line in out.splitlines():
                    line = line.strip()
                    if line and line not in gpus:
                        gpus.append(line)
            except Exception:
                pass
    elif system == "Linux":
        try:
            out = subprocess.check_output(["lspci"], timeout=3).decode()
            for line in out.splitlines():
                if "VGA" in line or "3D controller" in line:
                    parts = line.split(":", 2)
                    if len(parts) >= 3:
                        gpus.append(parts[2].strip())
        except Exception:
            pass
    elif system == "Darwin":
        try:
            out = subprocess.check_output(["system_profiler", "SPDisplaysDataType"], timeout=3).decode()
            for line in out.splitlines():
                if "Chipset Model:" in line:
                    gpus.append(line.split(":", 1)[1].strip())
        except Exception:
            pass

    return gpus or ["Placa de Vídeo Integrada / Genérica"]


def get_system_info() -> SystemInfo:
    """Coleta e retorna as informações estruturadas de hardware do PC."""
    info = SystemInfo()

    # Sistema Operacional
    info.os_name = platform.system()
    info.os_version = platform.version()
    info.os_arch = platform.machine() or "x86_64"

    # CPU
    info.cpu_model = _get_cpu_model()
    if psutil:
        info.cpu_cores_logical = psutil.cpu_count(logical=True) or (os.cpu_count() or 1)
        info.cpu_cores_physical = psutil.cpu_count(logical=False) or (info.cpu_cores_logical // 2 or 1)
        freq = psutil.cpu_freq()
        if freq and freq.current:
            info.cpu_frequency_ghz = round(freq.current / 1000.0, 2)
    else:
        info.cpu_cores_logical = os.cpu_count() or 1
        info.cpu_cores_physical = max(1, info.cpu_cores_logical // 2)

    # Memória RAM
    if psutil:
        vmem = psutil.virtual_memory()
        info.ram_total_gb = round(vmem.total / (1024 ** 3), 2)
        info.ram_available_gb = round(vmem.available / (1024 ** 3), 2)
    else:
        info.ram_total_gb = 8.0
        info.ram_available_gb = 4.0

    # GPUs
    info.gpus = _get_gpus()

    # Armazenamento (Drive principal / onde está o SO ou temp)
    try:
        drive_path = "C:\\" if info.os_name == "Windows" else "/"
        if psutil:
            disk = psutil.disk_usage(drive_path)
            info.storage_primary = drive_path
            info.storage_total_gb = round(disk.total / (1024 ** 3), 1)
            info.storage_free_gb = round(disk.free / (1024 ** 3), 1)
    except Exception:
        pass

    return info
