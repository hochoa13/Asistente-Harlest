#!/usr/bin/env python3
import os
import re
from pathlib import Path

# Traducciones principales
translations = {
    'title: "Quickstart"': 'title: "Inicio Rápido"',
    'title: "Installation"': 'title: "Instalación"',
    'title: "Learning Path"': 'title: "Ruta de Aprendizaje"',
    'title: "CLI"': 'title: "CLI"',
    'title: "Configuration"': 'title: "Configuración"',
    'title: "Messaging Gateway"': 'title: "Puerta de Enlace de Mensajería"',
    'title: "Security"': 'title: "Seguridad"',
    'description: "Your first conversation with Hermes Agent': 'description: "Tu primera conversación con Hermes Agent',
    'description: "Install in 60 seconds': 'description: "Instala en 60 segundos',
    'description: "Guided learning path': 'description: "Ruta de aprendizaje guiada',
    'description: "Language, settings': 'description: "Idioma, configuración',
    'description: "Set up Telegram': 'description: "Configura Telegram',
    'description: "Command approval': 'description: "Aprobación de comandos',
    '## Quick Links': '## Enlaces Rápidos',
    '## Key Features': '## Características Clave',
    'Install Hermes Agent': 'Instala Hermes Agent',
    'Run the one-line installer': 'Ejecuta el instalador de una línea',
    'After it finishes': 'Después de que termine',
    'reload your shell': 'recarga tu shell',
    'Windows Users': 'Usuarios de Windows',
    'Set Up a Provider': 'Configura un Proveedor',
    'Enter your API key': 'Ingresa tu clave API',
    'Your first conversation': 'Tu primera conversación',
    'Explore features': 'Explora características',
    'built by Nous Research': 'creado por Harlest',
    'Built by Nous Research': 'Creado por Harlest',
}

docs_path = Path('docs')

# Procesar todos los archivos .md
for md_file in docs_path.rglob('*.md'):
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Aplicar traducciones
        for english, spanish in translations.items():
            content = content.replace(english, spanish)
        
        # Cambiar Nous Research completo
        content = re.sub(
            r'\[Nous Research\]\(https://nousresearch\.com\)',
            '[Harlest](https://www.facebook.com/haroldandres.hernandezochoa/)',
            content
        )
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ {md_file.relative_to('.').as_posix()}")
    except Exception as e:
        print(f"⚠️ Error en {md_file}: {e}")

print("\n✅ Traducción completada")
