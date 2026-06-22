(function () {
  "use strict";

  var GUIDE_PATH = "./docs/CODEX-USER-GUIDE.md";
  var contentEl = document.getElementById("guideContent");

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function isSafeHref(value) {
    return /^(https?:\/\/|\.{0,2}\/|#)/.test(value);
  }

  function renderInline(value) {
    var codeTokens = [];
    var text = escapeHtml(value).replace(/`([^`]+)`/g, function (_, code) {
      var token = "\u0000CODE" + codeTokens.length + "\u0000";
      codeTokens.push("<code>" + code + "</code>");
      return token;
    });

    text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function (_, label, href) {
      var cleanHref = href.trim();
      var safeHref = isSafeHref(cleanHref) ? cleanHref : "#";
      var external = /^https?:\/\//.test(safeHref);
      var attrs = external ? ' target="_blank" rel="noopener noreferrer"' : "";
      return '<a href="' + safeHref + '"' + attrs + ">" + label + "</a>";
    });

    text = text.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

    codeTokens.forEach(function (html, index) {
      text = text.replace("\u0000CODE" + index + "\u0000", html);
    });

    return text;
  }

  function renderMarkdown(markdown) {
    var lines = markdown.replace(/\r\n?/g, "\n").split("\n");
    var html = [];
    var paragraph = [];
    var list = null;
    var inCode = false;
    var codeLines = [];

    function flushParagraph() {
      if (!paragraph.length) {
        return;
      }
      html.push("<p>" + renderInline(paragraph.join(" ")) + "</p>");
      paragraph = [];
    }

    function flushList() {
      if (!list) {
        return;
      }
      html.push("<" + list.type + ">" + list.items.map(function (item) {
        return "<li>" + renderInline(item) + "</li>";
      }).join("") + "</" + list.type + ">");
      list = null;
    }

    function flushCode() {
      html.push("<pre><code>" + escapeHtml(codeLines.join("\n")) + "</code></pre>");
      codeLines = [];
    }

    lines.forEach(function (line) {
      var heading;
      var unordered;
      var ordered;

      if (/^```/.test(line.trim())) {
        if (inCode) {
          flushCode();
          inCode = false;
        } else {
          flushParagraph();
          flushList();
          inCode = true;
          codeLines = [];
        }
        return;
      }

      if (inCode) {
        codeLines.push(line);
        return;
      }

      if (!line.trim()) {
        flushParagraph();
        flushList();
        return;
      }

      heading = /^(#{1,3})\s+(.+)$/.exec(line);
      if (heading) {
        flushParagraph();
        flushList();
        html.push("<h" + heading[1].length + ">" + renderInline(heading[2]) + "</h" + heading[1].length + ">");
        return;
      }

      unordered = /^\s*[-*+]\s+(.+)$/.exec(line);
      ordered = /^\s*\d+\.\s+(.+)$/.exec(line);

      if (unordered || ordered) {
        var type = ordered ? "ol" : "ul";
        var item = (ordered || unordered)[1];
        flushParagraph();
        if (!list || list.type !== type) {
          flushList();
          list = { type: type, items: [] };
        }
        list.items.push(item);
        return;
      }

      flushList();
      paragraph.push(line.trim());
    });

    if (inCode) {
      flushCode();
    }
    flushParagraph();
    flushList();

    return html.join("");
  }

  fetch(GUIDE_PATH)
    .then(function (response) {
      if (!response.ok) {
        throw new Error("无法加载使用手册");
      }
      return response.text();
    })
    .then(function (markdown) {
      contentEl.innerHTML = renderMarkdown(markdown);
    })
    .catch(function () {
      contentEl.innerHTML = '<p class="guide-error">使用手册加载失败，请返回知识库后重试。</p>';
    });
}());
