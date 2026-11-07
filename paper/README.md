# ACL working manuscript

Official ACL review template, pinned by TEMPLATE_PROVENANCE.json. English first working draft, not submission-ready. Sections1–6 exist. Earlier draft5.1 maps to4.1;5.3 to4.3; traps to5. Chinese originals are preserved under sources/.

Tables: run `python scripts/export_tables.py` from paper/. This reads private numeric sources when run in /data/HZX/Def, writes safe CSVs, then generates tables exclusively from those CSVs. Committed CSVs support standalone regeneration with `--from-csv`. No raw attack prompts, responses, or training targets are included.

Build: `tectonic --outdir build main.tex` (or `latexmk -pdf main.tex`). The official acl.sty and bibliography style are vendored unchanged; no margin or font-size overrides.

Evidence gaps: the augmentation holdouts are running, and the plain third arm is pending; no completed intervention claims. Human calibration and independent PAIR test are absent. Complete revision of Sections1–6 target11/12; evidence gaps remain labeled rather than invented.
