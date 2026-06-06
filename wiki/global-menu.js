/* === 棱镜全局导航 — 节点式可折叠菜单 === */
(function() {
  const ACTIVE = document.documentElement.getAttribute('data-activeWorld') ||
    document.documentElement.getAttribute('data-activeworld') ||
    document.documentElement.dataset.activeWorld ||
    document.documentElement.dataset.activeworld ||
    'concept-world';
  const KEY = 'seth_prism_nav';

  const worlds = [
    {
      id: 'book-world',
      label: '书宇宙',
      labelEn: 'Book Universe',
      icon: 'book',
      href: 'book.html',
      accent: '#d4af37',
      subs: [
        { label: '全部赛斯书', href: 'book.html', desc: 'Complete library' },
        { label: '赛斯说', href: 'book-detail.html?id=10-01', desc: 'Seth Speaks' },
        { label: '个人实相', href: 'book-detail.html?id=10-02', desc: 'Personal Reality' },
        { label: '未知的实相 卷一', href: 'book-detail.html?id=10-03', desc: 'Unknown Reality I' },
        { label: '未知的实相 卷二', href: 'book-detail.html?id=10-04', desc: 'Unknown Reality II' },
        { label: '心灵的本质', href: 'book-detail.html?id=10-05', desc: 'Nature of the Psyche' },
        { label: '个人与事件', href: 'book-detail.html?id=10-06', desc: 'Nature of Events' },
        { label: '梦与价值 卷一', href: 'book-detail.html?id=10-07', desc: 'Dreams & Value I' },
        { label: '梦与价值 卷二', href: 'book-detail.html?id=10-08', desc: 'Dreams & Value II' },
        { label: '神奇之道', href: 'book-detail.html?id=10-09', desc: 'Magical Approach' },
        { label: '健康之道', href: 'book-detail.html?id=10-10', desc: 'Way Toward Health' },
        { label: '早期课 第一册', href: 'book-detail.html?id=ES-1', desc: 'Early Sessions 1' },
        { label: '早期课 第二册', href: 'book-detail.html?id=ES-2', desc: 'Early Sessions 2' },
        { label: '早期课 第三册', href: 'book-detail.html?id=ES-3', desc: 'Early Sessions 3' },
        { label: '早期课 第四册', href: 'book-detail.html?id=ES-4', desc: 'Early Sessions 4' },
        { label: '早期课 第五册', href: 'book-detail.html?id=ES-5', desc: 'Early Sessions 5' },
        { label: '早期课 第六册', href: 'book-detail.html?id=ES-6', desc: 'Early Sessions 6' },
        { label: '早期课 第七册', href: 'book-detail.html?id=ES-7', desc: 'Early Sessions 7' },
        { label: '早期课 第八册', href: 'book-detail.html?id=ES-8', desc: 'Early Sessions 8' },
        { label: '早期课 第九册', href: 'book-detail.html?id=ES-9', desc: 'Early Sessions 9' }
      ]
    },
    {
      id: 'concept-world',
      label: '理宇宙',
      labelEn: 'Concept Universe',
      icon: 'concept',
      href: 'index.html',
      accent: '#7a6ab0',
      subs: [
        { label: '核心概念', href: 'index.html', desc: 'core concepts', countKey: 'concepts' },
        { label: '金句观点', href: 'quotes.html', desc: 'original quotes', countKey: 'quotes' },
        { label: '方法练习', href: '#', desc: 'Methods & exercises' },
        { label: '专题', href: 'topics.html', desc: 'Topics & themes' },
        { label: '机制原理', href: '#', desc: 'Mechanisms & principles' },
        { label: '人物实体', href: '#', desc: 'Entities & personas' }
      ]
    },
    {
      id: 'ai-world',
      label: 'AI赛斯',
      labelEn: 'AI Seth',
      icon: 'ai',
      href: 'ai.html',
      accent: '#4a8fa1',
      subs: []
    },
    {
      id: 'system-world',
      label: '系统',
      labelEn: 'System',
      icon: 'system',
      href: 'system.html',
      accent: '#6f7f8f',
      subs: [
        { label: '使用问答', href: 'system.html#faq', desc: 'FAQ' },
        { label: '系统介绍', href: 'system.html#intro', desc: 'About this wiki' }
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

  if (!document.getElementById('mobile-world-nav-style')) {
    const style = document.createElement('style');
    style.id = 'mobile-world-nav-style';
    style.textContent = `
      #mobile-world-nav{display:none}
      #mobile-sub-nav{display:none}
      @media(max-width:768px){
        #mobile-world-nav{
          position:fixed;top:var(--header-h);left:0;right:0;z-index:96;height:46px;
          display:flex;align-items:center;gap:6px;padding:6px 10px;
          overflow-x:auto;overflow-y:hidden;background:rgba(8,8,12,0.94);
          border-bottom:1px solid var(--border-subtle);backdrop-filter:blur(18px) saturate(1.1);
          scrollbar-width:none;
        }
        #mobile-world-nav::-webkit-scrollbar{display:none}
        .mwn-item{
          flex:0 0 auto;min-width:72px;height:34px;display:inline-flex;align-items:center;justify-content:center;gap:6px;
          padding:0 10px;color:var(--text-muted);text-decoration:none;border:1px solid transparent;border-radius:6px;
          background:rgba(255,255,255,0.018);font-size:13px;white-space:nowrap;
        }
        .mwn-item.active{color:var(--text-primary);border-color:var(--mwn-accent);background:rgba(180,160,100,0.08)}
        .mwn-icon{width:15px;height:15px;display:inline-flex;color:var(--mwn-accent)}
        .mwn-icon svg{width:100%;height:100%}
        #mobile-sub-nav{
          position:fixed;top:calc(var(--header-h) + 46px);left:0;right:0;z-index:95;height:42px;
          display:flex;align-items:center;gap:6px;padding:5px 10px;
          overflow-x:auto;overflow-y:hidden;background:rgba(10,10,15,0.92);
          border-bottom:1px solid var(--border-subtle);backdrop-filter:blur(16px) saturate(1.08);
          scrollbar-width:none;touch-action:pan-x;
        }
        #mobile-sub-nav::-webkit-scrollbar{display:none}
        .msn-item{
          flex:0 0 auto;height:31px;display:inline-flex;align-items:center;justify-content:center;
          padding:0 10px;color:var(--text-muted);text-decoration:none;border:1px solid transparent;border-radius:6px;
          background:rgba(255,255,255,0.018);font-size:13px;white-space:nowrap;
        }
        .msn-item.active{color:var(--text-primary);border-color:var(--mwn-accent);background:rgba(180,160,100,0.08)}
        body.has-mobile-world-nav .main,
        body.has-mobile-world-nav .workspace{margin-top:calc(var(--header-h) + 46px)!important}
        body.has-mobile-world-nav.has-mobile-sub-nav .main,
        body.has-mobile-world-nav.has-mobile-sub-nav .workspace{margin-top:calc(var(--header-h) + 88px)!important}
        body.has-mobile-world-nav .sidebar,
        body.has-mobile-world-nav .concept-rail{top:calc(var(--header-h) + 46px)!important}
        body.has-mobile-world-nav.has-mobile-sub-nav .sidebar,
        body.has-mobile-world-nav.has-mobile-sub-nav .concept-rail{top:calc(var(--header-h) + 88px)!important}
      }
    `;
    document.head.appendChild(style);
  }

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
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.14.31.49.99 1.51 1H21a2 2 0 1 1 0 4h-.09c-1.02.01-1.37.69-1.51 1z"/>
    </svg>`
  };

  /* 创建DOM */
  const nav = document.createElement('nav');
  nav.id = 'prism-nav';
  nav.className = state.collapsed ? 'pn-collapsed' : '';

  /* 设置初始CSS变量 */
  document.documentElement.style.setProperty('--prism-w', state.collapsed ? 'var(--prism-collapsed-w)' : 'var(--prism-expanded-w)');
  document.documentElement.style.setProperty('--prism-shift', state.collapsed ? 'calc(var(--prism-collapsed-w) - var(--prism-expanded-w))' : '0px');

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

  const mobileNav = document.createElement('nav');
  mobileNav.id = 'mobile-world-nav';
  mobileNav.setAttribute('aria-label', '宇宙菜单');
  mobileNav.innerHTML = worlds.map(w => `
    <a class="mwn-item${w.id === ACTIVE ? ' active' : ''}" href="${w.href}" ${w.id === ACTIVE ? 'aria-current="page"' : ''} style="--mwn-accent:${w.accent}">
      <span class="mwn-icon">${icons[w.icon]}</span>
      <span class="mwn-label">${w.label}</span>
    </a>
  `).join('');
  document.body.appendChild(mobileNav);
  document.body.classList.add('has-mobile-world-nav');

  if (curWorld.subs && curWorld.subs.length) {
    const currentPath = (location.pathname.split('/').pop() || 'index.html') + location.search + location.hash;
    const mobileSubNav = document.createElement('nav');
    mobileSubNav.id = 'mobile-sub-nav';
    mobileSubNav.setAttribute('aria-label', curWorld.label + '子菜单');
    mobileSubNav.innerHTML = curWorld.subs.map(s => {
      const href = s.href || '#';
      const hrefPage = href.split('#')[0];
      const isActive = href !== '#' && (
        currentPath === href ||
        location.href.endsWith(href) ||
        (hrefPage && location.pathname.endsWith('/' + hrefPage) && (!href.includes('?') || currentPath.startsWith(href)))
      );
      return `<a class="msn-item${isActive ? ' active' : ''}" href="${href}" style="--mwn-accent:${curWorld.accent}">${s.label}</a>`;
    }).join('');
    document.body.appendChild(mobileSubNav);
    document.body.classList.add('has-mobile-sub-nav');
  }

  /* 绑定事件 */
  const toggle = nav.querySelector('.pn-toggle');
  toggle.addEventListener('click', function() {
    nav.classList.add('pn-animating');
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
      const node = this.closest('.pn-node');
      const nodeId = node.dataset.node;
      const world = worlds.find(w => w.id === nodeId);
      if (world && (!world.subs || world.subs.length === 0) && world.href && world.href !== '#') {
        window.location.href = world.href;
        return;
      }
      if (state.collapsed) {
        state.collapsed = false;
        state.expandedNode = nodeId;
        nav.classList.add('pn-animating');
        save();
        updateView();
      } else {
        state.expandedNode = state.expandedNode === nodeId ? null : nodeId;
        save();
        if (state.expandedNode === null && world && world.href && world.href !== '#') {
          window.location.href = world.href;
          return;
        }
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
    document.documentElement.style.setProperty('--prism-shift', collapsed ? 'calc(var(--prism-collapsed-w) - var(--prism-expanded-w))' : '0px');

    /* 更新按钮 */
    toggle.querySelector('.pn-toggle-icon').textContent = collapsed ? '›' : '‹';
    toggle.querySelector('.pn-toggle-text').textContent = collapsed ? '展开' : '收起';
    toggle.setAttribute('aria-label', collapsed ? '展开' : '收起');
    clearTimeout(nav._pnTimer);
    nav._pnTimer = setTimeout(function() {
      nav.classList.remove('pn-animating');
    }, 320);
  }

  /* 初始化视图 */
  updateView();

  fetch('concepts-lite.json')
    .then(r => r.ok ? r.json() : null)
    .then(data => {
      if (!data) return;
      const concepts = Array.isArray(data) ? data : (data.concepts || []);
      const quoteTotal = concepts.reduce((sum, c) => sum + (c.quotes_count || (c.quotes || []).length || 0), 0);
      const conceptDesc = nav.querySelector('[data-count-key="concepts"] .pn-sub-desc');
      const quoteDesc = nav.querySelector('[data-count-key="quotes"] .pn-sub-desc');
      if (conceptDesc) conceptDesc.textContent = `${concepts.length} core concepts`;
      if (quoteDesc) quoteDesc.textContent = `${quoteTotal} original quotes`;
    })
    .catch(function() {});
})();
