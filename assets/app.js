/* ============================================================
   赛斯宇宙 · 概念口袋百科 —— 共享核心 + 首页逻辑
   ============================================================ */
(function () {
  "use strict";

  /* ---------- 工具 ---------- */
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var LS = { theme: "seth.theme", fs: "seth.fs" };

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  var ICON = {
    star: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="m12 2.6 2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.5l-5.9 3.1 1.2-6.5L2.5 9.5l6.6-.9Z"/></svg>',
    sun: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8m10.4 10.4 1.8 1.8m0-14-1.8 1.8M6.7 17.3l-1.8 1.8"/></svg>',
    moon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11Z"/></svg>',
    refresh: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-2.64-6.36M21 3v5h-5"/></svg>'
  };

  /* ---------- 主题 / 字号 ---------- */
  function getTheme() {
    return localStorage.getItem(LS.theme) ||
      (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  }
  function applyTheme(t) {
    document.documentElement.dataset.theme = t;
    var mt = document.querySelector('meta[name="theme-color"]');
    if (mt) mt.setAttribute("content", t === "dark" ? "#14121c" : "#f7f3ea");
    var b = $("#themeBtn");
    if (b) b.innerHTML = t === "dark" ? ICON.sun : ICON.moon;
  }
  applyTheme(getTheme());

  var FS_STEPS = [0.92, 1, 1.09];
  var fsIdx = parseInt(localStorage.getItem(LS.fs) || "1", 10);
  function applyFs() {
    document.documentElement.style.setProperty("--fs", FS_STEPS[fsIdx]);
    localStorage.setItem(LS.fs, String(fsIdx));
  }
  applyFs();

  /* ---------- 词条数据按需加载（file:// 下用 script 标签，绕开 fetch 限制） ---------- */
  var entryCache = {};
  function loadEntry(id) {
    return new Promise(function (res, rej) {
      if (entryCache[id]) return res(entryCache[id]);
      var s = document.createElement("script");
      s.src = "data/entries/" + id + ".js";
      s.onload = function () { entryCache[id] = window.WIKI_ENTRY; res(window.WIKI_ENTRY); };
      s.onerror = function () { rej(new Error("load fail: " + id)); };
      document.head.appendChild(s);
    });
  }

  /* ---------- 引文卡渲染（金 = 赛斯原文） ---------- */
  /* conceptId / conceptName 传了才长分享按钮（全站原文卡都传，日签也传） */
  function shareBtn(pickId, conceptId) {
    return '<button class="q-share" data-share="' + esc(pickId) + '" data-concept="' + esc(conceptId) + '" aria-label="生成分享卡片">' +
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="2.6"/><circle cx="6" cy="12" r="2.6"/><circle cx="18" cy="19" r="2.6"/><path d="m8.4 13.4 7.2 4.2M15.6 6.4 8.4 10.6"/></svg></button>';
  }
  /* footPre：插在出处行里、分享按钮前方的额外按钮 HTML（概念卡片的复制按钮用） */
  function quoteHTML(p, conceptId, conceptName, footPre) {
    var open = document.body.classList.contains("bilingual") ? " open" : "";
    var tag = p.tag ? '<span class="q-tag">' + esc(p.tag) + "</span>" : "";
    var oe = p.only_en ? '<span class="q-oe" title="仅英文检索命中">◆</span>' : "";
    var src = p.source
      ? '<span class="q-src">' + esc(p.source) + "</span>"
      : "";
    var year = p.year ? "<span>" + esc(p.year) + "</span>" : "";
    var share = conceptId ? shareBtn(p.id, conceptId) : "";
    /* 出处行常驻：收起时也能看到来源，▾ 暗示轻触看英文；
       复制/分享收进 .q-acts 贴右侧，flex-wrap 时两个按钮永不拆散 */
    var acts = (footPre || "") + share;
    return '<article class="q' + open + '" id="' + esc(p.id) + '">' +
      '<p class="q-zh">' + esc(p.zh) + "</p>" +
      (p.en ? '<p class="q-en">' + esc(p.en) + "</p>" : "") +
      '<div class="q-foot">' + src + year + tag + oe + '<span class="q-exp">▾</span>' +
      (acts ? '<span class="q-acts">' + acts + "</span>" : "") + "</div>" +
      "</article>";
  }
  // 事件委托：点引文卡展开 / 收起（.q-share 分享、.q-copy 复制按钮不触发收起）
  document.addEventListener("click", function (e) {
    if (e.target.closest && e.target.closest(".q-share, .q-copy")) return;
    var q = e.target.closest ? e.target.closest(".q") : null;
    if (q && !window.getSelection().toString()) q.classList.toggle("open");
  });

  /* ---------- 右上标跳转渲染 ---------- */
  var SUPER = { "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9" };
  function noteHTML(text, cites) {
    var map = {};
    (cites || []).forEach(function (c) { map[String(c.n)] = c.id; });
    var parts = String(text || "").split(/\n{2,}/);
    return parts.map(function (para) {
      var html = esc(para).replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹]+/g, function (run) {
        var num = run.split("").map(function (ch) { return SUPER[ch] || ""; }).join("");
        var id = map[num];
        return id
          ? '<sup><a href="#' + esc(id) + '" data-jump="1">' + num + "</a></sup>"
          : "<sup>" + num + "</sup>";
      });
      return "<p>" + html + "</p>";
    }).join("");
  }

  /* ---------- 通用按钮绑定 ---------- */
  function bindCommon() {
    var tb = $("#themeBtn");
    if (tb) tb.addEventListener("click", function () {
      applyTheme(getTheme() === "dark" ? "light" : "dark");
      localStorage.setItem(LS.theme, getTheme());
    });
    var fb = $("#fontBtn");
    if (fb) fb.addEventListener("click", function () {
      fsIdx = (fsIdx + 1) % FS_STEPS.length;
      applyFs();
    });
  }

  /* ---------- 暴露 ---------- */
  window.Wiki = {
    $: $, esc: esc, ICON: ICON, loadEntry: loadEntry,
    quoteHTML: quoteHTML, shareBtn: shareBtn, noteHTML: noteHTML, bindCommon: bindCommon,
    entryCache: function () { return entryCache; },
    setShareBg: function (i) { shareBgIdx = i; },   /* 测试钩子：强制分享卡背景序号（无 UI 入口） */
    /* 回到顶部：页面注入 .totop 按钮后调用一次。点击平滑回顶；滚动超过 600px 才显形。
       用 dataset 判重，避免页面重复调用导致多次绑定。样式共享 .totop（已对齐手机壳、压在底栏上方）。 */
    bindTotop: function () {
      var btn = document.getElementById("totop");
      if (!btn || btn.dataset.totopBound) return;
      btn.dataset.totopBound = "1";
      btn.addEventListener("click", function () { window.scrollTo({ top: 0, behavior: "smooth" }); });
      var onScroll = function () { btn.classList.toggle("show", window.scrollY > 600); };
      window.addEventListener("scroll", onScroll, { passive: true });
      onScroll();
    }
  };

  /* ============================================================
     分享卡片：1080×1440 竖版。
     背景 = 剧场前八幕的纯视觉截图（assets/share/bg*.jpg，遮掉了 UI 后截的），
     毛玻璃面板用「离屏 blur + 圆角裁剪 + 半透明白」在 canvas 里手搓
     （canvas 没有 backdrop-filter，只能自己糊一层）。
     二维码用 qrcode-generator（assets/lib/qrcode.js），指向这段原文的词条页。
     ============================================================ */
  var shareBgIdx = Math.floor(Math.random() * 8) + 1;   // 一次会话用同一张背景
  function loadScript(src) {
    return new Promise(function (res, rej) {
      var s = document.createElement("script");
      s.src = src;
      s.onload = function () { res(); };
      s.onerror = function () { rej(new Error("load fail: " + src)); };
      document.head.appendChild(s);
    });
  }
  function loadImg(src) {
    return new Promise(function (res, rej) {
      var i = new Image();
      i.onload = function () { res(i); };
      i.onerror = function () { rej(new Error("load fail: " + src)); };
      i.src = src;
    });
  }
  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }
  /* canvas 不自动断行，逐字累加测量；中英文混排也按实际宽度折。
     英文不在单词中间断：超宽时回退到行内最后一个空格（中文无空格，逐字断不受影响） */
  function wrapText(ctx, text, maxW) {
    var lines = [], line = "";
    for (var i = 0; i < text.length; i++) {
      var ch = text.charAt(i);
      var test = line + ch;
      if (ch === "\n" || ctx.measureText(test).width > maxW) {
        if (line) {
          var sp = line.lastIndexOf(" ");
          if (sp > 0) {
            lines.push(line.slice(0, sp));
            line = line.slice(sp + 1) + ch;
            continue;
          }
          lines.push(line);
        }
        line = ch === "\n" ? "" : ch;
      } else { line = test; }
    }
    if (line) lines.push(line);
    return lines;
  }
  function drawQR(ctx, text, cx, cy, size) {
    var qr = qrcode(0, "M");
    qr.addData(text);
    qr.make();
    var n = qr.getModuleCount();
    var unit = size / (n + 2);          // 含 1 模块静区，扫码更稳
    var x0 = cx - size / 2, y0 = cy - size / 2;
    ctx.fillStyle = "#fff";
    roundRect(ctx, cx - size / 2 - 9, cy - size / 2 - 9, size + 18, size + 18, 10);
    ctx.fill();
    ctx.fillStyle = "#1a1626";
    for (var r = 0; r < n; r++) {
      for (var c = 0; c < n; c++) {
        if (qr.isDark(r, c)) ctx.fillRect(x0 + (c + 1) * unit, y0 + (r + 1) * unit, unit * 0.95, unit * 0.95);
      }
    }
  }
  /* 二维码指向的深链：file:// 下从当前页面路径推导出含 mobile-wiki/ 的站点根
     （file:// 的 origin 是 "file://" 或 "null"，拼不出可用路径，必须靠 href 推导）；
     http(s) 下从当前页目录推导站点根 —— 站根部署得 "/"，
     /mobile-wiki/ 子目录部署得 "/mobile-wiki/"（EdgeOne 上是前者，原来硬编码
     "/mobile-wiki/" 会在站根部署时把二维码指向 404 路径） */
  function shareEntryUrl(conceptId, pickId) {
    var base = "";
    if (location.protocol === "file:") {
      var dir = location.href.split("?")[0].split("#")[0];
      var idx = dir.lastIndexOf("/mobile-wiki/");
      base = idx >= 0 ? dir.slice(0, idx + "/mobile-wiki/".length) : dir.replace(/[^/]*$/, "");
    } else if (location.origin && location.origin !== "null") {
      base = location.origin + location.pathname.replace(/[^/]*$/, "");
    }
    return base + "entry.html?id=" + conceptId + "#" + pickId;
  }
  /* 分享卡片背景：每张图的主体（金色主雕塑）视觉左上角，源图像素坐标。
     目的是把主体顶到卡片左上区，让主体从引文面板上方漏出来 —— 原来居中裁剪时
     主体全在面板后面，顶区只看到背景上部的空白。
     锚点取「受光主体」的左上（不是剪影包围盒左上 —— 包围盒角多是背光/空白，
     锚它受光面会跑到画面中间；这点在 bg1/bg3 上实测错过，已校正）；
     bg7 锚线球不锚黄六边体（六边体是平面衬底，锚它线球会被压到面板后）。
     坐标来源：探针实测金色像素（R-B>40 且 G-B>25，排除粉/紫/红点缀）+ 裁剪目视；
     浅色主体（bg2 檐角/bg4 轮角/bg5 壳角/bg6 柱帽）金色判据失效，按裁剪目视定位。 */
  var SUBJECT_BG = {
    1: [428, 530],  /* 人像胸像：受光额头左缘（剪影左缘 172 在背光处，冠顶点 562,501） */
    2: [95, 424],   /* 中式楼阁：顶层左檐角（x=0 处是底部宽云座的暖光，不是楼阁） */
    3: [361, 500],  /* 打坐像：受光头顶左缘（剪影左缘 170 在背光处） */
    4: [318, 628],  /* 转经轮：斜置圆筒的左上角（轮体左低右高，顶点 625,376 是顶上法轮饰） */
    5: [145, 470],  /* 怀表：表壳左上角（顶点 501,333 是顶上表冠） */
    6: [240, 360],  /* 拱门人像：左柱柱帽左上（顶点 537,282 是拱顶） */
    7: [245, 618],  /* 金线球：球体左上（黄六边体 98,15-978,519 是衬底不锚） */
    8: [450, 300]   /* 观音坐像：受光头冠左缘（冠顶点 528,296） */
  };
  var SUBJECT_TX = 80, SUBJECT_TY = 96;  /* 主体锚点在卡片上的目标位置：左上区 */
  /* iOS（含 iPad 桌面模式）：不拦原生长按——系统「存储图像」对 dataURL 图片可靠，
     且 a.download 在 iOS Safari 不可用；其余平台走自定义长按 + a.download。
     定义在本层（openShare 与分享面板 IIFE 共用）：面板 IIFE 在内层，拿不到这里的声明 */
  var isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  function setShareHint(t) { var h = $("#shareHint"); if (h) h.textContent = t; }
  function saveShareImg() {
    var img = $("#sharePreview");
    if (!img || !img.getAttribute("src")) return;
    var a = document.createElement("a");
    a.download = "seth-daily-" + Date.now() + ".jpg";
    a.href = img.getAttribute("src");
    document.body.appendChild(a); a.click(); a.remove();
    setShareHint("已保存 ✓");
    setTimeout(function () {
      setShareHint(isIOS ? "长按图片存储到相册，或点下方按钮保存" : "长按图片或点「保存图片」保存");
    }, 2000);
  }

  function buildShareCard(p, concept) {
    /* 画布宽固定 1080，高度不固定：顶区（背景留白 292，标题与日期已按要求去掉）与底区
       （站点名+标语+二维码，152）定高，面板贴顶区下方（py=440，即日期原位置下方 +100px），
       高度由内容排版算出；总高 = 440 + 面板 + 48 + 152。
       面板上限 3400 = 全语料 4006 段在 44px 苹方下的最大需求（3387，579 字那段）再加余量：
       即所有真实段落都按 44/30px 大字号排版、卡片随内容长高，不做任何压缩；
       上限只是留给日后更长内容的保险，超过才逐级缩字号 */
    var W = 1080;
    var TOP_H = 292, GAP = 48, BOT_H = 152;
    var GAP_TOP = GAP + 100;                          /* 日期标签与面板之间固定 +100px（只加上间距，面板与底区间距仍是 48） */
    var cv = document.createElement("canvas");
    cv.width = W; cv.height = TOP_H + GAP + 3400 + GAP + BOT_H;  /* 暂用上限尺寸，量完文字再定高 */
    var ctx = cv.getContext("2d");
    return Promise.all([
      /* 背景优先用内嵌 dataURL（file:// 打开或跨域部署时，canvas 不会被污染，toDataURL 才不会报错）；
         内嵌文件加载失败才回退到 jpg（同源 http 下的老路径） */
      loadScript("assets/share/bg" + shareBgIdx + ".data.js").then(function () {
        var url = window["SHARE_BG_" + shareBgIdx] || ("assets/share/bg" + shareBgIdx + ".jpg");
        return loadImg(url);
      }, function () {
        return loadImg("assets/share/bg" + shareBgIdx + ".jpg");
      }),
      loadScript("assets/lib/qrcode.js")
    ]).then(function (r) {
      var img = r[0];

      /* 1. 布局先行（只测文字宽高，不依赖画布尺寸）：字号从 44 逐级缩小，
            直到中英文全部行放得下面板（上限 3400，真实语料都在 44px 一档即命中）。
            行数上限取消——文字完整显示，不截断 */
      var px = 76, pw = W - 152, rad = 36;
      var inner = px + 46, innerW = pw - 92;
      var areaH = 3400;                             /* 面板高度上限（保险阀，真实语料不触发） */
      /* 全卡文字统一苹方（黑体兜底）：量宽与绘制必须用同一字体栈，否则排版错位 */
      var FONT_ZH = "'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Noto Sans SC', sans-serif";
      var FONT_EN = "'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif";
      var zhStr = String(p.zh || "");
      var enStr = p.en ? String(p.en) : "";
      var fit = null;
      for (var z = 44; z >= 17; z -= 3) {
        var e = Math.round(z * 0.68);
        ctx.font = "400 " + z + "px " + FONT_ZH;
        var zhLines = wrapText(ctx, zhStr, innerW);
        var enLines = [];
        if (enStr) {
          ctx.font = "italic 400 " + e + "px " + FONT_EN;
          enLines = wrapText(ctx, enStr, innerW);
        }
        var zhLH = Math.round(z * 1.55), eLH = Math.round(e * 1.3);
        /* 需要的高度：首行偏移92 + 中文(n-1)行距 + [分隔76 + 英文(m-1)行距] + 出处50 + 底部48 */
        var needH = 92 + (zhLines.length - 1) * zhLH +
          (enLines.length ? 76 + (enLines.length - 1) * eLH : 50) + 48;
        if (needH <= areaH) { fit = { z: z, e: e, zhLines: zhLines, enLines: enLines, zhLH: zhLH, eLH: eLH }; break; }
      }
      if (!fit) {   /* 兜底：最长段落（579字/1705字符）在 17px 也能放下；万一仍超则面板向下延伸，不截断 */
        ctx.font = "400 17px " + FONT_ZH;
        var zhL = wrapText(ctx, zhStr, innerW);
        var enL = enStr ? (ctx.font = "italic 400 12px " + FONT_EN, wrapText(ctx, enStr, innerW)) : [];
        fit = { z: 17, e: 12, zhLines: zhL, enLines: enL, zhLH: 26, eLH: 16 };
      }
      var zhEnd = 92 + (fit.zhLines.length - 1) * fit.zhLH;
      var srcY = fit.enLines.length
        ? zhEnd + 30 + 46 + (fit.enLines.length - 1) * fit.eLH + 50   /* 英文末行 + 50 */
        : zhEnd + 50;
      var ph = srcY + 48;
      var py = TOP_H + GAP_TOP;                     /* 面板贴顶区下方（440 = 日期下方 +100px），不再垂直居中 */
      var H = py + ph + GAP + BOT_H;
      cv.width = W; cv.height = H;                 /* 定高：宽固定，长度随内容 */

      /* 2. 背景：主体感知裁剪 —— 把主体锚点顶到 (SUBJECT_TX, SUBJECT_TY)，让主体从面板上方漏出。
             sc 取五个下界的最大值：全覆盖（cover）+ 四个「贴锚且四边不外露」约束
             （图左缘≤0、图右缘≥W、图上缘≤0、图下缘≥H），故画布恒被铺满、无裸露；
             dx/dy 把主体锚点精确落到目标点。卡片越高 sc 越大（长卡 zoom 多），
             主体始终钉在左上区。不在 SUBJECT_BG 表里的图退回居中 cover。 */
      var iw = img.width, ih = img.height;
      var sub = SUBJECT_BG[shareBgIdx];
      var sc, dx, dy;
      if (sub) {
        var sx = sub[0], sy = sub[1];
        sc = Math.max(W / iw, H / ih,
          SUBJECT_TX / sx, (W - SUBJECT_TX) / (iw - sx),
          SUBJECT_TY / sy, (H - SUBJECT_TY) / (ih - sy));
        dx = SUBJECT_TX - sx * sc;
        dy = SUBJECT_TY - sy * sc;
      } else {
        sc = Math.max(W / iw, H / ih);
        dx = (W - iw * sc) / 2; dy = (H - ih * sc) / 2;
      }
      ctx.drawImage(img, dx, dy, iw * sc, ih * sc);

      /* 3. 仅顶部渐变压暗（30% 处收淡到 0.16；原来为托住标题+日期，标题已去，
             现在是给顶区背景分层，让主体与白面板之间有过渡）。底部压暗早已去掉 */
      var g = ctx.createLinearGradient(0, 0, 0, H);
      g.addColorStop(0, "rgba(18,14,26,0.66)");
      g.addColorStop(0.30, "rgba(18,14,26,0.16)");
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);

      /* 黑底毛玻璃面板：先把当前画面整体糊一遍放离屏 canvas，圆角裁剪后叠回来，
         再压一层半透明黑（背景隐约可见，形成深色玻璃质感） */
      var blur = document.createElement("canvas");
      blur.width = W; blur.height = H;
      var bctx = blur.getContext("2d");
      bctx.filter = "blur(36px) brightness(0.92)";
      bctx.drawImage(cv, 0, 0);

      ctx.save();
      roundRect(ctx, px, py, pw, ph, rad);
      ctx.clip();
      ctx.drawImage(blur, 0, 0);
      ctx.fillStyle = "rgba(0, 0, 0, 0.42)";
      ctx.fillRect(px, py, pw, ph);
      ctx.restore();
      /* 高光描边：上亮下暗，像玻璃厚边 */
      ctx.save();
      roundRect(ctx, px + 1, py + 1, pw - 2, ph - 2, rad - 1);
      var lg = ctx.createLinearGradient(0, py, 0, py + ph);
      lg.addColorStop(0, "rgba(255,255,255,0.42)");
      lg.addColorStop(0.5, "rgba(255,255,255,0.16)");
      lg.addColorStop(1, "rgba(255,255,255,0.05)");
      ctx.strokeStyle = lg; ctx.lineWidth = 2; ctx.stroke();
      ctx.restore();

      /* 5. 引文中文（金色，全部行，不截断） */
      ctx.fillStyle = "#e6c68c";
      ctx.font = "400 " + fit.z + "px " + FONT_ZH;
      var y = py + 92;
      fit.zhLines.forEach(function (ln) { ctx.fillText(ln, inner, y); y += fit.zhLH; });

      /* 6. 分隔细线：只画左侧一小段，不通栏（仅中英文都有时） */
      if (fit.enLines.length) {
        var lineY = py + zhEnd + 30;
        ctx.strokeStyle = "rgba(255,255,255,0.22)";
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(inner, lineY); ctx.lineTo(inner + 200, lineY); ctx.stroke();

        /* 7. 英文（全部行，不截断） */
        ctx.fillStyle = "rgba(255,255,255,0.62)";
        ctx.font = "italic 400 " + fit.e + "px " + FONT_EN;
        var ey = lineY + 46;
        fit.enLines.forEach(function (ln) { ctx.fillText(ln, inner, ey); ey += fit.eLH; });
      }

      /* 8. 出处（白色，与金色中文互换） */
      var srcTxt = (p.source || "") + (p.year ? " · " + p.year : "");
      ctx.fillStyle = "#fdf9f0";
      ctx.font = "500 24px -apple-system, 'PingFang SC', sans-serif";
      ctx.fillText(srcTxt, inner, py + srcY);

      /* 9. 底部：左侧站点名 + slogan 与右侧二维码底对齐。
            二维码白盒底 = (H-168)+84 = H-84；slogan 基线下移到 H-87（CJK 标点下沉约 3px，
            字形底 ≈ H-84，与二维码白盒底齐平）；站点名在 slogan 上方 40px 基线处。
            左缘取 inner（面板内文字的左缘），与引文左对齐，而不是贴在面板边上。
            底部遮罩已去掉（背景透出，8 张背景底部亮度均约 200），白字加一层柔和暗投影、
            slogan 不透明度 0.55→0.8（原值是为深色遮罩底调的），保证亮背景下依然读得清；
            二维码前把投影复位，避免白盒挂影 */
      ctx.textAlign = "left";
      ctx.fillStyle = "rgba(255,255,255,0.92)";
      ctx.font = "700 32px " + FONT_ZH;
      ctx.shadowColor = "rgba(18,14,26,0.55)";
      ctx.shadowBlur = 12;
      ctx.shadowOffsetY = 2;
      ctx.fillText("赛斯Seth宇宙", inner, H - 127);
      ctx.fillStyle = "rgba(255,255,255,0.8)";
      ctx.font = "400 22px -apple-system, 'PingFang SC', sans-serif";
      ctx.fillText("理解赛斯哲学，探索多元实相的自己", inner, H - 87);
      ctx.shadowColor = "transparent"; ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;

      var url = shareEntryUrl(concept.id, p.id);
      drawQR(ctx, url, W - 176, H - 168, 150);

      /* jpg：背景满铺无透明区域，jpeg 质量 0.92 体积比 png 小一个量级 */
      return cv.toDataURL("image/jpeg", 0.92);
    });
  }
  function openShare(conceptId, pickId) {
    var mask = $("#shareMask"), sheet = $("#shareSheet"), hint = $("#shareHint"), img = $("#sharePreview");
    if (!mask || !sheet || !window.WIKI_INDEX) return;
    var concept = null;
    window.WIKI_INDEX.concepts.forEach(function (c) { if (c.id === conceptId) concept = c; });
    if (!concept) return;
    mask.classList.add("show"); sheet.classList.add("show");
    hint.textContent = "正在生成…";
    img.removeAttribute("src");
    var p = null;
    loadEntry(conceptId).then(function (e) {
      e.blocks.forEach(function (b) {
        (b.groups || []).forEach(function (g) {
          (g.picks || []).forEach(function (x) { if (x.id === pickId) p = x; });
        });
      });
      /* 「赛斯怎么定义」区的段不在 picks 里，按渲染时造的 id（q-{concept}-def{i}）回退查找；
         顺手补上 id，二维码 URL 与深链都要用它 */
      if (!p) (e.definitions || []).forEach(function (d, di) {
        if (pickId === "q-" + conceptId + "-def" + di) { d.id = pickId; p = d; }
      });
      if (!p) throw new Error("找不到这段原文");
      return buildShareCard(p, concept);
    }).then(function (url) {
      img.src = url;
      setShareHint(isIOS ? "长按图片存储到相册，或点下方按钮保存" : "长按图片或点「保存图片」保存");
    }).catch(function (err) {
      hint.textContent = "生成失败：" + ((err && err.message) || err);
    });
  }
  /* 分享按钮在 .q-foot 里，点了要打开预览而不是收起卡片 */
  document.addEventListener("click", function (e) {
    var btn = e.target.closest ? e.target.closest(".q-share") : null;
    if (!btn) return;
    e.preventDefault(); e.stopPropagation();
    openShare(btn.getAttribute("data-concept"), btn.getAttribute("data-share"));
  });
  /* 分享面板 DOM：index.html 里有一份；entry / book 页没有，这里补注一份（幂等，有就跳过） */
  (function () {
    if (!document.getElementById("shareMask")) {
      var d = document.createElement("div");
      d.innerHTML =
        '<div class="share-mask" id="shareMask"></div>' +
        '<div class="share-sheet" id="shareSheet">' +
        '  <div class="share-head">' +
        '    <div class="share-title">分享卡片</div>' +
        '    <button class="icon-btn" id="shareClose" aria-label="关闭">' +
        '      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>' +
        '    </button>' +
        '  </div>' +
        '  <div class="share-stage"><img id="sharePreview" alt="分享卡片"></div>' +
        '  <div class="share-actions">' +
        '    <button class="btn btn-primary" id="shareSave">保存图片</button>' +
        '  </div>' +
        '  <p class="share-hint" id="shareHint">正在生成…</p>' +
        '</div>';
      while (d.firstChild) document.body.appendChild(d.firstChild);
    }
    var mask = $("#shareMask"), sheet = $("#shareSheet"), btn = $("#shareClose");
    if (!mask || !sheet) return;
    function close() { mask.classList.remove("show"); sheet.classList.remove("show"); }
    mask.addEventListener("click", close);
    if (btn) btn.addEventListener("click", close);
    $("#shareSave").addEventListener("click", saveShareImg);

    /* 长按图片保存（非 iOS）：拦截原生菜单，500ms 触发保存 */
    var lpImg = $("#sharePreview"), lpTimer = null;
    if (lpImg && !isIOS) {
      lpImg.addEventListener("contextmenu", function (e) { e.preventDefault(); });
      lpImg.addEventListener("touchstart", function () {
        if (lpTimer) clearTimeout(lpTimer);
        lpTimer = setTimeout(function () { lpTimer = null; saveShareImg(); }, 500);
      }, { passive: true });
      ["touchend", "touchmove", "touchcancel"].forEach(function (ev) {
        lpImg.addEventListener(ev, function () { if (lpTimer) { clearTimeout(lpTimer); lpTimer = null; } }, { passive: true });
      });
    }
  })();

  /* ============================================================
     首页逻辑（仅在含概念列表的页面执行）
     ============================================================ */
  if (!window.WIKI_INDEX || !document.getElementById("conceptList")) return;
  bindCommon();

  var IDX = window.WIKI_INDEX;
  var BOOKS = window.WIKI_BOOKS;
  var state = { tab: "daily", q: "", deep: false, deepBusy: false };

  /* 英雄区统计：第 4 格不是统计数字，是档案视图的入口（可点击） */
  (function () {
    var m = IDX.meta;
    $("#heroStats").innerHTML =
      stat(m.total_concepts, "概念") + stat(m.total_quotes.toLocaleString(), "段原文") +
      stat(m.total_books, "部书") +
      '<button class="stat-chip stat-chip-link" data-goto="archive"><b>档案</b><span>时间线</span></button>';
    function stat(b, s) { return '<div class="stat-chip"><b>' + b + "</b><span>" + s + "</span></div>"; }
  })();

  /* 概念列表 */
  function matchConcept(c, q) {
    if (!q) return true;
    return (c.name_zh + " " + c.name_en + " " + c.tagline + " " + c.explanation)
      .toLowerCase().indexOf(q) !== -1;
  }
  function hl(text, q) {
    var s = esc(text);
    if (!q) return s;
    try {
      return s.replace(new RegExp("(" + q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi"), "<mark>$1</mark>");
    } catch (e) { return s; }
  }
  function conceptCard(c, q, i) {
    var meta = [];
    meta.push("<i>" + c.quotes + " 段</i>");
    meta.push('<span class="dot">·</span><i>' + c.blocks + " 节</i>");
    if (c.books) meta.push('<span class="dot">·</span><i>' + c.books + " 部书</i>");
    if (c.span) meta.push('<span class="dot">·</span><i>' + c.span[0] + "–" + c.span[1] + "</i>");
    return '<a class="card" style="animation-delay:' + Math.min(i * 28, 350) + 'ms" href="entry.html?id=' + c.id + '">' +
      '<div class="concept-head"><span class="concept-name">' + hl(c.name_zh, q) + '</span>' +
      '<span class="concept-en">' + esc(c.name_en) + "</span></div>" +
      (c.tagline ? '<p class="concept-tag">' + hl(c.tagline, q) + "</p>" : "") +
      '<div class="concept-meta">' + meta.join("") + "</div>" +
      "</a>";
  }
  /* 搜索框下面那行小字（命中数 / 深度搜索按钮）已从页面下线：
     这里统一走判空写入，元素不存在就静默跳过，别让 null.innerHTML 把整个渲染带崩。 */
  function setSearchMeta(html) {
    var el = $("#searchMeta");
    if (el) el.innerHTML = html;
  }
  function renderList() {
    var q = state.q.trim().toLowerCase();
    var box = $("#conceptList");
    if (state.deep) return; // 深度搜索接管列表
    var hits = IDX.concepts.filter(function (c) { return matchConcept(c, q); });
    setSearchMeta(q
      ? "<span>" + hits.length + " 个概念命中</span>" +
        (hits.length === 0 ? '<button class="deep-btn" id="deepBtn">在 ' + IDX.meta.total_quotes.toLocaleString() + " 段原文里搜 →</button>" : "")
      : "<span>共 " + IDX.concepts.length + " 个概念</span>");
    var db = $("#deepBtn");
    if (db) db.addEventListener("click", function () { deepSearch(); });
    box.innerHTML = hits.length
      ? hits.map(function (c, i) { return conceptCard(c, q, i); }).join("")
      : '<div class="empty">' + ICON.star + "<p><b>没有命中的概念</b>换个词试试。</p></div>";
  }

  /* 深度搜索：按需加载全部词条，搜引文原文 */
  function deepSearch() {
    var q = state.q.trim();
    if (!q || state.deepBusy) return;
    state.deep = true;
    state.deepBusy = true;
    var box = $("#conceptList");
    var ids = IDX.concepts.map(function (c) { return c.id; });
    var n = 0;
    setSearchMeta("<span>正在载入语料 0/" + ids.length + " …</span>");
    function step() {
      if (n >= ids.length) return done();
      var id = ids[n];
      setSearchMeta("<span>正在载入语料 " + (n + 1) + "/" + ids.length + " …</span>");
      loadEntry(id).then(step, step);
      n++;
    }
    function done() {
      state.deepBusy = false;
      var ql = q.toLowerCase();
      var results = [];
      IDX.concepts.forEach(function (c) {
        var e = Wiki.entryCache()[c.id];
        if (!e) return;
        e.blocks.forEach(function (b) {
          (b.groups || []).forEach(function (g) {
            (g.picks || []).forEach(function (p) {
              if ((p.zh + " " + p.en).toLowerCase().indexOf(ql) !== -1)
                results.push({ c: c, p: p });
            });
          });
        });
        (e.reading || []).forEach(function (p) {
          if ((p.zh + " " + p.en).toLowerCase().indexOf(ql) !== -1) results.push({ c: c, p: p });
        });
      });
      setSearchMeta("<span>" + results.length + " 段原文命中</span>" +
        '<button class="deep-btn" id="deepBack">← 回到概念搜索</button>');
      var back = $("#deepBack");
      if (back) back.addEventListener("click", function () {
        state.deep = false; renderList();
      });
      box.innerHTML = results.length
        ? '<div style="font-size:.72rem;color:var(--ink-3);padding:2px 2px 0">以下为原文段落，点开可中英对照</div>' +
          results.slice(0, 200).map(function (r, i) {
            var p = r.p;
            var tag = p.tag ? ' <span class="q-tag">' + esc(p.tag) + "</span>" : "";
            var oe = p.only_en ? ' <span class="q-oe">◆</span>' : "";
            return '<a class="card" style="animation-delay:' + Math.min(i * 20, 300) + 'ms" href="entry.html?id=' + r.c.id + "#" + esc(p.id) + '">' +
              '<div class="concept-head"><span class="concept-name">' + esc(r.c.name_zh) + "</span></div>" +
              '<p class="concept-tag q-zh" style="-webkit-line-clamp:3">' + hl(p.zh, q) + "</p>" +
              '<div class="concept-meta"><span class="q-src">' + esc(p.source) + "</span>" +
              (p.year ? " · " + esc(p.year) : "") + tag + oe + "</div></a>";
          }).join("")
        : '<div class="empty">' + ICON.star + "<p><b>原文里也没有</b>这个词没有以任何形式出现过。</p></div>";
    }
    step();
  }

  /* 时间线 */
  function renderTimeline() {
    var totals = {};
    IDX.concepts.forEach(function (c) {
      Object.keys(c.years || {}).forEach(function (y) {
        totals[y] = (totals[y] || 0) + c.years[y];
      });
    });
    var years = Object.keys(totals).sort();
    var max = Math.max.apply(null, years.map(function (y) { return totals[y]; }));
    var box = $("#timeline");
    box.innerHTML = years.map(function (y) {
      var w = Math.max(2, Math.round(totals[y] / max * 100));
      return '<button class="tl-year" data-year="' + y + '">' +
        '<span class="y">' + y + "</span>" +
        '<span class="bar-track"><span class="bar" data-w="' + w + '"></span></span>' +
        '<span class="n">' + totals[y] + "</span></button>";
    }).join("");
    requestAnimationFrame(function () {
      setTimeout(function () {
        box.querySelectorAll(".bar").forEach(function (b) { b.style.width = b.getAttribute("data-w") + "%"; });
      }, 60);
    });
    box.querySelectorAll(".tl-year").forEach(function (btn) {
      btn.addEventListener("click", function () {
        box.querySelectorAll(".tl-year").forEach(function (b) { b.classList.remove("active"); });
        btn.classList.add("active");
        showYear(btn.getAttribute("data-year"));
      });
    });
    function showYear(y) {
      var rows = IDX.concepts
        .map(function (c) { return { c: c, n: (c.years || {})[y] || 0 }; })
        .filter(function (r) { return r.n > 0; })
        .sort(function (a, b) { return b.n - a.n; });
      var d = $("#tlDetail");
      d.style.display = "block";
      d.innerHTML = "<h3>" + y + " 年</h3>" +
        '<div class="tl-detail-sub">' + rows.length + " 个概念 · " +
        rows.reduce(function (s, r) { return s + r.n; }, 0) + " 段原文被引用</div>" +
        rows.map(function (r) {
          return '<a class="card" style="margin:8px 0" href="entry.html?id=' + r.c.id + '">' +
            '<div class="concept-head"><span class="concept-name" style="font-size:.98rem">' + esc(r.c.name_zh) + "</span>" +
            '<span class="concept-en">' + esc(r.c.name_en) + "</span></div>" +
            '<div class="concept-meta"><i>' + r.n + " 段</i></div></a>";
        }).join("");
    }
  }

  /* 书海 */
  function renderBooks() {
    $("#bookCount").textContent = BOOKS.books.length + " 部";
    $("#bookGrid").innerHTML = BOOKS.books.map(function (b) {
      return '<a class="book-card" href="book.html?name=' + encodeURIComponent(b.name) + '">' +
        '<span class="spine"></span>' +
        '<div class="bname">' + esc(b.name) + "</div>" +
        '<div class="bmeta"><b>' + b.total + "</b> 段 · " + b.concepts.length + " 个概念</div></a>";
    }).join("");
  }

  /* 日签：随机抽一段原文。
     做法是「先随机概念、再随机它的段落」，不是把 61 个词条全加载再抽 ——
     全量约 62 MB，进一次日签要下完整个库。分布上段数多的概念更容易被抽到，
     但换一张就能重来，这个偏差不值得为它付全量加载的代价。 */
  function renderDaily() {
    var box = $("#dailyCard");
    if (!box) return;
    box.innerHTML = '<div class="q" style="border-bottom-color:var(--line-2)">' +
      '<div class="skel skel-line" style="width:72%"></div>' +
      '<div class="skel skel-line"></div>' +
      '<div class="skel skel-line" style="width:84%"></div>' +
      '<div class="skel skel-line" style="width:56%"></div></div>';
    var c = IDX.concepts[Math.floor(Math.random() * IDX.concepts.length)];
    loadEntry(c.id).then(function (e) {
      var all = [];
      e.blocks.forEach(function (b) {
        (b.groups || []).forEach(function (g) {
          (g.picks || []).forEach(function (p) { all.push(p); });
        });
      });
      if (!all.length) return renderDaily();
      var p = all[Math.floor(Math.random() * all.length)];
      /* 出处行：刷新按钮在左端（与卡片左对齐），词条链接在右端；按钮随本行动态生成，绑定在此 */
      box.innerHTML = quoteHTML(p, c.id, c.name_zh) +
        '<div class="daily-src">' +
        '<button class="icon-btn daily-refresh" id="dailyShuffle" aria-label="换一张" title="换一张">' + ICON.refresh + '</button>' +
        '<a href="entry.html?id=' + c.id + '#' + esc(p.id) + '">' + esc(c.name_zh) + " →</a></div>";
      var btn = box.querySelector("#dailyShuffle");
      if (btn) btn.addEventListener("click", renderDaily);
      /* 日签卡片默认展开英文（全站唯一）；其余卡片仍默认收起，轻触才展开。
         双语模式下全站展开是另一套开关（body.bilingual），与这里不冲突 */
      var q = box.querySelector(".q");
      if (q) q.classList.add("open");
    }, function () { box.innerHTML = "<p>载入失败，请重试。</p>"; });
  }
  (function () {
    var el = $("#dailyDate");
    if (!el) return;
    var d = new Date();
    el.textContent = d.getFullYear() + " 年 " + (d.getMonth() + 1) + " 月 " + d.getDate() + " 日";
  })();



  /* 视图切换：底栏 data-href（地图）直接跳转；data-tab 切 view；
     首屏 data-goto（档案）切过去但不点亮底栏任何一项（档案不在底栏了） */
  function switchView(tab, btn) {
    var view = $("#view-" + tab);
    if (!view) return;                // 页面还没做的先不响应
    state.tab = tab;
    document.querySelectorAll(".tabbar button").forEach(function (b) { b.classList.toggle("on", b === btn); });
    document.querySelectorAll(".view").forEach(function (v) { v.classList.remove("active"); });
    view.classList.add("active");
    if (tab === "archive") renderTimelineBars();
    if (tab === "daily") renderDaily();
    window.scrollTo(0, 0);
  }
  document.querySelectorAll(".tabbar button").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var href = btn.getAttribute("data-href");
      if (href) { location.href = href; return; }
      switchView(btn.getAttribute("data-tab"), btn);
    });
  });
  document.querySelectorAll("[data-goto]").forEach(function (btn) {
    btn.addEventListener("click", function () { switchView(btn.getAttribute("data-goto"), null); });
  });
  /* #dailyShuffle 是 renderDaily 动态生成的（在 daily-src 行里），绑定在 renderDaily 内 */
  function renderTimelineBars() {
    document.querySelectorAll("#timeline .bar").forEach(function (b) {
      b.style.width = b.getAttribute("data-w") + "%";
    });
  }

  /* 搜索 */
  var input = $("#searchInput");
  input.addEventListener("input", function () {
    state.q = input.value;
    state.deep = false;
    $("#searchbox").classList.toggle("has-value", !!input.value);
    renderList();
  });
  $("#searchClear").addEventListener("click", function () {
    input.value = ""; state.q = ""; state.deep = false;
    $("#searchbox").classList.remove("has-value");
    renderList(); input.focus();
  });

  /* 顶栏滚动态 */
  window.addEventListener("scroll", function () {
    $("#appbar").classList.toggle("scrolled", window.scrollY > 8);
  }, { passive: true });

  /* ---------- 随机引文抽屉 ---------- */
  var mask = $("#sheetMask"), sheet = $("#sheet"), sheetBody = $("#sheetBody");
  var currentConcept = null, currentPick = null;
  function openSheet() { mask.classList.add("show"); sheet.classList.add("show"); }
  function closeSheet() { mask.classList.remove("show"); sheet.classList.remove("show"); }
  mask.addEventListener("click", closeSheet);
  $("#sheetClose").addEventListener("click", closeSheet);

  function randomQuote() {
    var c = IDX.concepts[Math.floor(Math.random() * IDX.concepts.length)];
    $("#sheetTitle").textContent = "随机一段";
    sheetBody.innerHTML = '<div class="skel skel-line" style="width:70%"></div><div class="skel skel-line"></div><div class="skel skel-line" style="width:85%"></div><div class="skel skel-line" style="width:60%"></div>';
    $("#sheetOpen").style.display = "none";
    openSheet();
    loadEntry(c.id).then(function (e) {
      var all = [];
      e.blocks.forEach(function (b) {
        (b.groups || []).forEach(function (g) {
          (g.picks || []).forEach(function (p) { all.push(p); });
        });
      });
      if (!all.length) return randomQuote();
      currentPick = all[Math.floor(Math.random() * all.length)];
      currentConcept = c;
      sheetBody.innerHTML =
        '<div style="font-size:.74rem;color:var(--ink-3);margin-bottom:2px">来自词条</div>' +
        '<a href="entry.html?id=' + c.id + "#" + esc(currentPick.id) + '" style="font-family:var(--serif);font-size:1.05rem;font-weight:700;color:var(--accent);text-decoration:none">' + esc(c.name_zh) + " →</a>" +
        '<div style="margin-top:10px">' + quoteHTML(currentPick, c.id) + "</div>";
      var open = $("#sheetOpen");
      open.style.display = "";
      open.onclick = function () { location.href = "entry.html?id=" + c.id + "#" + esc(currentPick.id); };
    }, function () { sheetBody.innerHTML = "<p>载入失败，请重试。</p>"; });
  }
  /* 首屏那组 CTA 已下线，这两个入口可能不存在 —— 判空绑定，别让缺失的元素把后面整段初始化带崩 */
  var randQuoteBtn = $("#randQuoteBtn");
  if (randQuoteBtn) randQuoteBtn.addEventListener("click", randomQuote);
  $("#sheetShuffle").addEventListener("click", randomQuote);
  var randConceptBtn = $("#randConceptBtn");
  if (randConceptBtn) randConceptBtn.addEventListener("click", function () {
    var c = IDX.concepts[Math.floor(Math.random() * IDX.concepts.length)];
    location.href = "entry.html?id=" + c.id;
  });

  /* ---------- 启动 ---------- */
  renderList();
  renderTimeline();
  renderBooks();
  renderDaily();   /* 日签即站点首页：默认视图，启动时直接渲染 */
})();
