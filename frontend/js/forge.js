let forgePanelOpen = false;
let forgeNpcId = null;
let forgeRecipes = [];
let forgeFilter = "all";
const forgePage = { current: 1 };
const FORGE_PER_PAGE = 6;

const FORGE_TIER_NAMES = {
  basic: "初级",
  intermediate: "中级",
  advanced: "高级",
  master: "大师",
};

const FORGE_TIER_COLORS = {
  basic: "#aaaaaa",
  intermediate: "#1eff00",
  advanced: "#0070dd",
  master: "#a335ee",
};

function openForgePanel(npcId) {
  if (combatOpen) return;
  forgePanelOpen = true;
  forgeNpcId = npcId || "blacksmith";
  forgePage.current = 1;
  forgeFilter = "all";
  fetchForgeRecipes().then(() => renderForgePanel());
  document.getElementById("forge-panel").classList.add("active");
  document.getElementById("player-gold-forge").textContent = inventoryState.gold || 0;
}

function closeForgePanel() {
  forgePanelOpen = false;
  forgeNpcId = null;
  document.getElementById("forge-panel").classList.remove("active");
  document.getElementById("forge-message").style.display = "none";
}

async function fetchForgeRecipes() {
  try {
    const resp = await fetch(`/api/forge/recipes?npc_id=${forgeNpcId}`);
    const data = await resp.json();
    forgeRecipes = data.recipes || [];
    document.getElementById("player-gold-forge").textContent = data.player_gold || 0;
  } catch (e) {
    console.error("获取锻造配方失败:", e);
  }
}

function filterForgeRecipes(filter) {
  forgeFilter = filter;
  forgePage.current = 1;
  document.querySelectorAll(".forge-filter-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.filter === filter);
  });
  renderForgePanel();
}

function getFilteredForgeRecipes() {
  if (forgeFilter === "all") return forgeRecipes;
  return forgeRecipes.filter(r => r.category === forgeFilter);
}

function renderForgePanel() {
  const container = document.getElementById("forge-recipes");
  container.innerHTML = "";

  const filtered = getFilteredForgeRecipes();

  if (filtered.length === 0) {
    container.innerHTML = '<div class="empty-hint">暂无可用配方</div>';
    renderPagination("forge-pagination", 0, forgePage);
    return;
  }

  const total = filtered.length;
  const totalPages = Math.ceil(total / FORGE_PER_PAGE);
  if (forgePage.current > totalPages) forgePage.current = totalPages;
  const start = (forgePage.current - 1) * FORGE_PER_PAGE;
  const pageItems = filtered.slice(start, start + FORGE_PER_PAGE);

  for (const recipe of pageItems) {
    const div = document.createElement("div");
    const tierName = FORGE_TIER_NAMES[recipe.tier] || recipe.tier;
    const tierColor = FORGE_TIER_COLORS[recipe.tier] || "#aaa";
    const outputRarityColor = getRarityColor(recipe.rarity_guarantee);
    const outputRarityName = getRarityName(recipe.rarity_guarantee);

    let materialsHtml = "";
    for (const mat of recipe.materials) {
      const enough = mat.owned >= mat.quantity;
      const cls = enough ? "mat-enough" : "mat-lack";
      materialsHtml += `<span class="${cls}">${mat.name}×${mat.quantity}(${mat.owned})</span> `;
    }

    const successPercent = Math.round(recipe.success_rate * 100);
    const canCraft = recipe.can_craft;
    const btnText = canCraft ? "开始锻造" : (!recipe.level_ok ? "等级不足" : (!recipe.gold_ok ? "金币不足" : "材料不足"));
    const btnClass = canCraft ? "btn-forge" : "btn-forge-disabled";

    let outputStatsHtml = "";
    if (recipe.output.stats) {
      outputStatsHtml = `<div class="forge-output-stats">${formatItemStats(recipe.output.stats)}</div>`;
    }

    div.className = "forge-recipe-card";
    div.innerHTML = `
      <div class="forge-recipe-header">
        <span class="forge-recipe-name">${recipe.name}</span>
        <span class="forge-recipe-tier" style="color:${tierColor}">[${tierName}]</span>
      </div>
      <div class="forge-recipe-body">
        <div class="forge-recipe-output">
          <span class="forge-output-label">产出:</span>
          <span class="forge-output-name" style="color:${outputRarityColor}">${recipe.output.name}</span>
          <span class="forge-output-rarity" style="color:${outputRarityColor}">[${outputRarityName}]</span>
          ${recipe.output.equip_slot ? `<span class="forge-output-slot">${getSlotLabel(recipe.output.equip_slot)}</span>` : ""}
          ${outputStatsHtml}
        </div>
        <div class="forge-recipe-materials">
          <span class="forge-mat-label">材料:</span> ${materialsHtml}
        </div>
        <div class="forge-recipe-meta">
          <span>金币: ${recipe.gold_cost}</span>
          <span>等级: Lv.${recipe.level_requirement}</span>
          <span>成功率: ${successPercent}%</span>
          <span>保底: <span style="color:${outputRarityColor}">${outputRarityName}</span></span>
        </div>
      </div>
      <div class="forge-recipe-actions">
        <button class="${btnClass}" ${canCraft ? "" : "disabled"} onclick="doForge('${recipe.recipe_id}')">${btnText}</button>
      </div>
    `;
    container.appendChild(div);
  }

  renderPagination("forge-pagination", totalPages, forgePage);
}

async function doForge(recipeId) {
  if (!forgeNpcId) return;
  try {
    const resp = await fetch("/api/forge/craft", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipe_id: recipeId, npc_id: forgeNpcId }),
    });
    const data = await resp.json();

    showForgeMessage(data.message, data.forged);

    if (data.forged || data.success) {
      if (data.player_inventory) {
        inventoryState.items = data.player_inventory;
      }
      if (data.player_gold !== undefined) {
        inventoryState.gold = data.player_gold;
        updateGoldDisplay();
      }
      document.getElementById("player-gold-forge").textContent = inventoryState.gold || 0;
      fetchForgeRecipes().then(() => renderForgePanel());

      if (data.forged && data.result) {
        showForgeResult(data.result);
      }
    }
  } catch (e) {
    showForgeMessage("锻造请求失败，请重试", false);
    console.error("锻造请求失败:", e);
  }
}

function showForgeMessage(msg, success) {
  const el = document.getElementById("forge-message");
  el.textContent = msg;
  el.className = `trade-message ${success ? "success" : "fail"}`;
  el.style.display = "block";
  setTimeout(() => { el.style.display = "none"; }, 3000);
}

function showForgeResult(result) {
  const overlay = document.getElementById("forge-result-overlay");
  const content = document.getElementById("forge-result-content");

  const rarityColor = getRarityColor(result.rarity);
  const rarityName = getRarityName(result.rarity);

  let affixesHtml = "";
  if (result.affixes && result.affixes.length > 0) {
    affixesHtml = '<div class="forge-result-affixes">';
    for (const affix of result.affixes) {
      affixesHtml += `<div class="forge-result-affix"><span class="affix-tag">${affix.name}</span> <span class="affix-desc">${affix.description}</span></div>`;
    }
    affixesHtml += "</div>";
  }

  content.innerHTML = `
    <div class="forge-result-title">⚒️ 锻造成功！</div>
    <div class="forge-result-item">
      <span class="forge-result-name" style="color:${rarityColor}">${result.name}</span>
      <span class="forge-result-rarity" style="color:${rarityColor}">[${rarityName}]</span>
    </div>
    ${affixesHtml}
    <button class="btn-forge-confirm" onclick="closeForgeResult()">确定</button>
  `;

  overlay.classList.add("active");
}

function closeForgeResult() {
  document.getElementById("forge-result-overlay").classList.remove("active");
}
