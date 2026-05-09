let helpOpen = false;

function openHelp() {
  if (dialogueOpen || shopOpen || inventoryOpen || playerInfoOpen || combatOpen) return;
  helpOpen = true;
  document.getElementById("help-panel").classList.add("active");
}

function closeHelp() {
  helpOpen = false;
  document.getElementById("help-panel").classList.remove("active");
}

document.addEventListener("keydown", (e) => {
  if (e.key.toLowerCase() === "h" && !dialogueOpen && !gameMenuOpen && !shopOpen && !inventoryOpen && !playerInfoOpen && !combatOpen) {
    if (helpOpen) {
      closeHelp();
    } else {
      openHelp();
    }
  }
  if (e.key === "Escape" && helpOpen) {
    closeHelp();
  }
});
