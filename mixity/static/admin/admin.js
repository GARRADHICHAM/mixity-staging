/**
 * fetch the OpenAI Api endpoint
 * @param {Object} body - Parameters to send in JSON
 * @returns {Promise<Response>}
 */
function fetchOpenAIEndpoint(body) {
	const token = document.querySelector(
        "[name=csrfmiddlewaretoken]"
    ).value;
	return fetch('/open-ai-api/', {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			'X-CSRFToken': token,
		},
		body: JSON.stringify(body),
	});
}

/**
 * @description Use the Open AI to translate a text from a lang to another
 * @param {string} string - Original text to translate
 * @param {string} from - Lang of the original text
 * @param {string} to - Lang of the destination text
 */
function translateOpenAI(string, from, to) {
	return fetchOpenAIEndpoint({
		text: string,
		target_lang: to.toUpperCase(),
		source_lang: from.toUpperCase(),
	});
}

function getLanguageFromId(id) {
	let temp = id.split('_').slice(-1)[0];
	temp = temp.toLowerCase()
	switch (temp) {
		case "fr":
			return "french"
		case "en":
			return "english"
		case "es":
			return "spanish"
		case "it":
			return "italian"
		case "hans":
			return "chinese (simplified)"
		case "hant":
			return "chinese (traditionnal)"
		case "ja":
			return "japanese"
		default:
			return temp
	}
}

window.addEventListener('load', function () {
	let row = document.getElementsByClassName("submit-row")[0];
	let input = document.createElement("input");
	input.type = "button";
	input.value = gettext("Traduire tous les champs");
	input.name = "_translate";
	input.addEventListener("click", translateEverything);
	row.appendChild(input);

	let translatable = new Set();
	let BUTTON_STR = 'Traduire ce champ';
	/**
	 * @description browse the page to find translatable fields and add a button next to the french text input/textarea which can trigger a translation of all empty fields
	 * of one name
	 */
	function prepareTranslatedFields() {
		/* Fetch all textareas and text inputs */
		document.querySelectorAll('textarea, input[type="text"]').forEach((element) => {
			if (element.id.endsWith('_fr')) {
				// use the fr translation because first one and because Mixity is french by default
				if (!translatable.has(element)) {
					translatable.add(element);
					let button = document.createElement('input');
					button.value = BUTTON_STR;
					button.type = 'button';
					button.className = 'translate-button';
					element.parentNode.querySelectorAll('.translate-button').forEach((element) => {
						element.remove();
					});
					element.parentNode.appendChild(button); // add the translate button for this translatable field

					if (element.className === "tinymce") {
						button.addEventListener('click', function () {
							let id = element.id.slice(0, -2);
							let contentToTranslate;
							let contentLang;
							let promises = [];
							document.querySelectorAll('iframe[id="' + element.id + '_ifr"]').forEach((element) => {
								let iframeDoc = element.contentDocument || element.contentWindow.document;
								let iframeBody = iframeDoc.body;
								if (iframeBody.innerHTML.length > 0 && (contentToTranslate === undefined || contentToTranslate === null)) {
									contentToTranslate = iframeBody.innerHTML;
									contentLang = "french";
								}
							})
							document.querySelectorAll('iframe[id^="' + id + '"]').forEach((element) => {
								let iframeDoc = element.contentDocument || element.contentWindow.document;
								let iframeBody = iframeDoc.body;
								if (contentToTranslate !== undefined && contentToTranslate !== null && !iframeBody.dataset.id.endsWith('_fr')) {
									let currentLang = getLanguageFromId(iframeBody.dataset.id);
									promises.push(
										translateOpenAI(contentToTranslate, contentLang, currentLang)
											.then((response) =>
												response.json().then((data) => {
													iframeBody.innerHTML = data.text;
												}),
											)
											.catch((reason) => {
												console.log(
													'Une erreur est survenue lors de la traduction de ' +
														contentLang +
														' à ' +
														currentLang +
														' (' +
														reason.toString() +
														')',
												);
											}),
									);
								}
							})
							Promise.all(promises);
						});

					} else {
						button.addEventListener('click', function () {
							let id = element.id.slice(0, -2);
							let contentToTranslate;
							let contentLang;
							if (element.value.length > 0 && (contentToTranslate === undefined || contentToTranslate === null)) {
								contentToTranslate = element.value;
								contentLang = getLanguageFromId(element.id);
							}
							if (contentToTranslate !== undefined && contentToTranslate !== null) {
								let promises = [];
								document.querySelectorAll('[id^="' + id + '"]').forEach((element) => {
									if (!element.id.endsWith('_fr')) {
										// search all elements related to the French field (spanish, english, ...)
										let currentLang = getLanguageFromId(element.id);
										/* Disable Translate button in order to prevent any spam click by Nicolas (it would be quite unfortunate to reach the limit because of that :) ) */
										button.disabled = true;
										button.value = gettext('Traduction en cours...');
										/* we translate the empty field with the source text and source lang defined before */
										promises.push(
											translateOpenAI(contentToTranslate, contentLang, currentLang)
												.then((response) =>
													response.json().then((data) => {
														element.value = data.text;
													}),
												)
												.catch((reason) => {
													console.log(
														'Une erreur est survenue lors de la traduction de ' +
															contentLang +
															' à ' +
															currentLang +
															' (' +
															reason.toString() +
															')',
													);
												}),
										);
									}
								});

								/**
								 * @description Function triggered when translation either finished or failed. It reenables the translation button and fetch the Deepl Api to check usage
								 */
								function translationFinishedHandler() {
									button.disabled = false;
									button.value = BUTTON_STR;
								}
								Promise.all(promises).then(translationFinishedHandler).catch(translationFinishedHandler);
							}
						});
					}
				}
			}
		});
	}
	prepareTranslatedFields(); // browse all translatable fields on load
	document.querySelectorAll('.add-row a').forEach((element) => {
		element.addEventListener('click', prepareTranslatedFields); // browse again if we click on "Add" buttons
	});
	document.querySelectorAll('.diaspora-percent-compute').forEach((element) => {
		element.innerHTML = `${((parseInt(element.innerHTML) * 100) / element.getAttribute('data-total-value')).toFixed(2)} %`;
	});
	function translateEverything() {
		document.querySelectorAll('iframe').forEach((element) => {
			if (element.id && element.id.endsWith('_fr_ifr')) {
				let idWithLang = element.id.slice(0, -4);
				let id = element.id.slice(0, -6);
				let iframeDoc = element.contentDocument || element.contentWindow.document;
				let iframeBody = iframeDoc.body;
				let contentToTranslate;
				let contentLang;
				if (iframeBody.innerHTML.length > 0 && (contentToTranslate === undefined ||contentToTranslate === null)) {
					contentToTranslate = iframeBody.innerHTML;
					contentLang = getLanguageFromId(idWithLang)
				}
				if (contentToTranslate !== undefined && contentToTranslate !== null) {
					let promises = [];
					document.querySelectorAll('iframe[id^="' + id +'"]').forEach((element) => {
						let iframeDoc = element.contentDocument || element.contentWindow.document;
						let iframeBody = iframeDoc.body;
						if (!iframeBody.innerHTML || iframeBody.innerHTML.length === 0 || iframeBody.innerHTML == '<p></p>' || iframeBody.innerHTML == '<p><br></p>' || iframeBody.innerHTML == '<p><br data-mce-bogus="1"></p>') {
							let currentLang = getLanguageFromId(iframeBody.dataset.id);
							promises.push(
								translateOpenAI(contentToTranslate, contentLang, currentLang)
									.then((response) => 
										response.json().then((data) => {
											iframeBody.innerHTML = data.text;
										})
									)
									.catch((reason) => {
										console.log(
											'Une erreur est survenue lors de la traduction de ' +
												contentLang +
												' à ' +
												currentLang +
												' (' +
												reason.toString() +
												')',
										);
									}),
							);
						}
					});
					Promise.all(promises);
				}
			}
		});

		document.querySelectorAll('textarea, input[type="text"]').forEach((element) => {
			if (element.id.endsWith('_fr')) {
				let id = element.id.slice(0, -2);
				let contentToTranslate;
				let contentLang;
				if (element.value.length > 0 && (contentToTranslate === undefined || contentToTranslate === null)) {
					contentToTranslate = element.value;
					contentLang = getLanguageFromId(element.id);
				}
				if (contentToTranslate !== undefined && contentToTranslate !== null) {
					let promises = [];
					document.querySelectorAll('[id^="' + id + '"]').forEach((element) => {
						if (!element.value || element.value.length === 0) {
							// search all elements related to the French field (french, spanish, english, ...) that are empty
							let currentLang = getLanguageFromId(element.id);
							/* we translate the empty field with the source text and source lang defined before */
							promises.push(
								translateOpenAI(contentToTranslate, contentLang, currentLang)
									.then((response) =>
										response.json().then((data) => {
											element.value = data.text;
										}),
									)
									.catch((reason) => {
										console.log(
											'Une erreur est survenue lors de la traduction de ' +
												contentLang +
												' à ' +
												currentLang +
												' (' +
												reason.toString() +
												')',
										);
									}),
							);
						}
					});
					Promise.all(promises);
				}
			}
		});
	}
});
