<%*
// Asks which project the note belongs to; hubs live in Projects/.
const hubs = app.vault.getMarkdownFiles()
  .filter(f => f.path.startsWith("Projects/")).map(f => f.basename).sort();
const project = await tp.system.suggester(["(none)", ...hubs], ["", ...hubs]);
tR += "---\n";
tR += "note_type: Project Note\n";
tR += `created: ${tp.date.now("YYYY-MM-DD")}
`;
if (project) tR += `project: "[[${project}]]"\n`;
tR += "status: In Progress\n";
tR += "---\n";
%>
