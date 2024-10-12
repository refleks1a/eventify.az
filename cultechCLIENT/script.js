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

function createMarker(place) {
    const marker = new google.maps.Marker({
        position: place.geometry.location,
        map: map,
        title: place.name,
    });

    marker.addListener('click', () => {
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

        google.maps.event.addListenerOnce(infoWindow, 'domready', () => {
            document.getElementById("start-route-btn").addEventListener('click', () => {
                drawRoute(place);
            });
        });
    });
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
        const response = await fetch('http://localhost:8000/events/all');
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


// document.addEventListener("DOMContentLoaded", createEvent())

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