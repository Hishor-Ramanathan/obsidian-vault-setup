---
note_type: Book Summary
created: <% tp.date.now('YYYY-MM-DD') %>
category:
  - "<%= (Array.isArray(book.categories) ? book.categories.flat() : [book.categories]).filter(Boolean).map(category => `[[${category}]]`).join(', ') %>"
author:
  - "<%= (Array.isArray(book.authors) ? book.authors.flat() : [book.authors]).filter(Boolean).map(author => `[[${author }]]`).join(', ') %>"
rating:
status: In Progress
year: <%= book.publishDate.substring(0, 4) %>
pages: {{totalPage}}
cover: '[[<% tp.file.title.replace(/"/g, "") %>.jpg]]'
---
# Key Ideas


# Summary

## 1 

# Quotes
