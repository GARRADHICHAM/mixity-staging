import React from 'react';
import { SwitchTransition, CSSTransition, Transition } from 'react-transition-group';

import ChoicesSelect from './ChoicesSelect';
import ChoicesText from './ChoicesText';
import ChoicesSlider from './ChoicesSlider';
import './Question.css';
import DualSelect from './DualSelect';
import SubquestionSelect from './SubquestionSelect';
import SubquestionQCM from './SubquestionQCM';
import PageControls from './PageControls';

export default function Question(props) {
	const { id, label, ui_type, help_text } = props.questionObject;

	function renderChoices() {
		switch (ui_type) {
			case 'sq_dual':
				return (
					<DualSelect
						handleChoiceInput={props.handleChoiceInput}
						setUnlockNextbutton={props.setUnlockNextbutton}
						questionObject={props.questionObject}
					/>
				);
			case 'sq_select':
				return (
					<SubquestionSelect
						handleChoiceInput={props.handleChoiceInput}
						setUnlockNextbutton={props.setUnlockNextbutton}
						questionObject={props.questionObject}
					/>
				);
			case 'sq_qcm':
				return (
					<SubquestionQCM
						handleChoiceInput={props.handleChoiceInput}
						setUnlockNextbutton={props.setUnlockNextbutton}
						questionObject={props.questionObject}
					/>
				);
			case 'slider':
				return <ChoicesSlider handleChoiceInput={props.handleChoiceInput} questionObject={props.questionObject} />;
			case 'select':
				return <ChoicesSelect handleChoiceInput={props.handleChoiceInput} questionObject={props.questionObject} />;
			default:
				return (
					<ChoicesText
						handleChoiceInput={props.handleChoiceInput}
						questionObject={props.questionObject}
						setUnlockNextbutton={props.setUnlockNextbutton}
					/>
				);
		}
	}

	return (
		<div className="question-answer-container">
			<SwitchTransition>
				<CSSTransition key={id} appear={true} timeout={500} classNames="item">
					<div className="question-container">
						<p className="content-light">
							<strong>
								{label}
								{help_text && (
									<span className="tooltip px-3">
										<div className="tooltip__icon">?</div>
										<span className="tooltip__text mx-3">{gettext(help_text)}</span>
									</span>
								)}
							</strong>
						</p>
						{renderChoices()}
					</div>
				</CSSTransition>
			</SwitchTransition>
			<PageControls
				handleNextPageButtonClick={props.handleNextPageButtonClick}
				handlePreviousPageButtonClick={props.handlePreviousPageButtonClick}
				handleSubmit={props.handleSubmit}
				displaySubmit={props.displaySubmit}
				nextButtonLabel={props.nextButtonLabel}
				showPreviousButton={props.showPreviousButton}
				unlockNextButton={props.unlockNextButton}
				currentQuestionPageNumber={props.currentQuestionPageNumber}
			/>
		</div>
	);
}
