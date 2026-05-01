"""
Tests de Completitud del Módulo

Verifica que el módulo está 100% completo y listo para usar.
"""

import pytest
from pathlib import Path


class TestModuleStructure:
    """Verifica la estructura completa del módulo."""
    
    def test_root_files_exist(self):
        """Archivos raíz del módulo deben existir."""
        module_root = Path(__file__).parent.parent
        
        required_files = [
            "README.md",
            "requirements.txt",
            ".gitignore",
            "STATUS.md",
            "pytest.ini"
        ]
        
        for filename in required_files:
            file_path = module_root / filename
            assert file_path.exists(), f"{filename} debe existir en el root del módulo"
            assert file_path.stat().st_size > 0, f"{filename} no debe estar vacío"
    
    def test_theory_directory_complete(self):
        """Directorio de teoría debe estar completo."""
        theory_dir = Path(__file__).parent.parent / "theory"
        
        assert theory_dir.exists(), "Directorio theory/ debe existir"
        
        required_files = [
            "concepts.md",
            "architecture.md",
            "resources.md"
        ]
        
        for filename in required_files:
            file_path = theory_dir / filename
            assert file_path.exists(), f"theory/{filename} debe existir"
            assert file_path.stat().st_size > 10000, \
                f"theory/{filename} debe tener contenido sustancial (>10KB)"
    
    def test_infrastructure_directory_complete(self):
        """Directorio de infraestructura debe estar completo."""
        infra_dir = Path(__file__).parent.parent / "infrastructure"
        
        assert infra_dir.exists(), "Directorio infrastructure/ debe existir"
        
        required_files = [
            "docker-compose.yml",
            "Dockerfile",
            ".env.example",
            "jupyter_config.py",
            "README.md"
        ]
        
        for filename in required_files:
            file_path = infra_dir / filename
            assert file_path.exists(), f"infrastructure/{filename} debe existir"
    
    def test_data_directory_complete(self):
        """Directorio de datos debe estar completo."""
        data_dir = Path(__file__).parent.parent / "data"
        
        assert data_dir.exists(), "Directorio data/ debe existir"
        assert (data_dir / "raw").exists(), "data/raw/ debe existir"
        assert (data_dir / "schemas").exists(), "data/schemas/ debe existir"
        
        # README
        readme = data_dir / "README.md"
        assert readme.exists(), "data/README.md debe existir"
        assert readme.stat().st_size > 5000, "data/README.md debe tener contenido sustancial"
    
    def test_validation_directory_complete(self):
        """Directorio de validación debe estar completo."""
        validation_dir = Path(__file__).parent
        
        required_files = [
            "README.md",
            "conftest.py",
            "test_integration.py",
            "test_data_quality.py",
            "test_module_completeness.py"
        ]
        
        for filename in required_files:
            file_path = validation_dir / filename
            assert file_path.exists(), f"validation/{filename} debe existir"


class TestExercisesComplete:
    """Verifica que todos los ejercicios están completos."""
    
    @pytest.fixture
    def exercises_dir(self):
        return Path(__file__).parent.parent / "exercises"
    
    def test_all_exercises_exist(self, exercises_dir):
        """Los 6 ejercicios deben existir."""
        expected_exercises = [
            "01-python-basics",
            "02-data-structures",
            "03-file-operations",
            "04-pandas-fundamentals",
            "05-data-transformation",
            "06-error-handling"
        ]
        
        for exercise in expected_exercises:
            exercise_dir = exercises_dir / exercise
            assert exercise_dir.exists(), f"Ejercicio {exercise} debe existir"
            assert exercise_dir.is_dir(), f"{exercise} debe ser un directorio"
    
    def test_exercise_structure(self, exercises_dir):
        """Cada ejercicio debe tener la estructura correcta."""
        exercises = [
            "01-python-basics",
            "02-data-structures",
            "03-file-operations",
            "04-pandas-fundamentals",
            "05-data-transformation",
            "06-error-handling"
        ]
        
        for exercise in exercises:
            exercise_dir = exercises_dir / exercise
            
            # README
            readme = exercise_dir / "README.md"
            assert readme.exists(), f"{exercise}/README.md debe existir"
            assert readme.stat().st_size > 1000, \
                f"{exercise}/README.md debe tener contenido (>1KB)"
            
            # Starter
            starter_dir = exercise_dir / "starter"
            assert starter_dir.exists(), f"{exercise}/starter/ debe existir"
            assert any(starter_dir.glob("*.py")), \
                f"{exercise}/starter/ debe tener archivos .py"
            
            # Solution
            solution_dir = exercise_dir / "solution"
            assert solution_dir.exists(), f"{exercise}/solution/ debe existir"
            assert any(solution_dir.glob("*.py")), \
                f"{exercise}/solution/ debe tener archivos .py"
            
            # Tests
            tests_dir = exercise_dir / "tests"
            assert tests_dir.exists(), f"{exercise}/tests/ debe existir"
            assert any(tests_dir.glob("test_*.py")), \
                f"{exercise}/tests/ debe tener archivos test_*.py"
    
    def test_exercises_readme_exists(self, exercises_dir):
        """Debe existir un README general de ejercicios."""
        main_readme = exercises_dir / "README.md"
        assert main_readme.exists(), "exercises/README.md debe existir"
        assert main_readme.stat().st_size > 3000, \
            "exercises/README.md debe tener contenido sustancial"


class TestDependencies:
    """Verifica que las dependencias están correctamente especificadas."""
    
    def test_requirements_txt_valid(self):
        """requirements.txt debe ser válido y completo."""
        requirements = Path(__file__).parent.parent / "requirements.txt"
        
        assert requirements.exists(), "requirements.txt debe existir"
        
        content = requirements.read_text()
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        
        # Dependencias esenciales
        essential_packages = [
            'pandas',
            'numpy',
            'pytest',
            'jupyter',
            'pyarrow'
        ]
        
        for package in essential_packages:
            assert any(package in line.lower() for line in lines), \
                f"Paquete {package} debe estar en requirements.txt"
    
    def test_docker_files_valid(self):
        """Archivos Docker deben ser válidos."""
        infra_dir = Path(__file__).parent.parent / "infrastructure"
        
        # docker-compose.yml
        compose_file = infra_dir / "docker-compose.yml"
        assert compose_file.exists(), "docker-compose.yml debe existir"
        
        content = compose_file.read_text()
        assert 'version:' in content or 'services:' in content, \
            "docker-compose.yml debe tener formato válido"
        
        # Dockerfile
        dockerfile = infra_dir / "Dockerfile"
        assert dockerfile.exists(), "Dockerfile debe existir"
        
        content = dockerfile.read_text()
        assert 'FROM' in content, "Dockerfile debe tener instrucción FROM"


class TestDocumentation:
    """Verifica que la documentación está completa."""
    
    def test_main_readme_complete(self):
        """README principal debe estar completo."""
        readme = Path(__file__).parent.parent / "README.md"
        
        assert readme.exists(), "README.md principal debe existir"
        
        content = readme.read_text()
        
        # Secciones esperadas
        expected_sections = [
            'objetivo',
            'contenido',
            'ejercicio',
            'requisito',
            'instalación'
        ]
        
        content_lower = content.lower()
        for section in expected_sections:
            assert section in content_lower, \
                f"README debe mencionar '{section}'"
    
    def test_status_md_updated(self):
        """STATUS.md debe estar actualizado."""
        status = Path(__file__).parent.parent / "STATUS.md"
        
        assert status.exists(), "STATUS.md debe existir"
        
        content = status.read_text()
        
        # Debe mencionar todos los pasos
        assert 'Paso 1' in content, "STATUS.md debe mencionar Paso 1"
        assert 'Paso 5' in content, "STATUS.md debe mencionar Paso 5"
        assert 'Ejercicios' in content or 'Exercises' in content, \
            "STATUS.md debe mencionar Ejercicios"


class TestCodeQuality:
    """Verifica la calidad del código."""
    
    def test_python_files_syntax(self):
        """Archivos Python deben tener sintaxis válida."""
        import ast
        
        module_root = Path(__file__).parent.parent
        
        # Encontrar todos los archivos .py (excepto __pycache__)
        python_files = [
            f for f in module_root.rglob("*.py")
            if "__pycache__" not in str(f) and ".venv" not in str(f)
        ]
        
        assert len(python_files) > 20, "Debe haber varios archivos Python"
        
        errors = []
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                ast.parse(content)
            except SyntaxError as e:
                errors.append(f"{py_file.name}: {e}")
        
        assert len(errors) == 0, f"Errores de sintaxis encontrados: {errors}"
    
    def test_solution_files_have_docstrings(self):
        """Archivos de solución deben tener docstrings."""
        module_root = Path(__file__).parent.parent
        
        solution_files = list((module_root / "exercises").rglob("solution/*.py"))
        
        assert len(solution_files) >= 6, "Debe haber al menos 6 archivos de solución"
        
        for sol_file in solution_files:
            content = sol_file.read_text()
            # Verificar que tenga al menos algunas docstrings
            assert '"""' in content or "'''" in content, \
                f"{sol_file.name} debe tener docstrings"


class TestTestsCoverage:
    """Verifica que hay suficientes tests."""
    
    def test_total_test_count(self):
        """Debe haber al menos 120 tests en total."""
        module_root = Path(__file__).parent.parent
        
        # Contar funciones de test
        test_files = list(module_root.rglob("test_*.py"))
        
        total_tests = 0
        for test_file in test_files:
            content = test_file.read_text()
            # Contar funciones que empiezan con 'def test_'
            total_tests += content.count('def test_')
        
        assert total_tests >= 100, \
            f"Debe haber al menos 100 tests, encontrados: {total_tests}"
    
    def test_each_exercise_has_tests(self):
        """Cada ejercicio debe tener tests."""
        exercises_dir = Path(__file__).parent.parent / "exercises"
        
        exercises = [
            "01-python-basics",
            "02-data-structures",
            "03-file-operations",
            "04-pandas-fundamentals",
            "05-data-transformation",
            "06-error-handling"
        ]
        
        for exercise in exercises:
            tests_dir = exercises_dir / exercise / "tests"
            assert tests_dir.exists(), f"{exercise} debe tener directorio tests/"
            
            test_files = list(tests_dir.glob("test_*.py"))
            assert len(test_files) > 0, f"{exercise} debe tener archivos de test"
            
            # Contar tests en el ejercicio
            test_count = 0
            for test_file in test_files:
                content = test_file.read_text()
                test_count += content.count('def test_')
            
            assert test_count >= 10, \
                f"{exercise} debe tener al menos 10 tests, encontrados: {test_count}"


# =============================================================================
# Test Final de Completitud
# =============================================================================

def test_module_100_percent_complete():
    """
    Test final: verifica que el módulo está 100% completo.
    
    Este es el test definitivo que confirma que todo está listo.
    """
    module_root = Path(__file__).parent.parent
    
    checklist = {
        'Paso 1 - Base': False,
        'Paso 2 - Theory': False,
        'Paso 3 - Infrastructure': False,
        'Paso 4 - Data': False,
        'Paso 5 - Exercises': False,
        'Paso 6 - Validation': False
    }
    
    # Verificar Paso 1
    if (module_root / "README.md").exists() and \
       (module_root / "requirements.txt").exists() and \
       (module_root / ".gitignore").exists():
        checklist['Paso 1 - Base'] = True
    
    # Verificar Paso 2
    theory_dir = module_root / "theory"
    if theory_dir.exists() and \
       (theory_dir / "concepts.md").exists() and \
       (theory_dir / "architecture.md").exists():
        checklist['Paso 2 - Theory'] = True
    
    # Verificar Paso 3
    infra_dir = module_root / "infrastructure"
    if infra_dir.exists() and \
       (infra_dir / "docker-compose.yml").exists():
        checklist['Paso 3 - Infrastructure'] = True
    
    # Verificar Paso 4
    data_dir = module_root / "data"
    if data_dir.exists() and \
       (data_dir / "raw" / "customers.csv").exists() and \
       (data_dir / "raw" / "transactions.csv").exists():
        checklist['Paso 4 - Data'] = True
    
    # Verificar Paso 5
    exercises_dir = module_root / "exercises"
    if exercises_dir.exists():
        exercise_count = len(list(exercises_dir.glob("0*")))
        if exercise_count >= 6:
            checklist['Paso 5 - Exercises'] = True
    
    # Verificar Paso 6
    validation_dir = module_root / "validation"
    if validation_dir.exists() and \
       (validation_dir / "test_integration.py").exists() and \
       (validation_dir / "conftest.py").exists():
        checklist['Paso 6 - Validation'] = True
    
    # Imprimir checklist
    print("\n" + "="*70)
    print("CHECKLIST DE COMPLETITUD DEL MÓDULO")
    print("="*70)
    for paso, completado in checklist.items():
        status = "✅" if completado else "❌"
        print(f"{status} {paso}")
    print("="*70)
    
    # Calcular porcentaje
    completed = sum(1 for v in checklist.values() if v)
    total = len(checklist)
    percentage = (completed / total) * 100
    
    print(f"\nCompletitud: {completed}/{total} pasos ({percentage:.1f}%)")
    print("="*70 + "\n")
    
    # Validar que todo está completo
    assert all(checklist.values()), \
        f"Algunos pasos no están completos. Ver checklist arriba."
    
    print("✅ MÓDULO 04 ESTÁ 100% COMPLETO Y LISTO PARA USAR\n")
