# data/

Static content the app reads at build time. Written by `tools/` (problems) or by hand (curriculum, concepts, diagnostic). Nothing in here is copied from Stewart: only section titles and printed page numbers.

## Page numbers

`printedPages` in `curriculum.json` are the **printed** page numbers from the table of contents of Stewart, *Calculus: Early Transcendentals*, 8th ed. (Cengage, 2016). The learner reads from the physical book.

PDF offset for the project PDF (not committed): printed page `p` of the main text is PDF page `p + 32` (checked: section 1.1 starts on printed page 10, PDF page 42). Appendix pages (A2, A10, ...) are numbered separately at the back of the book; appendix A starts at PDF page ~1250. Verify against the physical copy when it arrives.

A section's page range is `[its start page, the next section's start page - 1]`. Where the next entry in the contents is a project or review, the range ends before that entry.

## Files

| File | Contents |
|---|---|
| `curriculum.json` | Skill graph: Track 0 ramp + Stewart nodes, prereqs, integral tiers |
| `problems/<node-id>.json` | SymPy-verified original problems per node |
| `concepts/<node-id>.json` | Original plain-language explanations per node |
| `diagnostic.json` | Placement questions |
