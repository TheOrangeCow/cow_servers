const title = document.getElementById("title");
const containor = document.getElementById("containor");

function spawnDust() {
    const rect = title.getBoundingClientRect();
    const startY = rect.bottom - 4;

    for (let i = 0; i < 120; i++) {
        setTimeout(() => {
            const dust = document.createElement("div");
            dust.className = "dust";
            dust.style.left = rect.left + Math.random() * rect.width + "px";
            dust.style.top = startY + "px";
            const x = (Math.random() - 0.5) * 40;
            const y = 180 + Math.random() * 80;
            dust.style.setProperty("--x", x + "px");
            dust.style.setProperty("--y", y + "px");
            document.body.appendChild(dust);
            setTimeout(() => dust.remove(), 2600);
        }, Math.random() * 350);
    }
}

title.addEventListener("animationend", () => {
    spawnDust();
    containor.classList.add("show");
});