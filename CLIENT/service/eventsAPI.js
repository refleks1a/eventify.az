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


export {getEvents, getEvent, getEventComments, getEventComment, createEvent};
