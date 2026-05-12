/* ===============================
   PROFILE PANEL + RBAC HANDLING
   =============================== */

async function openProfile(username){
    try{
        const res = await fetch(`/profile/${username}`);

        // ACCESS DENIED
        if(res.status === 403){
            showAccessDenied();
            return;
        }

        if(!res.ok){
            alert("Something went wrong");
            return;
        }

        const data = await res.json();

        // BASIC INFO
        document.getElementById("profileImg").src = data.image;
        document.getElementById("profileName").innerText = data.name;
        document.getElementById("profileRole").innerText = data.post;

        document.getElementById("profileInfo").innerText =
`Age: ${data.age}
Experience: ${data.experience}
Project: ${data.project}`;

        // TEAM MEMBERS
        const teamBox = document.getElementById("profileTeam");
        teamBox.innerHTML = "";

        if(data.team && data.team.length > 0){
            data.team.forEach(member => {
                const span = document.createElement("span");
                span.innerText = member;
                teamBox.appendChild(span);
            });
        } else {
            teamBox.innerHTML = "<span>No team members</span>";
        }

        // SHOW PANEL
        document.getElementById("profilePanel").classList.add("active");
    }
    catch(err){
        console.error(err);
    }
}

/* ===============================
   CLOSE PROFILE (❌ WORKING)
   =============================== */

function closeProfile(){
    const panel = document.getElementById("profilePanel");

    panel.classList.remove("active");

    // RESET DATA (IMPORTANT)
    document.getElementById("profileImg").src = "";
    document.getElementById("profileName").innerText = "";
    document.getElementById("profileRole").innerText = "";
    document.getElementById("profileInfo").innerText = "";
    document.getElementById("profileTeam").innerHTML = "";
}

/* ===============================
   ACCESS DENIED OVERLAY
   =============================== */

function showAccessDenied(){
    const el = document.getElementById("accessDenied");
    el.classList.add("active");

    setTimeout(() => {
        el.classList.remove("active");
    }, 2000);
}

/* ===============================
   ESC KEY CLOSE (OPTIONAL)
   =============================== */

document.addEventListener("keydown", function(e){
    if(e.key === "Escape"){
        closeProfile();
    }
});