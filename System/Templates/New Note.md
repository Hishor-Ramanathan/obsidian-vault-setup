<%*
// Folder template for Notes/: pick the kind of note, insert that template.
// Template Book is left out — the book-search plugin fills it, not Templater.
const kinds = app.vault.getMarkdownFiles()
  .filter(f => f.path.startsWith("System/Templates/Template ") && f.basename !== "Template Book")
  .map(f => f.basename).sort();
const pick = await tp.system.suggester(kinds.map(k => k.replace("Template ", "")), kinds);
if (pick) tR += await tp.file.include(`[[${pick}]]`);
%>
