#!/usr/bin/env python3
"""Monitor logs do bot Discord em tempo real."""

import time
import subprocess
import re

def follow_logfile(log_file):
    """Follow log file like tail -f."""
    with open(log_file, 'r') as f:
        # Move to end of file
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

def monitor_bot_logs():
    """Monitora logs do bot e highlights RAG activity."""

    log_file = "/Users/gabrielramos/.claude/projects/-Users-gabrielramos-repos-OraculoBOT/27d016b0-99b8-43e1-86dd-715002a89633/tasks/bo1x8zh1l.output"

    print("=" * 80)
    print("MONITOR DE LOGS - OraculoBOT")
    print("=" * 80)
    print("\nAguardando mensagens no Discord...")
    print("\nℹ️  Envie uma mensagem no canal configurado para testar o RAG.")
    print("   O bot mostrará logs de processamento aqui.")
    print("\n" + "-" * 80 + "\n")

    for line in follow_logfile(log_file):
        # Highlight RAG-related logs
        if "RAG" in line:
            print(f"🔍 [RAG] {line.strip()}")
        elif "enrich_with_rag" in line:
            print(f"📊 [ENRICH] {line.strip()}")
        elif "Bot conectado" in line or "Escutando" in line:
            print(f"✅ [BOT] {line.strip()}")
        elif "INFO" in line:
            # Regular info logs
            print(f"ℹ️  {line.strip()}")
        elif "ERROR" in line or "Falha" in line:
            print(f"❌ [ERROR] {line.strip()}")
        elif "WARNING" in line or "AVISO" in line:
            print(f"⚠️  [WARN] {line.strip()}")
        else:
            # Other logs
            print(f"   {line.strip()}")

if __name__ == "__main__":
    try:
        monitor_bot_logs()
    except KeyboardInterrupt:
        print("\n\n👋 Monitoramento encerrado.")
