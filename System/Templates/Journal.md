<%*
const fileName = tp.file.title;
const folderPath = tp.file.folder(true);
const folderName = folderPath ? folderPath.split("/").pop() : "";
const isFolderNote = fileName === folderName;

let templateFile = null;

// Detection logic

if (isFolderNote && /^\d{1,2}\s+Week$/i.test(fileName)) {
    templateFile = "System/Templates/2 Template Weekly.md";
}
else if (/^\d{1,2}\s+[A-Za-z]+$/.test(fileName)) {
    templateFile = "System/Templates/3 Template Monthly.md";
}
else if (/^\d{4}$/.test(fileName)) {
    templateFile = "System/Templates/4 Template Yearly.md";
}
else{
    templateFile = "System/Templates/1 Template Daily.md";
}

// Apply template
if (templateFile) {
-%>
<% await tp.file.include(tp.file.find_tfile(templateFile)) %>
<%*
}
%>
