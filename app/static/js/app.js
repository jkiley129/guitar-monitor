document.addEventListener("DOMContentLoaded", function () {
  // Dismiss individual match cards
  document.querySelectorAll(".dismiss-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const matchId = btn.dataset.matchId;
      const card = document.getElementById("match-" + matchId);

      fetch("/matches/" + matchId + "/seen", { method: "POST" })
        .then(function (res) {
          if (res.ok && card) {
            card.classList.add("dismissing");
            setTimeout(function () {
              card.remove();
              updateUnseenBadge();
            }, 200);
          }
        })
        .catch(function (err) {
          console.error("Dismiss failed:", err);
        });
    });
  });

  function updateUnseenBadge() {
    const remaining = document.querySelectorAll(".match-card").length;
    const badge = document.querySelector(".navbar .badge");
    if (badge) {
      if (remaining === 0) {
        badge.remove();
      } else {
        badge.textContent = remaining;
      }
    }
  }
});
