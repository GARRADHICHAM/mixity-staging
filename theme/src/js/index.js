import './Radar';

window.onload = function (event) {
	document.querySelectorAll('label > input[type="radio"]').forEach((element) => {
		let state = this.checked;
		element.parentNode.addEventListener('mousedown', function () {
			state = element.checked; // On sauvegarde l'état avant qu'il soit modifié
		});
		element.parentNode.addEventListener('click', function () {
			element.checked = !state; // L'état sera forcément inversé par rapport à avant le clic.
		});
	});

	// import dotenv from 'dotenv/config'
	let nd_count = 0;
	let nd_handler;
	let cookie = document.querySelector('#cookie_accept');
	if (cookie != null) {
		cookie.addEventListener('click', function () {
			Cookielaw.createCookielawCookie();
			$('#CookielawBanner').modal('hide');
		});
	}

	let invalid = false;

	let forms = document.querySelectorAll('.form');
	forms.forEach((form) => {
		form.addEventListener('submit', function (event) {
			if (!checkPourcentages()) {
				invalid = true;
				event.preventDefault();
			}
		});
	});
	let save_next = document.querySelector("[name='save_next']");
	if (save_next !== null) {
		save_next.addEventListener('click', function () {
			if (checkPourcentages() && invalid) {
				this.click();
			}
		});
	}

	function checkND() {
		nd_count++;
		if (nd_count > 8) {
			clearInterval(nd_handler);
		}
		try {
			document.querySelectorAll('.scorecategory').forEach((element) => {
				let html = element.innerHTML.replaceAll(' ', '').replaceAll('&nbsp;', '');
				let sc_cat = element.id.split('__')[1];
				let nd = document.getElementById('nd__' + sc_cat);
				if (!html.includes('ND*<') && !html.includes('>ND*') && !html.includes('UA*<') && !html.includes('>UA*')) {
					if (nd != null) {
						nd.style.display = 'none';
					}
				} else {
					if (nd != null) {
						nd.style.display = '';
					}
				}
			});
		} catch (e) {
			console.log(e.message());
			clearInterval(nd_handler);
		}
	}
	nd_handler = setInterval(checkND, 400);

	document.querySelectorAll('.public_axe').forEach((axe) => {
		let voir_suite = axe.querySelector('.voir_suite_bouton');
		let masquer_suite = axe.querySelector('.masquer_suite_bouton');
		let points = axe.querySelectorAll('.detail_pt');
		if (voir_suite !== null) {
			voir_suite.addEventListener('click', function (event) {
				masquer_suite.classList.remove('details_hidden');
				voir_suite.classList.add('details_hidden');

				points.forEach(function (point) {
					point.classList.remove('details_hidden');
				});
			});

			masquer_suite.addEventListener('click', function (event) {
				masquer_suite.classList.add('details_hidden');
				voir_suite.classList.remove('details_hidden');

				points.forEach(function (point) {
					point.classList.add('details_hidden');
				});
			});
		}
	});
	document.querySelectorAll('.team-collapse').forEach((element) => {
		collapseTeam(element.id);
	});
};

function checkPourcentages() {
	let valid = true;
	let subquestions_pourcentages = document.querySelectorAll('.sub_pourcentage');
	let sum_array = {};
	let group_array = {};
	subquestions_pourcentages.forEach(function (sq) {
		let sp = sq.id.split('_');
		if (sum_array[sp[2]] === undefined) {
			sum_array[sp[2]] = 0;
			group_array[sp[2]] = [];
		}
		let val = parseFloat(sq.value);
		if (!isNaN(val)) {
			sum_array[sp[2]] += val;
		}
		group_array[sp[2]].push(sq);
	});

	Object.keys(sum_array).forEach(function (key) {
		// console.log(key + "=>" + sum_array[key]);
		if (sum_array[key] !== 100) {
			console.log(sum_array[key]);
			group_array[key].forEach(function (sq) {
				if (sq.value !== '') {
					valid = false;
					sq.setCustomValidity('La somme des éléments doit être égale à 100%');
				} else {
					sq.setCustomValidity('');
				}
			});
		} else {
			group_array[key].forEach(function (sq) {
				sq.setCustomValidity('');
			});
		}
	});
	return valid;
}
/* Function to manage the collapse elements in about page. Hide already collapsed elements when clicking another element and change opacity of unselected elements */
function collapseTeam(groupId) {
	let current;
	document.querySelectorAll('#' + groupId + ' .button-expand').forEach((btn) => {
		btn.addEventListener('click', function () {
			if (current !== undefined && current !== btn) {
				current.click();
			}
			if (current !== btn) {
				current = btn;
				$(btn.getAttribute('data-target')).on('shown.bs.collapse', function () {
					this.scrollIntoView();
				});
				document.querySelectorAll('#' + groupId + ' .button-expand').forEach((element) => {
					if (element !== btn) {
						element.parentNode.style = 'opacity:0.6';
					}
				});
			} else {
				current = undefined;
				document.querySelectorAll('#' + groupId + ' .button-expand').forEach((element) => {
					element.parentNode.style = '';
				});
			}
		});
	});
	document.querySelectorAll('#' + groupId + ' .button-close').forEach((btn) => {
		btn.addEventListener('click', function () {
			setTimeout(function () {
				document.querySelector('#' + groupId + ' .button-expand').parentNode.scrollIntoView();
			}, 500);
			current = undefined;
			document.querySelectorAll('#' + groupId + ' .button-expand').forEach((element) => {
				element.parentNode.style = '';
			});
		});
	});
}
