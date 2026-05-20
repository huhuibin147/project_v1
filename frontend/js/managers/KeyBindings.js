// 快捷键绑定 - 集中注册所有键盘快捷键到 InputManager
// 消除各模块分散的 document.addEventListener("keydown", ...)

(function registerKeyBindings() {

  // ===== 战斗快捷键（优先级 100，战斗中最高） =====

  InputManager.register("1", (e) => {
    if (!PanelManager.isOpen('combat') || combatAnimating) return false;
    if (combatItemSelectOpen || combatSkillSelectOpen) return false;
    if (combatState && combatState.phase === "player_turn") {
      combatAction("attack");
      return true;
    }
    return false;
  }, 100);

  InputManager.register("2", (e) => {
    if (!PanelManager.isOpen('combat') || combatAnimating) return false;
    if (combatItemSelectOpen || combatSkillSelectOpen) return false;
    if (combatState && combatState.phase === "player_turn") {
      combatAction("defend");
      return true;
    }
    return false;
  }, 100);

  InputManager.register("3", (e) => {
    if (!PanelManager.isOpen('combat') || combatAnimating) return false;
    if (combatItemSelectOpen || combatSkillSelectOpen) return false;
    if (combatState && combatState.phase === "player_turn") {
      openCombatSkillSelect();
      return true;
    }
    return false;
  }, 100);

  InputManager.register("4", (e) => {
    if (!PanelManager.isOpen('combat') || combatAnimating) return false;
    if (combatItemSelectOpen || combatSkillSelectOpen) return false;
    if (combatState && combatState.phase === "player_turn") {
      openCombatItemSelect();
      return true;
    }
    return false;
  }, 100);

  InputManager.register("5", (e) => {
    if (!PanelManager.isOpen('combat') || combatAnimating) return false;
    if (combatItemSelectOpen || combatSkillSelectOpen) return false;
    if (combatState && combatState.phase === "player_turn") {
      combatAction("flee");
      return true;
    }
    return false;
  }, 100);

  InputManager.register("tab", (e) => {
    if (!PanelManager.isOpen('combat') || combatAnimating) return false;
    if (combatState && combatState.phase === "player_turn") {
      e.preventDefault();
      const monsters = combatState.monsters || [];
      const aliveIndices = monsters.map((m, i) => m.alive ? i : -1).filter(i => i >= 0);
      if (aliveIndices.length > 1) {
        const currentPos = aliveIndices.indexOf(currentTargetIndex);
        const nextPos = (currentPos + 1) % aliveIndices.length;
        selectTarget(aliveIndices[nextPos]);
      }
      return true;
    }
    return false;
  }, 100);


  // ===== NPC 交互选项快捷键（优先级 50） =====

  ["1", "2", "3", "4"].forEach((key, index) => {
    InputManager.register(key, (e) => {
      if (!PanelManager.isOpen('npcInteract')) return false;
      const actions = [interactTalk, interactQuest, interactShop, null];
      if (index === 3) {
        if (interactNpcId === "priest") interactHeal();
        else if (interactNpcId === "skill_master") interactLearnSkill();
        else return false;
      } else {
        actions[index]();
      }
      return true;
    }, 50);
  });


  // ===== 面板快捷键（优先级 10） =====

  // I - 背包
  InputManager.register("i", (e) => {
    if (GameManager.isMenuOpen()) return false;
    if (PanelManager.isOpen('inventory')) {
      closeInventory();
      return true;
    }
    if (!PanelManager.isAnyOpen()) {
      PanelManager.toggle('inventory');
      return true;
    }
    return false;
  }, 10);

  // P - 角色信息
  InputManager.register("p", (e) => {
    if (GameManager.isMenuOpen()) return false;
    if (PanelManager.isOpen('playerInfo')) {
      closePlayerInfo();
      return true;
    }
    if (!PanelManager.isAnyOpen()) {
      PanelManager.toggle('playerInfo');
      return true;
    }
    return false;
  }, 10);

  // K - 技能菜单
  InputManager.register("k", (e) => {
    if (GameManager.isMenuOpen()) return false;
    if (PanelManager.isOpen('skillMenu')) {
      closeSkillMenu();
      return true;
    }
    if (!PanelManager.isAnyOpen()) {
      PanelManager.toggle('skillMenu');
      return true;
    }
    return false;
  }, 10);

  // T - 天赋面板
  InputManager.register("t", (e) => {
    if (GameManager.isMenuOpen()) return false;
    if (PanelManager.isOpen('talent')) {
      closeTalentPanel();
      return true;
    }
    if (!PanelManager.isAnyOpen()) {
      PanelManager.toggle('talent');
      return true;
    }
    return false;
  }, 10);

  // Q - 任务面板
  InputManager.register("q", (e) => {
    if (!GameManager.isStarted() || GameManager.isMenuOpen()) return false;
    if (PanelManager.isOpen('quest')) {
      closeQuestManager();
      return true;
    }
    if (!PanelManager.isAnyOpen()) {
      PanelManager.toggle('quest');
      return true;
    }
    return false;
  }, 10);

  // H - 帮助面板
  InputManager.register("h", (e) => {
    if (GameManager.isMenuOpen()) return false;
    if (PanelManager.isOpen('help')) {
      closeHelp();
      return true;
    }
    if (!PanelManager.isAnyOpen()) {
      PanelManager.toggle('help');
      return true;
    }
    return false;
  }, 10);

  // E - 交互键
  InputManager.register("e", (e) => {
    if (PanelManager.isAnyOpen() || GameManager.isMenuOpen() || PanelManager.isOpen('combat')) return false;
    // 优先检查怪物
    const nearMonster = typeof getNearestMonster === "function" ? getNearestMonster() : null;
    if (nearMonster) {
      initiateCombat(nearMonster.instance_id);
      return true;
    }
    // 其次检查 NPC
    const nearest = getNearestNpc();
    if (nearest) {
      openNpcInteract(nearest);
      return true;
    }
    // 最后检查地图物件
    const nearObj = getNearbyInteractableObject();
    if (nearObj) {
      interactWithObject(nearObj);
      return true;
    }
    return false;
  }, 10);


  // ===== 全局操作（优先级 0） =====

  // O - 游戏菜单
  InputManager.register("o", (e) => {
    if (GameManager.isStarted() && !GameManager.isMenuOpen()) {
      if (!PanelManager.isOpen('combat')) {
        GameManager.toggleGameMenu();
        return true;
      }
    }
    return false;
  }, 0);

  // M - 世界地图
  InputManager.register("m", (e) => {
    if (GameManager.isStarted() && typeof toggleWorldMap === 'function') {
      toggleWorldMap();
      return true;
    }
    return false;
  }, 0);


  // ===== Escape 关闭面板（优先级 -10，最低） =====

  InputManager.register("escape", (e) => {
    // 战斗中的 Escape
    if (PanelManager.isOpen('combat')) {
      if (combatItemSelectOpen) {
        closeCombatItemSelect();
        return true;
      }
      if (combatSkillSelectOpen) {
        closeCombatSkillSelect();
        return true;
      }
      // 战斗进行中不响应 Escape
      return false;
    }

    // 按面板层级从内到外关闭
    if (PanelManager.isOpen('dialogue')) { closeDialogue(); return true; }
    if (GameManager.isMenuOpen()) { closeGameMenu(); return true; }
    if (PanelManager.isOpen('npcInteract')) { closeNpcInteract(); return true; }
    if (PanelManager.isOpen('shop')) { closeShop(); return true; }
    if (PanelManager.isOpen('inventory')) { closeInventory(); return true; }
    if (PanelManager.isOpen('playerInfo')) { closePlayerInfo(); return true; }
    if (PanelManager.isOpen('skillMenu')) { closeSkillMenu(); return true; }
    if (PanelManager.isOpen('talent')) { closeTalentPanel(); return true; }
    if (PanelManager.isOpen('quest')) { closeQuestManager(); return true; }
    if (PanelManager.isOpen('help')) { closeHelp(); return true; }
    if (PanelManager.isOpen('forge')) { PanelManager.close('forge'); return true; }
    if (PanelManager.isOpen('worldMap')) { closeWorldMap(); return true; }

    return false;
  }, -10);

})();
