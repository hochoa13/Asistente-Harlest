"""
Subcomando de cron para la CLI de Hermes.

Gestiona: hermes cron [list|status|tick]

Los trabajos cron se ejecutan automáticamente mediante el demonio del gateway (hermes gateway).
Instala el gateway como servicio para que se ejecute en segundo plano:
    hermes gateway install
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

from hermes_cli.colors import Colors, color


def cron_list(show_all: bool = False):
    """Listar todos los trabajos programados."""
    from cron.jobs import list_jobs
    
    jobs = list_jobs(include_disabled=show_all)
    
    if not jobs:
        print(color("No hay trabajos programados.", Colors.DIM))
        print(color("Crea uno con el comando /cron add en el chat, o vía Telegram.", Colors.DIM))
        return
    
    print()
    print(color("┌─────────────────────────────────────────────────────────────────────────┐", Colors.CYAN))
    print(color("│                       Trabajos programados                              │", Colors.CYAN))
    print(color("└─────────────────────────────────────────────────────────────────────────┘", Colors.CYAN))
    print()
    
    for job in jobs:
        job_id = job.get("id", "?")[:8]
        name = job.get("name", "(unnamed)")
        schedule = job.get("schedule_display", job.get("schedule", {}).get("value", "?"))
        enabled = job.get("enabled", True)
        next_run = job.get("next_run_at", "?")
        
        repeat_info = job.get("repeat", {})
        repeat_times = repeat_info.get("times")
        repeat_completed = repeat_info.get("completed", 0)
        
        if repeat_times:
            repeat_str = f"{repeat_completed}/{repeat_times}"
        else:
            repeat_str = "∞"
        
        deliver = job.get("deliver", ["local"])
        if isinstance(deliver, str):
            deliver = [deliver]
        deliver_str = ", ".join(deliver)
        
        if not enabled:
            status = color("[deshabilitado]", Colors.RED)
        else:
            status = color("[activo]", Colors.GREEN)
        
        print(f"  {color(job_id, Colors.YELLOW)} {status}")
        print(f"    Nombre:    {name}")
        print(f"    Horario:   {schedule}")
        print(f"    Repetir:   {repeat_str}")
        print(f"    Próxima:   {next_run}")
        print(f"    Entrega:   {deliver_str}")
        print()
    
    # Warn if gateway isn't running
    from hermes_cli.gateway import find_gateway_pids
    if not find_gateway_pids():
        print(color("  ⚠  El gateway no se está ejecutando — los trabajos no se dispararán automáticamente.", Colors.YELLOW))
        print(color("     Inícialo con: hermes gateway install", Colors.DIM))
        print()


def cron_tick():
    """Ejecutar una vez los trabajos pendientes y salir."""
    from cron.scheduler import tick
    tick(verbose=True)


def cron_status():
    """Mostrar el estado de ejecución de cron."""
    from cron.jobs import list_jobs
    from hermes_cli.gateway import find_gateway_pids
    
    print()
    
    pids = find_gateway_pids()
    if pids:
        print(color("✓ El gateway se está ejecutando — los trabajos de cron se dispararán automáticamente", Colors.GREEN))
        print(f"  PID: {', '.join(map(str, pids))}")
    else:
        print(color("✗ El gateway no se está ejecutando — los trabajos de cron NO se ejecutarán", Colors.RED))
        print()
        print("  Para habilitar la ejecución automática:")
        print("    hermes gateway install    # Instalar como servicio del sistema (recomendado)")
        print("    hermes gateway            # O ejecutarlo en primer plano")
    
    print()
    
    jobs = list_jobs(include_disabled=False)
    if jobs:
        next_runs = [j.get("next_run_at") for j in jobs if j.get("next_run_at")]
        print(f"  {len(jobs)} trabajo(s) activo(s)")
        if next_runs:
            print(f"  Próxima ejecución: {min(next_runs)}")
    else:
        print("  No hay trabajos activos")
    
    print()


def cron_command(args):
    """Gestionar los subcomandos de cron."""
    subcmd = getattr(args, 'cron_command', None)
    
    if subcmd is None or subcmd == "list":
        show_all = getattr(args, 'all', False)
        cron_list(show_all)
    
    elif subcmd == "tick":
        cron_tick()
    
    elif subcmd == "status":
        cron_status()
    
    else:
        print(f"Comando cron desconocido: {subcmd}")
        print("Uso: hermes cron [list|status|tick]")
        sys.exit(1)
