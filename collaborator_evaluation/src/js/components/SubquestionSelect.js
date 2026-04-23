import React from 'react';

import './SubquestionSelect.css';

export default function SubquestionSelect(props) {
	const { google_sheets_id, id, label, choices, subquestions } = props.questionObject;
	const subquestionsIds = [
		2021009, 20210090, 2021049, 20210491, 2021051, 20210512, 2021018, 20210091, 20210092, 20230109, 20230116, 20230117, 20230121, 20230122, 20230123,
		20230125, 20230126, 2021052111, 2021051,
	];
	function handleChecked() {
		let inputs = {};
		document.querySelectorAll('.radio_form_input').forEach((elem) => {
			inputs[elem.name] = inputs[elem.name] || elem.checked;
		});
		for (let id in inputs) {
			if (!inputs[id]) {
				props.setUnlockNextbutton(false);
				return;
			}
		}
		props.setUnlockNextbutton(true);
	}
	let count = 0;
	return (
		<div>
			<br />
			<div>
				{subquestions.map((subquestion) => {
					count++;
					let background_color = '';
					if (count % 2 === 0) background_color = '#e9ecef';
					return (
						<div style={{ display: 'flex', justifyContent: 'space-evenly', flexWrap: 'wrap', backgroundColor: background_color }}>
							<div className="label_container">
								<strong>- {subquestion.label}</strong>
							</div>
							<div className="choices_container">
								{subquestion.choices.map((choice) => {
									let class_not_first = '';
									let class_first = '';
									if (subquestionsIds.includes(google_sheets_id) && count > 1) {
										class_not_first = 'class_not_first';
									} else {
										class_first = 'class_first';
									}
									return (
										<li
											key={choice.label}
											onClick={() => {
												if (SubquestionSelect.answers[id] === undefined) {
													SubquestionSelect.answers[id] = {};
													SubquestionSelect.answers[id]['answers'] = {};
													SubquestionSelect.answers[id]['questionId'] = id;
												}
												SubquestionSelect.answers[id]['answers'][subquestion.id] = {
													questionGoogleSheetId: google_sheets_id,
													questionId: id,
													questionLabel: label,
													subquestionId: subquestion.id,
													answerId: choice.id,
													answerText: choice.label,
												};
												props.handleChoiceInput(SubquestionSelect.answers[id]);
												handleChecked();
											}}
										>
											<div
												className={class_first}
												style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: '130px' }}
											>
												<div className={'class_label ' + class_not_first}>
													<label htmlFor={'choice-select_' + subquestion.id}>
														<span style={{ display: 'inline-block' }}>{choice.label}</span>
													</label>
												</div>
												<div className="mobile_input">
													<input
														className="radio_form_input"
														style={{ border: '1px solid #707070', marginBottom: '12px' }}
														id={'sc_' + choice.id}
														type="radio"
														name={'choice-select_' + subquestion.id}
														value={choice.id}
													/>
												</div>
											</div>
										</li>
									);
								})}
							</div>
						</div>
					);
				})}
			</div>
		</div>
	);
}
SubquestionSelect.answers = {};
