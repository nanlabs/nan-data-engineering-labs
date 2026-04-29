# English Migration Guide

## Purpose

This guide documents the migration pattern used in the AI labs repository and adapts it to `nan-data-engineering-labs` so we can fully replace mixed Spanish and English module content with English-only governance content.

## Sources

- `nan-ai-engineering-labs/ENGLISH_CONVERSION_REPORT.md`
- `nan-ai-engineering-labs/ENGLISH_CONVERSION_AUDIT.md`
- `nan-data-engineering-labs/scripts/validate_english_content.py`
- `nan-data-engineering-labs/scripts/validate_learning_labs.py`

## Migration Principles

1. Translate content, not only headings.
2. Keep file structure and module contracts stable.
3. Preserve code blocks, URLs, and commands exactly as-is.
4. Standardize terminology across all modules.
5. Validate after each module batch, not only at the end.

## Proven Pattern from nan-ai-engineering-labs

The successful conversion pattern had four repeatable stages:

1. Audit current language state and classify files as English, Spanish, or Mixed.
2. Apply controlled translation with a terminology dictionary.
3. Rename Spanish file names to English naming conventions when needed.
4. Run validators and fix any regressions before committing.

This process produced stable results and kept quality gates green.

## Scope for nan-data-engineering-labs

Target modules for Phase 5.2 full replacement:

- `module-01-cloud-fundamentals`
- `module-02-storage-basics`
- `module-03-compute-options`
- `module-04-networking-basics`
- `module-05-data-ingestion`
- `module-06-data-transformation`
- `module-07-serverless-data-processing`
- `module-08-stream-processing`
- `module-09-data-warehousing`

Target files per module:

- `README.md`
- `theory/*.md`
- `exercises/**/README.md`
- `exercises/**/hints.md`
- `validation/**/*.md`
- Any governance-facing markdown under the module root

## Terminology Baseline

Use a stable glossary before translating:

- modulo -> module
- teoria -> theory
- practica -> practice
- ejercicio -> exercise
- evaluacion -> evaluation
- prerrequisitos -> prerequisites
- objetivos de aprendizaje -> learning objectives
- criterios de validacion -> validation criteria
- canalizacion -> pipeline
- calidad de datos -> data quality

Add project-specific terms as needed, but keep one canonical translation per term.

## Execution Plan (Batch-by-Batch)

### Step 1: Baseline Audit

Run current validators and capture findings:

```bash
cd nan-data-engineering-labs
make validate-language
make validate-contract
```

Save outputs for traceability in a working note or issue comment.

### Step 2: Translate One Module at a Time

For each module:

1. Translate markdown content fully to English.
2. Keep code examples and shell commands unchanged.
3. Ensure required heading groups remain present.
4. Replace Spanish section titles with English contract-aligned headings.

### Step 3: Optional Filename Standardization

If filenames are Spanish and hurt discoverability, rename to English.

Rules:

- Use kebab-case.
- Keep numeric prefixes where present.
- Update all in-repo references after rename.

### Step 4: Validate After Every Module

Run:

```bash
cd nan-data-engineering-labs
make validate-language
make validate-contract
```

Do not move to the next module until current module passes.

### Step 5: Batch Commit Strategy

Commit by small coherent batches to simplify review:

- Batch A: modules 01-03
- Batch B: modules 04-06
- Batch C: modules 07-09

Recommended commit message style:

- `Migrate modules 01-03 content to English`
- `Migrate modules 04-06 content to English`
- `Migrate modules 07-09 content to English`

## Quality Checklist

Before opening a PR:

- All target files are English-only.
- No required heading group is removed.
- Validators pass locally.
- Internal links still resolve after any rename.
- No accidental code translation in snippets.

## Risks and Mitigations

1. Risk: Literal translation degrades technical meaning.
   Mitigation: Use glossary and review by module domain owner.

2. Risk: Broken links after file renames.
   Mitigation: Run a reference search and fix links in same commit.

3. Risk: Contract drift while editing docs.
   Mitigation: Run contract validator for each module batch.

4. Risk: Huge PRs become unreviewable.
   Mitigation: Split into three batches (01-03, 04-06, 07-09).

## Definition of Done (Phase 5)

Phase 5 is complete when:

1. All nine target modules are fully English in governance content.
2. `make validate-language` exits with code 0.
3. `make validate-contract` exits with code 0.
4. PR review confirms no broken links and no contract regressions.
