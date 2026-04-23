import React, { useState, useEffect } from 'react';

import './ChoicesText.css';

export default function ChoicesText(props) {
	const { google_sheets_id, id, help_text, label } = props.questionObject;
	const [currentText, setCurrentText] = useState('');
	const [currentConsentState, setCurrentConsentState] = useState(null);
	function onChange(e) {
		setCurrentText(e.target.value);
	}

	// handles case when user erases text
	useEffect(() => {
		props.handleChoiceInput({
			questionGoogleSheetId: google_sheets_id,
			answerText: currentText,
			consent: currentConsentState,
			questionId: id,
			questionLabel: label,
		});
		props.setUnlockNextbutton(currentConsentState !== null);
	}, [currentText, currentConsentState]);
	return (
		<div>
			<textarea className="choices-text-input" type="text" placeholder={help_text} onChange={(e) => onChange(e)} />
			<div className="d-flex gap-2 align-items-center">
				<span>{gettext('Souhaitez-vous que votre réponse soit remontée telle que rédigée auprès de votre organisation ?*')}</span>
				<div className="p-1 d-flex justify-content-center gap-1">
					<input onClick={() => setCurrentConsentState(true)} className="m-0" type="radio" id="yes" name="consent" value="1" />
					<label onClick={() => setCurrentConsentState(true)} htmlFor="yes">
						{gettext('Oui')}
					</label>
				</div>
				<div className="p-1 d-flex justify-content-center gap-1">
					<input onClick={() => setCurrentConsentState(false)} className="m-0" type="radio" id="no" name="consent" value="0" />
					<label onClick={() => setCurrentConsentState(false)} htmlFor="no">
						{gettext('Non')}
					</label>
				</div>
			</div>
			<div>
				<span className="mxt--small">
					*
					{gettext(
						"Si vous acceptez, votre réponse sera transmise à votre organisation telle que vous l'avez rédigée. Sachez que votre organisation pourrait être en mesure de vous identifier ou d'identifier d'autres personnes en fonction du contenu de votre réponse.",
					)}
				</span>
			</div>
		</div>
	);
}
