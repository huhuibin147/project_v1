// 游戏核心管理器

const GameManager = (() => {
  let canvas, ctx;
  let lastTime = 0;
  let gameStarted = false;
  let gameMenuOpen = false;
  let positionSaveTimer = null;

  function initCanvas() {
    canvas = document.getElementById("game-canvas");
    ctx = canvas.getContext("2d");
    resizeCanvas();
    ctx.imageSmoothingEnabled = false;
    window.addEventListener('resize', resizeCanvas);
  }

  function resizeCanvas() {
    if (!canvas) return;
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    if (typeof camera !== 'undefined') {
      camera.viewportWidth = canvas.width;
      camera.viewportHeight = canvas.height;
    }
  }

  function gameLoop(timestamp) {
    const dt = timestamp - lastTime;
    lastTime = timestamp;

    if (gameStarted) {
      update(dt);
      render();
    }

    requestAnimationFrame(gameLoop);
  }

  function update(dt) {
    if (typeof updatePlayer === 'function') updatePlayer();
    if (typeof updateCamera === 'function') updateCamera();
    if (typeof checkPortalAutoTransfer === 'function') checkPortalAutoTransfer();
    if (typeof updateMonsters === 'function') updateMonsters(dt);
    if (typeof recordExploredTile === 'function') recordExploredTile();
  }

  function render() {
    if (!ctx || !canvas) return;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    
    if (typeof camera !== 'undefined') {
      ctx.translate(-camera.x, -camera.y);
    }

    if (typeof drawMap === 'function') drawMap(ctx);
    if (typeof drawObjects === 'function') drawObjects(ctx);
    if (typeof drawEnvironmentParticles === 'function') drawEnvironmentParticles(ctx);

    const drawables = [];

    if (typeof npcs !== 'undefined') {
      for (const npc of npcs) {
        drawables.push({ type: "npc", y: npc.y, data: npc });
      }
    }
    
    if (typeof mapMonsters !== 'undefined') {
      for (const m of mapMonsters) {
        if (m.alive) {
          drawables.push({ type: "monster", y: m.y, data: m });
        }
      }
    }
    
    if (typeof player !== 'undefined') {
      drawables.push({ type: "player", y: player.y, data: player });
    }

    drawables.sort((a, b) => a.y - b.y);

    for (const obj of drawables) {
      if (obj.type === "npc" && typeof drawNPC === 'function') {
        drawNPC(ctx, obj.data);
      } else if (obj.type === "monster" && typeof drawMapMonster === 'function') {
        drawMapMonster(ctx, obj.data);
      } else if (obj.type === "player" && typeof drawPlayer === 'function') {
        drawPlayer(ctx);
      }
    }

    ctx.restore();

    if (typeof renderMinimap === 'function') renderMinimap();
    if (typeof updateHudMapName === 'function') updateHudMapName();
    if (typeof drawGatherHint === 'function') drawGatherHint();
    if (typeof drawHUD === 'function') drawHUD(ctx);
  }

  async function startGame() {
    initCanvas();
    
    if (typeof LoadingManager !== 'undefined') {
      LoadingManager.startLoading();
    }

    try {
      if (typeof initMapSystem === 'function') await initMapSystem();
      if (typeof initWorldMap === 'function') initWorldMap();
      
      gameStarted = true;

      if (typeof fetchPlayerInfo === 'function') await fetchPlayerInfo();
      if (typeof loadMonstersConfig === 'function') await loadMonstersConfig();

      const mapId = typeof playerInfo !== 'undefined' ? (playerInfo.current_map || "village") : "village";
      if (typeof loadMap === 'function') await loadMap(mapId);

      if (typeof fetchAllNpcs === 'function') await fetchAllNpcs();
      if (typeof loadMapMonsters === 'function') loadMapMonsters();
      if (typeof fetchInventory === 'function') fetchInventory();
      if (typeof fetchAllQuests === 'function') await fetchAllQuests();
      if (typeof updateQuestTracker === 'function') updateQuestTracker();
      if (typeof startExploreCheck === 'function') startExploreCheck();

      if (typeof updateCamera === 'function') updateCamera();

      if (positionSaveTimer) clearInterval(positionSaveTimer);
      positionSaveTimer = setInterval(() => {
        if (gameStarted && typeof savePlayerPosition === 'function') {
          savePlayerPosition();
        }
      }, 5000);

      if (typeof InputManager !== 'undefined') {
        InputManager.init();
      }
    } catch (e) {
      console.error("游戏启动失败:", e);
    } finally {
      if (typeof LoadingManager !== 'undefined') {
        LoadingManager.finishLoading();
      }
    }
  }

  function stopGame() {
    gameStarted = false;
    if (positionSaveTimer) {
      clearInterval(positionSaveTimer);
      positionSaveTimer = null;
    }
  }

  function toggleGameMenu() {
    if (gameMenuOpen) {
      closeGameMenu();
    } else {
      openGameMenu();
    }
  }

  function openGameMenu() {
    gameMenuOpen = true;
    const menuPanel = document.getElementById("game-menu-panel");
    if (menuPanel) menuPanel.classList.add("active");
  }

  function closeGameMenu() {
    gameMenuOpen = false;
    const menuPanel = document.getElementById("game-menu-panel");
    if (menuPanel) menuPanel.classList.remove("active");
  }

  function saveGame() {
    closeGameMenu();
    if (typeof savePlayerPosition === 'function') {
      savePlayerPosition().then(() => {
        alert("游戏已保存！");
      });
    }
  }

  function returnToMainMenu() {
    closeGameMenu();
    if (!confirm("确定要返回主菜单吗？")) {
      return;
    }
    
    if (typeof savePlayerPosition === 'function') {
      savePlayerPosition().then(() => {
        stopGame();
        
        if (typeof dialogueOpen !== 'undefined' && dialogueOpen && typeof closeDialogue === 'function') closeDialogue();
        if (typeof inventoryOpen !== 'undefined' && inventoryOpen && typeof closeInventory === 'function') closeInventory();
        if (typeof shopOpen !== 'undefined' && shopOpen && typeof closeShop === 'function') closeShop();
        if (typeof playerInfoOpen !== 'undefined' && playerInfoOpen && typeof closePlayerInfo === 'function') closePlayerInfo();
        if (typeof talentPanelOpen !== 'undefined' && talentPanelOpen && typeof closeTalentPanel === 'function') closeTalentPanel();
        if (typeof forgePanelOpen !== 'undefined' && forgePanelOpen && typeof closeForgePanel === 'function') closeForgePanel();
        if (typeof npcInteractOpen !== 'undefined' && npcInteractOpen && typeof closeNpcInteract === 'function') closeNpcInteract();
        if (typeof combatOpen !== 'undefined' && combatOpen && typeof endCombat === 'function') endCombat();

        const gameContainer = document.getElementById("game-container");
        if (gameContainer) gameContainer.style.display = "none";
        
        const startScreen = document.getElementById("start-screen");
        if (startScreen) {
          startScreen.classList.remove("hidden");
          if (typeof initStartScreen === 'function') initStartScreen();
        }
      });
    }
  }

  function isStarted() {
    return gameStarted;
  }

  function isMenuOpen() {
    return gameMenuOpen;
  }

  function getCanvas() {
    return canvas;
  }

  function getContext() {
    return ctx;
  }

  return {
    init: () => {
      requestAnimationFrame(gameLoop);
    },
    start: startGame,
    stop: stopGame,
    toggleGameMenu,
    openGameMenu,
    closeGameMenu,
    saveGame,
    returnToMainMenu,
    isStarted,
    isMenuOpen,
    getCanvas,
    getContext
  };
})();
