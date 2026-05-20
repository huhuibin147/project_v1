let helpOpen = false;

// 注册面板
PanelManager.register('help',
  () => { helpOpen = true; document.getElementById("help-panel").classList.add("active"); },
  () => { helpOpen = false; document.getElementById("help-panel").classList.remove("active"); }
);

function openHelp() {
  if (PanelManager.isAnyOpen() || GameManager.isMenuOpen()) return;
  PanelManager.open('help');
}

function closeHelp() {
  PanelManager.close('help');
}


