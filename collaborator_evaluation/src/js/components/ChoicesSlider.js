import React from 'react';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';
import './ChoicesSlider.css';

export default function ChoicesSlider(props) {
	const { google_sheets_id, id, label, choices } = props.questionObject;
	function createMarks() {
		const marks = {};
		choices.map((choice) => {
			marks[choice.id] = choice.label;
		});
		return marks;
	}
	const marks = createMarks();
	const minMark = Math.min.apply(Math, Object.keys(marks));
	const maxMark = Math.max.apply(Math, Object.keys(marks));

	function handleValueChange(value) {
		props.handleChoiceInput({
			questionGoogleSheetId: google_sheets_id,
			questionId: id,
			questionLabel: label,
			answerId: value,
			answerText: marks[value],
		});
	}

	return (
		<>
			<div className="choices-slider">
				<Slider min={minMark} max={maxMark} marks={marks} step={null} onAfterChange={handleValueChange} defaultValue={null} />
			</div>
		</>
	);
}
