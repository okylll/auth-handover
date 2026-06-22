(function () {
  "use strict";

  var data = window.AUTH_HANDOVER_DATA;
  var state = {
    view: "rules",
    query: ""
  };

  var els = {
    searchInput: document.getElementById("searchInput"),
    clearSearch: document.getElementById("clearSearch"),
    tabs: Array.prototype.slice.call(document.querySelectorAll(".tab")),
    results: document.getElementById("results"),
    resultTitle: document.getElementById("resultTitle"),
    resultMeta: document.getElementById("resultMeta"),
    ruleCount: document.getElementById("ruleCount"),
    pageCount: document.getElementById("pageCount")
  };

  var STOP_WORDS = [
    "在哪里",
    "是否",
    "能否",
    "可以",
    "怎么",
    "如何",
    "什么",
    "吗",
    "呢",
    "的",
    "和",
    "与",
    "有"
  ];

  var BUSINESS_TERMS = [
    "保存并配置权限",
    "创建编辑用户",
    "超级管理员",
    "动态模板",
    "静态模板",
    "用户组",
    "区域授权",
    "选点授权",
    "导入授权",
    "菜单权限",
    "物联设备",
    "停车场",
    "角色",
    "用户",
    "权限",
    "限制",
    "回收",
    "授予",
    "继承",
    "审计",
    "配置",
    "流程",
    "页面",
    "来源",
    "保存",
    "创建",
    "编辑"
  ].sort(function (a, b) {
    return b.length - a.length;
  });

  var INTENT_TERMS = [
    "最多",
    "几个",
    "多少",
    "上限",
    "数量",
    "个数",
    "次数"
  ];

  function normalize(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/[\s!"#$%&'()*+,\-./:;<=>?@[\\\]^_`{|}~，。！？、；：“”‘’（）【】《》…—·]/g, "");
  }

  function removeStopWords(value) {
    return STOP_WORDS.reduce(function (text, word) {
      return text.split(word).join("");
    }, value);
  }

  function unique(items) {
    var seen = {};
    return items.filter(function (item) {
      if (!item || seen[item]) {
        return false;
      }
      seen[item] = true;
      return true;
    });
  }

  function getBusinessTerms(value) {
    return unique(BUSINESS_TERMS.filter(function (term) {
      return value.indexOf(term) !== -1;
    }));
  }

  function getIntentTerms(value) {
    return unique(INTENT_TERMS.filter(function (term) {
      return value.indexOf(term) !== -1;
    }));
  }

  function getBigrams(value) {
    var chars = value.split("");
    var grams = [];
    for (var index = 0; index < chars.length - 1; index += 1) {
      grams.push(chars[index] + chars[index + 1]);
    }
    return unique(grams);
  }

  function analyzeText(value) {
    var clean = normalize(value);
    var reduced = removeStopWords(clean);
    return {
      clean: clean,
      reduced: reduced,
      terms: getBusinessTerms(reduced),
      intents: getIntentTerms(reduced),
      bigrams: getBigrams(reduced)
    };
  }

  function countMatches(needles, haystack) {
    return needles.filter(function (needle) {
      return haystack.indexOf(needle) !== -1;
    }).length;
  }

  function overlapRatio(needles, haystackItems) {
    if (!needles.length) {
      return 0;
    }
    var haystack = haystackItems.join("|");
    return countMatches(needles, haystack) / needles.length;
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function listHtml(items, ordered) {
    if (!items || items.length === 0) {
      return "";
    }
    var tag = ordered ? "ol" : "ul";
    return "<" + tag + ">" + items.map(function (item) {
      return "<li>" + escapeHtml(item) + "</li>";
    }).join("") + "</" + tag + ">";
  }

  function chipList(items) {
    return '<div class="source-list">' + items.map(function (item) {
      return '<span class="chip">' + escapeHtml(item) + "</span>";
    }).join("") + "</div>";
  }

  function scoreItem(item, query, type) {
    if (!query) {
      return 1;
    }

    var queryAnalysis = analyzeText(query);
    var score = 0;
    var fields = type === "rules"
      ? [
          { value: item.id, weight: 40 },
          { value: item.title, weight: 58 },
          { value: item.question, weight: 64 },
          { value: item.conclusion.join(" "), weight: 28 },
          { value: item.notes.join(" "), weight: 18 },
          { value: (item.keywords || []).join(" "), weight: 24 },
          { value: item.sources.join(" "), weight: 12 }
        ]
      : [
          { value: item.id, weight: 40 },
          { value: item.name, weight: 64 },
          { value: item.type, weight: 18 },
          { value: item.contents.join(" "), weight: 24 },
          { value: item.keywords.join(" "), weight: 28 },
          { value: item.status, weight: 10 },
          { value: item.directory || "", weight: 8 }
        ];

    fields.forEach(function (field) {
      var fieldAnalysis = analyzeText(field.value);
      if (!fieldAnalysis.clean) {
        return;
      }

      if (fieldAnalysis.clean === queryAnalysis.clean || fieldAnalysis.reduced === queryAnalysis.reduced) {
        score += field.weight * 3;
      } else if (queryAnalysis.reduced && fieldAnalysis.reduced.indexOf(queryAnalysis.reduced) === 0) {
        score += field.weight * 2;
      } else if (queryAnalysis.reduced && fieldAnalysis.reduced.indexOf(queryAnalysis.reduced) !== -1) {
        score += field.weight;
      }

      var termHits = countMatches(queryAnalysis.terms, fieldAnalysis.reduced);
      if (termHits) {
        score += termHits * field.weight * 0.75;
      }

      var bigramCoverage = overlapRatio(queryAnalysis.bigrams, fieldAnalysis.bigrams);
      score += bigramCoverage * field.weight * 0.45;
    });

    return passesMatchThreshold(item, type, queryAnalysis, score) ? score : 0;
  }

  function getSearchableText(item, type) {
    if (type === "rules") {
      return [
        item.id,
        item.title,
        item.question,
        item.conclusion.join(" "),
        item.notes.join(" "),
        (item.keywords || []).join(" "),
        item.sources.join(" ")
      ].join(" ");
    }

    return [
      item.id,
      item.name,
      item.type,
      item.contents.join(" "),
      item.keywords.join(" "),
      item.status,
      item.directory || ""
    ].join(" ");
  }

  function passesMatchThreshold(item, type, queryAnalysis, score) {
    var textAnalysis = analyzeText(getSearchableText(item, type));
    var termHits = countMatches(queryAnalysis.terms, textAnalysis.reduced);
    var termCoverage = queryAnalysis.terms.length ? termHits / queryAnalysis.terms.length : 0;
    var bigramCoverage = overlapRatio(queryAnalysis.bigrams, textAnalysis.bigrams);
    var hasDirectHit = Boolean(
      queryAnalysis.reduced &&
      (textAnalysis.reduced.indexOf(queryAnalysis.reduced) !== -1 ||
        textAnalysis.clean.indexOf(queryAnalysis.clean) !== -1)
    );

    if (queryAnalysis.intents.length && countMatches(queryAnalysis.intents, textAnalysis.reduced) < queryAnalysis.intents.length) {
      return false;
    }

    if (hasDirectHit && score >= 24) {
      return true;
    }

    if (queryAnalysis.terms.length >= 2) {
      return termHits >= 2 && termCoverage >= 0.45 && bigramCoverage >= 0.42 && score >= 55;
    }

    if (queryAnalysis.terms.length === 1) {
      return termHits === 1 && bigramCoverage >= 0.55 && score >= 45;
    }

    return bigramCoverage >= 0.6 && score >= 45;
  }

  function getItems() {
    var items = state.view === "rules" ? data.rules : data.pages;
    var query = state.query.trim();

    if (!query) {
      return items.map(function (item, index) {
        return { item: item, score: items.length - index };
      });
    }

    return items
      .map(function (item) {
        return { item: item, score: scoreItem(item, query, state.view) };
      })
      .filter(function (entry) {
        return entry.score > 0;
      })
      .sort(function (a, b) {
        return b.score - a.score || a.item.id.localeCompare(b.item.id);
      });
  }

  function renderRule(rule) {
    return [
      '<article class="card">',
      '  <div class="card-head">',
      '    <h3>' + escapeHtml(rule.question) + "</h3>",
      '    <span class="badge">' + escapeHtml(rule.id) + "</span>",
      "  </div>",
      '  <div class="field"><span class="field-label">结论</span>' + listHtml(rule.conclusion, false) + "</div>",
      rule.notes.length ? '  <div class="field"><span class="field-label">必要说明</span>' + listHtml(rule.notes, false) + "</div>" : "",
      '  <div class="field"><span class="field-label">来源页面</span>' + chipList(rule.sources) + "</div>",
      "</article>"
    ].join("");
  }

  function renderPage(page) {
    return [
      '<article class="card">',
      '  <div class="card-head">',
      '    <h3>' + escapeHtml(page.name) + "</h3>",
      '    <span class="badge type">' + escapeHtml(page.id) + "</span>",
      "  </div>",
      '  <div class="field"><span class="field-label">页面类型</span><p>' + escapeHtml(page.type) + "</p></div>",
      '  <div class="field"><span class="field-label">主要内容</span>' + listHtml(page.contents, false) + "</div>",
      '  <div class="page-actions">',
      '    <a class="pixso-link" href="' + escapeHtml(page.pixsoUrl) + '" target="_blank" rel="noopener noreferrer">查看 Pixso</a>',
      '    <span class="status">当前状态：' + escapeHtml(page.status) + "</span>",
      "  </div>",
      "</article>"
    ].join("");
  }

  function render() {
    var entries = getItems();
    var isRules = state.view === "rules";
    var query = state.query.trim();
    var total = isRules ? data.rules.length : data.pages.length;
    var label = isRules ? "权限规则" : "流程索引";

    els.tabs.forEach(function (tab) {
      var active = tab.getAttribute("data-view") === state.view;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", active ? "true" : "false");
    });

    els.resultTitle.textContent = query ? "搜索结果" : "全部" + label;
    els.resultMeta.textContent = query
      ? "在" + label + "中找到 " + entries.length + " 条匹配内容。"
      : "共 " + total + " 条" + label + "。";

    if (entries.length === 0) {
      els.results.innerHTML = '<div class="empty">' + escapeHtml(data.emptyMessage) + "</div>";
      return;
    }

    els.results.innerHTML = entries.map(function (entry) {
      return isRules ? renderRule(entry.item) : renderPage(entry.item);
    }).join("");
  }

  function bindEvents() {
    els.searchInput.addEventListener("input", function (event) {
      state.query = event.target.value;
      render();
    });

    els.clearSearch.addEventListener("click", function () {
      state.query = "";
      els.searchInput.value = "";
      els.searchInput.focus();
      render();
    });

    els.tabs.forEach(function (tab) {
      tab.addEventListener("click", function () {
        state.view = tab.getAttribute("data-view");
        render();
      });
    });
  }

  function init() {
    els.ruleCount.textContent = data.rules.length;
    els.pageCount.textContent = data.pages.length;
    bindEvents();
    render();
  }

  init();
}());
