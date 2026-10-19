<%*
// Create the Week / Month / Year folder notes above this day, if any are missing.
//   Journal/2026/8 August/32 Week/04.08.2026.md
//     -> 32 Week/32 Week.md    (Weekly template)
//     -> 8 August/8 August.md  (Monthly template)
//     -> 2026/2026.md          (Yearly template)
const V = app.vault;
const TPL = "System/Templates";
const parts = tp.file.folder(true).split("/");
const root = parts.indexOf("Journal");
if (root !== -1) {
  for (let n = parts.length; n > root + 1; n--) {
    const name = parts[n - 1];
    const path = parts.slice(0, n).join("/") + "/" + name + ".md";
    if (V.getAbstractFileByPath(path)) continue;
    let tpl = null;
    // Both shapes: "32 Week" (current) and "Week 10" (from the old [Week] W
    // format). Matching only the first silently produced four weeks with no
    // weekly note at all - see issue #2.
    if (/^(?:\d{1,2}\s+Week|Week\s+\d{1,2})$/i.test(name))
                                           tpl = `${TPL}/2 Template Weekly.md`;
    else if (/^\d{4}$/.test(name))         tpl = `${TPL}/4 Template Yearly.md`;
    else if (/^\d{1,2}\s+\S+$/.test(name)) tpl = `${TPL}/3 Template Monthly.md`;
    await V.create(path, tpl ? await tp.file.include(tp.file.find_tfile(tpl)) : "");
  }
}
-%>
---
note_type: Daily
created: <% tp.date.now('YYYY-MM-DD') %>
experienced:
rating:
time_focused:
---

[[<% tp.date.now("DD.MM.YYYY", -1) %>|Yesterday]] | [[<% tp.date.now("DD.MM.YYYY", 1) %>|Tomorrow]]

#### Goals
- [ ] Physical Activity
- [ ] Meditate
- [ ] Deep Work

#### To Dos
- [ ] 

# Note

## Learning Journal


### Notes created today

```dataview
List FROM "" WHERE file.cday = date("<%tp.date.now('YYYY-MM-DD')%>") SORT file.mtime asc
```

### Notes last touched today

```dataview
List FROM "" WHERE file.mday = date("<%tp.date.now('YYYY-MM-DD')%>") SORT file.mtime asc
```
