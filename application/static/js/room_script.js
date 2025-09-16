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
const endRoomButton = document.getElementById('end-voting-btn');
const yumButton = document.getElementById("yum-btn");
const ewButton = document.getElementById("ew-btn");
const mehButton = document.getElementById("meh-btn");
const guestList = document.getElementById('guest-list');
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
    if (index >= restaurantData.length) {
        document.getElementById('completion-message').classList.remove('hidden');
        document.getElementById('restaurant-info').style.display = 'none';
        document.querySelector('.vote-buttons').style.display = 'none';
        document.getElementById('current-user').classList.add('user-avatar-done');
        
        await fetch('/set_guest_done', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ GuestUserID: currentGuestUser.id })
        });

        if (userId === hostUserId && endRoomButton) {
            endRoomButton.style.display = 'block';
        }
    } else {
        const restaurant = restaurantData[index];
        nameDiv.textContent = restaurant.name || "N/A";
        imageDiv.src = restaurant.image_url || "https://via.placeholder.com/400";
        ratingDiv.textContent = `Rating: ${restaurant.rating || "N/A"} (${restaurant.review_count || 0} reviews)`;
        // Convert numeric price_level to dollar signs
        priceDiv.textContent = `Price: ${'$'.repeat(restaurant.price_level) || 'N/A'}`;
        descriptionDiv.textContent = restaurant.categories ? restaurant.categories.map(c => c.title).join(', ') : "N/A";
    }
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
        const response = await fetch('/finalize_room', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ roomId })
        });
        if (!response.ok) alert('Failed to finalize room.');
    } catch (error) {
        console.error('Error finalizing room:', error);
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