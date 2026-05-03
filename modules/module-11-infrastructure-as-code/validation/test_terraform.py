"""
Tests de validación para configuraciones de Terraform
"""

import pytest
import os
import subprocess
import re


class TestTerraformSyntax:
    """Tests de sintaxis y validación de Terraform"""

    def test_terraform_installed(self):
        """Verificar que Terraform está instalado"""
        result = subprocess.run(
            ["terraform", "version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, "Terraform no está instalado"
        assert "Terraform v" in result.stdout, "Versión de Terraform no detectada"

    @pytest.mark.terraform
    def test_exercises_have_readme(self, exercises_dir):
        """Verificar que cada ejercicio tiene README"""
        exercises = [d for d in os.listdir(exercises_dir)
                    if os.path.isdir(os.path.join(exercises_dir, d))
                    and not d.startswith('.')]

        for exercise in exercises:
            readme_path = os.path.join(exercises_dir, exercise, "README.md")
            assert os.path.exists(readme_path), \
                f"Ejercicio {exercise} no tiene README.md"

            # Verificar que README no está vacío
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert len(content) > 100, \
                    f"README de {exercise} parece incompleto (< 100 chars)"

    @pytest.mark.terraform
    def test_terraform_files_syntax(self, infrastructure_dir):
        """Verificar sintaxis de archivos .tf"""
        modules_dir = os.path.join(infrastructure_dir, "modules")

        if not os.path.exists(modules_dir):
            pytest.skip("No hay módulos para validar")

        for module in os.listdir(modules_dir):
            module_path = os.path.join(modules_dir, module)
            if not os.path.isdir(module_path):
                continue

            # Verificar que tiene archivos .tf
            tf_files = [f for f in os.listdir(module_path) if f.endswith('.tf')]
            if not tf_files:
                continue

            # Terraform fmt check
            result = subprocess.run(
                ["terraform", "fmt", "-check", "-recursive", module_path],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, \
                f"Módulo {module} no está formateado correctamente:\n{result.stdout}"


class TestModuleStructure:
    """Tests de estructura de módulos"""

    def test_module_has_required_files(self, infrastructure_dir):
        """Verificar que módulos tienen archivos requeridos"""
        modules_dir = os.path.join(infrastructure_dir, "modules")

        if not os.path.exists(modules_dir):
            pytest.skip("No hay directorio de módulos")

        modules = [d for d in os.listdir(modules_dir)
                  if os.path.isdir(os.path.join(modules_dir, d))
                  and not d.startswith('.')]

        required_files = ["main.tf", "variables.tf", "outputs.tf"]

        for module in modules:
            module_path = os.path.join(modules_dir, module)

            # Verificar archivos requeridos
            for required_file in required_files:
                file_path = os.path.join(module_path, required_file)
                assert os.path.exists(file_path), \
                    f"Módulo {module} debe tener {required_file}"

    def test_module_has_readme(self, infrastructure_dir):
        """Verificar que módulos tienen README"""
        modules_dir = os.path.join(infrastructure_dir, "modules")

        if not os.path.exists(modules_dir):
            pytest.skip("No hay directorio de módulos")

        modules = [d for d in os.listdir(modules_dir)
                  if os.path.isdir(os.path.join(modules_dir, d))
                  and not d.startswith('.')]

        for module in modules:
            readme_path = os.path.join(modules_dir, module, "README.md")
            assert os.path.exists(readme_path), \
                f"Módulo {module} debe tener README.md"


class TestDocumentation:
    """Tests de documentación"""

    def test_theory_files_exist(self, theory_dir):
        """Verificar que archivos de teoría existen"""
        expected_files = [
            "01-terraform-fundamentals.md",
            "02-terraform-advanced.md",
            "03-iac-patterns.md"
        ]

        for file in expected_files:
            file_path = os.path.join(theory_dir, file)
            assert os.path.exists(file_path), \
                f"Archivo de teoría faltante: {file}"

            # Verificar contenido mínimo
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert len(content) > 1000, \
                    f"Archivo {file} parece incompleto (< 1000 chars)"

    def test_main_readme_exists(self, module_root):
        """Verificar que README principal existe"""
        readme_path = os.path.join(module_root, "README.md")
        assert os.path.exists(readme_path), "README.md principal faltante"

        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()

            # Verificar secciones clave
            assert "Terraform" in content or "terraform" in content
            assert "ejercicio" in content.lower() or "exercise" in content.lower()


class TestTerraformConfiguration:
    """Tests de configuración de Terraform"""

    @pytest.mark.terraform
    def test_no_hardcoded_secrets(self, infrastructure_dir):
        """Verificar que no hay secrets hardcodeados"""
        modules_dir = os.path.join(infrastructure_dir, "modules")

        if not os.path.exists(modules_dir):
            pytest.skip("No hay módulos")

        # Patrones sospechosos
        patterns = [
            r'password\s*=\s*["\'][^"\']{6,}["\']',
            r'secret\s*=\s*["\'][^"\']{6,}["\']',
            r'access_key\s*=\s*["\']AK[A-Z0-9]+["\']',
            r'secret_key\s*=\s*["\'][^"\']{20,}["\']',
        ]

        for root, dirs, files in os.walk(modules_dir):
            for file in files:
                if not file.endswith('.tf'):
                    continue

                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                    for pattern in patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        assert not matches, \
                            f"Posible secret hardcodeado en {file_path}: {matches}"

    @pytest.mark.terraform
    def test_providers_have_version_constraints(self, infrastructure_dir):
        """Verificar que providers tienen version constraints"""
        modules_dir = os.path.join(infrastructure_dir, "modules")

        if not os.path.exists(modules_dir):
            pytest.skip("No hay módulos")

        for root, dirs, files in os.walk(modules_dir):
            for file in files:
                if file == "versions.tf" or file == "main.tf":
                    file_path = os.path.join(root, file)

                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                        # Si define providers, debe tener version
                        if "required_providers" in content:
                            # Verificar que tiene version constraint
                            assert re.search(r'version\s*=\s*["\']', content), \
                                f"{file_path} debe especificar version de provider"


class TestScripts:
    """Tests de scripts"""

    def test_scripts_are_executable(self, module_root):
        """Verificar que scripts son ejecutables"""
        scripts_dir = os.path.join(module_root, "scripts")

        if not os.path.exists(scripts_dir):
            pytest.skip("No hay directorio de scripts")

        scripts = [f for f in os.listdir(scripts_dir) if f.endswith('.sh')]

        for script in scripts:
            script_path = os.path.join(scripts_dir, script)
            assert os.access(script_path, os.X_OK), \
                f"Script {script} no es ejecutable (ejecuta: chmod +x {script_path})"

    def test_scripts_have_shebang(self, module_root):
        """Verificar que scripts tienen shebang"""
        scripts_dir = os.path.join(module_root, "scripts")

        if not os.path.exists(scripts_dir):
            pytest.skip("No hay scripts")

        scripts = [f for f in os.listdir(scripts_dir) if f.endswith('.sh')]

        for script in scripts:
            script_path = os.path.join(scripts_dir, script)

            with open(script_path, 'r') as f:
                first_line = f.readline()
                assert first_line.startswith('#!'), \
                    f"Script {script} debe empezar con shebang (#!/bin/bash)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
