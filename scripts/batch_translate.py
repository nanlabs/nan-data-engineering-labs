#!/usr/bin/env python3
"""
Batch Translation Script: Spanish → English for nan-data-engineering-labs

Translates all markdown content from training-cloud-data modules into English,
following TRANSLATION-STYLE-GUIDE.md terminology and rules.

Preserves:
- Code blocks and syntax
- Links and URLs
- Markdown formatting
- File structure

Usage:
    python scripts/batch_translate.py --source ../training-cloud-data/modules --target modules --wave 1
    python scripts/batch_translate.py --full-scan  # Translate all 23 modules

Requires:
    - ANTHROPIC_API_KEY environment variable
    - Python 3.10+
    - anthropic package: pip install anthropic
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import tempfile
import shutil

# Try to import anthropic client
try:
    import anthropic
except ImportError:
    print("Error: anthropic package not found. Install with: pip install anthropic")
    sys.exit(1)


class TranslationBatchProcessor:
    """Handles batch translation of markdown files with style guide compliance."""

    # Module definitions for wave-based processing
    WAVES = {
        1: ["module-01", "module-02", "module-03", "module-04", "module-05", "module-06"],
        2: ["module-07", "module-08", "module-09", "module-10", "module-11", "module-12"],
        3: ["module-13", "module-14", "module-15", "module-16", "module-17", "module-18"],
        4: ["module-checkpoint-01", "module-checkpoint-02", "module-checkpoint-03"],
        5: ["module-bonus-01", "module-bonus-02"],
    }

    # File types to translate (markdown only)
    TRANSLATABLE_EXTENSIONS = {".md", ".txt"}

    # Paths to skip during translation
    SKIP_PATTERNS = {
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".venv",
        "node_modules",
        ".gitkeep",
        ".env",
    }

    # Terminology mapping (Spanish → English)
    TERMINOLOGY = {
        "módulo": "module",
        "modulo": "module",
        "ejercicio": "exercise",
        "prerequisito": "prerequisite",
        "objetivo": "objective",
        "contenido": "content",
        "solución": "solution",
        "validación": "validation",
        "resumen": "summary",
        "pasos": "steps",
        "lago de datos": "data lake",
        "lakehouse": "data lakehouse",
        "análisis de costos": "cost analysis",
        "calidad de datos": "data quality",
        "orquestación": "orchestration",
        "tubería": "pipeline",
        "transformación": "transformation",
        "nube": "cloud",
        "contenedor": "container",
        "catálogo de datos": "data catalog",
        "gobernanza": "governance",
        "seguridad": "security",
        "ETL": "ETL",
    }

    def __init__(self, source_dir: str, target_dir: str, api_key: Optional[str] = None):
        """Initialize translation processor."""
        self.source_dir = Path(source_dir)
        self.target_dir = Path(target_dir)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.translated_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.translations: Dict[str, str] = {}

    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        for pattern in self.SKIP_PATTERNS:
            if pattern in path.parts:
                return True
        if path.name.startswith("."):
            return True
        return False

    def _is_translatable(self, path: Path) -> bool:
        """Check if file should be translated."""
        return path.suffix.lower() in self.TRANSLATABLE_EXTENSIONS

    def _extract_code_blocks(self, content: str) -> Tuple[str, Dict[str, str]]:
        """
        Extract code blocks from markdown, replace with placeholders.
        
        Returns:
            (content_with_placeholders, code_blocks_dict)
        """
        code_blocks = {}
        counter = 0

        # Match triple backtick code blocks
        pattern = r"```[\w\-]*\n(.*?)\n```"
        matches = list(re.finditer(pattern, content, re.DOTALL))

        for match in reversed(matches):  # Reverse to maintain positions
            placeholder = f"__CODE_BLOCK_{counter}__"
            code_blocks[placeholder] = match.group(0)
            content = content[:match.start()] + placeholder + content[match.end():]
            counter += 1

        # Match inline code (backticks)
        pattern = r"`([^`]+)`"
        matches = list(re.finditer(pattern, content))

        for match in reversed(matches):
            placeholder = f"__INLINE_CODE_{counter}__"
            code_blocks[placeholder] = match.group(0)
            content = content[:match.start()] + placeholder + content[match.end():]
            counter += 1

        return content, code_blocks

    def _restore_code_blocks(self, content: str, code_blocks: Dict[str, str]) -> str:
        """Restore code blocks from placeholders."""
        for placeholder, code in code_blocks.items():
            content = content.replace(placeholder, code)
        return content

    def _create_translation_prompt(self, content: str) -> str:
        """Create Claude prompt for translation."""
        return f"""You are a professional translator specializing in technical documentation for cloud data engineering.

Your task: Translate the following Spanish markdown content to English.

CRITICAL RULES:
1. Preserve ALL code blocks exactly as-is (do not translate code)
2. Preserve ALL URLs and links
3. Preserve ALL file paths and commands
4. Preserve markdown formatting (headers, lists, bold, italic, etc.)
5. Use the following terminology mapping:
   - módulo/modulo → module
   - ejercicio → exercise
   - prerequisito → prerequisite
   - objetivo → objective/goal
   - lago de datos → data lake
   - análisis de costos → cost analysis
   - calidad de datos → data quality
   - orquestación → orchestration
   - tubería → pipeline
   - transformación → transformation

6. Translate only instructional text, explanations, and descriptions
7. Keep professional, educational tone
8. Do not add explanations or comments—only the translated content

Content to translate:
---
{content}
---

Provide ONLY the translated markdown content, no explanations or metadata."""

    def _translate_content(self, content: str) -> str:
        """Translate content using Claude API."""
        try:
            # Extract code blocks to preserve them
            content_clean, code_blocks = self._extract_code_blocks(content)

            # Create translation prompt
            prompt = self._create_translation_prompt(content_clean)

            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract translated content
            translated = message.content[0].text

            # Restore code blocks
            translated = self._restore_code_blocks(translated, code_blocks)

            return translated

        except Exception as e:
            print(f"Error translating content: {e}", file=sys.stderr)
            raise

    def process_file(self, source_file: Path, target_file: Path) -> bool:
        """Process single file translation."""
        try:
            # Read source file
            with open(source_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Skip if already English or very small
            if len(content) < 50:
                self.skipped_count += 1
                return False

            print(f"Translating: {source_file.relative_to(self.source_dir)}")

            # Translate content
            translated_content = self._translate_content(content)

            # Create target directory if needed
            target_file.parent.mkdir(parents=True, exist_ok=True)

            # Write translated file
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(translated_content)

            self.translated_count += 1
            self.translations[str(source_file)] = str(target_file)
            return True

        except Exception as e:
            print(f"Error processing {source_file}: {e}", file=sys.stderr)
            self.error_count += 1
            return False

    def process_directory(self, source_path: Path, target_path: Path) -> int:
        """Process all translatable files in directory."""
        count = 0

        for source_file in source_path.rglob("*"):
            if self._should_skip(source_file):
                continue

            if not source_file.is_file():
                continue

            if not self._is_translatable(source_file):
                # Copy non-markdown files as-is
                rel_path = source_file.relative_to(source_path)
                target_file = target_path / rel_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                if not target_file.exists():
                    shutil.copy2(source_file, target_file)
                continue

            # Translate markdown file
            rel_path = source_file.relative_to(source_path)
            target_file = target_path / rel_path

            if self.process_file(source_file, target_file):
                count += 1

        return count

    def process_wave(self, wave_num: int) -> None:
        """Process specific wave of modules."""
        if wave_num not in self.WAVES:
            raise ValueError(f"Invalid wave number: {wave_num}")

        module_prefixes = self.WAVES[wave_num]

        print(f"\n=== Processing Wave {wave_num} ===")
        print(f"Modules: {', '.join(module_prefixes)}")

        for prefix in module_prefixes:
            source_modules = list(self.source_dir.glob(f"{prefix}*"))
            for source_module in source_modules:
                if not source_module.is_dir():
                    continue

                module_name = source_module.name
                target_module = self.target_dir / module_name

                print(f"\nProcessing module: {module_name}")
                self.process_directory(source_module, target_module)

    def process_all(self) -> None:
        """Process all 5 waves."""
        for wave in sorted(self.WAVES.keys()):
            self.process_wave(wave)

    def generate_report(self) -> str:
        """Generate translation processing report."""
        report = f"""
Translation Batch Processing Report
====================================

Date: {os.popen("date").read().strip()}

Summary:
--------
Total Files Translated: {self.translated_count}
Files Skipped: {self.skipped_count}
Errors: {self.error_count}

Source Directory: {self.source_dir}
Target Directory: {self.target_dir}

Translation Map:
----------------
"""
        for source, target in sorted(self.translations.items()):
            report += f"  {source} → {target}\n"

        return report

    def save_report(self, output_path: str) -> None:
        """Save report to file."""
        report = self.generate_report()
        with open(output_path, "w") as f:
            f.write(report)
        print(f"\nReport saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Batch translate modules from Spanish to English"
    )
    parser.add_argument(
        "--source",
        default="../training-cloud-data/modules",
        help="Source modules directory",
    )
    parser.add_argument(
        "--target", default="modules", help="Target modules directory"
    )
    parser.add_argument(
        "--wave",
        type=int,
        choices=[1, 2, 3, 4, 5],
        help="Process specific wave only",
    )
    parser.add_argument(
        "--full-scan",
        action="store_true",
        help="Process all 5 waves",
    )
    parser.add_argument(
        "--report",
        default="translation_report.txt",
        help="Output report file",
    )

    args = parser.parse_args()

    # Validate API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    # Initialize processor
    processor = TranslationBatchProcessor(args.source, args.target)

    # Process requested waves
    if args.full_scan:
        processor.process_all()
    elif args.wave:
        processor.process_wave(args.wave)
    else:
        # Default: Wave 1
        processor.process_wave(1)

    # Generate and save report
    print("\n" + processor.generate_report())
    processor.save_report(args.report)


if __name__ == "__main__":
    main()
