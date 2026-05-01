#!/usr/bin/env python3
"""
Module 1 Translation Script (Piloto)

Translates only Module 01: Cloud Fundamentals from Spanish to English.
This serves as a pilot for the full batch translation process.

Usage:
    python scripts/translate_module_1.py

Requires:
    - ANTHROPIC_API_KEY environment variable
    - anthropic package
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

try:
    import anthropic
except ImportError:
    print("Error: anthropic package not found. Install with: pip install anthropic")
    sys.exit(1)


class Module1Translator:
    """Translates only Module 01 files from Spanish to English."""

    # Files to translate in Module 1 (high-priority first)
    FILES_TO_TRANSLATE = [
        # Theory (highest priority - foundation concepts)
        "theory/concepts.md",
        "theory/architecture.md",
        "theory/resources.md",
        # Exercise READMEs and scenarios (clear learning path)
        "exercises/01-s3-basics/README.md",
        "exercises/01-s3-basics/starter/scenario.md",
        "exercises/01-s3-basics/hints.md",
        "exercises/02-iam-policies/README.md",
        "exercises/02-iam-policies/starter/scenario.md",
        "exercises/02-iam-policies/hints.md",
        "exercises/03-s3-advanced/README.md",
        "exercises/03-s3-advanced/starter/scenario.md",
        "exercises/03-s3-advanced/hints.md",
        "exercises/04-lambda-functions/README.md",
        "exercises/04-lambda-functions/starter/scenario.md",
        "exercises/04-lambda-functions/hints.md",
        "exercises/05-infrastructure-as-code/README.md",
        "exercises/05-infrastructure-as-code/starter/scenario.md",
        "exercises/05-infrastructure-as-code/hints.md",
        "exercises/06-cost-optimization/README.md",
        "exercises/06-cost-optimization/starter/scenario.md",
        "exercises/06-cost-optimization/hints.md",
        # Docs
        "docs/localstack-guide.md",
        "docs/troubleshooting.md",
        # Module READMEs
        "README.md",
        "exercises/README.md",
    ]

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.module_1_path = Path(__file__).parent.parent / "modules" / "module-01-cloud-fundamentals"
        self.translations: Dict[str, str] = {}
        self.errors: List[Tuple[str, str]] = []

    def _extract_code_blocks(self, content: str) -> Tuple[str, Dict[str, str]]:
        """Extract code blocks to preserve them."""
        code_blocks = {}
        counter = 0

        # Triple backticks
        pattern = r"```[\w\-]*\n(.*?)\n```"
        for match in list(re.finditer(pattern, content, re.DOTALL))[::-1]:
            placeholder = f"__CODE_{counter}__"
            code_blocks[placeholder] = match.group(0)
            content = content[:match.start()] + placeholder + content[match.end():]
            counter += 1

        # Inline code
        pattern = r"`([^`]+)`"
        for match in list(re.finditer(pattern, content))[::-1]:
            placeholder = f"__INLINE_{counter}__"
            code_blocks[placeholder] = match.group(0)
            content = content[:match.start()] + placeholder + content[match.end():]
            counter += 1

        return content, code_blocks

    def _restore_code_blocks(self, content: str, code_blocks: Dict[str, str]) -> str:
        """Restore code blocks from placeholders."""
        for placeholder, code in code_blocks.items():
            content = content.replace(placeholder, code)
        return content

    def _translate_content(self, content: str) -> str:
        """Translate content using Claude."""
        # Extract code blocks
        content_clean, code_blocks = self._extract_code_blocks(content)

        prompt = f"""You are a professional translator specializing in technical documentation for cloud data engineering.

Translate this Spanish markdown content to English. 

CRITICAL RULES:
1. Preserve ALL code blocks exactly as-is
2. Preserve ALL URLs and links
3. Preserve file paths and commands
4. Preserve markdown formatting
5. Use standard data engineering English terminology

Use these term mappings:
- módulo/modulo → module
- ejercicio → exercise
- prerequisito → prerequisite
- objetivo → objective/goal
- escenario → scenario
- paso → step
- pista → hint
- solución → solution

Content to translate:
---
{content_clean}
---

Provide ONLY the translated content, no explanations."""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )

        translated = message.content[0].text
        translated = self._restore_code_blocks(translated, code_blocks)
        return translated

    def translate_file(self, relative_path: str) -> bool:
        """Translate a single file."""
        try:
            file_path = self.module_1_path / relative_path
            if not file_path.exists():
                print(f"⚠️  SKIP: {relative_path} (not found)")
                return False

            print(f"📖 Translating: {relative_path}", end=" ... ")

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Skip very short files
            if len(content) < 50:
                print("SKIP (too short)")
                return False

            # Translate
            translated = self._translate_content(content)

            # Write back
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(translated)

            self.translations[relative_path] = file_path
            print("✅ DONE")
            return True

        except Exception as e:
            error_msg = f"{relative_path}: {str(e)}"
            self.errors.append((relative_path, str(e)))
            print(f"❌ ERROR: {e}")
            return False

    def translate_all(self) -> None:
        """Translate all files in Module 1."""
        print("\n" + "=" * 70)
        print("MODULE 1 TRANSLATION PILOT")
        print("=" * 70)
        print(f"Module Path: {self.module_1_path}")
        print(f"Total Files: {len(self.FILES_TO_TRANSLATE)}")
        print("=" * 70 + "\n")

        success_count = 0
        for relative_path in self.FILES_TO_TRANSLATE:
            if self.translate_file(relative_path):
                success_count += 1

        print("\n" + "=" * 70)
        print(f"SUMMARY: {success_count}/{len(self.FILES_TO_TRANSLATE)} files translated")
        if self.errors:
            print(f"ERRORS: {len(self.errors)}")
            for file_path, error in self.errors:
                print(f"  - {file_path}: {error}")
        print("=" * 70)

        # Save report
        self._save_report(success_count)

    def _save_report(self, success_count: int) -> None:
        """Save translation report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "module": "module-01-cloud-fundamentals",
            "total_files": len(self.FILES_TO_TRANSLATE),
            "successful": success_count,
            "failed": len(self.errors),
            "translations": self.translations,
            "errors": {file: error for file, error in self.errors},
        }

        report_path = self.module_1_path.parent.parent / "module_1_translation_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n📋 Report saved: {report_path}")


def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Error: ANTHROPIC_API_KEY not set")
        print("   export ANTHROPIC_API_KEY='sk-...'")
        sys.exit(1)

    try:
        translator = Module1Translator()
        translator.translate_all()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
