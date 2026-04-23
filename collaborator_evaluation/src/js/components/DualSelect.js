import React from 'react';

import './ChoicesSelect.css';

export default function DualSelect(props) {
	const { google_sheets_id, id, label, choices, subquestions } = props.questionObject;
	function removeAllSelectedFirstColumnExcept(elem) {
		if (elem.classList.contains('columnFirst')) {
			let elems = document.querySelectorAll('.columnFirst');
			elems.forEach((elem_tmp) => {
				if (elem !== elem_tmp) {
					delete DualSelect.answers[id]['answers'][elem_tmp.getAttribute('subquestion')];
					elem_tmp.checked = false;
				}
			});
		}
	}
	function unselect(elem) {
		if (elem.classList.contains('columnSecond')) {
			if (elem.classList.contains('is-selected')) {
				delete DualSelect.answers[id]['answers'][elem.getAttribute('subquestion')];
				elem.checked = false;
				elem.classList.remove('is-selected');
			} else {
				elem.classList.add('is-selected');
			}
		}
	}
	function handleChecked() {
		props.setUnlockNextbutton(false);
		document.querySelectorAll('.columnFirst').forEach((elem) => {
			if (elem.checked) {
				props.setUnlockNextbutton(true);
				return;
			}
		});
	}
	let count = 0;
	return (
		<div style={{ 'margin-top': '81px' }}>
			{subquestions.map((subquestion) => {
				let visibility = '';
				let margin_bottom = '';
				let background_color = '';
				count++;
				if (
					(google_sheets_id === 2021005 ||
						google_sheets_id === 20210050 ||
						google_sheets_id === 20210051 ||
						google_sheets_id === 20210052 ||
						google_sheets_id === 20210053) &&
					count > 1
				) {
					visibility = 'hidden';
				}
				if (count % 2 === 0) background_color = '#e9ecef';
				let firstColumn = true;
				return (
					<div className="choices-select" style={{ display: 'flex', justifyContent: 'center', flexDirection: 'column' }}>
						<div
							style={{
								display: 'flex',
								justifyContent: 'space-evenly',
								alignItems: 'center',
								flexWrap: 'wrap',
								backgroundColor: background_color,
							}}
						>
							<div style={{ width: '50%', minWidth: '300px' }}>
								<strong>- {subquestion.label}</strong>
							</div>
							<div style={{ display: 'flex', justifyContent: 'space-evenly', flexWrap: 'nowrap', width: '50%', minWidth: '300px' }}>
								{subquestion.choices.map((choice) => {
									let className = 'columnSecond';
									if (firstColumn) {
										className = 'columnFirst';
										firstColumn = false;
									}
									return (
										<li
											key={choice.label}
											onClick={() => {
												if (DualSelect.answers[id] === undefined) {
													DualSelect.answers[id] = {};
													DualSelect.answers[id]['answers'] = {};
													DualSelect.answers[id]['questionId'] = id;
												}
												removeAllSelectedFirstColumnExcept(document.getElementById('sc_' + choice.id));
												unselect(document.getElementById('sc_' + choice.id));
												DualSelect.answers[id]['answers'][subquestion.id] = {
													questionGoogleSheetId: google_sheets_id,
													questionId: id,
													questionLabel: label,
													subquestionId: subquestion.id,
													answerId: choice.id,
													answerText: choice.label,
												};
												props.handleChoiceInput(DualSelect.answers[id]);
												handleChecked();
											}}
										>
											<label>
												<span
													style={{
														visibility: visibility,
														width: '130px',
														marginTop: '-54px',
														height: '50px',
														marginBottom: margin_bottom,
													}}
												>
													<span>{choice.label}</span>
												</span>
												<br />
												<input
													style={{ border: '1px solid #707070', marginBottom: '12px' }}
													className={className}
													id={'sc_' + choice.id}
													type="radio"
													subquestion={subquestion.id}
													name={'choice-select_' + subquestion.id}
													value={choice.id}
												/>
											</label>
										</li>
									);
								})}
							</div>
						</div>
					</div>
				);
			})}
		</div>
	);
}
DualSelect.answers = {};
