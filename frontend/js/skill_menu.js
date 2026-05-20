let skillMenuOpen = false;
let skillMenuData = null;
let skillMenuTab = "learned";

const DAMAGE_TYPE_NAMES = {
  physical: "物理",
  magic: "魔法",
};

const SKILL_TYPE_NAMES = {
  damage: "伤害",
  heal: "治疗",
  buff: "增益",
  shield: "护盾",
};

const TARGET_NAMES = {
  enemy: "敌人",
  self: "自身",
  all_enemies: "全体敌人",
};

const EFFECT_NAMES = {
  poison: "中毒",
  burn: "灼烧",
  freeze: "冻结",
  stun: "眩晕",
  silence: "沉默",
  speed_down: "减速",
  bleed: "流血",
  defense_down: "防御降低",
  attack_down: "攻击降低",
  evasion_up: "闪避提升",
  attack_up: "攻击提升",
  defense_up: "防御提升",
  speed_up: "速度提升",
  regen: "再生",
  lifesteal: "吸血",
  reflect: "反伤",
  damage_reduction: "伤害减免",
};

async function fetchSkillMenuData() {
  try {
    const resp = await fetch("/api/skills");
    const data = await resp.json();
    skillMenuData = data;
    return data;
  } catch (e) {
    console.error("获取技能数据失败:", e);
    return null;
  }
}

async function openSkillMenu() {
  if (skillMenuOpen) {
    closeSkillMenu();
    return;
  }
  if (dialogueOpen || shopOpen || GameManager.isMenuOpen() || combatOpen || npcInteractOpen || healPanelOpen || skillLearnPanelOpen || (typeof forgePanelOpen !== 'undefined' && forgePanelOpen)) return;
  if (playerInfoOpen) closePlayerInfo();
  if (inventoryOpen) closeInventory();
  if (helpOpen) closeHelp();
  if (questManagerOpen) closeQuestManager();
  if (talentPanelOpen) closeTalentPanel();
  if (typeof worldMapOpen !== 'undefined' && worldMapOpen) closeWorldMap();
  const data = await fetchSkillMenuData();
  if (!data) return;
  skillMenuData = data;
  renderSkillMenu(data);
  document.getElementById("skill-menu-panel").style.display = "flex";
  skillMenuOpen = true;
}

function closeSkillMenu() {
  document.getElementById("skill-menu-panel").style.display = "none";
  skillMenuOpen = false;
  hideSkillMenuMessage();
}

function hideSkillMenuMessage() {
  const el = document.getElementById("skill-menu-message");
  el.style.display = "none";
  el.textContent = "";
}

function showSkillMenuMessage(msg, isError) {
  const el = document.getElementById("skill-menu-message");
  el.textContent = msg;
  el.style.display = "block";
  el.style.color = isError ? "#e74c3c" : "#5cb85c";
  clearTimeout(el._timer);
  el._timer = setTimeout(hideSkillMenuMessage, 3000);
}

let _skillMenuTabsInitialized = false;

function renderSkillMenu(data) {
  const className = data.class_id ? (typeof playerInfo !== 'undefined' && playerInfo.class_name || data.class_id) : "";
  const summary = document.getElementById("skill-menu-summary");
  summary.textContent = `职业: ${className}  等级: ${data.level}  已学: ${data.learned_skills.length}`;

  if (!_skillMenuTabsInitialized) {
    setupSkillMenuTabs();
    _skillMenuTabsInitialized = true;
  }
  const activeTab = document.querySelector(".skill-tab.active");
  if (activeTab) {
    skillMenuTab = activeTab.dataset.tab;
  }
  renderSkillMenuTab();
}

function setupSkillMenuTabs() {
  const tabs = document.querySelectorAll(".skill-tab");
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      skillMenuTab = tab.dataset.tab;
      renderSkillMenuTab();
    });
  });
}

function renderSkillMenuTab() {
  const container = document.getElementById("skill-menu-content");
  if (!skillMenuData) return;

  if (skillMenuTab === "learned") {
    renderLearnedSkills(container);
  } else {
    renderAvailableSkills(container);
  }
}

function renderLearnedSkills(container) {
  const skills = skillMenuData.learned_skills;
  if (!skills || skills.length === 0) {
    container.innerHTML = '<div class="skill-empty">尚未学会任何技能</div>';
    return;
  }
  container.innerHTML = skills.map((s) => buildLearnedSkillCard(s)).join("");
}

function renderAvailableSkills(container) {
  const skills = skillMenuData.available_skills;
  if (!skills || skills.length === 0) {
    container.innerHTML = '<div class="skill-empty">没有可学习的技能</div>';
    return;
  }
  container.innerHTML = skills.map((s) => buildAvailableSkillCard(s)).join("");
}

function buildLearnedSkillCard(skill) {
  const levelText = `Lv.${skill.current_level}<span class="max">/${skill.max_level}</span>`;
  const dmgType = DAMAGE_TYPE_NAMES[skill.damage_type] || skill.damage_type || "";
  const skillType = SKILL_TYPE_NAMES[skill.type] || skill.type;
  const target = TARGET_NAMES[skill.target] || skill.target;

  let metaParts = [];
  metaParts.push(`<span class="skill-meta-mp">MP: ${skill.mp_cost}</span>`);
  metaParts.push(`<span class="skill-meta-cd">冷却: ${skill.cooldown}回合</span>`);
  metaParts.push(`<span class="skill-meta-target">目标: ${target}</span>`);
  if (dmgType) metaParts.push(`<span class="skill-meta-type">${dmgType}</span>`);

  let upgradeHtml = "";
  if (skill.can_upgrade) {
    const preview = skill.next_level_preview || {};
    let previewParts = [];
    if (preview.power) previewParts.push(`威力 ${preview.power}`);
    if (preview.mp_cost !== undefined) previewParts.push(`MP ${preview.mp_cost}`);
    if (preview.cooldown !== undefined) previewParts.push(`冷却 ${preview.cooldown}回合`);
    if (preview.effects && preview.effects.length > 0) {
      const effNames = preview.effects.map((e) => EFFECT_NAMES[e.type] || e.type).join(", ");
      previewParts.push(effNames);
    }
    const previewText = previewParts.length > 0 ? `→ ${previewParts.join("  ")}` : "";
    upgradeHtml = `
      <div class="skill-card-upgrade">
        <div class="skill-upgrade-preview">${previewText}</div>
        <button class="skill-upgrade-btn" onclick="upgradeSkill('${skill.skill_id}', ${skill.upgrade_cost})">升级 ${skill.upgrade_cost}金币</button>
      </div>`;
  } else if (skill.current_level >= skill.max_level) {
    upgradeHtml = `<div class="skill-card-max">已达最高等级</div>`;
  }

  return `
    <div class="skill-card">
      <div class="skill-card-header">
        <span class="skill-card-name">${skill.name}</span>
        <span class="skill-card-level">${levelText}</span>
      </div>
      <div class="skill-card-desc">${skill.description}</div>
      <div class="skill-card-meta">${metaParts.join("")}</div>
      ${upgradeHtml}
    </div>`;
}

function buildAvailableSkillCard(skill) {
  const dmgType = DAMAGE_TYPE_NAMES[skill.damage_type] || skill.damage_type || "";
  const skillType = SKILL_TYPE_NAMES[skill.type] || skill.type;
  const target = TARGET_NAMES[skill.target] || skill.target;

  let metaParts = [];
  metaParts.push(`<span class="skill-meta-mp">MP: ${skill.mp_cost}</span>`);
  metaParts.push(`<span class="skill-meta-cd">冷却: ${skill.cooldown}回合</span>`);
  metaParts.push(`<span class="skill-meta-target">目标: ${target}</span>`);
  if (dmgType) metaParts.push(`<span class="skill-meta-type">${dmgType}</span>`);

  const locked = !skill.can_learn;
  const lockedClass = locked ? " locked" : "";
  const reasonText = locked ? skill.reason : "";

  let learnHtml = "";
  if (!locked) {
    learnHtml = `
      <div class="skill-card-learn">
        <div class="skill-learn-info">可学习</div>
        <button class="skill-learn-btn" onclick="learnSkillFromMenu('${skill.skill_id}')">学习</button>
      </div>`;
  } else {
    learnHtml = `
      <div class="skill-card-learn">
        <div class="skill-learn-info" style="color:#e74c3c">${reasonText}</div>
      </div>`;
  }

  return `
    <div class="skill-card${lockedClass}">
      <div class="skill-card-header">
        <span class="skill-card-name">${skill.name}</span>
        <span class="skill-card-level">Lv.0<span class="max">/${skill.max_level}</span></span>
      </div>
      <div class="skill-card-desc">${skill.description}</div>
      <div class="skill-card-meta">${metaParts.join("")}</div>
      ${learnHtml}
    </div>`;
}

async function upgradeSkill(skillId, cost) {
  try {
    const resp = await fetch("/api/skills/upgrade", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ skill_id: skillId }),
    });
    const result = await resp.json();
    if (result.success) {
      showSkillMenuMessage(result.message, false);
      if (result.player_info) {
        Object.assign(playerInfo, result.player_info);
      }
      const data = await fetchSkillMenuData();
      if (data) {
        skillMenuData = data;
        renderSkillMenu(data);
      }
    } else {
      showSkillMenuMessage(result.message, true);
    }
  } catch (e) {
    console.error("升级技能失败:", e);
    showSkillMenuMessage("升级失败，请重试", true);
  }
}

async function learnSkillFromMenu(skillId) {
  showSkillMenuMessage("请前往技能训练师处学习技能", true);
}

document.addEventListener("keydown", (e) => {
  if (e.key.toLowerCase() === "k" && !dialogueOpen && !GameManager.isMenuOpen() && !shopOpen && !inventoryOpen && !playerInfoOpen && !combatOpen && !helpOpen && !questManagerOpen && !npcInteractOpen && !healPanelOpen && !skillLearnPanelOpen && !talentPanelOpen && !(typeof forgePanelOpen !== 'undefined' && forgePanelOpen) && !(typeof worldMapOpen !== 'undefined' && worldMapOpen)) {
    if (skillMenuOpen) {
      closeSkillMenu();
    } else {
      openSkillMenu();
    }
  }
  if (e.key === "Escape" && skillMenuOpen) {
    closeSkillMenu();
  }
});
