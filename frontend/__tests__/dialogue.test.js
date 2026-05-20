const fs = require('fs');
const path = require('path');

function loadScript(relativePath) {
  const fullPath = path.resolve(__dirname, '..', 'js', relativePath);
  let code = fs.readFileSync(fullPath, 'utf-8');
  code = code.replace(/"use strict";?/g, '');
  code = code.replace(/'use strict';?/g, '');
  code = code.replace(/\bconst\b/g, 'var');
  code = code.replace(/\blet\b/g, 'var');
  (0, eval)(code);
}

describe('对话模块 (dialogue.js)', () => {
  beforeAll(() => {
    document.body.innerHTML = `
      <div id="dialogue-panel">
        <div id="dialogue-messages"></div>
        <div id="dialogue-loading" style="display:none"></div>
        <div id="npc-mood"></div>
        <div id="npc-affinity"></div>
        <input type="text" id="dialogue-input" />
        <button id="dialogue-send">发送</button>
        <span id="intent-badge"></span>
      </div>
      <div id="npc-interact-panel">
        <span id="npc-interact-title"></span>
        <div id="npc-interact-actions"></div>
      </div>
      <div id="heal-panel">
        <span id="heal-title"></span>
        <span id="player-gold-heal"></span>
        <div id="heal-services"></div>
        <div id="heal-message" style="display:none"></div>
      </div>
      <div id="skill-learn-panel">
        <span id="skill-learn-title"></span>
        <span id="player-gold-skill"></span>
        <div id="skill-learn-list"></div>
        <div id="skill-learn-message" style="display:none"></div>
      </div>
      <div id="game-container"></div>
    `;
    loadScript('managers/PanelManager.js');
    loadScript('managers/GameManager.js');
    loadScript('map.js');
    loadScript('player.js');
    loadScript('npc.js');
    loadScript('dialogue.js');
  });

  describe('DLG-01: 对话状态初始值', () => {
    it('dialogueOpen 初始应为 false', () => {
      expect(dialogueOpen).toBe(false);
    });

    it('typewriterTimer 初始应为 null', () => {
      expect(typewriterTimer).toBeNull();
    });

    it('dialogueShowAll 初始应为 false', () => {
      expect(dialogueShowAll).toBe(false);
    });
  });

  describe('DLG-02: getDialogueState 对话状态管理', () => {
    it('应创建新的对话状态', () => {
      const state = getDialogueState('test_npc');
      expect(state).toBeDefined();
      expect(state.messages).toEqual([]);
      expect(state.loading).toBe(false);
    });

    it('同一 NPC 应返回相同状态', () => {
      const state1 = getDialogueState('test_npc_2');
      const state2 = getDialogueState('test_npc_2');
      expect(state1).toBe(state2);
    });
  });

  describe('DLG-03: addPlayerMessage 添加玩家消息', () => {
    it('应添加玩家消息到对话记录', () => {
      const npcId = 'test_player_msg';
      addPlayerMessage(npcId, '你好');
      const state = getDialogueState(npcId);
      expect(state.messages.length).toBe(1);
      expect(state.messages[0].role).toBe('player');
      expect(state.messages[0].text).toBe('你好');
    });
  });

  describe('DLG-04: addNPCMessage 添加NPC消息', () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <div id="dialogue-messages"></div>
        <div id="dialogue-loading" style="display:none"></div>
        <div id="npc-mood"></div>
        <div id="npc-affinity"></div>
      `;
      if (typewriterTimer) {
        clearInterval(typewriterTimer);
        typewriterTimer = null;
      }
    });

    it('应添加 NPC 消息到对话记录', () => {
      const npcId = 'test_npc_msg';
      addNPCMessage(npcId, '欢迎光临');
      const state = getDialogueState(npcId);
      expect(state.messages.length).toBe(1);
      expect(state.messages[0].role).toBe('npc');
      expect(state.messages[0].text).toBe('欢迎光临');
    });

    it('应触发打字机效果', () => {
      const npcId = 'test_npc_msg_tw';
      addNPCMessage(npcId, '测试打字机');
      expect(typewriterTimer).not.toBeNull();
      if (typewriterTimer) {
        clearInterval(typewriterTimer);
        typewriterTimer = null;
      }
    });
  });

  describe('DLG-05: startTypewriter / finishTypewriter', () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <div id="dialogue-messages"></div>
        <div id="dialogue-loading" style="display:none"></div>
        <div id="npc-mood"></div>
        <div id="npc-affinity"></div>
      `;
      if (typewriterTimer) {
        clearInterval(typewriterTimer);
        typewriterTimer = null;
      }
    });

    afterEach(() => {
      if (typewriterTimer) {
        clearInterval(typewriterTimer);
        typewriterTimer = null;
      }
    });

    it('startTypewriter 应设置 typewriterTimer', () => {
      const npcId = 'test_tw';
      addNPCMessage(npcId, '打字机测试文本');
      expect(typewriterTimer).not.toBeNull();
    });

    it('finishTypewriter 应清除 typewriterTimer', () => {
      const npcId = 'test_tw_finish';
      addNPCMessage(npcId, '完成打字机测试');
      expect(typewriterTimer).not.toBeNull();
      finishTypewriter();
      expect(typewriterTimer).toBeNull();
    });

    it('finishTypewriter 应显示完整文本', (done) => {
      const npcId = 'test_tw_full';
      const fullText = '完整文本显示';
      addNPCMessage(npcId, fullText);
      finishTypewriter();
      const state = getDialogueState(npcId);
      const lastMsg = state.messages[state.messages.length - 1];
      expect(lastMsg.text).toBe(fullText);
      done();
    });
  });

  describe('DLG-06: toggleDialogueHistory 对话历史切换', () => {
    it('应切换 dialogueShowAll 状态', () => {
      expect(dialogueShowAll).toBe(false);
      toggleDialogueHistory();
      expect(dialogueShowAll).toBe(true);
      toggleDialogueHistory();
      expect(dialogueShowAll).toBe(false);
    });
  });

  describe('DLG-07: escapeHTML 转义', () => {
    it('应转义 HTML 特殊字符', () => {
      expect(escapeHTML('<script>alert(1)</script>')).not.toContain('<script>');
      expect(escapeHTML('&test')).toContain('&amp;');
    });

    it('普通文本应保持不变', () => {
      expect(escapeHTML('你好世界')).toBe('你好世界');
    });
  });

  describe('DLG-08: showIntentBadge 意图标签', () => {
    beforeEach(() => {
      document.body.innerHTML = `<span id="intent-badge"></span>`;
    });

    it('应显示正确的意图标签', () => {
      showIntentBadge('chat');
      const badge = document.getElementById('intent-badge');
      expect(badge.textContent).toBe('闲聊');
      expect(badge.style.display).toBe('inline-block');
    });

    it('未知意图应显示"未知"', () => {
      showIntentBadge('unknown_intent');
      const badge = document.getElementById('intent-badge');
      expect(badge.textContent).toBe('未知');
    });
  });

  describe('DLG-09: Loading 状态与防重复发送', () => {
    it('loading 状态下 sendMessage 应直接返回', async () => {
      document.body.innerHTML = `
        <div id="dialogue-messages"></div>
        <div id="dialogue-loading" style="display:none"></div>
        <div id="npc-mood"></div>
        <div id="npc-affinity"></div>
        <input type="text" id="dialogue-input" value="测试" />
        <button id="dialogue-send">发送</button>
      `;
      activeNpcId = 'test_loading';
      const state = getDialogueState('test_loading');
      state.loading = true;
      const msgCountBefore = state.messages.length;
      await sendMessage();
      expect(state.messages.length).toBe(msgCountBefore);
      state.loading = false;
      activeNpcId = null;
    });

    it('空消息应直接返回', async () => {
      document.body.innerHTML = `
        <div id="dialogue-messages"></div>
        <div id="dialogue-loading" style="display:none"></div>
        <div id="npc-mood"></div>
        <div id="npc-affinity"></div>
        <input type="text" id="dialogue-input" value="" />
        <button id="dialogue-send">发送</button>
      `;
      activeNpcId = 'test_empty';
      const state = getDialogueState('test_empty');
      const msgCountBefore = state.messages.length;
      await sendMessage();
      expect(state.messages.length).toBe(msgCountBefore);
      activeNpcId = null;
    });
  });
});
