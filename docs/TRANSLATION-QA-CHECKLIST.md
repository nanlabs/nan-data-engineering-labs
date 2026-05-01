# Translation QA Checklist

**Purpose**: Module-level quality assurance template for verifying translated content meets English standards and maintains instructional integrity.

**Usage**: One checklist per module or batch. Completed by QA reviewer before wave merge.

**Status**: Template (copy and rename per wave/module)

---

## Module Information

- **Module ID**: `________________` (e.g., module-01-cloud-fundamentals)
- **Wave**: `_____` (1-5)
- **Translator(s)**: `_________________________`
- **QA Reviewer**: `_________________________`
- **Review Date**: `_________________________`
- **Files Reviewed**: `_____` of `_____` (e.g., 12 of 12)

---

## Automated Validation (Pre-Submission)

**Command**: `python scripts/validate_english_content.py <module-path>`

- [ ] Run validation passed (0 findings expected)
- [ ] No Spanish markers (modulo, ejercicio, prerequisito, objetivo, etc.)
- [ ] No accented characters (á, é, í, ó, ú, ñ) in non-code sections
- [ ] File path confirms: `modules/module-XX-<name>/`

**Validator Output Summary**:
```
[Paste validator output here or mark "PASS"]
```

---

## Content Structure & Integrity

### Module Scaffold
- [ ] README.md exists and is in English
- [ ] theory/ folder populated with theory/*.md files
- [ ] exercises/ folder has exercises/01/ through exercises/06/ (or correct count)
- [ ] validation/ folder has required subfolders (data-quality, infrastructure, integration, query-results)
- [ ] scripts/ folder has any required automation scripts
- [ ] data/ folder populated (if applicable)
- [ ] infrastructure/ folder populated (if applicable)

### File Encoding & Format
- [ ] All .md files are UTF-8 encoded (no encoding errors)
- [ ] No Windows line endings (CRLF); Unix line endings (LF) only
- [ ] No trailing whitespace in lines
- [ ] Markdown formatting is valid (headers, lists, code blocks parse correctly)

---

## Language & Terminology Quality

### Terminology Consistency
- [ ] All module references use "module" (not "modulo")
- [ ] All exercise references use "exercise" (not "ejercicio")
- [ ] Learning objectives use "goal" or "objective" (not "objetivo")
- [ ] Data Lake terminology consistent ("Data Lake", "data lake" per context)
- [ ] ETL spelled out at least once: "ETL (Extract, Transform, Load)"
- [ ] Governance terms use standard English (not "gobernanza")
- [ ] Storage terms consistent (S3, object storage, cloud storage per context)

### Grammar & Readability
- [ ] All sentences are grammatically correct English
- [ ] Tone is professional and educational (not colloquial)
- [ ] No machine-translation artifacts (awkward phrasings, literal translations)
- [ ] Acronyms are spelled out on first mention (ETL, IAM, etc.)
- [ ] Abbreviations are standard (e.g., "e.g.", "i.e.", "etc.")

### Completeness
- [ ] No "TODO", "[TRANSLATE]", or placeholder markers remain
- [ ] No partially translated sections
- [ ] No Spanish mixed with English in same paragraph
- [ ] All headers translated to English
- [ ] All lists translated to English

---

## Code, Commands, and Examples

### Code Integrity
- [ ] Python code blocks unchanged and valid syntax
- [ ] SQL queries unchanged and readable
- [ ] Shell/Bash commands unchanged and accurate
- [ ] Terraform, Docker, and IaC files unchanged
- [ ] Variable names and function signatures preserved
- [ ] Code comments in code blocks remain unchanged (or translated separately per comment style guide)

### Output and CLI Examples
- [ ] Example command outputs preserved as-is
- [ ] Error messages preserved as-is (don't translate error text)
- [ ] File paths in examples preserved
- [ ] Environment variable names preserved (uppercase, snake_case)
- [ ] Package names and version numbers preserved

### Inline Code and Symbols
- [ ] Backtick-wrapped code (e.g., `pip install`, `SELECT *`) remains in code formatting
- [ ] Function calls like `my_function()` unchanged
- [ ] File paths preserved exactly
- [ ] CLI flags preserved (e.g., `-v`, `--verbose`)

---

## Links, References, and Cross-References

### Internal Links
- [ ] Cross-references to other modules still resolve (e.g., "See Module 03" links work)
- [ ] Relative paths in links are correct (e.g., `../../theory/`)
- [ ] README links to exercises, scripts, infrastructure are intact
- [ ] Section anchor links still work (after header translation)

### External Links
- [ ] URLs unchanged (no broken links)
- [ ] Link text is translated to English
- [ ] Markdown link syntax preserved: `[text](url)`

### Code References
- [ ] Function/method references unchanged
- [ ] GitHub repo links preserved
- [ ] API documentation links preserved
- [ ] Package repository links preserved

---

## Formatting and Metadata

### Markdown Formatting
- [ ] Headers (H1-H6) translated and properly nested
- [ ] Bold (`**text**`) and italic (`*text*`) preserved
- [ ] Code blocks with triple backticks preserved (` ``` `)
- [ ] Lists (ordered and unordered) structure preserved
- [ ] Tables formatted correctly with headers translated
- [ ] Blockquotes preserved and text translated

### YAML/Front Matter (if applicable)
- [ ] YAML keys unchanged (e.g., `title:`, `description:`, `author:`)
- [ ] YAML values translated to English where descriptive
- [ ] YAML syntax remains valid (quotes, colons, indentation)

### Comments and Metadata
- [ ] File headers/docstrings translated
- [ ] Inline comments in learning instructions translated (but not code comments)
- [ ] Author notes and version history updated if needed
- [ ] Date fields preserved (do not translate dates)

---

## Module-Specific Checks

### Theory Content
- [ ] Concept explanations are clear in English
- [ ] Examples and analogies make sense in English context
- [ ] Technical depth is appropriate for target learner level
- [ ] No Spanish technical jargon remains

### Exercises
- [ ] Exercise instructions are clear and unambiguous
- [ ] Success criteria are well-defined
- [ ] Expected outputs are described in English
- [ ] Hints are helpful and use standard English terminology
- [ ] Solutions are present and accessible

### Validation
- [ ] Validation test descriptions translated
- [ ] Query results and expected outputs documented
- [ ] Data quality rules clearly stated
- [ ] Infrastructure validation criteria clear

### Infrastructure Documentation
- [ ] Deployment instructions are clear
- [ ] Configuration parameters documented in English
- [ ] Prerequisites listed (dependencies, versions, accounts)
- [ ] Troubleshooting section helpful and in English

---

## Quality Score

### Scoring Guidance
- **Pass (No Issues)**: All items checked; 0 findings in validation
- **Pass with Warnings**: Minor formatting or clarity issues noted but content is sound
- **Needs Revision**: 1-3 items unchecked; resubmit after fixes
- **Reject**: 4+ items unchecked; requires substantial rework

### Overall Assessment

| Criteria | Status | Notes |
|----------|--------|-------|
| Automated validation | ☐ PASS ☐ FAIL | |
| Content structure | ☐ PASS ☐ FAIL | |
| Language quality | ☐ PASS ☐ FAIL | |
| Code/examples | ☐ PASS ☐ FAIL | |
| Links/references | ☐ PASS ☐ FAIL | |
| Formatting | ☐ PASS ☐ FAIL | |

**Final Status**: ☐ APPROVED ☐ APPROVED WITH CHANGES ☐ NEEDS REVISION ☐ REJECTED

---

## Sign-Off

**QA Reviewer Name**: `_________________________`

**QA Reviewer Signature/Email**: `_________________________`

**Date Approved**: `_________________________`

**Comments/Notes**:
```
[Use this section for any additional observations, recommended improvements, or context for future waves]
```

---

## Issue Tracking

| Issue ID | Description | Severity | Status | Assigned To |
|----------|-------------|----------|--------|------------|
| | | | | |
| | | | | |

**Severity Levels**: Critical (breaks learning), High (clarity/accuracy issue), Medium (minor improvement), Low (nice-to-have)

---

## Sign-Off for Submission

- [ ] All checks completed
- [ ] QA reviewer approved
- [ ] Module ready for merge to main branch
- [ ] Evidence attached or referenced (validator output, spot-check notes)

**Ready to Merge**: ☐ YES ☐ NO

**Merged By**: `_________________________` (Authorized Reviewer)

**Merge Date**: `_________________________`

**Merge Commit**: `_________________________` (e.g., abc1234)

---

## Template Notes

- **Copy and rename**: `TRANSLATION-QA-CHECKLIST-WAVE-[N]-MODULE-[XX].md`
- **One per module per wave** (or batch if all modules in wave translated together)
- **Archive** completed checklists in `docs/qa-history/` after merge
- **Reference** in PR description or commit message for traceability

---

**Related Documents**

- [docs/TRANSLATION-STYLE-GUIDE.md](TRANSLATION-STYLE-GUIDE.md): Terminology and translation rules
- [docs/TODO-TRANSLATION-BATCH.md](TODO-TRANSLATION-BATCH.md): Batch workflow and timeline
- [docs/TODO-TRANSLATION-WAVES.md](TODO-TRANSLATION-WAVES.md): Wave execution plan
- [scripts/validate_english_content.py](../scripts/validate_english_content.py): Automated validation

---

**Document Version**: 1.0  
**Created**: May 1, 2026  
**Last Updated**: May 1, 2026  
**Status**: Active (template for Wave 1-5 QA)
