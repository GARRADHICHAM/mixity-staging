function submit(finalAnswers) {
	const profile = finalAnswers.shift(); // get the profile ( first question )
	const form = document.getElementById('collaborator_form');

	for (var key in profile) {
		let infoInput = document.createElement('input');
		infoInput.type = 'hidden';
		infoInput.name = key;
		infoInput.value = profile[key].map((e) => e[0]).join(',');
		form.appendChild(infoInput);
	}

	let uuid = localStorage.getItem('uuid');
	if (uuid === undefined || uuid === null) {
		uuid = crypto.randomUUID(); // can only be used over HTTPS or localhost ! 0.0.0.0 doesn't work if HTTP.
		localStorage.setItem('uuid', uuid);
	}
	let uuidInput = document.createElement('input');
	uuidInput.type = 'hidden';
	uuidInput.name = 'uuid';
	uuidInput.value = uuid;
	form.appendChild(uuidInput);

	finalAnswers.map((answer, index) => {
		let input = null;
		if (answer.consent) {
			input = document.createElement('input');
			input.type = 'hidden';
			input.name = `answer_${answer.questionId}_consent`;
			input.value = 'true';
			form.appendChild(input);
		}
		if (answer.answers === undefined) {
			input = document.createElement('input');
			input.type = 'hidden';
			input.name = `answer_${answer.questionId}`;
			input.value = `${answer.answerText}`;
			form.appendChild(input);
		} else {
			for (let id in answer.answers) {
				let subanswer = answer.answers[id];
				input = document.createElement('input');
				input.type = 'hidden';
				if (subanswer.answerId !== undefined) {
					input.name = `answer_${answer.questionId}_${subanswer.subquestionId}_id`;
					input.value = `${subanswer.answerId}`;
				} else if (typeof subanswer.answerText === 'number') {
					input.name = `answer_${answer.questionId}_${subanswer.subquestionId}_value`;
					input.value = `${subanswer.answerText}`;
				} else {
					input.name = `answer_${answer.questionId}_${subanswer.subquestionId}`;
					input.value = `${subanswer.answerText}`;
				}
				form.appendChild(input);
			}
		}
	});
	form.submit();
}

export default submit;
