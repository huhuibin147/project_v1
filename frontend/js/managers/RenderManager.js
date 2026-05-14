// 渲染管理器 - 脏矩形优化渲染

const RenderManager = (() => {
  let dirty = true;
  let lastState = {
    playerX: 0,
    playerY: 0,
    cameraX: 0,
    cameraY: 0,
    monsterCount: 0,
    npcCount: 0,
    mapObjectsHash: '',
    monsterPositionsHash: ''
  };
  let frameCount = 0;
  let forceRenderEveryNFrames = 2;

  function checkDirty() {
    if (dirty) return true;

    if (typeof player !== 'undefined') {
      if (player.x !== lastState.playerX || player.y !== lastState.playerY) {
        return true;
      }
    }

    if (typeof camera !== 'undefined') {
      if (camera.x !== lastState.cameraX || camera.y !== lastState.cameraY) {
        return true;
      }
    }

    if (typeof mapMonsters !== 'undefined') {
      const aliveCount = mapMonsters.filter(m => m.alive).length;
      if (aliveCount !== lastState.monsterCount) {
        return true;
      }
      const posHash = mapMonsters.filter(m => m.alive).map(m => `${m.x.toFixed(1)},${m.y.toFixed(1)}`).join('|');
      if (posHash !== lastState.monsterPositionsHash) {
        return true;
      }
    }

    if (typeof npcs !== 'undefined') {
      if (npcs.length !== lastState.npcCount) {
        return true;
      }
    }

    frameCount++;
    if (frameCount >= forceRenderEveryNFrames) {
      frameCount = 0;
      return true;
    }

    return false;
  }

  function updateState() {
    if (typeof player !== 'undefined') {
      lastState.playerX = player.x;
      lastState.playerY = player.y;
    }

    if (typeof camera !== 'undefined') {
      lastState.cameraX = camera.x;
      lastState.cameraY = camera.y;
    }

    if (typeof mapMonsters !== 'undefined') {
      lastState.monsterCount = mapMonsters.filter(m => m.alive).length;
      lastState.monsterPositionsHash = mapMonsters.filter(m => m.alive).map(m => `${m.x.toFixed(1)},${m.y.toFixed(1)}`).join('|');
    }

    if (typeof npcs !== 'undefined') {
      lastState.npcCount = npcs.length;
    }
  }

  function markDirty() {
    dirty = true;
  }

  function render(ctx, canvas) {
    if (!checkDirty()) {
      return;
    }

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

    updateState();
    dirty = false;
  }

  function setForceRenderInterval(frames) {
    forceRenderEveryNFrames = frames;
  }

  return {
    markDirty,
    render,
    setForceRenderInterval,
    isDirty: () => dirty
  };
})();
