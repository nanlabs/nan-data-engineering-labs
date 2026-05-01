# TODO: Translation Batch Processing

Goal: Systematically translate 3,233+ Spanish language markers from all 23 modules into English, maintaining quality and consistency.

## Translation Scope Assessment

### Findings from Wave 1 Scan
- **Total Spanish markers detected**: 3,233
- **Affected modules**: All 23 (01-18 core, 01-03 checkpoints, bonus 01-02)
- **File types with Spanish**:
  - README.md (module root + exercise level)
  - hints.md (exercise hints)
  - STATUS.md / STATUS-FINAL.md
  - theory/*.md (concepts, architecture, resources)
  - infrastructure/README.md
  - validation/README.md
  - docs/ subdirectories

### Common Spanish Markers Found
- Accented characters: á, é, í, ó, ú, ñ
- Content words: "modulo", "ejercicio", "prerequisito", "objetivo", "resumen", "pasos"
- Phrases: "Resumen Ejecutivo", "Listo para producción", "análisis de costos", etc.

## Translation Strategy

### Option A: Batch Automated + Manual QA
1. Extract all source module content from `training-cloud-data/modules/module-0{1..18}`
2. Run batch translation tool (e.g., Claude batch API, DeepL, or manual review)
3. Stage translated files in intermediate branch
4. QA manual review (10% spot check per module)
5. Merge to main in single commit

**Pro**: Fast, parallel processing
**Con**: Quality risk if automated poorly

### Option B: Wave-by-Wave Manual Translation
1. Select 2-3 volunteers per wave
2. Translate Wave 1 (modules 01-06) manually
3. QA by different reviewer
4. Commit and validate
5. Repeat for Waves 2-5

**Pro**: High quality, clear ownership
**Con**: Slower (weeks vs days)

### Option C: Hybrid (Recommended)
1. Use automated translation for first pass on all 23 modules
2. Focus manual QA on high-impact files: README.md, hints.md, theory/concepts.md
3. Defer lower-priority translations (infrastructure docs, STATUS files) to Wave 2
4. Establish translation style guide (terminology mapping) before QA

**Pro**: Balanced speed/quality, clear prioritization
**Con**: Requires upfront QA template

## Recommended Workflow (Hybrid)

### Phase 1: Prepare Translation Assets (1-2 days)
- [x] Create `docs/TRANSLATION-STYLE-GUIDE.md` with terminology mapping ✅ *Complete May 1*
  - Spanish ↔ English terminology mapping (module, exercise, objective, prerequisite, data lake, ETL, cost analysis, etc.)
  - Translation rules (preserve code, links, formatting; translate only instructional text)
  - Quality gate definitions (0 Spanish markers, no accented chars, consistency checks)
- [ ] Extract all module content into translation staging directory
  - Copy `training-cloud-data/modules/module-0{1..18}-*/` into staging branch or temp folder
  - Create batches list: modules 01–06 (Wave 1), 07–12 (Wave 2), 13–18 (Wave 3), checkpoints 01–03, bonus 01–02
- [x] Create QA checklist template in `docs/TRANSLATION-QA-CHECKLIST.md` ✅ *Complete May 1*
  - Module-level QA checklist with automated validation criteria
  - Manual review guidance and sign-off tracking
  - Copy and customize per wave/module (e.g., `TRANSLATION-QA-CHECKLIST-WAVE-1-MODULE-01.md`)

### Phase 2: Automated Translation Batch (1 day)
- [ ] Set up batch translation job for all 23 modules
- [ ] Generate translated versions in staging branch `feature/module-translation`
- [ ] Diff against originals to verify coverage

### Phase 3: Manual QA and Refinement (3-5 days)
- [ ] QA Wave 1 (modules 01-06) - high priority files only
- [ ] QA Wave 2 (modules 07-12) - standard coverage
- [ ] QA Wave 3 (modules 13-18) - standard coverage  
- [ ] QA Wave 4 (checkpoints) - high priority
- [ ] QA Wave 5 (bonus) - standard coverage

### Phase 4: Validation and Merge
- [ ] Run full validation suite: `python scripts/validate_english_content.py --full-scan`
- [ ] Verify contract compliance: `python scripts/validate_learning_labs.py --strict-core`
- [ ] Merge staging branch to main with atomic commit

## Rollout Schedule (Proposed)

| Phase | Timeline | Responsible |
|-------|----------|-------------|
| Prepare assets | May 2-3 | Dev |
| Batch translate | May 4-5 | Dev + Tool |
| Manual QA | May 6-10 | QA reviewers |
| Final validation | May 11 | Dev |
| Production merge | May 12 | Ops |

## Translation Quality Criteria

Each translated file must pass:
- ✓ No Spanish markers detected by `validate_english_content.py`
- ✓ No accented Spanish characters remaining
- ✓ Terminology consistent with `TRANSLATION-STYLE-GUIDE.md`
- ✓ Code examples unchanged (only comments/descriptions translated)
- ✓ Links and paths preserved
- ✓ Markdown formatting preserved

## Notes

- This is a separate isolated workflow from content population waves
- Translation can proceed in parallel with structure unification tasks
- Once complete, modules will be ready for Wave 1-5 content migration with no language blockers
- Consider reusing translated content if source modules are updated

## Related Documents

- [docs/TRANSLATION-STYLE-GUIDE.md](TRANSLATION-STYLE-GUIDE.md): Terminology mapping and translation rules (Phase 1, ✅ Complete)
- [docs/TRANSLATION-QA-CHECKLIST.md](TRANSLATION-QA-CHECKLIST.md): Module-level QA template (Phase 1, ✅ Complete)
- [docs/TODO-TRANSLATION-WAVES.md](TODO-TRANSLATION-WAVES.md): Wave-by-wave execution checklists
- [docs/TODO-STRUCTURE-UNIFICATION.md](TODO-STRUCTURE-UNIFICATION.md): Parallel task for module folder standardization
- [scripts/validate_english_content.py](../scripts/validate_english_content.py): Automated language validation tool
