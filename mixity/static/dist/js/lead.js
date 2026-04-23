function add_objectives(evaluation_pk){
    // Getting the structure slug value from the metadata
    let slug = $('#add-objectives-slug').data().slug;
    // Fetching the view
    return fetch(`/${slug}/lead/add_objectives/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json;charset=utf-8'
        },
        body: JSON.stringify({"evaluation_pk":evaluation_pk})
    }).then((response) => response.json())
        .then(data => {
                if(data.result === "NO OBJECTIVES"){
                    let no_objectives_alert = document.getElementById("lead_no_objectives_msg")
                    setTimeout(function (){
                        hideAlert(no_objectives_alert)
                    },6000)
                    showAlert(no_objectives_alert)
                }else if(data.result === "NO EVALUATIONS"){
                    let no_evaluations_alert = document.getElementById("lead_no_evaluations_msg")
                    setTimeout(function (){
                        hideAlert(no_evaluations_alert)
                    },6000)
                    showAlert(no_evaluations_alert)
                }else if(data.result === "ALREADY ADDED"){
                    let already_exist_alert = document.getElementById("lead_already_exist_msg")
                    setTimeout(function (){
                        hideAlert(already_exist_alert)
                    },6000)
                    showAlert(already_exist_alert)
                }else{
                    location.reload()
                }
            }
        ).catch((error) => {
            let error_msg = "Error while adding objectives :"+error
            alert(error_msg)
        })
}
function showAlert(elem){
    elem.style.display = "block"
}
function hideAlert(elem){
    elem.style.display = "none"
}
