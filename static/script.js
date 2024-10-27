function toggleAdvancedOptions() {
  const advancedSection = document.getElementById("advanced-options");
  const button = document.getElementById("toggle-button");

  if (advancedSection) {
    // Toggle visibility
    if (
      advancedSection.style.display === "none" ||
      advancedSection.style.display === ""
    ) {
      advancedSection.style.display = "block";
      button.textContent = "Hide Advanced Parameters";
    } else {
      advancedSection.style.display = "none";
      button.textContent = "Show Advanced Parameters";
    }
  } else {
    console.error("Advanced options section not found");
  }
}
