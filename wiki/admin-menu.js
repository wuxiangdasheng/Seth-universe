/* === 棱镜后台导航 — 节点式可折叠菜单（管理版）=== */
(function() {
  const ACTIVE = document.documentElement.dataset.activeWorld || 'concept-world';
  const KEY = 'seth_admin_nav';

  const worlds = [
    {
      id: 'book-world',
      label: '书宇宙管理',
      labelEn: 'Book Management',
      icon: 'book',
      href: '#',
      accent: '#d4af37',
      subs: [
        { label: '全部典籍', href: '#', desc: 'Book management' },
        { label: '灵魂永生', href: '#', desc: 'Life Before Life' },
        { label: '个人实相', href: '#', desc: 'Personal Reality' },
        { label: '未知的实相', href: '#', desc: 'Unknown Reality' },
        { label: '心灵的本质', href: '#', desc: 'Mass Psyche' },
        { label: '神奇之道', href: '#', desc: 'Magic Approach' }
      ]
    },
    {
      id: 'concept-world',
      label: '理宇宙管理',
      labelEn: 'Concept Management',
      icon: 'concept',
      href: '#',
      accent: '#7a6ab0',
      subs: [
        { label: '核心概念', href: 'admin.html', desc: 'core concepts', countKey: 'concepts' },
        { label: '金句观点', href: 'admin-quotes.html', desc: 'original quotes', countKey: 'quotes' },
        { label: '方法练习', href: '#', desc: 'Methods & exercises' },
        { label: '专题', href: 'admin-topics.html', desc: 'Topics & themes' },
        { label: '机制原理', href: '#', desc: 'Mechanisms & principles' },
        { label: '人物实体', href: '#', desc: 'Entities & personas' }
      ]
    },
    {
      id: 'dream-world',
      label: '梦宇宙管理',
      labelEn: 'Dream Management',
      icon: 'dream',
      href: 'admin-dream.html',
      accent: '#5a8ab0',
      subs: [
        { label: '梦境地图', href: '#', desc: 'Dream landscape' },
        { label: '梦练习', href: '#', desc: 'Dream exercises' },
        { label: '梦概念', href: '#', desc: 'Dream concepts' }
      ]
    },
    {
      id: 'ai-world',
      label: 'AI赛斯管理',
      labelEn: 'AI Management',
      icon: 'ai',
      href: '#',
      accent: '#4a8fa1',
      subs: [
        { label: 'AI对话', href: '#', desc: 'Interactive dialogue' },
        { label: '知识库', href: '#', desc: 'Knowledge base' }
      ]
    },
    {
      id: 'system-world',
      label: '系统管理',
      labelEn: 'System',
      icon: 'system',
      href: '#',
      accent: '#888',
      subs: [
        { label: '内容备份管理', href: 'admin-backup.html', desc: 'Backup management' }
      ]
    }
  ];

  /* 状态管理 */
  let state = { collapsed: false, expandedNode: ACTIVE };
  try {
    const s = localStorage.getItem(KEY);
    if (s) Object.assign(state, JSON.parse(s));
  } catch(e) {}

  function save() {
    localStorage.setItem(KEY, JSON.stringify(state));
  }

  const curWorld = worlds.find(w => w.id === ACTIVE) || worlds[1];

  /* SVG图标路径 */
  const icons = {
    book: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
      <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
    </svg>`,
    concept: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="3"/>
      <circle cx="12" cy="12" r="8" stroke-dasharray="4 3"/>
      <line x1="12" y1="2" x2="12" y2="6"/>
      <line x1="12" y1="18" x2="12" y2="22"/>
      <line x1="2" y1="12" x2="6" y2="12"/>
      <line x1="18" y1="12" x2="22" y2="12"/>
    </svg>`,
    dream: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
    </svg>`,
    ai: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="8" width="18" height="12" rx="2"/>
      <circle cx="9" cy="14" r="1.5" fill="currentColor"/>
      <circle cx="15" cy="14" r="1.5" fill="currentColor"/>
      <path d="M12 2v4"/>
      <path d="M8 4h8"/>
      <path d="M12 20v2"/>
    </svg>`,
    system: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="12" r="3"/>
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
    </svg>`
  };

  /* 创建DOM */
  const nav = document.createElement('nav');
  nav.id = 'prism-nav';
  nav.className = state.collapsed ? 'pn-collapsed' : '';

  /* 设置初始CSS变量 */
  document.documentElement.style.setProperty('--prism-w', state.collapsed ? 'var(--prism-collapsed-w)' : 'var(--prism-expanded-w)');

  nav.innerHTML = `
    <div class="pn-inner">
      <div class="pn-nodes">
        ${worlds.map(w => {
          const isActive = w.id === ACTIVE;
          const isExpanded = state.expandedNode === w.id && !state.collapsed;
          return `
            <div class="pn-node${isActive ? ' pn-node-active' : ''}${isExpanded ? ' pn-node-expanded' : ''}" data-node="${w.id}">
              <a class="pn-node-trigger" href="${w.href}" ${isActive ? 'aria-current="page"' : ''}>
                <span class="pn-node-icon" style="color:${w.accent}">${icons[w.icon]}</span>
                <span class="pn-node-label">${w.label}</span>
                <span class="pn-node-label-en">${w.labelEn}</span>
                ${isActive ? '<span class="pn-node-glow"></span>' : ''}
              </a>
              <div class="pn-node-subs">
                ${w.subs.map(s => `
                  <a class="pn-sub" href="${s.href}" ${s.countKey ? `data-count-key="${s.countKey}"` : ''}>
                    <span class="pn-sub-dot"></span>
                    <div class="pn-sub-text">
                      <span class="pn-sub-label">${s.label}</span>
                      <span class="pn-sub-desc">${s.desc}</span>
                    </div>
                  </a>
                `).join('')}
              </div>
            </div>
          `;
        }).join('')}
      </div>
      <div class="pn-footer">
        <button class="pn-toggle" aria-label="${state.collapsed ? '展开' : '收起'}">
          <span class="pn-toggle-icon">${state.collapsed ? '›' : '‹'}</span>
          <span class="pn-toggle-text">${state.collapsed ? '展开' : '收起'}</span>
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(nav);

  /* 绑定事件 */
  const toggle = nav.querySelector('.pn-toggle');
  toggle.addEventListener('click', function() {
    state.collapsed = !state.collapsed;
    if (!state.collapsed && !state.expandedNode) {
      state.expandedNode = ACTIVE;
    }
    save();
    updateView();
  });

  nav.querySelectorAll('.pn-node-trigger').forEach(trigger => {
    trigger.addEventListener('click', function(e) {
      e.preventDefault();
      if (state.collapsed) {
        state.collapsed = false;
        state.expandedNode = this.closest('.pn-node').dataset.node;
        save();
        updateView();
      } else {
        const nodeId = this.closest('.pn-node').dataset.node;
        state.expandedNode = state.expandedNode === nodeId ? null : nodeId;
        save();
        updateView();
      }
    });
  });

  nav.querySelectorAll('.pn-sub').forEach(sub => {
    sub.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href && href !== '#') {
        return;  // let normal navigation happen
      }
      e.preventDefault();
    });
  });

  function updateView() {
    const collapsed = state.collapsed;
    const expanded = state.expandedNode;

    nav.classList.toggle('pn-collapsed', collapsed);

    /* 更新每个节点 */
    nav.querySelectorAll('.pn-node').forEach(node => {
      const id = node.dataset.node;
      const isActive = id === ACTIVE;
      const isExpanded = id === expanded && !collapsed;

      node.classList.toggle('pn-node-active', isActive);
      node.classList.toggle('pn-node-expanded', isExpanded);
    });

    /* 更新CSS变量 */
    document.documentElement.style.setProperty('--prism-w', collapsed ? 'var(--prism-collapsed-w)' : 'var(--prism-expanded-w)');

    /* 更新按钮 */
    toggle.querySelector('.pn-toggle-icon').textContent = collapsed ? '›' : '‹';
    toggle.querySelector('.pn-toggle-text').textContent = collapsed ? '展开' : '收起';
    toggle.setAttribute('aria-label', collapsed ? '展开' : '收起');
  }

  /* 初始化视图 */
  updateView();

  fetch('/api/concepts')
    .then(r => r.ok ? r.json() : null)
    .then(data => {
      if (!data) return;
      const concepts = data.concepts || [];
      const quoteTotal = concepts.reduce((sum, c) => sum + (c.quotes_count || 0), 0);
      const conceptDesc = nav.querySelector('[data-count-key="concepts"] .pn-sub-desc');
      const quoteDesc = nav.querySelector('[data-count-key="quotes"] .pn-sub-desc');
      if (conceptDesc) conceptDesc.textContent = `${concepts.length} core concepts`;
      if (quoteDesc) quoteDesc.textContent = `${quoteTotal} original quotes`;
    })
    .catch(function() {});
})();
