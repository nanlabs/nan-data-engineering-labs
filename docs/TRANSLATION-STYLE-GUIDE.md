# Translation Style Guide: Spanish → English

**Purpose**: Standardize terminology and translation patterns for nan-data-engineering-labs across all 23 modules.

**Scope**: All instructional content, governance, and documentation. Code comments and output examples must remain in English unless explicitly part of localized instructional blocks.

**Quality Gate**: After translation, all module content must pass `validate_english_content.py --full-scan` with zero findings.

---

## Core Terminology Mapping

### Module and Learning Structure

| Spanish | English | Context | Example |
|---------|---------|---------|---------|
| **módulo** | **module** | Refers to numbered learning units (01-18 regular, checkpoints, bonus) | "Módulo 01: Fundamentos" → "Module 01: Cloud Fundamentals" |
| **ejercicio** | **exercise** | Numbered labs within a module (exercise 01-06 per module) | "Ejercicio 3: Análisis de Datos" → "Exercise 3: Data Analysis" |
| **prerequisito** | **prerequisite** | Learning dependencies or prior knowledge | "Prerequisitos: Módulo 02, Python basics" |
| **objetivo** | **learning objective** or **goal** | Statement of intent per module/section | "El objetivo es..." → "The goal is..." |
| **contenido** | **content** or **section** | Instructional blocks, theory, or narrative | "Contenido del módulo" → "Module content" |
| **solución** | **solution** or **answer** | Exercise solutions and hints | "Ver solución" → "See solution" |
| **validación** | **validation** or **assessment** | Testing and verification framework | "Validación de datos" → "Data validation" |

### Data Engineering Concepts

| Spanish | English | Context | Notes |
|---------|---------|---------|-------|
| **almacenamiento** | **storage** | Cloud storage systems (S3, GCS, etc.) | Use "object storage" when specifically S3-like |
| **base de datos** | **database** | SQL/NoSQL databases | "Relational database", "data warehouse" per type |
| **lago de datos** | **data lake** | Unstructured/raw data repository | Capitalized: "Data Lake" in headings |
| **data lakehouse** | **data lakehouse** | Hybrid architecture (preserve term) | Hybrid of lake + warehouse; already English |
| **ETL** | **ETL** | Extract, Transform, Load (preserve acronym) | Spell out once per document: "ETL (Extract, Transform, Load)" |
| **análisis de costos** | **cost analysis** | FinOps and billing | "Cost optimization", "cost tracking" as variants |
| **calidad de datos** | **data quality** | Validation and anomaly detection | "Quality checks", "quality gates", "quality metrics" |
| **orquestación** | **orchestration** | Workflow and job scheduling | "Workflow orchestration", "job orchestration" |
| **tubería** | **pipeline** | Data processing workflow | "Data pipeline", "ETL pipeline", "ML pipeline" per context |
| **transformación** | **transformation** | Data processing step | "Transform" (verb), "Transformation" (noun) |
| **nube** / **en la nube** | **cloud** / **in the cloud** | Cloud platform context | "Cloud provider", "cloud infrastructure" |
| **contenedor** | **container** | Docker/Kubernetes units | "Containerization", "container registry" |
| **catálogo de datos** | **data catalog** | Metadata and discovery tool | "Data Catalog" (capitalized as proper noun) |
| **gobernanza** | **governance** | Data governance policies | "Data governance", "governance framework" |
| **seguridad** | **security** | Data protection and access control | "Security best practices", "security policies" |

### Infrastructure and Tools

| Spanish | English | Context | Notes |
|---------|---------|---------|-------|
| **script** | **script** | Python/shell automation files | Preserve as-is in code references |
| **flujo de trabajo** | **workflow** | Automation workflows (Airflow DAGs, etc.) | "Workflow orchestration", "CI/CD workflow" |
| **variable de entorno** | **environment variable** | Config parameters | "Set environment variables" |
| **configuración** | **configuration** or **config** | Setup and parameters | "Configuration file", "config section" |
| **instalación** | **installation** or **setup** | Setup process | "Installation guide", "Setup instructions" |
| **dependencia** | **dependency** | Library/package requirement | "Python dependencies", "external dependencies" |
| **versión** | **version** | Software/schema versioning | "Version control", "versioning strategy" |
| **rama** | **branch** | Git branch | "Feature branch", "main branch" (preserve Git terms) |
| **confirmación** | **commit** | Git commit (preserve as standard term) | Use "commit" in Git contexts |

### File and Folder Structure

| Spanish | English | Context | Notes |
|---------|---------|---------|-------|
| **teoría** | **theory** | Conceptual content folder | Preserve folder name as `theory/` |
| **ejercicios** | **exercises** | Hands-on labs folder | Preserve folder name as `exercises/` |
| **validación** | **validation** | Testing/verification folder | Preserve folder name as `validation/` |
| **scripts** | **scripts** | Automation scripts folder | Preserve folder name as `scripts/` |
| **datos** | **data** | Dataset folder | Preserve folder name as `data/` |
| **infraestructura** | **infrastructure** | IaC and deployment folder | Preserve folder name as `infrastructure/` |

---

## Translation Rules

### 1. Preserve Code and Output Examples
- **Never translate code** (Python, SQL, shell, Terraform, Docker, etc.)
- **Never translate CLI output** or error messages
- **Preserve variable names** and function signatures
- **Quote code blocks** with triple backticks or code tags

**Example:**
```
Spanish: "Ejecutar este comando para instalar:"
English: "Run this command to install:"

// Code block remains:
pip install tensorflow
```

### 2. Preserve Links and References
- **Do not change URLs** or anchor references
- **Update link text** to English (display text only)
- Preserve GitHub refs, file paths, and code symbols

**Example:**
```markdown
Spanish: [Ver documentación oficial](https://docs.example.com)
English: [See official documentation](https://docs.example.com)
```

### 3. Headers and Metadata
- **Translate all headers** (H1-H6) consistently with terminology mapping
- **Translate metadata** (title, description, author notes)
- **Preserve front matter keys** (YAML/TOML keys remain unchanged)

**Example:**
```markdown
Spanish: ## Módulo 01: Configuración Inicial
English: ## Module 01: Initial Setup
```

### 4. Lists and Bullets
- **Translate each bullet** independently
- **Preserve nesting and structure**
- **Translate any trailing inline comments**

**Example:**
```markdown
Spanish:
- Requisito: tener Python 3.10+
- Validar con: `python --version`

English:
- Requirement: Python 3.10 or later
- Validate with: `python --version`
```

### 5. Tables and Structured Data
- **Translate headers** (column names)
- **Translate cell values** that are descriptive text
- **Preserve cell values** that are codes, IDs, or command examples

**Example:**
```markdown
Spanish:
| Parámetro | Descripción | Valor por Defecto |
|-----------|-------------|-------------------|
| timeout   | segundos máximos | 30 |

English:
| Parameter | Description | Default Value |
|-----------|-------------|-----------------|
| timeout   | maximum seconds | 30 |
```

### 6. Emphasis and Formatting
- **Preserve bold, italic, code formatting**
- **Update text within formatting** per translation rules
- **Translate alt text** in images (but preserve image paths)

**Example:**
```markdown
Spanish: **Esta es una nota importante:**
English: **This is an important note:**
```

### 7. File Naming
- **Update README filenames** and cross-references in navigation
- **Preserve script filenames** (keep snake_case Python names)
- **Translate display names** in file lists or TOCs

### 8. Hints and Solutions
- **Translate all hint text** and explanations
- **Preserve hint structure** (headers, sections)
- **Preserve code snippets** within hints

**Example:**
```markdown
Spanish: 
## Pista
Intenta usar la función `map()` para transformar...

English:
## Hint
Try using the `map()` function to transform...
```

---

## Terminology Decisions and Context

### Why These Mappings?

1. **Module/Exercise/Objective**: Aligns with standard English learning design terminology (Bloom's taxonomy, instructional design)
2. **Data Lake/Lakehouse**: Industry-standard terms; "Data Lakehouse" is established in English BI/engineering contexts
3. **Pipeline/Transformation**: Standard data engineering vocabulary (Apache, Databricks, dbt communities)
4. **Container/Orchestration**: Docker/Kubernetes industry standards (already English in Spanish tech communities)
5. **Cost Analysis/Governance**: FinOps and data governance are English-first disciplines in cloud computing

### Regional and Company Consistency

- **Target audience**: International engineers, Spanish-speaking learners in English-first environments
- **NaNLABS standard**: All governance, instructional governance, and new instructional content is English
- **Source precedent**: training-cloud-data originated in Spanish but nan-data-engineering-labs is established as English-first

---

## Quality Checks Before Merge

After completing all phases of translation:

1. **Run validation**:
   ```bash
   python scripts/validate_english_content.py --full-scan
   ```
   Expected result: 0 findings

2. **Spot-check translations**:
   - Review 5% of translated files manually
   - Verify terminology consistency
   - Confirm no Spanish markers remain

3. **Diff review**:
   - Compare module README.md in original vs. translated
   - Verify links, code blocks, and formatting are intact
   - Check for any introduced typos or formatting breaks

4. **Link validation** (if automated):
   - Ensure internal cross-references still resolve
   - Verify relative paths in exercises

---

## Related Documents

- [docs/TODO-TRANSLATION-BATCH.md](TODO-TRANSLATION-BATCH.md): Translation batch workflow and timeline
- [docs/TRANSLATION-QA-CHECKLIST.md](TRANSLATION-QA-CHECKLIST.md): Module-level QA template
- [docs/TODO-TRANSLATION-WAVES.md](TODO-TRANSLATION-WAVES.md): Wave-by-wave execution plan
- [scripts/validate_english_content.py](../scripts/validate_english_content.py): Automated language validation

---

## Version History

| Date | Version | Notes |
|------|---------|-------|
| May 1, 2026 | 1.0 | Initial style guide created for translation batch Phase 1 |

---

**Last Updated**: May 1, 2026  
**Maintained By**: NaNLABS Engineering  
**Status**: Active (used during translation batch processing)
