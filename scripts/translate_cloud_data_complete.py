#!/usr/bin/env python3
"""
Complete English translation for nan-data-engineering-labs modules.
3-pass strategy:
  PASS 1: Cloud+technical terms dictionary (deterministic)
  PASS 2: Metadata field replacements (Nivel → Level, etc)
  PASS 3: GoogleTranslator for residual Spanish (with safety checks)
  VALIDATION: Scan for remaining accented characters
"""

import re
from pathlib import Path
from typing import Dict, Set
from deep_translator import GoogleTranslator

# PASS 1: Cloud + Technical Dictionary (Deterministic)
CLOUD_TECH_DICTIONARY = {
    # Cloud concepts
    "computación en la nube": "cloud computing",
    "Computación en la Nube": "Cloud Computing",
    "nube": "cloud",
    "proveedor cloud": "cloud provider",
    "centro de datos": "data center",
    "centros de datos": "data centers",
    
    # Data Engineering specific
    "ingesta de datos": "data ingestion",
    "transformación de datos": "data transformation",
    "almacén de datos": "data warehouse",
    "lago de datos": "data lake",
    "pipeline": "pipeline",
    "orquestación": "orchestration",
    "ETL": "ETL",
    
    # AWS/Cloud services
    "servidor": "server",
    "servidores": "servers",
    "almacenamiento": "storage",
    "base de datos": "database",
    "bases de datos": "databases",
    "máquina virtual": "virtual machine",
    "máquinas virtuales": "virtual machines",
    
    # Technical terms
    "recurso": "resource",
    "recursos": "resources",
    "servicio": "service",
    "servicios": "services",
    "características": "features",
    "característica": "feature",
    "modelo": "model",
    "escalabilidad": "scalability",
    "escalable": "scalable",
    "elasticidad": "elasticity",
    "elástico": "elastic",
    "disponibilidad": "availability",
    "confiabilidad": "reliability",
    "seguridad": "security",
    "rendimiento": "performance",
    "latencia": "latency",
    "throughput": "throughput",
    
    # Data/Database
    "tabla": "table",
    "tablas": "tables",
    "fila": "row",
    "filas": "rows",
    "columna": "column",
    "columnas": "columns",
    "índice": "index",
    "índices": "indexes",
    "consulta": "query",
    "consultas": "queries",
    "transacción": "transaction",
    "transacciones": "transactions",
    
    # Common action words
    "provisión": "provisioning",
    "provisionar": "provision",
    "desplegar": "deploy",
    "deployar": "deploy",
    "monitorizar": "monitor",
    "monitorear": "monitor",
    "escalar": "scale",
    "escalado": "scaling",
    "autoescalado": "autoscaling",
    "replicar": "replicate",
    "replicación": "replication",
    "sincronizar": "synchronize",
    "sincronización": "synchronization",
    "migrar": "migrate",
    "migración": "migration",
}

# PASS 2: Metadata field replacements
METADATA_REPLACEMENTS = {
    "**Nivel:**": "**Level:**",
    "Nivel:": "Level:",
    "**Prerequisitos:**": "**Prerequisites:**",
    "Prerequisitos:": "Prerequisites:",
    "Prerrequisitos:": "Prerequisites:",
    "**Prerequisitos:**": "**Prerequisites:**",
    "**Tiempo estimado:**": "**Estimated time:**",
    "Tiempo estimado:": "Estimated time:",
    "**Duración:**": "**Duration:**",
    "Duración:": "Duration:",
    "**Objetivos:**": "**Learning Objectives:**",
    "Objetivos de Aprendizaje:": "Learning Objectives:",
    "**Recursos:**": "**Resources:**",
    "Recursos:": "Resources:",
    "**Ejercicios:**": "**Exercises:**",
    "Ejercicios:": "Exercises:",
    "**Validación:**": "**Validation:**",
    "Validación:": "Validation:",
    
    # Common responses
    "Ninguno": "None",
    "ninguno": "none",
    "Sí": "Yes",
    "sí": "yes",
    "No": "No",
    "no": "no",
}

def preserve_code_links(text: str) -> tuple[str, Dict]:
    """Extract code blocks and links to preserve them."""
    preserved = {}
    counter = 0
    
    # Extract code blocks
    code_pattern = r"```[\s\S]*?```"
    def replace_code(m):
        nonlocal counter
        placeholder = f"__PRESERVED_{counter}__"
        preserved[placeholder] = m.group(0)
        counter += 1
        return placeholder
    text = re.sub(code_pattern, replace_code, text)
    
    # Extract markdown links [text](url)
    link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    def replace_link(m):
        nonlocal counter
        placeholder = f"__PRESERVED_{counter}__"
        preserved[placeholder] = m.group(0)
        counter += 1
        return placeholder
    text = re.sub(link_pattern, replace_link, text)
    
    return text, preserved


def restore_code_links(text: str, preserved: Dict) -> str:
    """Restore preserved code blocks and links."""
    for placeholder, original in preserved.items():
        text = text.replace(placeholder, original)
    return text


def pass1_dictionary_replacement(text: str) -> str:
    """PASS 1: Apply cloud-tech dictionary with word boundary safety."""
    for es, en in CLOUD_TECH_DICTIONARY.items():
        # Case-sensitive replacements first
        text = text.replace(es, en)
        # Case-insensitive for lowercase variants
        if es.islower():
            text = re.sub(r'\b' + re.escape(es) + r'\b', en, text, flags=re.IGNORECASE)
    return text


def pass2_metadata_replacement(text: str) -> str:
    """PASS 2: Replace metadata fields deterministically."""
    for es_field, en_field in METADATA_REPLACEMENTS.items():
        text = text.replace(es_field, en_field)
    return text


ACCENT_RE = re.compile(r"[áéíóúñÁÉÍÓÚÑ¿¡àâäãèêëìîïòôöõùûüÀÂÄÃÈÊËÌÎÏÒÔÖÕÙÛÜ]")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_CODE_RE = re.compile(r"(`[^`]+`)")


def pass3_deep_translation(text: str, translator: GoogleTranslator) -> str:
    """PASS 3: Use GoogleTranslator line-by-line only for lines with accented chars."""
    lines = text.split('\n')
    result = []
    in_fence = False

    for line in lines:
        if FENCE_RE.match(line):
            in_fence = not in_fence
            result.append(line)
            continue

        # Skip code blocks, empty lines, pure markdown structure
        if in_fence or not line.strip() or not ACCENT_RE.search(line):
            result.append(line)
            continue

        # Extract markdown prefix (headings, bullets, etc.) and preserve it
        prefix_m = re.match(r'^(\s*(?:#{1,6} |[-*+] |\d+\. |> )*)(.*)', line)
        if not prefix_m:
            result.append(line)
            continue

        prefix, body = prefix_m.group(1), prefix_m.group(2)
        if not body.strip() or not ACCENT_RE.search(body):
            result.append(line)
            continue

        # Preserve inline code snippets
        parts = INLINE_CODE_RE.split(body)
        translated_parts = []
        for part in parts:
            if part.startswith('`') and part.endswith('`'):
                translated_parts.append(part)
            elif ACCENT_RE.search(part) and part.strip():
                try:
                    translated = translator.translate(part)
                    translated_parts.append(translated if translated else part)
                except Exception:
                    translated_parts.append(part)
            else:
                translated_parts.append(part)

        result.append(prefix + ''.join(translated_parts))

    return '\n'.join(result)


def validate_english_only(text: str, filepath: str) -> Set[str]:
    """
    Validate that text is English-only (except in code blocks).
    Returns set of problematic lines.
    """
    accent_pattern = re.compile(r"[áéíóúñÁÉÍÓÚÑ¿¡àâäãèêëêìîïòôöõùûüÀÂÄÃÈÊËÌÎÏÒÔÖÕÙÛÜ]")
    issues = set()
    
    in_code = False
    for i, line in enumerate(text.split('\n'), 1):
        if line.strip().startswith('```'):
            in_code = not in_code
            continue
        
        if in_code:
            continue
        
        if accent_pattern.search(line):
            issues.add(f"{filepath}:{i}: {line[:80]}")
    
    return issues


def translate_module_file(filepath: Path) -> bool:
    """
    Translate a single markdown file using 3-pass strategy.
    Returns True if file was changed.
    """
    original_text = filepath.read_text(encoding='utf-8')
    
    # PASS 1: Extract and preserve
    text, preserved = preserve_code_links(original_text)
    
    # Apply 3-pass translation
    text = pass1_dictionary_replacement(text)
    text = pass2_metadata_replacement(text)
    
    # PASS 3: Deep translation for residuals
    try:
        translator = GoogleTranslator(source='es', target='en')
        text = pass3_deep_translation(text, translator)
    except Exception as e:
        print(f"⚠️  Could not initialize GoogleTranslator: {e}")
    
    # Restore preserved blocks
    text = restore_code_links(text, preserved)
    
    # Validate
    issues = validate_english_only(text, filepath.as_posix())
    if issues:
        print(f"⚠️  {filepath.name} still has accented chars:")
        for issue in list(issues)[:3]:
            print(f"   {issue}")
    
    # Write back if changed
    if text != original_text:
        filepath.write_text(text, encoding='utf-8')
        return True
    return False


def translate_module(module_path: Path) -> None:
    """Translate all MD files in a module recursively."""
    print(f"\n📦 Translating module: {module_path.name}")
    
    # Scan ALL .md files recursively, skip my_solution dirs
    md_files = sorted([
        f for f in module_path.rglob("*.md")
        if "my_solution" not in f.parts
    ])
    
    changed_count = 0
    unchanged_count = 0
    for filepath in md_files:
        if translate_module_file(filepath):
            changed_count += 1
            print(f"  ✅ {filepath.relative_to(module_path.parent)}")
        else:
            unchanged_count += 1

    print(f"  📊 Changed: {changed_count}, Unchanged: {unchanged_count} (total {changed_count + unchanged_count})")


def main():
    """Translate specific modules — pass module names as args or use defaults."""
    import sys as _sys
    base_path = Path("modules")
    
    if len(_sys.argv) > 1:
        modules = _sys.argv[1:]
    else:
        # Default: modules 02 and 03 with correct names
        modules = [
            "module-02-storage-basics",
            "module-03-sql-foundations",
        ]
    
    for module_name in modules:
        module_path = base_path / module_name
        if module_path.exists():
            translate_module(module_path)
        else:
            print(f"⚠️  {module_path} does not exist, skipping")


if __name__ == "__main__":
    main()
