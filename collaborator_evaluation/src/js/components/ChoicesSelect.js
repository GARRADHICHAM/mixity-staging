import React from 'react';

import './ChoicesSelect.css';

export default function ChoicesSelect(props) {
	const { google_sheets_id, id, label, choices } = props.questionObject;
	return (
		<div className="choices-select">
			{choices.map((choice) => (
				<li
					key={choice.label}
					onClick={() =>
						props.handleChoiceInput({
							questionGoogleSheetId: google_sheets_id,
							questionId: id,
							questionLabel: label,
							answerId: choice.id,
							answerText: choice.label,
						})
					}
				>
					<label>
						{choice.label}
						<br />
						<input type="radio" name="choice-select" value={choice.id} />
					</label>
				</li>
			))}
		</div>
	);
}
