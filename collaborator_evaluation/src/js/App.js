import React, { useState, useEffect, useRef } from 'react';

import './App.css';
import Question from './components/Question';
import PageControls from './components/PageControls';
import Subcategories from './components/Subcategories';
import ProgressBar from './components/ProgressBar';
import Profile from './components/Profile';

import nextQuestion from './utilities/nextQuestion';
import getSubcategories from './utilities/getSubcategories';
import submit from './utilities/submit';
import HasSubmittedCookie from './utilities/HasSubmittedCookie';

let previousQuestionsNumber = [];
function App() {
	const [currentQuestionPageNumber, setCurrentQuestionPageNumber] = useState(0);
	const [previousQuestionPageNumber, setPreviousQuestionPageNumber] = useState(0);
	const mandatoryQuestions = useRef(new Set());
	const forbiddenQuestions = useRef(new Set());
	const criteriaTags = useRef(new Set());
	const [currentAnswer, setCurrentAnswer] = useState(null);
	const [allAnswers, addAnswer] = useState([]);
	const [unlockNextButton, setUnlockNextbutton] = useState(false);

	const profileData = questionnaire.questions[0].form;
	const currentQuestion = questionnaire.questions[currentQuestionPageNumber];
	const showPreviousButton = currentQuestionPageNumber !== 0;
	const currentSubcategory = currentQuestion.subcategory;
	const currentCategory = currentQuestion.category;
	const totalNumberOfQuestions = questionnaire.questions.length;
	const currentQuestionIndex = questionnaire.questions.indexOf(currentQuestion);
	const progress = (currentQuestionIndex / totalNumberOfQuestions) * 100;
	const displaySubmit = currentQuestionIndex === totalNumberOfQuestions - 1 && currentQuestionPageNumber !== 0;

	function handleChoiceInput(answerObject) {
		setUnlockNextbutton(true);
		setCurrentAnswer(answerObject);
	}

	function handleNextPageButtonClick() {
		setUnlockNextbutton(false);
		let promises = [];
		if (currentQuestionPageNumber === 0) {
			displayLoading();
			promises.push(
				fetch('../sheet/', {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({
						mandatory_questions: Array.from(mandatoryQuestions.current),
						forbidden_questions: Array.from(forbiddenQuestions.current),
						criteria_tags: Array.from(criteriaTags.current),
					}),
				})
					.catch((reason) => {
						alert(gettext("Une erreur est survenue. Veuillez recharger la page. Si l'erreur persiste, contactez le support."));
					})
					.then((response) => response.json())
					.catch((reason) => {
						alert(gettext("Une erreur est survenue. Veuillez recharger la page. Si l'erreur persiste, contactez le support."));
					})
					.then((json) => {
						questionnaire.questions = [questionnaire.questions[0], ...json['questions']];
						closeLoading();
					}),
			);
		}
		Promise.all(promises).then(() => {
			addAnswer([...allAnswers, currentAnswer]);
			if (!previousQuestionsNumber.includes(previousQuestionPageNumber)) previousQuestionsNumber.push(previousQuestionPageNumber);
			setPreviousQuestionPageNumber(currentQuestionPageNumber);
		});
	}

	// fires nextQuestion function when a new answer is added
	// makes sures nextQuestion has access to the latest state of allAnswers
	useEffect(() => {
		if (allAnswers.length !== 0) {
			nextQuestion(currentQuestionPageNumber, allAnswers, setCurrentQuestionPageNumber);
		}
	}, [allAnswers]);

	// resets next button color to grey unless text question
	useEffect(() => {
		currentQuestion.ui_type != 'text' && setUnlockNextbutton(false);
	}, [currentQuestionPageNumber]);

	function handlePreviousPageButtonClick() {
		setCurrentQuestionPageNumber(previousQuestionPageNumber);
		setPreviousQuestionPageNumber(previousQuestionsNumber.pop());
		allAnswers.pop();
		if (currentQuestionPageNumber === 1) {
			questionnaire.questions = [questionnaire.questions[0]];
		}
	}
	function displayLoading() {
		let div = document.createElement('div');
		div.innerHTML =
			"<div id='loading_screen' style='background: #9ea0a4ad; width: 100%;height: 100vh;position: absolute;display: flex; align-items: center; justify-content: center; z-index:3; flex-direction: column'><img style='width:200px; ' src='/static/img/loading.svg' /><span id='loading_infos'>" +
			gettext('Chargement en cours...') +
			'</span></span></div>';
		document.body.insertBefore(div.firstChild, document.body.firstChild);
		document.body.scrollIntoView();
	}
	function closeLoading() {
		let elem = document.getElementById('loading_screen');
		elem.parentNode.removeChild(elem);
	}

	function getNextButtonLabel() {
		if (currentQuestionPageNumber === 0) {
			return gettext("Commencer l'évaluation >");
		} else {
			return gettext('Question suivante >');
		}
	}
	function handleSubmit() {
		window.onpopstate = null;
		window.onbeforeunload = null;
		HasSubmittedCookie.createHasSubmittedCookie();
		const finalAnswers = allAnswers;
		finalAnswers.push(currentAnswer);
		submit(finalAnswers);
	}

	const showQuestionnaire = !HasSubmittedCookie.checkHasSubmittedCookie();
	if (!showQuestionnaire) {
		window.location.replace(window.location.href.replace('fill', 'thanks'));
	}

	return (
		<div className="App">
			<ProgressBar progress={progress} />
			<img className="questionnaire-logo" src="/static/img/logo-mixity.svg" alt="Logo Mixity" />

			{questionnaire.slug === 'evaluation_collaborateurs_360' && (
				<h2 className="questionnaire-title title--h1 color--primary-light">
					{gettext('Questionnaire Mixity Human')}
					<br />
					{gettext("L'évaluation du sentiment de")}
					<br /> {gettext("diversité et d'inclusion dans votre organisation")}{' '}
				</h2>
			)}
			{questionnaire.slug !== 'evaluation_collaborateurs_360' && (
				<h2 className="questionnaire-title title--h1 color--primary-light">
					Questionnaire <br />
					Evaluation inclusion LGBTQIA+
				</h2>
			)}
			<div className="col--15-45">
				<Subcategories questions={questionnaire.questions} currentSubcategory={currentSubcategory} currentCategory={currentCategory} />
				{currentQuestionPageNumber === 0 ? (
					<Profile
						handleNextPageButtonClick={handleNextPageButtonClick}
						handlePreviousPageButtonClick={handlePreviousPageButtonClick}
						handleSubmit={handleSubmit}
						displaySubmit={displaySubmit}
						nextButtonLabel={getNextButtonLabel()}
						showPreviousButton={showPreviousButton}
						unlockNextButton={unlockNextButton}
						setUnlockNextbutton={setUnlockNextbutton}
						currentQuestionPageNumber={currentQuestionPageNumber}
						handleChoiceInput={handleChoiceInput}
						profileData={profileData}
						criteriaTags={criteriaTags}
						mandatoryQuestions={mandatoryQuestions}
						forbiddenQuestions={forbiddenQuestions}
					/>
				) : (
					<Question
						handleNextPageButtonClick={handleNextPageButtonClick}
						handlePreviousPageButtonClick={handlePreviousPageButtonClick}
						handleSubmit={handleSubmit}
						displaySubmit={displaySubmit}
						nextButtonLabel={getNextButtonLabel()}
						showPreviousButton={showPreviousButton}
						unlockNextButton={unlockNextButton}
						currentQuestionPageNumber={currentQuestionPageNumber}
						questionObject={currentQuestion}
						handleChoiceInput={handleChoiceInput}
						setUnlockNextbutton={setUnlockNextbutton}
					/>
				)}
			</div>
		</div>
	);
}

export default App;
