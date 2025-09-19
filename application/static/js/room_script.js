// application/static/js/room_script.js
///////////////////////////////////////////////////////////////////////////////
// After 01/2025
// Modified by: Sherry Saavedra
// Before 12/2024 
// Original Author:  Seth Ely
// Description: JavaScript for handling room interactions, voting, and real-time updates.
///////////////////////////////////////////////////////////////////////////////

// --- Global Variables ---
const restaurantInfo = document.getElementById('restaurant-info');
const nameDiv = document.getElementById('restaurant-name');
const imageDiv = document.getElementById('restaurant-image');
const ratingDiv = document.getElementById('restaurant-rating');
const priceDiv = document.getElementById('restaurant-price');
const descriptionDiv = document.getElementById('restaurant-description');

// --- Buttons ---
const endRoomButton = document.getElementById('end-voting-btn');
const yumButton = document.getElementById("yum-btn");
const ewButton = document.getElementById("ew-btn");
const mehButton = document.getElementById("meh-btn");

// --- Users ---
const guestList = document.getElementById('guest-list');
const IS_HOST = String(userId) === String(hostUserId);


// --- Index for restaurant list. passed throuhg /room route ---
let currentIndex = 0;

// --- Functions ---
function updateGuestUserList(users) {
    guestList.innerHTML = '';
    users.forEach(user => {
        if (user.id !== currentGuestUser.id) {
            const li = document.createElement('li');
            li.className = 'user-avatar';
            li.textContent = user.Username;
            if (user.done) {
                li.classList.add('user-avatar-done');
            }
            guestList.appendChild(li);
        }
    });
}

async function checkRoomState() {
    try {
        const roomStatusResponse = await fetch(`/get_room_status?RoomID=${roomId}`);
        if (roomStatusResponse.ok) {
            const roomData = await roomStatusResponse.json();
            if (roomData.roomStatus === 'inactive') {
                window.location.reload();
                return;
            }
        }
        // Update guest user list if room is still active
        const usersResponse = await fetch(`/get_room_users?RoomID=${roomId}`);
        if (usersResponse.ok) {
            const users = await usersResponse.json();
            updateGuestUserList(users);
        }
    } catch (error) {
        console.error('Error polling for room state:', error);
    }
}

async function updateRestaurantCard(index) {
  // done with all restaurants
  if (index >= restaurantData.length) {
    document.getElementById('completion-message')?.classList.remove('hidden');
    restaurantInfo?.classList.add('hidden'); // or try: restaurantInfo.style.display = 'none'; if this doesnt work

    // Hide only voting buttons, NOT the container (so the end button can show)
    yumButton?.classList.add('hidden');
    ewButton?.classList.add('hidden');
    mehButton?.classList.add('hidden');

    document.getElementById('current-user')?.classList.add('user-avatar-done');

    // Show the end button for the host
    if (IS_HOST && endRoomButton) {
      endRoomButton.classList.remove('hidden');
      endRoomButton.style.display = 'inline-block';
    }

    try {
      await fetch('/set_guest_done', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ GuestUserID: currentGuestUser.id })
      });
    } catch (err) {
      console.error('set_guest_done failed:', err);
    }
    return;
  }

  // otherwise, render the current restaurant
  const r = restaurantData[index] || {};
  nameDiv.textContent = r.name ?? 'N/A';
  imageDiv.src = r.image_url || 'https://via.placeholder.com/400';
  ratingDiv.textContent = `Rating: ${r.rating ?? 'N/A'} (${r.review_count ?? 0} reviews)`;

  const priceLevel = Math.max(0, Math.min(4, Number(r.price_level) || 0));
  priceDiv.textContent = `Price: ${priceLevel ? '$'.repeat(priceLevel) : 'N/A'}`;

  const cats = Array.isArray(r.categories) ? r.categories.map(c => c.title).join(', ') : 'N/A';
  descriptionDiv.textContent = cats;
}


async function castVote(voteChoice) {
    const restaurantID = restaurantData[currentIndex]?.id;
    if (!restaurantID) return;

    const payload = {
        RoomID: roomId,
        GuestUserID: currentGuestUser.id,
        RestaurantID: restaurantID,
        VoteChoice: voteChoice
    };

    try {
        const response = await fetch("/create_vote", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            currentIndex++;
            updateRestaurantCard(currentIndex);
        } else {
            alert("Failed to cast vote. Please try again.");
        }
    } catch (error) {
        console.error("Error submitting vote:", error);
    }
}

async function endVoting() {
  try {
    const res = await fetch('/finalize_room', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ roomId })
    });
    if (res.ok) {
      // show results
      window.location.reload();
    } else {
      alert('Failed to finalize room.');
    }
  } catch (err) {
    console.error('Error finalizing room:', err);
    alert('An error occurred. Please try again.');
  }
}

// --- Event Listeners ---
document.addEventListener('DOMContentLoaded', function () {
    if (!roomId || !restaurantData || !currentGuestUser) {
        console.error("Missing required data from template.");
        return;
    }

    // Voting buttons
    if (yumButton) yumButton.addEventListener('click', () => castVote(1));
    if (ewButton) ewButton.addEventListener('click', () => castVote(-1));
    if (mehButton) mehButton.addEventListener('click', () => castVote(0));
    if (endRoomButton) endRoomButton.addEventListener('click', endVoting);
    
    // Share button
    const shareButton = document.getElementById('share-btn');
    if (shareButton) {
        shareButton.addEventListener('click', () => {
            navigator.clipboard.writeText(window.location.href).then(() => {
                const originalText = shareButton.textContent;
                shareButton.textContent = 'Copied!';
                setTimeout(() => { shareButton.textContent = originalText; }, 2000);
            }).catch(err => console.error('Failed to copy link: ', err));
        });
    }

    // Initial setup
    updateRestaurantCard(currentIndex);
    checkRoomState(); // Initial check
    setInterval(checkRoomState, 5000); // Poll every 5 seconds
});