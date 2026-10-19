<%*
// Creates a hub note in Projects/ + its base in Projects/, in one step.
// Insert this template from anywhere — it writes nothing into the current note.
const V = app.vault;

const kind = await tp.system.suggester(
  ["Course  — a new course",
   "Subject — a new subject inside a course",
   "Project — a new project or organisation"],
  ["course", "subject", "project"]);
if (!kind) return;

const name = (await tp.system.prompt("Name")) || "";
if (!name.trim()) return;

let noteType, props, filter, crumb;

if (kind === "course") {
  noteType = "Course";
  props = "";
  filter = `note.course == "[[${name}]]"\n        - note.note_type != "Course"`;
  crumb = `[[Home]] › ${name}`;

} else if (kind === "subject") {
  const courses = V.getMarkdownFiles()
    .filter(f => app.metadataCache.getFileCache(f)?.frontmatter?.note_type === "Course")
    .map(f => f.basename).sort();
  const course = await tp.system.suggester(courses, courses);
  if (!course) return;
  noteType = "Subject";
  props = `course: "[[${course}]]"\n`;
  filter = `note.subject == "[[${name}]]"`;
  crumb = `[[Home]] › [[${course}]] › ${name}`;

} else {
  noteType = "Hub";
  props = `project: "[[${name}]]"\n`;
  filter = `note.project == "[[${name}]]"\n        - note.note_type != "Hub"`;
  crumb = `[[Home]] › ${name}`;
}

if (V.getAbstractFileByPath(`Projects/${name}.md`)) { new Notice(`"${name}" already exists`); return; }

await V.create(`Projects/${name}.base`,
`formulas:
  updated: file.mtime.format("DD.MM.YYYY")

views:
  - type: table
    name: Notes
    filters:
      and:
        - ${filter}
        - '!file.inFolder("System")'
    order:
      - file.name
      - note_type
      - formula.updated
newItemFolder: Notes
`);

const hub = await V.create(`Projects/${name}.md`,
`---
note_type: ${noteType}
${props}---

${crumb}

## Notes

![[${name}.base]]
`);

await app.workspace.getLeaf().openFile(hub);
new Notice(`Created ${name}`);
%>
