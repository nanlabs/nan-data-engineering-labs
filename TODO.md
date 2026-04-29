# TODO: Bootstrap Roadmap

Status: Bootstrap in progress
Last updated: 2026-04-29

## Priority 1: Repository Normalization

- [x] Copy governance and automation scaffold from source repository.
- [x] Keep modules as structure-only placeholders using `.gitkeep` files.
- [x] Remove legacy Spanish status reports from repository root.
- [ ] Run full validation suite and fix findings.
- [ ] Open first bootstrap PR with validation evidence.

## Priority 2: Validation and CI Hardening

- [ ] Run contract validation: `make validate-contract`.
- [ ] Run English validation: `make validate-language`.
- [ ] Run full checks: `make validate-all`.
- [ ] Verify GitHub workflow behavior in the destination repository.

## Priority 3: Content Population (Future Phase)

- [ ] Populate module instructional content incrementally.
- [ ] Keep all new governance and instructional content in English.
- [ ] Preserve module contract compliance for each delivery.

## Notes

- This repository bootstrap intentionally excludes module instructional content.
- The `modules/` tree is committed as placeholders only for structural continuity.
