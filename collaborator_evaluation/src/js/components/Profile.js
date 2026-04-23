import React, { useState, useEffect, useRef } from 'react';
import './Profile.css';
import PageControls from './PageControls';
import ProfileMultiple from './ProfileMultiple';

export default function Profile(props) {
	const [openListId, setOpenListId] = useState(null);
	const dropdownRefs = useRef([]);
	const [answerObject, _setAnswerObject] = useState({});
	// in order to access the state inside the click event function I had to create a reference to the state
	const answerRef = React.useRef(answerObject);

	function setAnswerObject(data) {
		answerRef.current = data;
		_setAnswerObject(data);
	}

	function updateTagsAndQuestions() {
		let currentMandatoryQuestions = [];
		let currentForbiddenQuestions = [];
		let currentCriteriaTags = [];
		Object.entries(answerObject).forEach(([name, valueList]) => {
			valueList.forEach((value) => {
				if (value.length >= 5) {
					currentMandatoryQuestions.push(...value[2]);
					currentForbiddenQuestions.push(...value[3]);
					currentCriteriaTags.push(...value[4]);
				}
				currentCriteriaTags.push(value[0]);
				if (
					"campus_teacher__cadre" == value[0] ||
					"campus_teacher__no_cadre" == value[0] ||
					"campus_collaborator__cadre" == value[0] ||
					"campus_collaborator__no_cadre" == value[0]
				) {
					currentCriteriaTags.push("campus_no_student");
				}
			});
		});
		props.mandatoryQuestions.current = new Set(currentMandatoryQuestions);
		props.forbiddenQuestions.current = new Set(currentForbiddenQuestions);
		props.criteriaTags.current = new Set(currentCriteriaTags);
	}

	// listens for clicks on the entire document in order to handle clicks outside the dropdown menu
	useEffect(() => {
		document.addEventListener('mousedown', documentClick);
		return () => document.removeEventListener('mousedown', documentClick);
	}, []);

	function documentClick(e) {
		// checks if user clicked on a menu
		if (Object.entries(dropdownRefs.current).some(([_, ref]) => ref && ref.contains(e.target))) {
			const id = e.target.parentElement.parentElement.previousSibling.dataset.id;
			let target = e.target;
			if (!e.target.dataset.valuenames) target = e.target.parentElement;
			setAnswerObject({
				...answerRef.current,
				[id]: [JSON.parse(target.dataset.valuenames)],
			});
			const tick = document.createElement('SPAN');
			addTick(tick, e);
			setTimeout(() => {
				tick.remove();
				setOpenListId(null);
			}, 250);
			// else closes the menu
		} else if (!(e.target.getAttribute('data-ismultiple') === 'true')) {
			setOpenListId(null);
		}
	}

	function addTick(tick, e) {
		tick.innerHTML = '<i class="fa fa-check"></i>';
		tick.style.float = 'right';
		e.target.appendChild(tick);
	}

	function getAllowedCriterias() {
		return props.profileData.filter((x) => {
			let allow = true;
			if (x.mandatory_tags !== undefined) {
				allow = allow && x.mandatory_tags.every((val) => props.criteriaTags.current.has(val));
			}
			if (x.forbidden_tags !== undefined) {
				allow = allow && !x.forbidden_tags.some((val) => props.criteriaTags.current.has(val));
			}
			if (!allow && x.id !== undefined && 'criteria_' + x.id in answerObject) {
				delete answerObject['criteria_' + x.id];
			}
			return allow;
		});
	}

	// sends answers to the global answer object only when the 4 forms are filled
	function handleInputs() {
		if (Object.keys(answerObject).length === getAllowedCriterias().length) {
			props.handleChoiceInput(answerObject);
		} else {
			props.setUnlockNextbutton(false);
		}
	}

	useEffect(handleInputs, [answerObject]);

	function toggleList(id) {
		setOpenListId(id);
	}

	function renderFormValues(form) {
		return form.values.map((value, i) => {
			return (
				<a key={'value' + i} className="profile-form-dropdown-value" data-valuenames={JSON.stringify(value)}>
					{value[1]}
					{i === 0 && <i className="fa fa-chevron-down dropdown-value-icon"></i>}
				</a>
			);
		});
	}

	updateTagsAndQuestions();
	return (
		<div className="col--2">
			{getAllowedCriterias().map((form, id) => {
				id = (form.id && 'criteria_' + form.id) || form.slug;
				return (
					<div key={'form' + id} className="profile-form-container">
						<strong data-slug={form.slug} data-id={id} className="profile-form-label">
							{form.label}
						</strong>
						{form.allow_multiple ? (
							<ProfileMultiple
								isOpened={openListId === id}
								id={id}
								toggleList={toggleList}
								answerRef={answerRef}
								setAnswerObject={_setAnswerObject}
								form={form}
								answerId={'criteria_' + form.id}
								handleInputs={() => {
									updateTagsAndQuestions();
									handleInputs();
									setAnswerObject({
										...answerRef.current,
									});
								}}
							/>
						) : (
							<div className="profile-form-dropdown ">
								<button
									onClick={() => {
										toggleList(id);
									}}
									className="profile-form-dropbtn button button--circle"
								>
									{answerObject[id] ? answerObject[id][0][1] : form.helper}
									<i className="fa fa-chevron-right"></i>
								</button>
								<div
									className="profile-form-dropdown-content"
									style={{
										border: openListId === id ? '' : 'none',
									}}
									ref={(el) => (dropdownRefs.current[id] = el)}
								>
									{openListId === id && renderFormValues(form)}
								</div>
							</div>
						)}
					</div>
				);
			})}
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
