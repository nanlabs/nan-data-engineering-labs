# TODO: Bootstrap Roadmap

Status: Bootstrap in progress
Last updated: 2026-04-29

## Priority 1: Publish-Ready Normalization

- [x] Copy governance and automation scaffold from source repository.
- [x] Keep modules as structure-only placeholders using `.gitkeep` files.
- [x] Remove legacy Spanish status reports from repository root.
- [x] Verify governance English validation (`scripts/validate_english_content.py`) with zero findings.
- [ ] Capture validation evidence snapshot in `docs/validation-evidence/bootstrap-YYYYMMDD.md`.
- [ ] Open first bootstrap PR with validation evidence (push is currently postponed by admin).

## Priority 2: Submodule Translation Migration (Execution Waves)

- [ ] Execute Wave 1 migration (modules 01-06): bring translated content from source and keep destination naming conventions.
- [ ] Execute Wave 2 migration (modules 07-12): preserve exercise unit contract (`README.md`, `hints.md`, `starter/`, `solution/`, `my_solution/`).
- [ ] Execute Wave 3 migration (modules 13-18): align advanced modules with same adoption pattern as previous waves.
- [ ] Execute Wave 4 migration (checkpoints 01-03): include `README.md`, starter template, reference solution, architecture docs.
- [ ] Execute Wave 5 migration (bonus 01-02): migrate optional tracks without breaking core learning path.
- [ ] After each wave, run `python scripts/validate_learning_labs.py --strict-core --strict-headings` and attach findings delta.
- [ ] After each wave, run `python scripts/validate_english_content.py --full-scan` and fix new language findings.

## Priority 3: Structure Uniformity for Easy Study Adoption

- [ ] Resolve regular-module drift: decide if `docs/` is mandatory for all regular modules or remove it from modules 01-05.
- [ ] Resolve regular-module drift: decide if `dags/` stays only in module 10 or becomes standardized template folder.
- [ ] Resolve regular-module drift: remove accidental `venv/` from module 05.
- [ ] Decide checkpoint policy for `extensions/`: keep in all checkpoints with docs, or remove for strict uniformity.
- [ ] Add and enforce a canonical per-type folder baseline in `docs/MODULE-CONTRACT-MATRIX.md` (required + approved optional).
- [ ] Extend `scripts/validate_learning_labs.py` to fail on unapproved extra folders per module type.

## Priority 4: Skills, Agents, and Internal-Workstation Alignment

- [x] Verify workstation baseline with `nan-doctor` (17/17 compliant).
- [x] Verify installed local agents under `~/.claude/agents`.
- [x] Verify skill links with `nan-skills list`.
- [ ] Install missing CLI dependencies for skill parity: `clickup` and `glab`.
- [ ] Re-run `nan-skills check` until no missing tools remain.
- [ ] Document the validated delivery stack in `docs/operations/agent-skill-playbook.md`.

## Priority 5: Validation and CI Hardening

- [ ] Run contract validation: `make validate-contract`.
- [ ] Run English validation: `make validate-language`.
- [ ] Run full checks: `make validate-all`.
- [ ] Verify GitHub workflow behavior in the destination repository.

## Priority 6: Content Population (Future Phase)

- [ ] Populate module instructional content incrementally.
- [ ] Keep all new governance and instructional content in English.
- [ ] Preserve module contract compliance for each delivery.

## Notes

- This repository bootstrap intentionally excludes module instructional content.
- The `modules/` tree is committed as placeholders only for structural continuity.
- Push is intentionally postponed until admin resolves repository permissions.
- Detailed execution checklists are in `docs/TODO-TRANSLATION-WAVES.md` and `docs/TODO-STRUCTURE-UNIFICATION.md`.
