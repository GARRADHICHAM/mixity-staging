function nextQuestion(currentQuestionPageNumber, allAnswers, setCurrentQuestionPageNumber) {
	const nextIndex = currentQuestionPageNumber + 1;
	let tag = null;
	if (allAnswers[0].status) tag = allAnswers[0].status[0][0].split('__')[0];
	if (!tag && questionnaire.questions[nextIndex].mandatory_tags.length > 0) nextQuestion(nextIndex, allAnswers, setCurrentQuestionPageNumber);
	else if (
		tag &&
		(questionnaire.questions[nextIndex].forbidden_tags.includes(tag) ||
			(questionnaire.questions[nextIndex].mandatory_tags.length != 0 && !questionnaire.questions[nextIndex].mandatory_tags.includes(tag)))
	) {
		nextQuestion(nextIndex, allAnswers, setCurrentQuestionPageNumber);
	} else if (firstConditionQuestionIds.includes(questionnaire.questions[nextIndex].google_sheets_id)) {
		if (getAnswerTextFromGoogleSheetId(51015, allAnswers) === 'Oui') {
			setCurrentQuestionPageNumber(nextIndex);
		} else if (getAnswerTextFromGoogleSheetId(51015, allAnswers) === 'Non' || getAnswerTextFromGoogleSheetId(51015, allAnswers) === 'Je ne sais pas') {
			setCurrentQuestionPageNumber(nextIndex + 8);
		} else {
			nextQuestion(nextIndex, allAnswers, setCurrentQuestionPageNumber);
		}
	} else if (secondConditionQuestionIds.includes(questionnaire.questions[nextIndex].google_sheets_id)) {
		if (getAnswerTextFromGoogleSheetId(51015, allAnswers) === 'Oui' && getAnswerTextFromGoogleSheetId(51017, allAnswers) === 'Oui') {
			setCurrentQuestionPageNumber(nextIndex);
		} else {
			nextQuestion(nextIndex, allAnswers, setCurrentQuestionPageNumber);
		}
	} else if (thirdConditionIds.includes(questionnaire.questions[nextIndex].google_sheets_id)) {
		if (
			allAnswers[allAnswers.length - 1].answerText === gettext('Oui') ||
			allAnswers[allAnswers.length - 1].answerText === gettext("Oui, c'est certain") ||
			allAnswers[allAnswers.length - 1].answerText === gettext('Oui, probablement') ||
			allAnswers[allAnswers.length - 1].answerText === gettext("Aucune réaction")
		)
			setCurrentQuestionPageNumber(nextIndex);
		else nextQuestion(nextIndex, allAnswers, setCurrentQuestionPageNumber);
	} else if (questionnaire.questions[nextIndex].google_sheets_id === 51022) {
		if (
			getAnswerTextFromGoogleSheetId(51015, allAnswers) === 'Oui' &&
			getAnswerTextFromGoogleSheetId(51017, allAnswers) === 'Oui' &&
			getAnswerTextFromGoogleSheetId(51021, allAnswers) === 'Oui'
		) {
			setCurrentQuestionPageNumber(nextIndex);
		} else {
			nextQuestion(nextIndex, allAnswers, setCurrentQuestionPageNumber);
		}
	} else if (questionnaire.questions[nextIndex].google_sheets_id === 51024) {
		if (getAnswerTextFromGoogleSheetId(51017, allAnswers) === 'Non' || getAnswerTextFromGoogleSheetId(51017, allAnswers) === 'Je ne sais pas') {
			setCurrentQuestionPageNumber(nextIndex);
		} else {
			nextQuestion(nextIndex, allAnswers, setCurrentQuestionPageNumber);
		}
	} else if (questionnaire.questions[nextIndex].google_sheets_id === 51025) {
		if (getAnswerTextFromGoogleSheetId(51024, allAnswers) === 'Oui') {
			setCurrentQuestionPageNumber(nextIndex);
		} else {
			nextQuestion(nextIndex, allAnswers, setCurrentQuestionPageNumber);
		}
	} else {
		setCurrentQuestionPageNumber(nextIndex);
	}
}

const firstConditionQuestionIds = [51016, 51017, 51018, 51019];
const secondConditionQuestionIds = [51020, 51021, 51023];
const thirdConditionIds = [2021002, 20210020, 2021028, 2021048, 20230105, 20210071, 32021007, 420210071];

function getAnswerTextFromGoogleSheetId(i, allAnswers) {
	return (
		allAnswers.filter((item) => item.questionGoogleSheetId === i).length != 0 && allAnswers.filter((item) => item.questionGoogleSheetId === i)[0].answerText
	);
}

export default nextQuestion;
