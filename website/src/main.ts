import "./styles.css";

const copyButtons = document.querySelectorAll<HTMLButtonElement>("[data-copy]");

for (const button of copyButtons) {
  button.addEventListener("click", async () => {
    const value = button.dataset.copy;
    const label = button.querySelector("span");

    if (!value || !label) return;

    try {
      await navigator.clipboard.writeText(value);
      label.textContent = "Copied";
      button.classList.add("is-copied");
      window.setTimeout(() => {
        label.textContent = "Copy";
        button.classList.remove("is-copied");
      }, 1800);
    } catch {
      label.textContent = "Select text";
    }
  });
}
