import React, { useState, useEffect } from 'react';

export function QCMQuestionWithSolution(props) {
	const [selectedChoice, setSelectedChoice] = useState('');
	const [selectedChoices, setSelectedChoices] = useState([]);
	const [isSubmitted, setIsSubmitted] = useState(false);
	const [placeholder, setPlaceholder] = useState('');

	useEffect(() => {
		// Réinitialiser les états quand les nouvelles props arrivent
		setPlaceholder('');
		if (props.data.answer) {
			setSelectedChoice(props.data.answer.choice);
			setSelectedChoices(props.data.answer.choices);
			setIsSubmitted(true);
		} else {
			setSelectedChoice('');
			setSelectedChoices([]);
			setIsSubmitted(false);
		}
	}, [props.data.question]);

	const handleChoiceChange = (event) => {
		setSelectedChoice(event.target.value);
	};

	const handleChoicesChange = (event) => {
		const value = event.target.value;

		// Si la checkbox est cochée, on ajoute la valeur à selectedChoices
		if (event.target.checked) {
			setSelectedChoices((prevChoices) => [...prevChoices, value]);
		} else {
			// Si la checkbox est décochée, on retire la valeur de selectedChoices
			setSelectedChoices((prevChoices) =>
				prevChoices.filter((choice) => choice !== value),
			);
		}
	};

	const fetchErrorMessage = (response) => {
		if (response.status > 400) {
			setPlaceholder('Quelque chose s\'est mal passé !');
		}
		return;
	};

	const handleSubmit = (event) => {
		event.preventDefault();
		let body = {
			'answer_id': props.data.answer ? props.data.answer.id : null,
			'question_id': props.data.question.google_sheets_id,
			'choice': selectedChoice,
			'choices': selectedChoices,
		};
		const requestOptions = {
			credentials: 'include',
			method: 'POST',
			headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
			body: JSON.stringify(body),
		};
		setIsSubmitted(true);
		props.data.submitAnswer(requestOptions);
	};

	const checkedVerification = (idChoice) => {
		if (props.data.question.type === 'qcm') {
			if (props.data.answer && props.data.answer.choice === idChoice)
				return true;
		} else {
			if (props.data.answer) {
				const choice = props.data.answer.choices.find(ch => ch.id === idChoice);
				if (choice && choice.id === idChoice)
					return true;
			}
		}
	};

	const formatText = (text) => {
		const links = [];
		const linkRegex = /(https?:\/\/[^\s]+)/g;
		//Création de la liste de liens
		text = text.replace(linkRegex, (match, link) => {
			links.push(link);
			return `{link${links.length - 1}}`;
		});

		//Mettre en gras aux textes avant les deux-points
		text = text.replace(/(^|\n)(.*?):/g, '$1<br/><br/><strong>$2:</strong>');
		text = text.replace(/^(<br\s*\/?>)+/, '');

		//Remets les liens à leur place originale
		links.forEach((link, index) => {
			text = text.replace(`{link${index}}`, `  <a href="${link}" target="_blank" rel="noopener noreferrer">${gettext('Voir plus')}</a>`);
		});

		return text;
	};

	return (
		<React.Fragment>
			<form onSubmit={handleSubmit}>
				<div
					className="bg-white d-flex flex-column p-4"
					style={{ width: '100%', minWidth: '500px', borderRadius: '16px' }}
				>
					<h3 className="text-start">{props.data.question.label}</h3>
					<div className={'mt-3 d-flex flex-column text-start'}>
						{props.data.question.choices.map((choice) => (
							<div key={choice.id} className="pt-3 d-inline-flex">
								<input type={props.data.question.type === 'qcm' ? 'radio' : 'checkbox'} id={choice.id}
									   value={choice.id}
									   onChange={props.data.question.type === 'qcm' ? handleChoiceChange : handleChoicesChange}
									   checked={checkedVerification(choice.id)}
									   disabled={isSubmitted} name="qcm" />
								<label className="ms-2" style={{ fontSize: '1rem' }} htmlFor={choice.id}>{choice.label}</label>
							</div>
						))}
					</div>
					{!isSubmitted &&
						<button type="submit" className="align-self-start mt-2" name="return"
								style={{
									borderRadius: '6px',
									padding: '10px 16px 10px 16px',
									color: '#fff',
									borderColor: '#181B3D',
									backgroundColor: `${!selectedChoice && selectedChoices.length === 0 ? '#D2D2D2' : '#000'}`,
									border: '1px',
								}}
								disabled={!selectedChoice && selectedChoices.length === 0}>{gettext('Valider mon choix')}</button>
					}
				</div>
				{isSubmitted &&
					<div
						className="bg-white d-flex align-items-center flex-column mt-4 p-4 text-start"
						style={{ width: '100%', minWidth: '500px', borderRadius: '16px' }}
					>

						<div dangerouslySetInnerHTML={{ __html: formatText(props.data.question.feedback) }}></div>
					</div>
				}
			</form>
		</React.Fragment>
	);
}
