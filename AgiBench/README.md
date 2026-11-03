#  AgiBench - Benchmark Universal para Todos os Tipos de PC

O **AgiBench** é um aplicativo moderno, leve e completo de medição de desempenho (benchmark) de hardware para computadores pessoais. Desenvolvido para rodar de forma suave tanto em computadores mais antigos/básicos quanto em máquinas gamer e workstations topo de linha.

---

##  Principais Recursos

- **Detecção Automática de Hardware**:
  - Processador (Nome, núcleos físicos e lógicos, frequência).
  - Memória RAM total e disponível.
  - Placa de Vídeo / Adaptador gráfico (GPU dedicada ou integrada).
  - Armazenamento (Espaço total, livre e drive principal).
  - Sistema Operacional e arquitetura (x64, ARM).

- **Bateria Completa de Testes**:
  1.  **CPU Single-Core**: Mede a velocidade de um único núcleo com instruções matemáticas avançadas (ponto flutuante / FPU) e rodadas criptográficas SHA-256.
  2.  **CPU Multi-Core**: Mede o ganho e a eficiência de paralelismo em 100% de todos os núcleos lógicos.
  3.  **Memória RAM**: Mede velocidade sequencial de escrita, velocidade sequencial de leitura e latência de saltos em nanossegundos (ns).
  4.  **Armazenamento (SSD / HD / NVMe)**: Mede taxa de escrita sequencial direta no disco (`fsync`), leitura sequencial e operações aleatórias por segundo (IOPS 4K).
  5.  **Gráficos 2D/3D em Tempo Real**: Renderiza uma malha 3D geométrica com perspectiva e sombreamento somada a uma simulação física de 250 partículas com contador de FPS ao vivo.

- **Classificação por Categorias (Tiers)**:
  -  **Básico / Escritório** (< 2.000 pts)
  -  **Intermediário / Multitarefas e jogos leves  e intermediarios** (2.000 a 4.500 pts)
  -  **Avançado / Produtividade & Jogos mais pesados** (4.500 a 8.000 pts)
  - **Alto Desempenho / Gamer & Criação** (8.000 a 13.000 pts)
  -  **Extremo / Workstation & Entusiasta** (> 13.000 pts)

- **Exportação e Compartilhamento**:
  - Copiar resumo com 1 clique para a área de transferência.
  - Salvar relatório técnico em formato de texto (`.txt`).
  - Salvar métricas brutas em formato JSON (`.json`).

---

## 💻 Como Executar

### Método 1: Início Rápido (Recomendado no Windows)
Basta dar dois cliques no arquivo:
```
iniciar.bat
```

### Método 2: Pelo Terminal / Linha de Comando
1. Abra o terminal na pasta do projeto:
   ```bash
   cd C:\Users\jojo\AgiBench
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute o programa:
   ```bash
   python main.py
   ```

---

## 🛠️ Tecnologias Utilizadas
- **Python 3.10+**
- **CustomTkinter**: Interface gráfica moderna em Dark Mode.
- **Psutil**: Telemetria e diagnóstico de recursos de hardware.
- **Multiprocessing**: Paralelismo real contornando o GIL para estresse 100% multinúcleo.
