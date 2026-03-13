#!/usr/bin/env python3
"""
Ejemplo: Hermes Agent especializado en Ransomware & Penetration Testing

Este script muestra cómo inicializar Hermes como especialista en:
- Análisis de ransomware (ingeniería inversa, detección)
- Penetration testing profesional
- Análisis de malware
- Respuesta a incidentes de ciberseguridad
"""

from run_agent import AIAgent

def main():
    # Inicializa Hermes como especialista en ransomware/pentesting
    agent = AIAgent(
        model="anthropic/claude-opus-4.6",  # O cualquier otro modelo
        agent_specialty="ransomware_pentesting",  # ← Activa especialización
        quiet_mode=False,
        max_iterations=50,
    )

    # Ejemplos de consultas que puedes hacer:
    example_queries = [
        "Analiza el siguiente malware y dame un reporte de IOCs",
        "¿Cuál es el vector de ataque más común en ransomware?",
        "Dame una guía de hardening para Windows Server contra ransomware",
        "Explica las tácticas MITRE ATT&CK usadas por LockBit",
        "¿Cómo detecto un ataque de ransomware en fase de reconocimiento?",
    ]

    print("=" * 80)
    print("🛡️  HERMES AGENT - ESPECIALISTA EN RANSOMWARE & PENTESTING")
    print("=" * 80)
    print("\nNota: Este agente responderá con expertise profesional en seguridad ofensiva.")
    print("Todas las respuestas estarán en español neutralizado.\n")

    # Ejemplo interactivo
    while True:
        user_input = input("\n🔍 Consulta (o 'exit' para salir): ").strip()
        
        if user_input.lower() in ("exit", "salir", "quit"):
            print("\n👋 Hasta luego.")
            break
        
        if not user_input:
            continue
        
        print("\n⏳ Analizando...\n")
        
        try:
            # Chat con el agente especializado
            response = agent.chat(user_input)
            print(f"\n✅ Respuesta:\n{response}")
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
