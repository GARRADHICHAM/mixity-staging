import React from 'react';
import { useRef } from 'react';
import './ChoicesSelect.css';

export default function SubquestionQCM(props) {
	const { google_sheets_id, id, label, choices, subquestions } = props.questionObject;
	const answer = useRef({ answers: {}, questionId: id });

	function handleChecked(props) {
		props.setUnlockNextbutton(false);
		let unlockButton = false;

		subquestions.map((subquestion) => {
			const checked = document.getElementById('sq_' + subquestion.id) != null && document.getElementById('sq_' + subquestion.id).checked ? 1 : 0;
			if (checked) {
				unlockButton = true;
			}
			answer.current['answers'][subquestion.id] = {
				questionGoogleSheetId: google_sheets_id,
				questionId: id,
				questionLabel: label,
				subquestionId: subquestion.id,
				answerText: checked,
			};
		});
		props.handleChoiceInput(answer.current);
		props.setUnlockNextbutton(unlockButton);
	}

	function render_questions(modulo, subquestions, props) {
		let i = 0;
		return (
			<div className="border-0 d-flex flex-wrap flex-column" style={{ width: '48%', minWidth: '300px' }}>
				{subquestions
					.filter(function (element, index, array) {
						return index % 2 === modulo;
					})
					.map((subquestion) => {
						return (
							<div className="checkbox-wrapper" onClick={() => handleChecked(props)}>
								<label data-ismultiple="true" className="checkbox d-grid checkbox-line mb-3" key={subquestion.label}>
									<input
										className="subquestion_qcm_answer checkbox__trigger visuallyhidden"
										type="checkbox"
										name={'sq_' + subquestion.id}
										id={'sq_' + subquestion.id}
										value="1"
									/>
									<span className="checkbox__symbol">
										<svg
											aria-hidden="true"
											className="icon-checkbox"
											width="28px"
											height="28px"
											viewBox="0 0 28 28"
											version="1"
											xmlns="http://www.w3.org/2000/svg"
										>
											<path d="M4 14l8 7L24 7"></path>
										</svg>
									</span>
									<span className="checkbox__textwrapper text-start">{subquestion.label}</span>
								</label>
							</div>
						);
					})}
			</div>
		);
	}

	return (
		<div className="choices-select d-flex flex-wrap justify-content-evenly">
			{render_questions(0, subquestions, props)}
			{render_questions(1, subquestions, props)}
		</div>
	);
}
