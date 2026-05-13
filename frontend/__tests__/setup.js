// 全局测试环境配置

// 模拟 TILE_SIZE（map.js 中定义）
global.TILE_SIZE = 32;

// 模拟 PLAYER_SIZE（player.js 中定义，引用 TILE_SIZE）
global.PLAYER_SIZE = 32;

// 模拟 requestAnimationFrame
global.requestAnimationFrame = (cb) => setTimeout(cb, 0);

// 模拟 fetch（默认返回空响应）
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({}),
    text: () => Promise.resolve(''),
  })
);

// 模拟 console 避免测试输出噪音
global.console = {
  ...console,
  error: jest.fn(),
  log: jest.fn(),
  warn: jest.fn(),
};

// 设置 DOM 结构
document.body.innerHTML = `
  <canvas id="game-canvas"></canvas>
  <div id="game-menu-panel"></div>
  <div id="game-container" style="display:none"></div>
  <div id="start-screen" class="hidden"></div>
  <div id="quest-panel"><span id="quest-panel-title"></span><div id="quest-list"></div></div>
  <div id="quest-message" style="display:none"></div>
  <div id="quest-tracker" style="display:none"></div>
  <div id="quest-manager-panel"><div id="quest-manager-content"></div></div>
  <div id="inventory-panel"><div id="inventory-items"></div><span id="inventory-gold">0</span></div>
  <div id="inventory-pagination" style="display:none"></div>
  <div id="shop-panel"><div id="shop-items"></div></div>
  <div id="shop-pagination" style="display:none"></div>
  <div id="player-info-panel"></div>
  <div id="help-panel"></div>
  <div id="combat-panel">
    <span id="combat-turn-info"></span>
    <span id="combat-monster-name"></span>
    <div id="combat-monster-hp-bar"></div>
    <span id="combat-monster-hp-text"></span>
    <div id="combat-player-hp-bar"></div>
    <span id="combat-player-hp-text"></span>
    <div id="combat-player-mp-bar"></div>
    <span id="combat-player-mp-text"></span>
    <div id="combat-player-effects"></div>
    <div id="combat-monster-effects"></div>
    <div id="combat-log"></div>
    <div id="combat-monster-area"></div>
    <div id="combat-player-area"></div>
    <button id="btn-combat-attack"></button>
    <button id="btn-combat-defend"></button>
    <button id="btn-combat-skill"></button>
    <button id="btn-combat-item"></button>
    <button id="btn-combat-flee"></button>
    <div id="combat-result-overlay" style="display:none"><div id="combat-result-content"></div></div>
    <canvas id="monster-sprite-canvas"></canvas>
  </div>
  <div id="dialogue-panel"></div>
  <div id="npc-interact-panel"></div>
  <div id="talent-panel" style="display:none"></div>
  <div id="hud-bar"><span id="hud-gold">0</span></div>
  <div id="forge-panel"></div>
  <div id="heal-panel"></div>
  <div id="skill-learn-panel"></div>
`;