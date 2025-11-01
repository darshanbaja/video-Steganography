document.addEventListener("DOMContentLoaded", () => {
  const flashBox = document.querySelector(".flash");
  if (flashBox) {
    setTimeout(() => flashBox.style.display = "none", 4000);
  }
});
