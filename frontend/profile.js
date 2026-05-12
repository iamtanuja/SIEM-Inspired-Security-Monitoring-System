// Open profile
function openProfile(username) {
    const loggedInUser = document.getElementById('profileIcon').dataset.username;

    fetch(`/profile/${username}`)
        .then(res => {
            if (res.status === 403) {
                document.getElementById('accessDenied').classList.add('active');
                return null;
            } else if (!res.ok) {
                console.error('Error fetching profile');
                return null;
            }
            return res.json();
        })
        .then(data => {
            if (!data) return;

            document.getElementById('profileImg').src = `/static/${data.image.split('static/')[1]}`;
            document.getElementById('profileName').innerText = data.name;
            document.getElementById('profilePost').innerText = data.post;
            document.getElementById('profileInfo').innerText = `Age: ${data.age}, Experience: ${data.experience} yrs`;
            document.getElementById("profileProject").innerText = "Project: " + (data.project ? data.project : "Not Assigned");
            const teamDiv = document.getElementById('profileTeam');
            teamDiv.innerHTML = '';
            data.team.forEach(member => {
                const span = document.createElement('span');
                span.innerText = member;
                teamDiv.appendChild(span);
            });

            // Show Logout button **only for logged-in user's profile**
            const logoutBtn = document.querySelector('#profilePanel button');
            if(username === loggedInUser){
                logoutBtn.style.display = 'block';
            } else {
                logoutBtn.style.display = 'none';
            }

            document.getElementById('profilePanel').classList.add('active');
        })
        .catch(err => console.error(err));
}

// Close panels
function closeProfile() {
    document.getElementById('profilePanel').classList.remove('active');
    document.getElementById('accessDenied').classList.remove('active');
}

// Access Denied overlay click closes it
document.getElementById('accessDenied').addEventListener('click', function() {
    this.classList.remove('active');
});

// Logout
function logoutUser() {
    window.location.href = '/logout';
}

// Profile icon click (shows own profile)
document.getElementById('profileIcon').addEventListener('click', function() {
    const username = this.dataset.username;
    if(username) openProfile(username);
});

