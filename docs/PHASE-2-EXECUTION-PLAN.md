# Translation Batch Phase 2 Execution Plan

**Status**: Ready for execution (May 4-5, 2026)

**Previous Completion**: Phase 1 assets created
- ✅ TRANSLATION-STYLE-GUIDE.md
- ✅ TRANSLATION-QA-CHECKLIST.md
- ✅ extract_wave_1.py (extraction script)
- ✅ batch_translate.py (batch translation script)

---

## Current State

### Wave 1 Extraction Complete ✅

```
Source: training-cloud-data/modules/module-0{1..6}-*
Target: nan-data-engineering-labs/modules/
Status: 555 files extracted (411.66 MB)
```

**Module Inventory**:
| Module | Files | Size |
|--------|-------|------|
| module-01-cloud-fundamentals | 103 | 16.1 MB |
| module-02-storage-basics | 80 | 290 KB |
| module-03-sql-foundations | 97 | 421 KB |
| module-04-python-for-data | 97 | 71.4 MB |
| module-05-data-lakehouse | 109 | 323 MB |
| module-06-etl-fundamentals | 69 | 147 KB |
| **TOTAL** | **555** | **411.66 MB** |

---

## Phase 2 Execution: Three Translation Options

### Option A: Claude API (Automated Batch) ⚡ RECOMMENDED

**Advantages**:
- Fast (1-2 hours for all 555 files)
- Consistent with style guide terminology
- Code-preserving (smart code block detection)
- Repeatable and auditable

**Requirements**:
- `ANTHROPIC_API_KEY` environment variable
- `pip install anthropic` (already done)

**Execution**:
```bash
export ANTHROPIC_API_KEY="sk-..."  # Your API key
python scripts/batch_translate.py --wave 1 --report wave_1_translation_report.txt
```

**Cost Estimate**:
- ~4-8 MB per Wave 1 (compressed text)
- Using Claude 3.5 Sonnet: ~$0.50-$1.00 per wave
- All 5 waves: ~$2-5 total

**Expected Output**:
- Translated markdown files in modules/module-0{1..6}-*
- wave_1_translation_report.txt with file mapping

---

### Option B: Manual Tier-1 (Focus on High-Impact Files) 📝

**Advantages**:
- Perfect accuracy and terminology consistency
- Human review embedded in process
- Lower cost (free, volunteer)

**Disadvantages**:
- Slower (3-5 days for full Wave 1)
- Resource intensive

**Process**:
1. Focus on high-priority files first:
   - All README.md files (6 files)
   - All theory/*.md files (60-80 files)
   - All hints.md files (30-40 files)
   
2. Defer lower-priority:
   - Infrastructure docs (can follow standard patterns)
   - Validation guides (more technical, less ambiguous)
   - Data files (often unchanged)

3. Estimated time breakdown:
   - README files: 2 hours
   - Theory content: 8 hours
   - Exercise hints: 4 hours
   - **Total: 14 hours**

---

### Option C: Hybrid (Recommended Path) 🎯

**Process**:
1. **Automated Phase** (Claude API, 2 hours)
   - Translate all 555 files automatically
   - Use batch_translate.py with style guide
   
2. **Manual Refinement Phase** (3-5 hours)
   - QA review high-impact files (README, theory, hints)
   - Use TRANSLATION-QA-CHECKLIST.md
   - Spot-check 10% of content
   - Fix terminology inconsistencies

3. **Validation Phase** (1 hour)
   - Run `validate_english_content.py --full-scan`
   - Expect 0 findings
   - Re-translate any failures

**Advantages**:
- Fast initial turnaround (2 hours)
- High quality final output (QA embedded)
- Cost-effective ($0.50-$1.00)
- Risk-mitigated (human review gates)

---

## Implementation Steps

### Step 1: Choose Translation Method
User must select: **Option A (Claude API)**, **Option B (Manual)**, or **Option C (Hybrid)**

### Step 2: Execute Translation

**For Option A or C (Claude API)**:
```bash
# Set API key
export ANTHROPIC_API_KEY="your-key-here"

# Translate Wave 1
cd nan-data-engineering-labs
source ../.venv/bin/activate
python scripts/batch_translate.py --wave 1 \
  --source ../training-cloud-data/modules \
  --target modules \
  --report wave_1_translation_report.txt

# Expected runtime: 30-120 minutes (depends on API rate limits)
```

**For Option B or C (Manual QA)**:
```bash
# High-priority files list
find modules/module-0{1..6}-* -name "README.md" -o -name "theory/*.md" -o -name "*/hints.md"

# Use TRANSLATION-QA-CHECKLIST.md per module
# Review each file with terminology mapping
```

### Step 3: Validate Translations

```bash
# Run full validation (expect 0 findings)
python scripts/validate_english_content.py --full-scan

# Check specific modules
python scripts/validate_english_content.py --path modules/module-01-*
```

### Step 4: QA Checklist Sign-Off

For each module, copy and complete:
```bash
cp docs/TRANSLATION-QA-CHECKLIST.md \
   docs/TRANSLATION-QA-CHECKLIST-WAVE-1-MODULE-01.md

# Fill out checklist:
# - Automated validation results
# - Manual review confirmation
# - QA reviewer signature
# - Ready for merge date
```

### Step 5: Commit to Feature Branch

```bash
git add modules/ docs/TRANSLATION-QA-CHECKLIST-WAVE-1-*.md wave_1_*
git commit -m "feat: translate Wave 1 modules (01-06) to English

Automated Translation:
- 555 files translated using Claude 3.5 Sonnet
- Terminology: docs/TRANSLATION-STYLE-GUIDE.md
- Code blocks preserved, links intact, formatting maintained

QA Review:
- docs/TRANSLATION-QA-CHECKLIST-WAVE-1-MODULE-*.md per module
- validate_english_content.py: 0 findings
- Manual spot-check: 10% of content verified

Affected Modules:
- module-01-cloud-fundamentals (103 files)
- module-02-storage-basics (80 files)
- module-03-sql-foundations (97 files)
- module-04-python-for-data (97 files)
- module-05-data-lakehouse (109 files)
- module-06-etl-fundamentals (69 files)

Total: 555 files, 411.66 MB"
```

---

## Quality Validation

### Automated Checks
```bash
# Zero Spanish markers expected
python scripts/validate_english_content.py --full-scan modules/module-0{1..6}-*

# Contract compliance expected
python scripts/validate_learning_labs.py modules/module-0{1..6}-*
```

### Manual Spot-Checks
- [ ] At least 1 README.md per module
- [ ] At least 2 theory/*.md files
- [ ] At least 1 hints.md per module type
- [ ] Terminology consistency vs. TRANSLATION-STYLE-GUIDE.md

### Sign-Off Criteria
- [ ] validate_english_content.py returns 0 findings
- [ ] No Spanish accented characters (á, é, í, ó, ú, ñ)
- [ ] All QA checklists completed per module
- [ ] Code blocks verified intact
- [ ] Links and paths verified
- [ ] Markdown formatting verified

---

## Timeline

| Phase | Time | Owner |
|-------|------|-------|
| Prepare (Phase 1) | May 2-3 | ✅ Complete |
| Translate (Phase 2) | May 4-5 | Start now |
| QA Manual Review | May 6-7 | QA team |
| Validation | May 8 | Dev |
| Merge to main | May 9 | Ops |

---

## Files Created This Phase

| File | Purpose |
|------|---------|
| `scripts/extract_wave_1.py` | Extracts Wave 1 modules from source |
| `scripts/batch_translate.py` | Batch translates using Claude API |
| `wave_1_inventory.json` | Machine-readable extraction metadata |
| `wave_1_extraction_report.txt` | Human-readable extraction summary |
| `docs/PHASE-2-EXECUTION-PLAN.md` | This document |

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| API rate limits | Use batch API endpoint for bulk processing |
| Translation quality | Manual QA on high-impact files (README, theory, hints) |
| Terminology inconsistency | Use TRANSLATION-STYLE-GUIDE.md and automated validation |
| Markdown corruption | Code block detection and restoration in batch_translate.py |
| Link breakage | Manual spot-check phase catches broken references |

---

## Decision Gate

**User Input Required**: Select translation option
- [ ] Option A: Claude API (automated batch, ~$1, 2 hours)
- [ ] Option B: Manual (perfect quality, 14 hours, free)
- [ ] Option C: Hybrid (fast + QA, ~$1, 5 hours total) **RECOMMENDED**

Once selected, proceed with implementation.

---

## Related Documents

- [docs/TRANSLATION-STYLE-GUIDE.md](TRANSLATION-STYLE-GUIDE.md): Terminology and rules
- [docs/TRANSLATION-QA-CHECKLIST.md](TRANSLATION-QA-CHECKLIST.md): QA template
- [scripts/extract_wave_1.py](../scripts/extract_wave_1.py): Wave 1 extraction
- [scripts/batch_translate.py](../scripts/batch_translate.py): Batch translation engine
- [docs/TODO-TRANSLATION-BATCH.md](TODO-TRANSLATION-BATCH.md): Batch workflow overview
- [docs/TODO-TRANSLATION-WAVES.md](TODO-TRANSLATION-WAVES.md): Wave-by-wave checklist

---

**Document Created**: May 1, 2026  
**Status**: Awaiting user decision on translation method  
**Next Action**: Choose translation option and proceed with Phase 2 execution
