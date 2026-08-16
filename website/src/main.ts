import "./styles.css";

const copyButtons = document.querySelectorAll<HTMLButtonElement>("[data-copy]");
const menuButton = document.querySelector<HTMLButtonElement>(".menu-button");
const mobileNav = document.querySelector<HTMLElement>("#mobile-nav");

menuButton?.addEventListener("click", () => {
  const isOpen = mobileNav?.classList.toggle("is-open") ?? false;
  menuButton.setAttribute("aria-expanded", String(isOpen));
});

mobileNav?.querySelectorAll<HTMLAnchorElement>("a").forEach((link) => {
  link.addEventListener("click", () => {
    mobileNav.classList.remove("is-open");
    menuButton?.setAttribute("aria-expanded", "false");
  });
});

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
