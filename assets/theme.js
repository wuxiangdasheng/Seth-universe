/* ============================================================
   主题（亮 / 暗 / 跟随系统）· 字号 · 共用图标
   ------------------------------------------------------------
   2026-10-20 从 app.js 与 admin.js 各抽一份合并到这里 —— 那两份
   是逐字相同的副本，2026-10-18 做「主题三态化」时三处（含
   ai-seth.html）各改一遍，就是这么踩的。现在站点与后台只有这一份。

   用法：必须在 app.js / admin.js **之前**加载（它们在启动时就要主题已生效）。
   绑定按钮由页面调 SethTheme.bindButtons()（幂等，可重复调用）；
   ai-seth.html 是自包含单文件页，不引本文件，那页自带一份等价实现。
   ============================================================ */
(function () {
  "use strict";

  var LS = { theme: "seth.theme", fs: "seth.fs" };
  var FS_STEPS = [0.92, 1, 1.09];

  var ICON = {
    star: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"><path d="m12 2.6 2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.5l-5.9 3.1 1.2-6.5L2.5 9.5l6.6-.9Z"/></svg>',
    sun: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8m10.4 10.4 1.8 1.8m0-14-1.8 1.8M6.7 17.3l-1.8 1.8"/></svg>',
    moon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11Z"/></svg>',
    refresh: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-2.64-6.36M21 3v5h-5"/></svg>',
    /* 跟随系统：右半圆填充 + 整圆描边（一半固定一半跟随） */
    auto: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="8.5"/><path d="M12 3.5a8.5 8.5 0 0 1 0 17z" fill="currentColor" stroke="none"/></svg>'
  };

  function $(s) { return document.querySelector(s); }

  /* HTML 转义：与主题无关，但站点与后台两份逐字相同，一并收在这里 */
  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function systemDark() {
    return !!(window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches);
  }
  /* 存的是「模式」不是「生效颜色」：light / dark / auto（auto = 跟随系统实时切换）。
     旧数据只可能是 light/dark（那时尚无 auto），直接沿用；异常/无记录一律 auto */
  function themeMode() {
    var v = null;
    try { v = localStorage.getItem(LS.theme); } catch (e) {}
    return (v === "light" || v === "dark") ? v : "auto";
  }
  function themeEffective(mode) {
    return mode === "auto" ? (systemDark() ? "dark" : "light") : mode;
  }
  function applyTheme() {
    var mode = themeMode();
    var t = themeEffective(mode);
    document.documentElement.dataset.theme = t;
    var mt = document.querySelector('meta[name="theme-color"]');
    if (mt) mt.setAttribute("content", t === "dark" ? "#14121c" : "#f7f3ea");
    var b = $("#themeBtn");
    if (b) {
      b.innerHTML = mode === "dark" ? ICON.sun : (mode === "light" ? ICON.moon : ICON.auto);
      b.title = mode === "dark" ? "深色 · 点按切换到浅色"
        : (mode === "light" ? "浅色 · 点按切换到深色" : "跟随系统 · 点按切换到浅色");
    }
  }

  var fsIdx = parseInt(localStorage.getItem(LS.fs) || "1", 10);
  if (!(fsIdx >= 0 && fsIdx < FS_STEPS.length)) fsIdx = 1;   // 坏值/旧值回落到标准字号
  function applyFs() {
    document.documentElement.style.setProperty("--fs", FS_STEPS[fsIdx]);
    try { localStorage.setItem(LS.fs, String(fsIdx)); } catch (e) {}
  }

  /* 三态循环：亮 → 暗 → 跟随系统 → 亮 …；auto 态下系统变化由下面的监听实时处理 */
  function cycleTheme() {
    var order = ["light", "dark", "auto"];
    var next = order[(order.indexOf(themeMode()) + 1) % order.length];
    try { localStorage.setItem(LS.theme, next); } catch (e) {}
    applyTheme();
  }
  function cycleFs() {
    fsIdx = (fsIdx + 1) % FS_STEPS.length;
    applyFs();
  }

  /* 幂等绑定：页面可以重复调（app.js 的 bindCommon 与各页启动都可能调到） */
  function bindButtons() {
    var tb = $("#themeBtn");
    if (tb && !tb.dataset.themeBound) {
      tb.dataset.themeBound = "1";
      tb.addEventListener("click", cycleTheme);
    }
    var fb = $("#fontBtn");
    if (fb && !fb.dataset.themeBound) {
      fb.dataset.themeBound = "1";
      fb.addEventListener("click", cycleFs);
    }
  }

  applyTheme();
  applyFs();

  (function () {
    if (!window.matchMedia) return;
    var mq = matchMedia("(prefers-color-scheme: dark)");
    var onChange = function () { if (themeMode() === "auto") applyTheme(); };
    if (mq.addEventListener) mq.addEventListener("change", onChange);
    else if (mq.addListener) mq.addListener(onChange);
  })();

  window.SethTheme = {
    LS: LS, FS_STEPS: FS_STEPS, ICON: ICON, esc: esc,
    systemDark: systemDark, themeMode: themeMode, themeEffective: themeEffective,
    applyTheme: applyTheme, applyFs: applyFs,
    cycleTheme: cycleTheme, cycleFs: cycleFs,
    bindButtons: bindButtons
  };
})();
