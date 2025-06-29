import os
import json

DIR = "htmls"
files = sorted([
    f for f in os.listdir(DIR)
    if f.endswith(".html") and f != "index.html"
])

# 1. Write filelist.json
with open(os.path.join(DIR, "filelist.json"), "w", encoding="utf-8") as f:
    json.dump(files, f, ensure_ascii=False, indent=2)

# 2. Write index.html
with open(os.path.join(DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write("""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>HTML 파일 목록</title>
</head>
<body>
  <h1>HTML 파일 목록</h1>
  <ul id="file-list"></ul>

  <script>
    fetch("filelist.json")
      .then(response => response.json())
      .then(files => {
        const list = document.getElementById("file-list");
        files.forEach(file => {
          const li = document.createElement("li");
          const a = document.createElement("a");
          a.href = file;
          a.textContent = file;
          a.target = "_blank";
          li.appendChild(a);
          list.appendChild(li);
        });
      });
  </script>
</body>
</html>""")
