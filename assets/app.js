(function () {
  const data = window.XHS_DATA;
  if (!data) return;

  const PALETTE = [
    "#f48fb1", "#ff8a80", "#ce93d8", "#90caf9", "#80cbc4",
    "#ffcc80", "#a5d6a7", "#9fa8da", "#ef9a9a", "#80deea",
    "#b39ddb", "#ffab91", "#81c784", "#64b5f6", "#f06292"
  ];

  const firstCategory = (data.categories && data.categories[0]) || null;
  const state = {
    query: "",
    sort: "time",
    category: firstCategory ? firstCategory.id : "all",
    skillId: (firstCategory && firstCategory.skillId) || (data.skills && data.skills[0] && data.skills[0].id) || "",
    expandAll: false,
    expanded: new Set(),
    collapsed: new Set(),
    likes: new Set()
  };

  const els = {
    sourceLink: document.getElementById("sourceLink"),
    noteCard: document.getElementById("noteCard"),
    tocList: document.getElementById("tocList"),
    tocCount: document.getElementById("tocCount"),
    sheetTitle: document.getElementById("sheetTitle"),
    sheetSub: document.getElementById("sheetSub"),
    commentList: document.getElementById("commentList"),
    emptyState: document.getElementById("emptyState"),
    searchInput: document.getElementById("searchInput"),
    sortSelect: document.getElementById("sortSelect"),
    expandAllToggle: document.getElementById("expandAllToggle"),
    categoryChips: document.getElementById("categoryChips"),
    backTop: document.getElementById("backTop"),
    pageUpdated: document.getElementById("pageUpdated"),
    skillList: document.getElementById("skillList"),
    skillCount: document.getElementById("skillCount"),
    skillDetail: document.getElementById("skillDetail")
  };

  function hashName(name) {
    let hash = 0;
    for (const ch of name) hash = (hash * 33 + ch.codePointAt(0)) >>> 0;
    return hash;
  }

  function avatarLetter(name, isAuthor) {
    if (isAuthor || name === "李沐") return "沐";
    const chars = Array.from(name.trim());
    return chars[0] || "?";
  }

  function avatarStyle(name, isAuthor) {
    if (isAuthor) return "";
    return `background:${PALETTE[hashName(name) % PALETTE.length]}`;
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function renderRichText(text) {
    return escapeHtml(text).replace(
      /\[([^\[\]\n]{1,16})\]/g,
      '<span class="sticker">$1</span>'
    );
  }

  function formatTime(datetime) {
    if (!datetime) return "";
    const [date, time] = datetime.split(" ");
    const [, month, day] = date.split("-");
    return `${Number(month)}-${day} ${time}`;
  }

  function threadText(thread) {
    const parts = [
      thread.root.name,
      thread.root.content,
      ...thread.replies.flatMap((item) => [item.name, item.content, item.replyTo || ""])
    ];
    return parts.join("\n").toLowerCase();
  }

  function authorReplies(thread) {
    return thread.replies.filter((item) => item.isAuthor);
  }

  function otherReplyCount(thread) {
    return thread.replies.length - authorReplies(thread).length;
  }

  function visibleText(thread) {
    const parts = [
      thread.root.name,
      thread.root.content,
      ...authorReplies(thread).flatMap((item) => [item.name, item.content, item.replyTo || ""])
    ];
    return parts.join("\n").toLowerCase();
  }

  function isExpanded(thread) {
    if (state.collapsed.has(thread.dialogId)) return false;
    if (state.expandAll || state.expanded.has(thread.dialogId)) return true;
    const query = state.query.trim().toLowerCase();
    if (!query) return false;
    if (visibleText(thread).includes(query)) return false;
    return threadText(thread).includes(query);
  }

  function categories() {
    return data.categories || [];
  }

  function skills() {
    return data.skills || [];
  }

  function skillById(id) {
    return skills().find((item) => item.id === id) || null;
  }

  function skillForCategory(categoryId) {
    const cat = categories().find((item) => item.id === categoryId);
    if (cat && cat.skillId) return skillById(cat.skillId);
    return skills().find((item) => item.categoryId === categoryId) || null;
  }

  function inlineMd(text) {
    return escapeHtml(text)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\*([^*]+)\*/g, "<em>$1</em>");
  }

  function renderMarkdown(md) {
    const lines = String(md || "").replace(/\r\n/g, "\n").split("\n");
    const out = [];
    let i = 0;
    while (i < lines.length) {
      const line = lines[i];
      if (/^##\s+/.test(line)) {
        out.push(`<h2>${inlineMd(line.replace(/^##\s+/, ""))}</h2>`);
        i += 1;
        continue;
      }
      if (/^#\s+/.test(line)) {
        out.push(`<h1>${inlineMd(line.replace(/^#\s+/, ""))}</h1>`);
        i += 1;
        continue;
      }
      if (/^[-*]\s+/.test(line)) {
        const items = [];
        while (i < lines.length && /^[-*]\s+/.test(lines[i])) {
          items.push(`<li>${inlineMd(lines[i].replace(/^[-*]\s+/, ""))}</li>`);
          i += 1;
        }
        out.push(`<ul>${items.join("")}</ul>`);
        continue;
      }
      if (/^\d+\.\s+/.test(line)) {
        const items = [];
        while (i < lines.length && /^\d+\.\s+/.test(lines[i])) {
          items.push(`<li>${inlineMd(lines[i].replace(/^\d+\.\s+/, ""))}</li>`);
          i += 1;
        }
        out.push(`<ol>${items.join("")}</ol>`);
        continue;
      }
      if (!line.trim()) {
        i += 1;
        continue;
      }
      const paras = [line];
      i += 1;
      while (
        i < lines.length &&
        lines[i].trim() &&
        !/^#{1,2}\s/.test(lines[i]) &&
        !/^[-*]\s+/.test(lines[i]) &&
        !/^\d+\.\s+/.test(lines[i])
      ) {
        paras.push(lines[i]);
        i += 1;
      }
      out.push(`<p>${inlineMd(paras.join(" "))}</p>`);
    }
    return out.join("");
  }

  function skillIndexLabel(skill) {
    const match = String(skill.categoryId || "").match(/^(\d+)/);
    return match ? match[1] : "";
  }

  function selectSkill(id, updateHash) {
    if (!skillById(id)) return;
    state.skillId = id;
    if (updateHash) {
      history.replaceState(null, "", `#skill-${id}`);
    }
  }

  function renderSkills() {
    if (!els.skillList || !els.skillDetail) return;
    const list = skills();
    if (els.skillCount) els.skillCount.textContent = `${list.length} 个`;
    els.skillList.innerHTML = list.map((skill) => {
      const label = skill.titleZh || skill.title;
      return `
      <li>
        <button type="button" data-skill="${escapeHtml(skill.id)}" class="${state.skillId === skill.id ? "active" : ""}"${state.skillId === skill.id ? ' aria-current="true"' : ""}>
          <span class="idx">${escapeHtml(skillIndexLabel(skill))}</span>
          <span class="q">${escapeHtml(label)}</span>
        </button>
      </li>
    `;
    }).join("");
    const skill = skillById(state.skillId) || list[0];
    if (!skill) {
      els.skillDetail.innerHTML = '<p class="skill-empty">暂无技能</p>';
      return;
    }
    const cat = categories().find((item) => item.id === skill.categoryId);
    const lead = (cat && cat.description) || "";
    els.skillDetail.innerHTML = `
      <header class="skill-detail-head">
        <h1>${escapeHtml(skill.titleZh || skill.title)}</h1>
        ${skill.titleZh && skill.title ? `<p class="skill-en">${escapeHtml(skill.title)}</p>` : ""}
        ${lead ? `<p class="skill-lead">${escapeHtml(lead)}</p>` : ""}
      </header>
      <div class="skill-md">${renderMarkdown(skill.body)}</div>
    `;
  }

  function searchSortedThreads() {
    const query = state.query.trim().toLowerCase();
    let threads = data.threads.filter((thread) => {
      if (!query) return true;
      return threadText(thread).includes(query);
    });
    threads = threads.slice();
    if (state.sort === "replies") {
      threads.sort((a, b) => b.replyCount - a.replyCount || a.dialogId.localeCompare(b.dialogId));
    } else if (state.sort === "id") {
      threads.sort((a, b) => a.dialogId.localeCompare(b.dialogId));
    } else {
      threads.sort((a, b) => a.root.datetime.localeCompare(b.root.datetime) || a.dialogId.localeCompare(b.dialogId));
    }
    return threads;
  }

  function visibleThreads() {
    const threads = searchSortedThreads();
    if (state.category === "all") return threads;
    return threads.filter((thread) => thread.categoryId === state.category);
  }

  function groupedThreads(threads) {
    const cats = categories();
    const groups = cats
      .map((cat) => ({
        ...cat,
        threads: threads.filter((thread) => thread.categoryId === cat.id)
      }))
      .filter((group) => group.threads.length);
    const known = new Set(cats.map((cat) => cat.id));
    const leftover = threads.filter((thread) => !known.has(thread.categoryId));
    if (leftover.length) {
      groups.push({
        id: "uncategorized",
        titleZh: "未分类",
        description: "",
        threads: leftover
      });
    }
    return groups;
  }

  function likeKey(threadId, index) {
    return `${threadId}:${index}`;
  }

  function heartSvg() {
    return '<svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true"><path d="M12.1 20.3s-6.6-4.2-8.8-8.1C1.6 9.1 3 6 6.2 6c1.8 0 3 1.1 3.8 2.3C10.8 7.1 12 6 13.8 6c3.2 0 4.6 3.1 2.9 6.2-2.2 3.9-8.6 8.1-8.6 8.1z" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/></svg>';
  }

  function renderComment(comment, threadId, index, isReply) {
    const key = likeKey(threadId, index);
    const liked = state.likes.has(key);
    const authorClass = comment.isAuthor ? " author-reply" : "";
    const replyPrefix = comment.replyTo
      ? `<span class="reply-to">回复 <em>${escapeHtml(comment.replyTo)}</em>：</span>`
      : "";
    const location = comment.location ? ` · ${escapeHtml(comment.location)}` : "";
    return `
      <article class="comment${isReply ? " reply" : ""}${authorClass}">
        <div class="avatar${comment.isAuthor ? " author" : ""}" style="${avatarStyle(comment.name, comment.isAuthor)}">${escapeHtml(avatarLetter(comment.name, comment.isAuthor))}</div>
        <div class="body">
          <div class="name-line">
            <span class="username${comment.isAuthor ? " author-name" : ""}">${escapeHtml(comment.name)}</span>
            ${comment.isAuthor ? '<span class="badge">作者</span>' : ""}
          </div>
          <div class="content">${replyPrefix}${renderRichText(comment.content)}</div>
          <div class="info">
            <span>${escapeHtml(formatTime(comment.datetime))}${location}</span>
            <span class="reply-label">回复</span>
          </div>
        </div>
        <button class="like${liked ? " active" : ""}" type="button" data-like="${escapeHtml(key)}" aria-label="点赞">
          ${heartSvg()}
        </button>
      </article>
    `;
  }

  function renderExpandControl(thread, expanded) {
    const hiddenCount = otherReplyCount(thread);
    if (hiddenCount <= 0) return "";
    if (expanded) {
      return `<button class="expand-btn" type="button" data-expand="${escapeHtml(thread.dialogId)}" aria-expanded="true">收起 ${hiddenCount} 条回复</button>`;
    }
    return `<button class="expand-btn" type="button" data-expand="${escapeHtml(thread.dialogId)}" aria-expanded="false">展开 ${hiddenCount} 条回复</button>`;
  }

  function renderThread(thread) {
    const expanded = isExpanded(thread);
    const replies = expanded ? thread.replies : authorReplies(thread);
    const replyBits = replies
      .map((item, idx) => renderComment(item, thread.dialogId, idx + 1, true))
      .join("");
    return `
      <section class="thread${expanded ? " is-expanded" : ""}" id="thread-${thread.dialogId}">
        ${renderComment(thread.root, thread.dialogId, 0, false)}
        ${replyBits}
        ${renderExpandControl(thread, expanded)}
      </section>
    `;
  }

  function renderNote() {
    const note = data.sourceNote;
    const stats = data.stats;
    els.sourceLink.href = note.url;
    els.noteCard.innerHTML = `
      <div class="note-user">
        <div class="avatar author">沐</div>
        <div class="meta">
          <div class="name-row">
            <span class="name">${escapeHtml(note.author)}</span>
            <span class="badge">${escapeHtml(note.badge)}</span>
          </div>
          <div class="when">${escapeHtml(note.posted)} · ${escapeHtml(note.location)}</div>
        </div>
      </div>
      <p class="note-content">${escapeHtml(note.content)}</p>
      <div class="tags">${note.tags.map((tag) => `<span class="tag">#${escapeHtml(tag)}</span>`).join("")}</div>
      <div class="stats">
        <div class="stat"><b>${stats.authorThreads}</b><span>作者回复楼层</span></div>
        <div class="stat"><b>${stats.authorReplies}</b><span>李沐回复</span></div>
        <div class="stat"><b>${stats.mainComments}</b><span>主评论</span></div>
        <div class="stat"><b>${stats.allComments}</b><span>所有评论</span></div>
      </div>
      <p class="updated">最后更新：${escapeHtml(stats.updatedAt)}</p>
    `;
    if (els.pageUpdated) {
      els.pageUpdated.textContent = `最后更新：${stats.updatedAt}`;
    }
    els.sheetTitle.textContent = `${firstCategory ? firstCategory.titleZh + " · " + (firstCategory.count || "") + " 条" : "评论"}`;
    els.sheetSub.textContent = `${stats.parsedThreads} 条提问中，仅展示李沐回复过的 ${stats.authorThreads} 条楼层，按 10 个主题分类；其他回复默认收起`;
  }

  function renderChips(searched) {
    if (!els.categoryChips) return;
    const counts = {};
    categories().forEach((cat) => { counts[cat.id] = 0; });
    searched.forEach((thread) => {
      if (counts[thread.categoryId] != null) counts[thread.categoryId] += 1;
    });
    const chips = [
      `<button class="chip${state.category === "all" ? " active" : ""}" type="button" data-cat="all" role="tab" aria-selected="${state.category === "all"}">全部 <b>${searched.length}</b></button>`
    ];
    categories().forEach((cat) => {
      const active = state.category === cat.id;
      chips.push(
        `<button class="chip${active ? " active" : ""}" type="button" data-cat="${escapeHtml(cat.id)}" role="tab" aria-selected="${active}">${escapeHtml(cat.titleZh)} <b>${counts[cat.id] || 0}</b></button>`
      );
    });
    els.categoryChips.innerHTML = chips.join("");
  }

  function renderToc(threads) {
    const groups = groupedThreads(threads);
    els.tocCount.textContent = `${threads.length} 条`;
    els.tocList.innerHTML = groups.map((group) => `
      <li class="toc-cat">${escapeHtml(group.titleZh)} · ${group.threads.length}</li>
      ${group.threads.map((thread) => `
        <li>
          <a href="#thread-${thread.dialogId}">
            <span class="idx">${escapeHtml(thread.dialogId)}</span>
            <span class="q">${escapeHtml(thread.root.content)}</span>
          </a>
        </li>
      `).join("")}
    `).join("");
  }

  function render() {
    const searched = searchSortedThreads();
    const threads = visibleThreads();
    renderChips(searched);
    renderToc(threads);
    const groups = groupedThreads(threads);
    els.commentList.innerHTML = groups.map((group) => `
      <section class="category-block" id="cat-${escapeHtml(group.id)}">
        <header class="category-head">
          <h2>${escapeHtml(group.titleZh)} <b>${group.threads.length}</b></h2>
          ${group.description ? `<p>${escapeHtml(group.description)}</p>` : ""}
        </header>
        ${group.threads.map((thread) => renderThread(thread)).join("")}
      </section>
    `).join("");
    els.emptyState.hidden = threads.length > 0;
    const searching = Boolean(state.query.trim());
    const cat = categories().find((item) => item.id === state.category);
    if (searching) {
      els.sheetTitle.textContent = `找到 ${threads.length} 条楼层`;
    } else if (state.category === "all") {
      els.sheetTitle.textContent = `全部 · ${threads.length} 条`;
    } else if (cat) {
      els.sheetTitle.textContent = `${cat.titleZh} · ${threads.length} 条`;
    } else {
      els.sheetTitle.textContent = `共 ${data.stats.shownComments} 条评论`;
    }
    renderSkills();
    highlightActiveToc();
  }

  function highlightActiveToc() {
    const hash = decodeURIComponent(location.hash || "");
    els.tocList.querySelectorAll("a").forEach((link) => {
      link.classList.toggle("active", hash && link.getAttribute("href") === hash);
    });
  }

  function applyHash() {
    const hash = decodeURIComponent(location.hash || "").replace(/^#/, "");
    if (hash.startsWith("cat-")) {
      const id = hash.slice(4);
      if (id === "all" || categories().some((cat) => cat.id === id)) {
        state.category = id === "all" ? "all" : id;
        const skill = skillForCategory(state.category);
        if (skill) state.skillId = skill.id;
      }
    } else if (hash.startsWith("skill-")) {
      const id = hash.slice(6);
      if (skillById(id)) state.skillId = id;
    }
  }

  els.searchInput.addEventListener("input", () => {
    state.query = els.searchInput.value;
    render();
  });

  els.sortSelect.addEventListener("change", () => {
    state.sort = els.sortSelect.value;
    render();
  });

  els.expandAllToggle.addEventListener("change", () => {
    state.expandAll = els.expandAllToggle.checked;
    state.expanded.clear();
    state.collapsed.clear();
    render();
  });

  if (els.categoryChips) {
    els.categoryChips.addEventListener("click", (event) => {
      const btn = event.target.closest("[data-cat]");
      if (!btn) return;
      const id = btn.getAttribute("data-cat");
      state.category = id;
      const skill = skillForCategory(id);
      if (skill) state.skillId = skill.id;
      render();
      if (id === "all") {
        history.replaceState(null, "", location.pathname + location.search);
        const sheet = document.querySelector(".sheet");
        if (sheet) sheet.scrollIntoView({ block: "start", behavior: "smooth" });
      } else {
        history.replaceState(null, "", `#cat-${id}`);
        const target = document.getElementById(`cat-${id}`);
        if (target) target.scrollIntoView({ block: "start", behavior: "smooth" });
      }
    });
  }

  els.commentList.addEventListener("click", (event) => {
    const expandBtn = event.target.closest("[data-expand]");
    if (expandBtn) {
      const id = expandBtn.getAttribute("data-expand");
      const open = expandBtn.getAttribute("aria-expanded") === "true";
      if (state.expandAll) {
        state.expandAll = false;
        els.expandAllToggle.checked = false;
        data.threads.forEach((thread) => {
          if (thread.dialogId !== id) state.expanded.add(thread.dialogId);
        });
        state.collapsed.add(id);
      } else if (open) {
        state.expanded.delete(id);
        state.collapsed.add(id);
      } else {
        state.collapsed.delete(id);
        state.expanded.add(id);
      }
      render();
      return;
    }
    const btn = event.target.closest("[data-like]");
    if (!btn) return;
    const key = btn.getAttribute("data-like");
    if (state.likes.has(key)) state.likes.delete(key);
    else state.likes.add(key);
    btn.classList.toggle("active", state.likes.has(key));
  });

  els.backTop.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  if (els.skillList) {
    els.skillList.addEventListener("click", (event) => {
      const btn = event.target.closest("[data-skill]");
      if (!btn) return;
      selectSkill(btn.getAttribute("data-skill"), true);
      render();
    });
  }

  window.addEventListener("hashchange", () => {
    const hash = decodeURIComponent(location.hash || "").replace(/^#/, "");
    if (hash.startsWith("cat-") || hash.startsWith("skill-")) {
      applyHash();
      render();
    }
    highlightActiveToc();
  });

  applyHash();
  renderNote();
  render();
})();
