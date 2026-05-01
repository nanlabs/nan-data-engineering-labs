# 📚 Assets - Visual resources and Quick References

## 📋 General Description

This directory contains visual resources and quick references designed to facilitate learning and query while working with Python for Data Engineering.

## 📂 Estructura de Assets

```
assets/
├── README.md                          # Este archivo
├── cheatsheets/                       # Hojas de referencia rápida
│   ├── python-basics.md              # Fundamentos de Python
│   ├── pandas-reference.md           # Operaciones de Pandas
│   ├── data-cleaning.md              # Limpieza de datos
│   └── file-formats.md               # Formatos de archivo
└── diagrams/                          # Diagramas y flujos
    ├── data-flow.md                  # Flujos de datos ETL
    └── pandas-operations.md          # Operaciones de Pandas
```

## 🎯 Purpose

The assets are designed to:

1. **Quick query**: Find common syntax and patterns without searching the documentation
2. **Referencia Visual**: Entender flujos de datos y transformaciones mediante diagramas
3. **Aprendizaje Activo**: Tener ejemplos concretos al alcance durante los ejercicios
4. **Troubleshooting**: Quick Guides to Common Errors and Best Practices

## 📝 Cheatsheets Disponibles

### 1. Python Basics (`cheatsheets/python-basics.md`)
- Variables y tipos de datos
- Estructuras de control (if/for/while)
- Funciones y lambdas
- Comprehensions
- Manejo de strings y colecciones
- **When to use**: First exercises, syntax review

### 2. Pandas Reference (`cheatsheets/pandas-reference.md`)
- Creating DataFrames
- Data selection (loc/iloc/boolean indexing)
- Filtering and transformation
- Grouping operations (groupby)
- Joins y merges
- Manejo de fechas
- **When to use**: Exercises 04, 05 and projects with datasets

### 3. Data Cleaning (`cheatsheets/data-cleaning.md`)
- Null value detection
- Estrategias para manejar nulls
- Duplicate removal
- Type conversion
- Data normalization
- Quality validation
- **When to use**: Exercise 05 (transformations), cleaning pipelines

### 4. File Formats (`cheatsheets/file-formats.md`)
- CSV: Lectura/escritura, delimitadores
- JSON: Nested structures, normalization
- Parquet: Compression, columnr storage
- Format comparison
- When to use each format
- **When to use**: Exercise 03 (file operations), storage decisions

## 📊 Diagramas Disponibles

### 1. Data Flow (`diagrams/data-flow.md`)
- pipeline ETL completo (Extract → Transform → Load)
- Data flow through exercises
- Validation points and checkpoints
- Transformaciones comunes
- **When to use**: pipeline design, understanding general flow

### 2. Pandas Operations (`diagrams/pandas-operations.md`)
- Flujo de transformaciones de DataFrames
- Filtering and selection operations
- Grouping and aggregation processes
- Tipos de joins y sus resultados
- **When to use**: Exercise 04 and 05, debugging transformations

## 🎨 How to Use Cheatsheets

### Durante los Ejercicios
```bash
# Abre el cheatsheet relevante en una pestaña del editor
# Mantén el cheatsheet visible mientras trabajas en el ejercicio
```

### As a Quick Reference
1. **Forgot syntax?** → query the corresponding cheatsheet
2. **Not sure about the flow?** → Review the diagrams
3. **Unexpected error?** → Check the "Common Errors" section in each cheatsheet

### Durante el Estudio
- Print the cheatsheets most relevant to your current job
- Usa los diagramas para entender el "big picture" antes de codificar
- query specific examples when you need to implement a pattern

## 📐 Formato de los Diagramas

The diagrams are written in **Mermaid**, a diagramming language that renders in Markdown.

### Display
- **GitHub**: Diagrams render automatically
- **VS Code**: Install the "Markdown Preview Mermaid Support" extension
- **Navegador**: Usa [Mermaid Live Editor](https://mermaid.live/)

## 💡 Tips de Uso

### Para Principiantes
1. Comienza con `python-basics.md` para refrescar conceptos
2. Usa `data-flow.md` para entender el objetivo final
3. query specific cheatsheets when you need them

### Para Usuarios Intermedios
1. Ten `pandas-reference.md` siempre a mano
2. Usa `data-cleaning.md` como checklist de calidad
3. query `file-formats.md` al decidir formatos de salida

### Para Proyectos Reales
1. Design your pipeline using`data-flow.md`as a guide
2. Implementa transformaciones queryndo `pandas-operations.md`
3. Valida calidad usando patrones de `data-cleaning.md`

## 🔄 Actualizaciones

Assets are periodically updated to include:
- Nuevos patrones descubiertos durante los ejercicios
- Mejoras en diagramas basadas en feedback
- Errores comunes reportados por estudiantes
- Industry best practices

## 📚 resources Complementarios

Los assets complementan:
- **Theory/** → Detailed theoretical concepts
- **Exercises/** → Hands-on practice
- **Validation/** → Knowledge verification
- **Docs/** → Troubleshooting guides

## 🤝 Contribuciones

Si encuentras errores o tienes sugerencias:
1. Check that the content is technically correct
2. Make sure the examples work
3. Keep the format consistent with other assets
4. Prioritize clarity and conciseness

---

**Last update**: Module 04 - Step 7
**Version**: 1.0
**Mantenedor**: Training Cloud Data
