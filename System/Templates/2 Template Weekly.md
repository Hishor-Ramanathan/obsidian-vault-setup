---
note_type: Weekly
created: <% tp.date.now('YYYY-MM-DD') %>
rating:
---

[[|Last Week]] | [[|Next Week]]

# Weekly Goal
 - [ ] 
# Weekly Reflexion 

## What did I learn this Week?


## Which habit did I keep consistently? Which did I neglect?

```dataviewjs
// Kept AND neglected, in THIS note's week - not "the last 7 days", which made
// every weekly note show the current week. A week can straddle two month
// folders (10 October/44 Week + 11 November/44 Week), so match the week folder
// name inside the year rather than this one folder. Full history: [[Habits]]
const DAILY_NAME = /^\d{2}\.\d{2}\.\d{4}$/;
const [, year, , week] = dv.current().file.folder.split("/");

const tally = new Map();   // habit -> { offered, done }
for (const page of dv.pages(`"Journal/${year}"`)) {
  if (!DAILY_NAME.test(page.file.name)) continue;
  if (page.file.folder.split("/").pop() !== week) continue;
  for (const task of page.file.tasks) {
    const name = task.text.trim();
    if (!name) continue;
    const row = tally.get(name) ?? { offered: 0, done: 0 };
    row.offered++;
    if (task.completed) row.done++;
    tally.set(name, row);
  }
}

const rows = [...tally].sort((a, b) => a[1].done / a[1].offered - b[1].done / b[1].offered);
dv.table(["Habit", "Kept", "Offered"], rows.map(([name, r]) => [name, r.done, r.offered]));
if (rows.length && rows[0][1].done === 0) dv.paragraph(`Neglected all week: **${rows[0][0]}**.`);
```


## What was my biggest achievement this week?


## What do I want to focus on next week to grow?

