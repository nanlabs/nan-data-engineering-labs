# Exercise 02: Validation Rules

⏱️ **Estimated duration:** 2 hours
⭐⭐ **Difficulty:** Basic-Intermediate

## 🎯 Goals

- Implement custom validation rules
- Validar formatos (emails, phones, dates)
- Validar rangos y dominios de valores
- Validar integridad referencial
- Validar reglas de negocio
- Create a reusable validation framework

## 📚 Conceptos Clave

- **Validation Rules**: Rules that the data must comply with
- **Schema Validation**: Structure and type validation
- **Business Rules**: Domain specific rules
- **Referential Integrity**: Relaciones entre tables
- **Data Contracts**: Agreements on data quality

## 📝 Exercises

### Part 1: Basic Validations

**Task 1.1: Validar Nulls**

```python
def validate_not_null(df: pd.DataFrame, columns: list) -> dict:
    """
    Valida que columnas no tengan nulls.

    Returns:
        dict con resultados: {'passed': bool, 'violations': list}
    """
    violations = []

    for col in columns:
        null_count = df[col].isna().sum()
        if null_count > 0:
            violations.append({
                'column': col,
                'issue': 'null_values',
                'count': null_count,
                'percentage': (null_count / len(df)) * 100
            })

    return {
        'passed': len(violations) == 0,
        'violations': violations
    }
```

**Task 1.2: Validar Formatos**

```python
import re

def validate_email_format(df: pd.DataFrame, column: str) -> dict:
    """Valida formato de emails."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    invalid = df[~df[column].str.match(email_pattern, na=False)]

    return {
        'passed': len(invalid) == 0,
        'violations': invalid[[column]].to_dict('records') if len(invalid) > 0 else []
    }

def validate_phone_format(df: pd.DataFrame, column: str, min_length: int = 10) -> dict:
    """Valida formato de teléfonos."""
    # TODO: Implementar
    # Eliminar caracteres no numéricos
    # Validar longitud mínima
    pass

def validate_date_format(df: pd.DataFrame, column: str, format: str = '%Y-%m-%d') -> dict:
    """Valida formato de fechas."""
    # TODO: Implementar
    pass
```

**Task 1.3: Validar Rangos**

```python
def validate_range(df: pd.DataFrame, column: str, min_val=None, max_val=None) -> dict:
    """Valida que valores estén en rango."""
    violations = []

    if min_val is not None:
        below_min = df[df[column] < min_val]
        if len(below_min) > 0:
            violations.extend([
                {'value': row[column], 'issue': f'below_min_{min_val}'}
                for _, row in below_min.iterrows()
            ])

    if max_val is not None:
        above_max = df[df[column] > max_val]
        if len(above_max) > 0:
            violations.extend([
                {'value': row[column], 'issue': f'above_max_{max_val}'}
                for _, row in above_max.iterrows()
            ])

    return {
        'passed': len(violations) == 0,
        'violations': violations
    }

# Uso
result = validate_range(transactions, 'amount', min_val=0, max_val=1000000)
```

**Task 1.4: Validar Dominios**

```python
def validate_in_domain(df: pd.DataFrame, column: str, valid_values: list) -> dict:
    """Valida que valores estén en dominio permitido."""
    # TODO: Implementar
    # Encontrar valores no en valid_values
    # Retornar violations con valores inválidos
    pass

# Uso
valid_statuses = ['active', 'inactive', 'suspended', 'pending']
result = validate_in_domain(customers, 'account_status', valid_statuses)
```

---

### Parte 2: Validaciones de Integridad

**Task 2.1: Unicidad**

```python
def validate_uniqueness(df: pd.DataFrame, columns: list) -> dict:
    """Valida que combinación de columnas sea única."""
    duplicates = df[df.duplicated(subset=columns, keep=False)]

    return {
        'passed': len(duplicates) == 0,
        'duplicate_count': len(duplicates),
        'violations': duplicates[columns].to_dict('records') if len(duplicates) > 0 else []
    }
```

**Task 2.2: Integridad Referencial**

```python
def validate_foreign_key(
    child_df: pd.DataFrame,
    parent_df: pd.DataFrame,
    foreign_key: str,
    primary_key: str
) -> dict:
    """
    Valida integridad referencial entre tablas.

    Example:
        validate_foreign_key(
            transactions, customers,
            'customer_id', 'customer_id'
        )
    """
    # TODO: Implementar
    # 1. Obtener IDs válidos de parent
    # 2. Encontrar child records con FK no en parent
    # 3. Retornar orphan records
    pass

# Uso
result = validate_foreign_key(
    transactions, customers,
    'customer_id', 'customer_id'
)
```

---

### Parte 3: Reglas de Negocio

**Task 3.1: Logical Validations**

```python
class BusinessRuleValidator:
    """Validador de reglas de negocio."""

    @staticmethod
    def validate_dates_logical_order(df: pd.DataFrame,
                                     earlier_col: str,
                                     later_col: str) -> dict:
        """Valida que earlier_date < later_date."""
        df_copy = df.copy()
        df_copy[earlier_col] = pd.to_datetime(df_copy[earlier_col])
        df_copy[later_col] = pd.to_datetime(df_copy[later_col])

        violations = df_copy[df_copy[earlier_col] > df_copy[later_col]]

        return {
            'passed': len(violations) == 0,
            'violations': violations[[earlier_col, later_col]].to_dict('records')
        }

    @staticmethod
    def validate_calculated_field(df: pd.DataFrame,
                                  field: str,
                                  formula: callable) -> dict:
        """
        Valida que campo calculado sea correcto.

        Example:
            validate_calculated_field(
                transactions,
                'total',
                lambda row: row['amount'] * row['quantity']
            )
        """
        # TODO: Implementar
        # Calcular expected value
        # Comparar con actual value
        # Retornar discrepancias
        pass

    @staticmethod
    def validate_business_constraint(df: pd.DataFrame,
                                    constraint_func: callable,
                                    constraint_name: str) -> dict:
        """
        Valida constraint arbitrario.

        Example:
            validate_business_constraint(
                products,
                lambda row: row['price'] > row['cost'],
                'price_greater_than_cost'
            )
        """
        # TODO: Implementar
        pass
```

---

### Part 4: Validation Framework


**Task 4.1: Validation Engine**

```python
from dataclasses import dataclass
from typing import Callable, List, Dict, Any

@dataclass
class ValidationRule:
    """Define una regla de validation."""
    name: str
    description: str
    severity: str  # 'critical', 'warning', 'info'
    validator: Callable
    columns: List[str] = None

class ValidationEngine:
    """Motor de validation extensible."""

    def __init__(self):
        self.rules = []
        self.results = []

    def add_rule(self, rule: ValidationRule):
        """Agrega regla de validation."""
        self.rules.append(rule)
        return self

    def validate(self, df: pd.DataFrame) -> Dict:
        """Ejecuta todas las validaciones."""
        self.results = []

        for rule in self.rules:
            try:
                result = rule.validator(df)
                self.results.append({
                    'rule': rule.name,
                    'severity': rule.severity,
                    'passed': result['passed'],
                    'violations': result.get('violations', [])
                })
            except Exception as e:
                self.results.append({
                    'rule': rule.name,
                    'severity': 'error',
                    'passed': False,
                    'error': str(e)
                })

        return self._generate_summary()

    def _generate_summary(self) -> Dict:
        """Genera resumen de validaciones."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed

        critical_failures = [r for r in self.results
                           if not r['passed'] and r['severity'] == 'critical']

        return {
            'total_rules': total,
            'passed': passed,
            'failed': failed,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'critical_failures': len(critical_failures),
            'results': self.results,
            'overall_passed': len(critical_failures) == 0
        }

    def print_report(self):
        """Imprime reporte de validaciones."""
        summary = self._generate_summary()

        print("=" * 70)
        print("VALIDATION REPORT")
        print("=" * 70)
        print(f"Total Rules: {summary['total_rules']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Critical Failures: {summary['critical_failures']}")
        print()

        for result in self.results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"{status} [{result['severity'].upper()}] {result['rule']}")

            if not result['passed'] and result.get('violations'):
                violations = result['violations']
                if len(violations) <= 5:
                    for v in violations:
                        print(f"    {v}")
                else:
                    print(f"    {len(violations)} violations (showing first 5):")
                    for v in violations[:5]:
                        print(f"    {v}")

        print("=" * 70)
```

**Task 4.2: Usar el Framework**

```python
# Definir reglas
engine = ValidationEngine()

# Regla 1: Nulls críticos
engine.add_rule(ValidationRule(
    name="no_null_customer_id",
    description="customer_id no puede ser null",
    severity="critical",
    validator=lambda df: validate_not_null(df, ['customer_id'])
))

# Regla 2: Email format
engine.add_rule(ValidationRule(
    name="valid_email_format",
    description="Emails deben tener formato válido",
    severity="critical",
    validator=lambda df: validate_email_format(df, 'email')
))

# Regla 3: Amount range
engine.add_rule(ValidationRule(
    name="amount_in_range",
    description="Amount debe estar entre 0 y 1M",
    severity="critical",
    validator=lambda df: validate_range(df, 'amount', min_val=0, max_val=1000000)
))

# Regla 4: Foreign key integrity
engine.add_rule(ValidationRule(
    name="valid_customer_reference",
    description="customer_id debe existir en tabla customers",
    severity="critical",
    validator=lambda df: validate_foreign_key(
        df, customers, 'customer_id', 'customer_id'
    )
))

# Ejecutar validaciones
summary = engine.validate(transactions)
engine.print_report()

# Decidir si proceder
if not summary['overall_passed']:
    print("\n⚠️ Critical validations failed. Pipeline stopped.")
    raise ValidationException("Data quality validation failed")
else:
    print("\n✅ All validations passed. Proceeding to next step.")
```

---

## ✅ Success Criteria

- [ ] Implementaste validaciones de nulls, formatos, rangos
- [ ] Validaste integridad referencial entre tables
- [ ] Creaste reglas de negocio personalizadas
- [ ] Implementaste el ValidationEngine framework
- [ ] You generated validation reports
- [ ] All validations pass in clean data

## 🎓 Conceptos Aprendidos

- Schema validation
- Format validation (regex)
- Range and domain validation
- Referential integrity
- Business rules
- Validation frameworks

## ➡️ Next Exercise

**Exercise 03: Great Expectations** - Usar framework empresarial para validaciones
