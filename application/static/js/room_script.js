// application/static/js/room_script.js
///////////////////////////////////////////////////////////////////////////////
// After 01/2025
// Modified by: Sherry Saavedra
// Before 12/2024
// Original Author: Seth Ely
// Description: JavaScript for handling room interactions, voting, and real-time
// updates (categories removed).
///////////////////////////////////////////////////////////////////////////////

"use strict";

// --- DOM refs ---
const restaurantInfo = document.getElementById("restaurant-info");
const nameDiv        = document.getElementById("restaurant-name");
const imageDiv       = document.getElementById("restaurant-image");
const ratingDiv      = document.getElementById("restaurant-rating");
const priceDiv       = document.getElementById("restaurant-price");

// --- Buttons ---
const endRoomButton  = document.getElementById("end-voting-btn");
const yumButton      = document.getElementById("yum-btn");
const ewButton       = document.getElementById("ew-btn");
const mehButton      = document.getElementById("meh-btn");

// --- Users ---
const guestList = document.getElementById("guest-list");
const IS_HOST =
  typeof userId !== "undefined" &&
  typeof hostUserId !== "undefined" &&
  String(userId) === String(hostUserId);

// --- Polling ---
const POLL_MS = 5000;
let pollTimer = null;

// --- Index for restaurant list (passed via template /room route) ---
let currentIndex = 0;

// Fallback image if a photo fails to load
if (imageDiv) {
  imageDiv.addEventListener("error", () => {
    imageDiv.onerror = null; // prevent loop
    imageDiv.src = "https://via.placeholder.com/400";
    imageDiv.alt = "Restaurant image";
  });
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function updateGuestUserList(users) {
  if (!guestList) return;
  guestList.innerHTML = "";
  users.forEach((user) => {
    if (!currentGuestUser || user.id === currentGuestUser.id) return;
    const li = document.createElement("li");
    li.className = "user-avatar";
    li.textContent = user.Username;
    if (user.done) li.classList.add("user-avatar-done");
    guestList.appendChild(li);
  });
}

async function checkRoomState() {
  try {
    const statusRes = await fetch(`/get_room_status?RoomID=${roomId}`);
    if (statusRes.ok) {
      const { roomStatus } = await statusRes.json();
      if (roomStatus === "inactive") {
        window.location.reload();
        return;
      }
    }
    const usersRes = await fetch(`/get_room_users?RoomID=${roomId}`);
    if (usersRes.ok) updateGuestUserList(await usersRes.json());
  } catch (err) {
    console.error("Error polling for room state:", err);
  }
}

function setVotingEnabled(enabled) {
  [yumButton, mehButton, ewButton].forEach((b) => {
    if (!b) return;
    b.disabled = !enabled;
    b.classList.toggle("disabled", !enabled);
  });
}

// ---------------------------------------------------------------------------
// UI rendering
// ---------------------------------------------------------------------------
function updateRestaurantCard(index) {
  if (!Array.isArray(restaurantData)) return;

  // Finished with all restaurants
  if (index >= restaurantData.length) {
    document.getElementById("completion")?.classList.remove("hidden");
    restaurantInfo?.classList.add("hidden");

    yumButton?.classList.add("hidden");
    ewButton?.classList.add("hidden");
    mehButton?.classList.add("hidden");
    document.getElementById("current-user")?.classList.add("user-avatar-done");

    if (IS_HOST && endRoomButton) {
      endRoomButton.classList.remove("hidden");
      endRoomButton.style.display = "inline-block";
    }

    // Mark this guest as done (once)
    try {
      fetch("/set_guest_done", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ GuestUserID: currentGuestUser?.id }),
      }).catch(() => {});
    } catch (err) {
      console.error("set_guest_done failed:", err);
    }
    return;
  }

  // Render current restaurant
  const r = restaurantData[index] || {};
  if (nameDiv)  nameDiv.textContent = r.name ?? "N/A";

  if (imageDiv) {
    imageDiv.src = r.image_url || "https://via.placeholder.com/400";
    imageDiv.alt = r.name ? `Photo of ${r.name}` : "Restaurant image";
  }

  if (ratingDiv) {
    const rating = r.rating ?? "N/A";
    const reviews = r.review_count ?? 0;
    ratingDiv.textContent = `Rating: ${rating} (${reviews} reviews)`;
  }

  if (priceDiv) {
    const priceLevel = Math.max(0, Math.min(4, Number(r.price_level) || 0));
    priceDiv.textContent = `Price: ${priceLevel ? "$".repeat(priceLevel) : "N/A"}`;
  }
}

// ---------------------------------------------------------------------------
// Actions
// ---------------------------------------------------------------------------
async function castVote(voteChoice) {
  const restaurantID = restaurantData?.[currentIndex]?.id;
  if (!restaurantID) return;

  setVotingEnabled(false);
  try {
    const res = await fetch("/create_vote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        RoomID: roomId,
        GuestUserID: currentGuestUser?.id,
        RestaurantID: restaurantID,
        VoteChoice: voteChoice,
      }),
    });

    if (!res.ok) {
      const { error } = await res.json().catch(() => ({}));
      alert(error || "Failed to cast vote. Please try again.");
      return;
    }

    currentIndex = Math.min(currentIndex + 1, restaurantData.length);
    updateRestaurantCard(currentIndex);
  } catch (err) {
    console.error("Error submitting vote:", err);
    alert("Network error. Please try again.");
  } finally {
    setVotingEnabled(true);
  }
}

async function endVoting() {
  try {
    const res = await fetch("/finalize_room", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ roomId }),
    });
    if (res.ok) {
      window.location.reload();
    } else {
      alert("Failed to finalize room.");
    }
  } catch (err) {
    console.error("Error finalizing room:", err);
    alert("An error occurred. Please try again.");
  }
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  if (
    typeof roomId === "undefined" ||
    typeof restaurantData === "undefined" ||
    typeof currentGuestUser === "undefined"
  ) {
    console.error("Missing required data from template.");
    return;
  }

  // Voting buttons
  if (yumButton) yumButton.addEventListener("click", () => castVote(1));
  if (ewButton)  ewButton.addEventListener("click", () => castVote(-1));
  if (mehButton) mehButton.addEventListener("click", () => castVote(0));

  // Only the host should see/use the end voting action
  if (endRoomButton && IS_HOST) endRoomButton.addEventListener("click", endVoting);

  // Share button with fallback
  const shareButton = document.getElementById("share-btn");
  if (shareButton) {
    shareButton.addEventListener("click", async () => {
      const link = window.location.href;
      try {
        if (navigator.clipboard?.writeText) {
          await navigator.clipboard.writeText(link);
        } else {
          const ta = document.createElement("textarea");
          ta.value = link;
          document.body.appendChild(ta);
          ta.select();
          document.execCommand("copy");
          ta.remove();
        }
        const original = shareButton.textContent;
        shareButton.textContent = "Copied!";
        setTimeout(() => (shareButton.textContent = original), 2000);
      } catch (e) {
        console.error("Copy failed:", e);
        alert("Could not copy the link. You can copy it from the address bar.");
      }
    });
  }

  // Initial render & polling
  updateRestaurantCard(currentIndex);
  checkRoomState();
  pollTimer = setInterval(checkRoomState, POLL_MS);
});

// Clean up polling on page unload
window.addEventListener("beforeunload", () => {
  if (pollTimer) clearInterval(pollTimer);
});