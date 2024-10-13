let map;
let infoWindow;
let directionsService;
let directionsRenderer;

function initMap() {
    const myloc = { lat: 40.38127583822331, lng: 49.86776630483177 };

    map = new google.maps.Map(document.getElementById("map"), {
        zoom: 12,
        center: myloc,
    });

    new google.maps.Marker({
        position: myloc,
        map: map,
        title: "You are here",
        icon: {
            url: "https://maps.google.com/mapfiles/ms/icons/blue-dot.png",
            scaledSize: new google.maps.Size(50, 50)
        },
    });

    infoWindow = new google.maps.InfoWindow();

    directionsService = new google.maps.DirectionsService();
    directionsRenderer = new google.maps.DirectionsRenderer();
    directionsRenderer.setMap(map);

    fetchNearbyPlaces(myloc);

    map.addListener("click", () => {
        infoWindow.close();
    });
}

function fetchNearbyPlaces(location) {
    const service = new google.maps.places.PlacesService(map);
    const request = {
        location: location,
        radius: '500',
        type: 'museum'
    };

    service.nearbySearch(request, processResults);
}

function processResults(results, status, pagination) {
    if (status === google.maps.places.PlacesServiceStatus.OK) {
        for (let i = 0; i < results.length; i++) {
            createMarker(results[i]);
        }

        if (pagination && pagination.hasNextPage) {
            setTimeout(() => {
                pagination.nextPage();
            }, 2000);
        }
    } else {
        console.error('Places request failed due to ' + status);
    }
}

function createMarker(place, eventMarker = false) {
    const iconUrl = eventMarker
        ? "https://maps.google.com/mapfiles/ms/icons/red-dot.png" // Color for venues with events
        : "https://maps.google.com/mapfiles/ms/icons/green-dot.png"; // Color for regular venues

    const marker = new google.maps.Marker({
        position: place.geometry.location,
        map: map,
        title: place.name,
        icon: {
            url: iconUrl,
            scaledSize: new google.maps.Size(50, 50),
        },
    });

    marker.addListener("click", () => {
        map.setZoom(15);
        map.setCenter(place.geometry.location);

        const infoWindowContent = `
            <div style="
                width: 200px; 
                display: flex; 
                flex-direction: column; 
                justify-content: space-between; 
                height: auto;
            ">
                <div>
                    <h3 style="margin: 0; font-size: 16px;">${place.name}</h3>
                    <p style="margin: 5px 0; font-size: 14px;">${place.vicinity}</p>
                </div>
                <button id="start-route-btn" style="
                    align-self: flex-end;
                    padding: 5px 10px;
                    background-color: #4CAF50;
                    color: white;
                    margin-right: 10px;
                    border: none;
                    border-radius: 3px;
                    cursor: pointer;
                    margin-top: 10px;
                    padding-right: 10px;
                ">Start Route</button>
            </div>
        `;

        infoWindow.setContent(infoWindowContent);
        infoWindow.open(map, marker);

        google.maps.event.addListenerOnce(infoWindow, "domready", () => {
            document.getElementById("start-route-btn").addEventListener("click", () => {
                drawRoute(place);
            });
        });
    });

    return marker;
}

function drawRoute(place) {
    const myloc = { lat: 40.38127583822331, lng: 49.86776630483177 };
    const destination = {
        lat: place.geometry.location.lat(),
        lng: place.geometry.location.lng(),
    };

    const request = {
        origin: myloc,
        destination: destination,
        travelMode: 'DRIVING'
    };

    directionsService.route(request, (result, status) => {
        if (status === 'OK') {
            directionsRenderer.setDirections(result);
        } else {
            console.error('Directions request failed due to ' + status);
        }
    });
}

// API calls

// Events

// Get
async function getEvents() {
    try {
        const response = await fetch("http://localhost:8000/events/all");
        const events = await response.json();

        const eventsContainer = document.querySelector(".upcoming-events");
        eventsContainer.innerHTML = "<h2>Upcoming Events</h2>";

        for (const event of events) {
            const eventElement = document.createElement("div");
            eventElement.style.display = "flex";
            eventElement.style.alignItems = "center";
            eventElement.style.marginBottom = "20px";
            eventElement.style.cursor = "pointer";

            const eventImage = document.createElement("img");
            eventImage.src = "./event3.jpg";
            eventImage.alt = event.title;
            eventImage.classList.add("event-image");
            eventImage.style.marginRight = "20px";
            eventImage.style.width = "80px";
            eventImage.style.height = "80px";

            const eventTextContainer = document.createElement("div");
            eventTextContainer.style.display = "flex";
            eventTextContainer.style.flexDirection = "column";

            const eventTitle = document.createElement("h3");
            eventTitle.textContent = event.title;

            const eventDescription = document.createElement("p");
            eventDescription.textContent = event.description;

            const eventDate = document.createElement("p");
            eventDate.innerHTML = `<strong>Date:</strong> ${new Date(event.date).toLocaleString()}`;

            eventTextContainer.appendChild(eventTitle);
            eventTextContainer.appendChild(eventDescription);
            eventTextContainer.appendChild(eventDate);

            eventElement.appendChild(eventImage);
            eventElement.appendChild(eventTextContainer);
            eventsContainer.appendChild(eventElement);

            const responsex = await fetch(`http://localhost:8000/events/${event.id}`);
            const marked_event = await responsex.json();

            const respond_venues = await fetch(`http://localhost:8000/venues/${marked_event.venue_id}`);
            const marked_venue = await respond_venues.json();

            const lat = parseFloat(marked_venue.lat);
            const lng = parseFloat(marked_venue.lng);

            if (!isNaN(lat) || !isNaN(lng)){
                const marker = createMarker({
                    geometry: {
                        location: new google.maps.LatLng(lat, lng),
                    },
                    name: marked_event.title,
                    vicinity: marked_venue.name || "Unknown location"
                }, true);

                eventElement.addEventListener("click", () => {
                    map.setZoom(15);
                    map.setCenter(marker.getPosition());
                });
            }
        }
    } catch (error) {
        console.error("Error fetching events:", error);
    }
}

async function getFavoriteEvents() {
    try {
        const response = await fetch('http://localhost:8000/events/favorites', {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json', 
              "Authorization" : `Bearer ${localStorage.getItem("token")}`
            },
        });
        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error('Error:', error);
    }
}

async function getEvent(event_id) {
    try {
        const response = await fetch('http://localhost:8000/events/'+ event_id);
        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error('Error:', error);
    }
}

// Comment
async function getEventComments(event_id) {
    try {
        const response = await fetch('http://localhost:8000/events/' + event_id + "/comment");
        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error('Error:', error);
    }
}

async function getEventComment(comment_id) {
    try {
        const response = await fetch('http://localhost:8000/events/comment/' + comment_id);
        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error('Error:', error);
    }
}

// Post

async function createEvent(inputData) {
    try {
        const response = await fetch('http://localhost:8000/events', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json', 
            },
            body: JSON.stringify(inputData),
          })
            .then(response => response.json())
            .then(data => {
              console.log('Success:', data);
            })
            .catch(error => {
              console.error('Error:', error);
            });

        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error('Error:', error);
    }
}

// Like
//Get

// Post

async function createEventLike(inputData) {
    try {
        const response = await fetch('http://localhost:8000/events/like', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json', 
              "Authorization" : `Bearer ${localStorage.getItem("token")}`
            },
            body: JSON.stringify({
                event: inputData.event
            }),
          })
            .then(response => response.json())
            .then(data => {
                console.log('Success:', data);
            })
            .catch(error => {
                console.error('Error:', error);
            });

        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error('Error:', error);
    }
}

// Delete

function drawRoute(place) {
    const myloc = { lat: 40.38127583822331, lng: 49.86776630483177 };
    const destination = {
        lat: place.geometry.location.lat(),
        lng: place.geometry.location.lng(),
    };

    const request = {
        origin: myloc,
        destination: destination,
        travelMode: "DRIVING",
    };

    directionsService.route(request, (result, status) => {
        if (status === "OK") {
            directionsRenderer.setDirections(result);
        } else {
            console.error("Directions request failed due to " + status);
        }
    });
}

// Venues

// Get
async function getVenues() {
    try {
        const response = await fetch('http://localhost:8000/venues/all');
        const venues = await response.json();
        
        const venuesContainer = document.querySelector(".main_left2");

        venues.forEach(venue => {
            const venueElement = document.createElement("div");
            venueElement.className = "left2_imgs"

            const venueImage = document.createElement("img");
            venueImage.src = "./images/hq720.jpg";
            venueImage.alt = venue.name;

            const venueStarElement = document.createElement("div");
            venueStarElement.className = "staricondesign"

            const venuePElement = document.createElement("p");
            venuePElement.innerHTML = "4.8"

            const venueStarImage = document.createElement("img");
            venueStarImage.src = "./images/star.svg";
            venueStarImage.style.width = "15px"

            const descImgElement = document.createElement("div");
            descImgElement.className = "imgdescdesign"

            const descImgPElement = document.createElement("p");

            if (venue.name.length > 17) {
                descImgPElement.innerHTML = `${venue.name.substring(0, 16)}...`
            }else{
                descImgPElement.innerHTML = `${venue.name.substring(0, 17)}`
            }

            descImgElement.appendChild(descImgPElement)

            venueStarElement.appendChild(venueStarImage)
            venueStarElement.appendChild(venuePElement)
            
            venueElement.appendChild(venueImage)
            venueElement.appendChild(venueStarElement)
            venueElement.appendChild(descImgElement)

            venuesContainer.appendChild(venueElement)

            const lat = parseFloat(venue.lat);
            const lng = parseFloat(venue.lng);
            
            if (!isNaN(lat) || !isNaN(lng)){
                const marker = createMarker({
                    geometry: {
                        location: new google.maps.LatLng(lat, lng),
                    },
                    name: venue.name,
                    vicinity: venue.name || "Unknown location"
                }, false);

                venueElement.addEventListener("click", () => {
                    map.setZoom(15);
                    map.setCenter({
                        lat: lat,
                        lng: lng,
                    });
                });
            }

        });

    } catch (error) {
        console.error('Error:', error);
    }
}

async function getVenue(venue_id) {
    try {
        const response = await fetch('http://localhost:8000/venues/'+ venue_id);
        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error('Error:', error);
    }
}

// Login

async function login(inputData) {
    try {
        const response = await fetch('http://localhost:8000/auth/token', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json', 
            },
            body: JSON.stringify(inputData),
          })
            .then(response => response.json())
            .then(data => {
                localStorage.setItem("token", data.access_token)
                console.log('Success:', data);
            })
            .catch(error => {
              console.error('Error:', error);
            });

        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error('Error:', error);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    // login({
    //     username: "123",
    //     password: "123",
    // })
        
    initMap()
    getEvents();
    getVenues();
})

// {
//     venue_id: 1,
//     organizer_id: 1,
//     title: "bla",
//     description: "bla",
//     event_type: "concert",
//     date: "2024-10-12T18:00:18.248Z",
//     start: "18:00:18.248Z",
//     finish: "18:00:18.248Z"
// }

window.initMap = initMap;
