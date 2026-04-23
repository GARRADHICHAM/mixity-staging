/*
 This function fetch a view to add/delete a solution to/form the structure customer favorites solutions
 without redirecting or refreshing the page
*/
function act_favorites(action,solution_id){

    // Defining common data between add and delete views
    let slug = ""
    let fetch_url = ""
    let json_msg = {"solution_id": solution_id, "action": action}
    let success_alert_id = ""
    let failure_alert_id = ""

        slug =  $('#fav-solution-slug').data().slug;
        fetch_url = `/${slug}/take-action/fav_solution/`
        success_alert_id = "fav_solution_success_msg"
        failure_alert_id = "fav_solution_failure_msg"

    // Fetching the view
    return fetch(fetch_url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json;charset=utf-8'
        },
        body: JSON.stringify(json_msg)
    }).then((response) => response.json())
        .then(data => {
            if(data.result === "SUCCESS"){
                let success_alert = document.getElementById(success_alert_id)
                setTimeout(function (){
                    hideAlert(success_alert)
                },6000)
                showAlert(success_alert)
                if(action == "DELETE"){
                    location.reload()
                }
            }else if(data.result === "FAILURE"){
                let failure_alert = document.getElementById(failure_alert_id)
                setTimeout(function (){
                    hideAlert(failure_alert)
                },6000)
                showAlert(failure_alert)
            }
        }
   ).catch((error) => {
            let error_msg = "Error while adding or deleting favorite solutions :"+error
            alert(error_msg)
        })
}
function showAlert(elem){
    elem.style.display = "block"
}
function hideAlert(elem){
    elem.style.display = "none"
}

