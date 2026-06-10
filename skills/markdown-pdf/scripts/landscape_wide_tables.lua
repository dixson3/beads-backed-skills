-- Wrap any table whose column count exceeds a threshold in a LaTeX `landscape`
-- environment (from the pdflscape package), so genuinely wide tables get the
-- page's long edge instead of overflowing the text block.
--
-- The threshold comes from the LANDSCAPE_COLS env var, set by md2pdf.py. A value
-- of 0 (the default) disables the filter entirely — nothing is wrapped. This is
-- a render-time mechanism: the Markdown source stays pure GFM (no \begin{...}
-- markup that would show as literal text in Obsidian/GitHub).

local threshold = tonumber(os.getenv("LANDSCAPE_COLS")) or 0

function Table(elem)
  if threshold <= 0 then
    return nil
  end
  if #elem.colspecs > threshold then
    return {
      pandoc.RawBlock("latex", "\\begin{landscape}"),
      elem,
      pandoc.RawBlock("latex", "\\end{landscape}"),
    }
  end
  return nil
end
