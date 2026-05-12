/* ===============================
   PROJECT ACCESS (FRONTEND)
   =============================== */

async function openProject(projectKey){
    try{
        const res = await fetch(`/project/${projectKey}`);

        if(res.status === 403){
            showAccessDenied();
            return;
        }

        if(!res.ok){
            alert("Something went wrong");
            return;
        }

        // TEMP: backend nahi hai abhi
        alert("Project access allowed: " + projectKey);
    }
    catch(err){
        console.error(err);
    }
}