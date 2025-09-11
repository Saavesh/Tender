///////////////////////////////////////////////////////////////////////////////
// room_script.js
///////////////////////////////////////////////////////////////////////////////
// Author:  Seth Ely
// Date:    11/22/2024
///////////////////////////////////////////////////////////////////////////////
// Description:
//   This script maintains and manages all dynamic room functionality for the
//   main voting rooms. It is used to set the username for the user using a
//   cookie, cycling through each restaurant in the room, and allowing the host
//   user to end all voting for the room to serve the final results for all 
//   voting. 
//
//   In addition, it utilizes the following routes located in app.py:
//     - `/get_room_status` queries the database for the current room and
//        returns the status of the room (active/inactive)
//     - `get_room_users` queries the database for all guest users associated
//        with the current room and returns the guest user information
//     - `add_guest_user` creates a new guest user entry in the guest user table
//        and sets a cookie for the user to be remembered for this room
//     - `create_vote` creates a new vote entry in the vote table
//     - `finalize_room` queries the votes from the vote table associated with
//       the room and tabulates the winning restaurant before updating the room
//       entry in the room table to inactive, as well as setting the restaurant 
//       id for the WinningRestaurant foreign key: room.WinningRestaurant
//
// Usage:
//   To use this script, the following variables must be declared before including 
//   the script tag that uses this as a source:
//
//    <script>
//      const roomId = "{{ room.RoomID }}";
//      const userId = {{ current_user.id | default(-1) }};
//      const hostUserId = {{ room.HostUserID }};
//      const restaurantData = {{ restaurant_data|tojson }};
//    </script>
//    <script src="{{ url_for('static', filename='js/room_script.js') }}"></script>
//
//    These are the room attributes that are passed through by the backend route 
//    `/room/<string:roomid>` defined in app.py
//
//    default(-1) is required so that a guest user has an alternative value for 
//    userId (since they are not a logged in user and will not have one)
//
//    |tojson is required to convert the restaurant_data python dictionary to
//    json format
///////////////////////////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////////////////////////
// Global Variables
///////////////////////////////////////////////////////////////////////////////

// Restaurant Info Elements
const restaurantInfo = document.getElementById('restaurant-info');
const nameDiv = document.getElementById('restaurant-name');
const imageDiv = document.getElementById('restaurant-image');
const ratingDiv = document.getElementById('restaurant-rating');
const priceDiv = document.getElementById('restaurant-price');
const descriptionDiv = document.getElementById('restaurant-description');

// Button Elements
const endRoomButton = document.getElementById('end-voting-btn');
const yumButton = document.getElementById("yum-btn");
const ewButton = document.getElementById("ew-btn");
const mehButton = document.getElementById("meh-btn");

// List of Users Elements
const guestList = document.getElementById('guest-list');
const li = document.createElement('li');

// Index for the restaurant list (restaurantData array passed through /room route)
let currentIndex = 0;

///////////////////////////////////////////////////////////////////////////////
// updateGuestUserList(users)
//
// Updates the UI list of guest users based on data received from the server
//
// Parameters:
//    - users: An array of guest user retrieved from the guest user table using
//             the room id in the `get_room_users` route
//
// Returns:
//    - Does not return a value, but updates the list of users in the DOM
///////////////////////////////////////////////////////////////////////////////
function updateGuestUserList(users) {
    // Step 1.
    //   Clear the current list of users
    // Step 2.
    //   Iterate through each user, creating a list item for each
    // Step 3.
    //   Add the avatar class for CSS styling
    // Step 4.
    //   Check if the user is done, and append the user-avatar-done class
    //   to render the div green to indicate completion
    
    guestList.innerHTML = '';
    
    users.forEach(user => {
        if (user.id != currentGuestUser.id) {
            const li = document.createElement('li'); // Create a new list item
            li.className = 'user-avatar';
            li.textContent = user.Username;
            if (user.done) {
                li.classList.add('user-avatar-done');
            }
            guestList.appendChild(li);
        }
    });
}

///////////////////////////////////////////////////////////////////////////////
// checkRoomState()
//
// Used to continuously check the state of the room and reloads the room if
// voting is completed as well as updates the list of users if voting is 
// ongoing. It is run continuously according to the setInterval within the 
// DOMContentLoaded event listener.
//
// Parameters:
//    - None
//
// Returns:
//    - Does not return a value, but updates the list of users in the DOM or
//      causes the page to reload if room is inactive. In this event, the
//      `/room/<string:roomid>` route will render the results template
///////////////////////////////////////////////////////////////////////////////
async function checkRoomState() {
    // Step 1.
    //   Check to see if the room is active or inactive
    //   If inactive, reloading the page will cause the `/room/<string:roomid>`
    //   route to render the results template instead of the voting room
    // Step 2.
    //   Get the list of users for the room using the `get_room_users` route
    // Step 3.
    //   Update the DOM to display the current users using updateGuestUserList
    
    try {
        // Fetch the room status
        const roomStatusResponse = await fetch(`/get_room_status?RoomID=${roomId}`);
        if (roomStatusResponse.ok) {
            const roomData = await roomStatusResponse.json();
            // Check if the room is inactive
            if (roomData.roomStatus === 'inactive') {
                console.log('Room is inactive. Redirecting to the results page.');
                // Reload when inactive will render the results template
                window.location.reload();
                return;
            }
        } else {
            console.error('Failed to fetch room status:', roomStatusResponse.status);
        }

        // If the room is active, fetch guest users
        const response = await fetch(`/get_room_users?RoomID=${roomId}`);
        if (response.ok) {
            const users = await response.json();
            // update the list of users in the DOM
            updateGuestUserList(users);
        } else {
            console.error('Failed to fetch guest users:', response.status);
        }
    } catch (error) {
        console.error('Error fetching guest users or room status:', error);
    }
}

///////////////////////////////////////////////////////////////////////////////
// getCookie(name)
//
// Helper function to get the value of a cookie
//
// Parameters:
//    - name: The name of the cookie to retrieve
//
// Return value:
//    - The value of the cookie if found, null otherwise
///////////////////////////////////////////////////////////////////////////////
function getCookie(name) {
    // Step 1.
    //   Use the following regex to find the cookie in the document cookies:
    //     (?:^|; ) lookbehind, either the beginning of the string or "; "
    //     ${name}= the name parameter followed by the = sign (1st capture group)
    //     ([^;]*) all characters until a ; or end of the string (2nd capture group)
    // Step 2.
    //   If a match is found, return the second capture group (the cookie's value)
    //   If not, return null

    const regex = new RegExp(`(?:^|; )${name}=([^;]*)`);
    const match = document.cookie.match(regex);

    // If a match is found, return the cookie value
    if (match) {
        return match[1];
    }

    // If no match, return null
    console.log(`Cookie not found: ${name}`);
    return null;
}

///////////////////////////////////////////////////////////////////////////////
// updateRestaurantCard()
//
// Updates the UI with the details of the current restaurant or clears it when
// the voting process is complete. If the user is the host user, makes the
// end voting button visible once all voting is complete.
//
// Parameters:
//    - index: The index of the restaurant in the restaurantData array 
//             to be displayed.
//
// Return value:
//    - None
//
// NOTE: Uses the restaurantData array which should be set globally before
//       this script tag in the DOM. See usage in the file header for more info
//
///////////////////////////////////////////////////////////////////////////////
async function updateRestaurantCard(index) {
    // Step 1.
    //   Capture the restaurant info elements in the DOM
    // Step 2.
    //   Checks if voting is complete (index >= length of array) and changes
    //   the UI accordingly, displaying the "end voting" button if the user
    //   is the current room host. Additionally calls set_guest_done to set the
    //   the current user status to done in the database.
    // Step 3.
    //   Finds the current restaurant in the restaurantData array using the
    //   given index
    // Step 4.
    //   Updates the restaurant card with the new restaurant information

    // Restaurant DOM elements
    
    if (index >= restaurantData.length) {       
        const guestUserId = getCookie('GuestUserID');
        if (guestUserId) {
            try {
                const response = await fetch('/set_guest_done', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ GuestUserID: guestUserId })
                });

                if (response.ok) {
                    console.log("User marked as done.");
                } else {
                    const error = await response.json();
                    console.error("Failed to mark user as done:", error.error);
                }
            } catch (error) {
                console.error("Error calling set_guest_done route:", error);
            }
        } else {
            console.warn("GuestUserID not found. Unable to mark user as done.");
        }
        
        
        if (restaurantInfo) {restaurantInfo.innerHTML = ""};
        document.getElementById('current-user').classList.add('user-avatar-done');
        
        
        // Clear the current restaurant details
        nameDiv.textContent = "";
        imageDiv.src = "";
        imageDiv.alt = "No restaurant to display";
        ratingDiv.textContent = "";
        priceDiv.textContent = "";
        descriptionDiv.textContent = "";

        // Hide voting buttons
        yumButton.style.display = "none";
        ewButton.style.display = "none";
        mehButton.style.display = "none";

        // Show the "end voting" button if the user is the host
        if (userId === hostUserId) {
            endRoomButton.style.display = 'block';
            
            const message = document.createElement('p');
            message.id = 'voting-complete-message';
            message.textContent = "Voting complete! Click the button below to end voting for all users.";
            document.getElementById('restaurant-info').appendChild(message);
        } else {
            const message = document.createElement('p');
            message.id = 'voting-complete-message';
            message.textContent = "Voting complete! Please wait for the host to end voting.";
            document.getElementById('restaurant-info').appendChild(message);
        }
    } else {
        const restaurant = restaurantData[index];
        nameDiv.textContent = restaurant.name || "N/A";
        imageDiv.src = restaurant.image_url || "N/A";
        ratingDiv.textContent = `Rating: ${restaurant.rating || "N/A"} (${restaurant.review_count || 0} reviews)`;
        priceDiv.textContent = `Price: ${restaurant.price || "N/A"}`;
        
        // the description is made up of the titles for all categories in the 
        // restaurant data (retrieved from Yelp API)
        let description = "N/A";
        if (restaurant.categories) {
            description = restaurant.categories.map(c => c.title).join(', ');
        }
        descriptionDiv.textContent = description;
    }
}

///////////////////////////////////////////////////////////////////////////////
// castVote(voteChoice)
//
// Creates an entry in the vote table for the current user/restaurant and 
// updates the current restaurant using `updateRestaurantCard`
//
// Parameters:
//    - voteChoice: The vote value (1 for "yum", -1 for "ew", 0 for "meh").
//
// Return value:
//    - None
///////////////////////////////////////////////////////////////////////////////
async function castVote(voteChoice) {
    // Step 1.
    //   sets the current restaurant ID and guest user ID (will be foreign keys
    //   for the vote entry)
    // Step 2.
    //   Set the room id (another foreign key) and vote choice with previous
    //   values to the payload to be sent
    // Step 3.
    //   Use the payload as the body of the request sent to the `/create_vote`
    //   route
    // Step 4.
    //   Increment the current index and render the new restaurant using
    //   updateRestaurantCard and the new index
    
    // set the restaurant id
    const restaurantID = restaurantData[currentIndex].id;
    if (!restaurantID) {
        console.log("Restaurant data not found.");
        return;
    }

    // set the guest user ID
    const guestUserID = getCookie("GuestUserID"); // Retrieve GuestUserID from the cookie
    if (!guestUserID) {
        console.log("Guest User not found.");
        return;
    }

    // create the payload for the create_vote route
    const payload = {
        RoomID: roomId,
        GuestUserID: guestUserID, // Send GuestUserID instead of display name
        RestaurantID: restaurantID,
        VoteChoice: voteChoice
    };

    try {
        // request the create_vote route
        const response = await fetch("/create_vote", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        // update to the next restaurant on success
        if (response.ok) {
            currentIndex++;
            updateRestaurantCard(currentIndex);
        } else {
            const error = await response.json();
            console.error(`Error casting vote: ${error.error}`);
            alert("Failed to cast vote. Please try again.");
        }
    } catch (error) {
        console.error("Error in vote submission:", error);
        alert("An error occurred while submitting your vote.");
    }
}

///////////////////////////////////////////////////////////////////////////////
// endVoting()
//
// Finalizes the voting process for the current room by sending a request to 
// the server to update the room's state. Reloads the page to call the room
// route, which will render the results template now that the page is "inactive"
//
// Parameters:
//    - None
//
// Returns:
//    - None
///////////////////////////////////////////////////////////////////////////////
async function endVoting() {
    // Step 1.
    //   Call the finalize_room route which takes a room id and does the following:
    //     - Tallies all votes with the given room id and determines a winning
    //       restaurant
    //     - Updates the WinningRestaurant foreign key of the current room to
    //       the winner
    //     - Updates the status of the room to "inactive"
    // Step 2.
    //   Reload the page on success, given the /room route will render the
    //   results page now that the room is set to inactive
    
    try {
        const response = await fetch('/finalize_room', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ roomId })
        });

        if (response.ok) {
            const result = await response.json();
            // Reload page to render results template
            window.location.reload();
        } else {
            alert('Failed to finalize room. Please try again.');
        }
    } catch (error) {
        console.error('Error finalizing room:', error);
        alert('An error occurred. Please try again later.');
    }
}


///////////////////////////////////////////////////////////////////////////////
// initializeVoting()
//
// Runs the initial functions for initializing the room logic, such as getting
// the guest user ID, checking the initial room state and setting an interval
// to continuously check the room state every 5 seconds
//
// Parameters:
//    - millis: the number of milliseconds between each call to checkRoomStatus
//
// Returns:
//    - None
///////////////////////////////////////////////////////////////////////////////
async function initializeVoting(millis) {
    updateRestaurantCard(currentIndex);
    checkRoomState();
    setInterval(checkRoomState, millis);
}

///////////////////////////////////////////////////////////////////////////////
// DOMContentLoaded Event Listener
//
// Represents the main entry point for this script. Initializes the current
// index for the restaurant list, assigns the functionality for all buttons
//
// Parameters:
//    - None (Triggered automatically when the DOM is fully loaded.)
//
// Return value:
//    - None
//
// Notes:
//    - Ensures that required global variables (`roomId`, `userId`, `restaurantData`)
//      are defined before proceeding. Displays an alert and halts initialization
//      if any required data is missing.
//    - Sets up the voting process by:
//        1. Initializing DOM elements for dynamic updates.
//        2. Attaching click handlers for voting buttons and the finalize button.
//        3. Periodically checking the room's state to handle real-time updates.
//    - Calls `initializeVoting()` to begin the voting flow, which updates the
//      restaurant card and verifies the room state at regular intervals.
//
// Example Usage:
//    document.addEventListener('DOMContentLoaded', function () { ... });
///////////////////////////////////////////////////////////////////////////////
document.addEventListener('DOMContentLoaded', function () {
    console.log("Script loaded.");

    // Check if required variables are available
    if (!roomId || !userId || !restaurantData) {
        console.error("Missing required data. Ensure 'roomId', 'userId', and 'restaurantData' are provided.");
        alert("Unable to initialize. Missing required data.");
        return;
    }
    
    // Set the function on click for each button
    if (endRoomButton) {endRoomButton.addEventListener('click', endVoting)};
    if (yumButton) {yumButton.addEventListener('click', () => castVote(1))};
    if (ewButton) {ewButton.addEventListener('click', () => castVote(-1))};
    if (mehButton) {mehButton.addEventListener('click', () => castVote(0))};

    initializeVoting(5000, currentIndex);
});
