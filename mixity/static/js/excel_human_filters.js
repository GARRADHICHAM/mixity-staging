function send_excel_human_filters() {
	// Getting filters
	let human_selected_filters = {
		pk: 0,
		collab_filters: {},
		collab_human_criteria: {},
		language_code: '',
		second_filter_activated: 'false',
		second_collab_filters: {},
		second_collab_human_criteria: {},
	};
	let filters = document.querySelectorAll('.excel_collab_filter');
	let second_filters = document.querySelectorAll('.second_excel_collab_filter');
	let human_criteria = document.querySelectorAll('.excel_collab_human_criteria');
	let second_human_criteria = document.querySelectorAll('.second_excel_collab_human_criteria');

	human_selected_filters['pk'] = document.getElementById('human_excel_pk').getAttribute('data-pk');
	// Collab Filters
	filters.forEach(function (f) {
		let checked_values = f.children[2].querySelectorAll('input[type="checkbox"]:checked');
		let slug = f.children[1].id;
		if (human_selected_filters['collab_filters'][slug] === undefined && checked_values.length > 0) {
			human_selected_filters['collab_filters'][slug] = [];
		}
		checked_values.forEach(function (value) {
			let current_label = value.getAttribute('choice-value');
			human_selected_filters['collab_filters'][slug].push({ slug: value.getAttribute('choice-key'), label: current_label });
		});
	});
	// Collab Human Criteria
	human_criteria.forEach(function (f) {
		let checked_values = f.children[2].querySelectorAll('input[type="checkbox"]:checked');
		let label = f.children[1].textContent;
		if (human_selected_filters['collab_human_criteria'][label] === undefined && checked_values.length > 0) {
			human_selected_filters['collab_human_criteria'][label] = [];
		}
		checked_values.forEach(function (value) {
			human_selected_filters['collab_human_criteria'][label].push(value.getAttribute('choice-id'));
		});
	});
	//check if second filter is activated
	if (document.getElementById('second-filter').getAttribute('is-active') === 'true') {
		human_selected_filters['second_filter_activated'] = 'true';
		//second filters
		second_filters.forEach(function (f) {
			let checked_values = f.children[2].querySelectorAll('input[type="checkbox"]:checked');
			let slug = f.children[1].id;
			if (human_selected_filters['second_collab_filters'][slug] === undefined && checked_values.length > 0) {
				human_selected_filters['second_collab_filters'][slug] = [];
			}
			checked_values.forEach(function (value) {
				let current_label = value.getAttribute('choice-value');
				human_selected_filters['second_collab_filters'][slug].push({ slug: value.getAttribute('choice-key'), label: current_label });
			});
		});
		//second human criteria
		second_human_criteria.forEach(function (f) {
			let checked_values = f.children[2].querySelectorAll('input[type="checkbox"]:checked');
			let label = f.children[1].textContent;
			if (human_selected_filters['second_collab_human_criteria'][label] === undefined && checked_values.length > 0) {
				human_selected_filters['second_collab_human_criteria'][label] = [];
			}
			checked_values.forEach(function (value) {
				human_selected_filters['second_collab_human_criteria'][label].push(value.getAttribute('choice-id'));
			});
		});
	} else {
		human_selected_filters['second_filter_activated'] = 'false';
	}

	// Getting language
	let language_code = document.querySelector('.excel_languages').querySelector('input[type="radio"]:checked');
	if (language_code) {
		human_selected_filters['language_code'] = language_code.getAttribute('choice-id');
	}
	if (human_selected_filters['language_code']) {
		// Sending filters to APIView
		return fetch(`/scoring/evaluation/${this.props.evaluation.pk}/human-filtered-excel/`, {
			credentials: 'include',
			method: 'POST',
			headers: {
				'Content-Type': 'application/json;charset=utf-8',
				'X-CSRFToken': csrftoken,
			},
			body: JSON.stringify(human_selected_filters),
		})
			.then((response) => response.json())
			.then((data) => {
				if (data.result === 'failure') {
					document.getElementById('close_btn_excel_human_filters').click();
					window.location.reload();
				} else if (data.result === 'close') {
					document.getElementById('close_btn_excel_human_filters').click();
				}
			})
			.catch((error) => {
				let error_msg = 'Error while exporting excel with filters :' + error;
				alert(error_msg);
			});
	} else {
		alert(gettext('Veuillez choisir une langue !'));
	}
}

function add_second_filter() {
	document.getElementById('excel_human_filters_Modal').scroll({ top: 0, behavior: 'smooth' });
	document.getElementById('second-filter').setAttribute('is-active', 'true');
	document.getElementById('second-filter').style.display = 'block';
	document.getElementById('first-filter').style.display = 'none';
	document.getElementById('add_second_filter_button').style.display = 'none';
	document.getElementById('modif_first_filter_button').style.display = 'block';
	document.getElementById('delete_second_filter_button').style.display = 'block';
}

function modif_first_filter() {
	document.getElementById('excel_human_filters_Modal').scroll({ top: 0, behavior: 'smooth' });
	document.getElementById('second-filter').style.display = 'none';
	document.getElementById('first-filter').style.display = 'block';
	document.getElementById('modif_first_filter_button').style.display = 'none';
	document.getElementById('modif_second_filter_button').style.display = 'block';
}

function modif_second_filter() {
	document.getElementById('excel_human_filters_Modal').scroll({ top: 0, behavior: 'smooth' });
	document.getElementById('second-filter').style.display = 'block';
	document.getElementById('first-filter').style.display = 'none';
	document.getElementById('modif_second_filter_button').style.display = 'none';
	document.getElementById('modif_first_filter_button').style.display = 'block';
}

function delete_second_filter() {
	document.getElementById('excel_human_filters_Modal').scroll({ top: 0, behavior: 'smooth' });
	document.getElementById('second-filter').setAttribute('is-active', 'false');
	document.getElementById('modif_second_filter_button').style.display = 'none';

	document.getElementById('second-filter').style.display = 'none';
	document.getElementById('first-filter').style.display = 'block';
	document.getElementById('add_second_filter_button').style.display = 'block';
	document.getElementById('modif_first_filter_button').style.display = 'none';
	document.getElementById('delete_second_filter_button').style.display = 'none';
}

export default send_excel_human_filters;
export { add_second_filter, modif_first_filter, modif_second_filter, delete_second_filter };
