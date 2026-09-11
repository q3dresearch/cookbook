# PNG renders

Every figure in `../` at 1.25×, for readers whose viewer will not preview SVG — most
IDE file panes will not, though GitHub renders SVG in markdown natively, so the
recipe's own README displays correctly on the web without these.

**The SVGs are the source of truth.** These are generated, and regenerating them is
one command:

```sh
python - <<'PY'
import cairosvg, glob, os
for f in sorted(glob.glob("artifacts/charts/*.svg")):
    cairosvg.svg2png(url=f, scale=1.25,
                     write_to=f"artifacts/charts/png/{os.path.basename(f)[:-4]}.png")
PY
```

If a chart script changes and only the SVG is rebuilt, the PNG here goes stale
silently. Rebuild both, or delete the folder.
