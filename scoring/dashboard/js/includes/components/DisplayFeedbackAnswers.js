import React, { useState, useEffect } from 'react';
import { Card, Button } from 'react-bootstrap';

export default function DisplayFeedbackAnswers(props) {
	const [answers, setAnswers] = useState([]);
	const [showSolutionStates, setShowSolutionStates] = useState([]);

	useEffect(() => {
		if (props.data.answers) {
			setAnswers(props.data.answers)
			setShowSolutionStates(new Array(props.data.answers.length).fill(false))
		}
	}, [props.data.answers]);

	const handleShowSolutionToggle = (index) => {
		const updatedShowSolutionStates = [...showSolutionStates];
		updatedShowSolutionStates[index] = !updatedShowSolutionStates[index];
		setShowSolutionStates(updatedShowSolutionStates);
	};

	if (!answers) {
		return <div></div>;
	}

	const convertHexToRgba = (hex, opacity) => {
		let r = 0,
			g = 0,
			b = 0;
		if (hex.length === 4) {
			r = parseInt(hex[1] + hex[1], 16);
			g = parseInt(hex[2] + hex[2], 16);
			b = parseInt(hex[3] + hex[3], 16);
		} else if (hex.length === 7) {
			r = parseInt(hex[1] + hex[2], 16);
			g = parseInt(hex[3] + hex[4], 16);
			b = parseInt(hex[5] + hex[6], 16);
		}
		return `rgba(${r}, ${g}, ${b}, ${opacity})`;
	};

	const checkUserAnswer = (answer, choiceId) => {
		if (answer.answer_choice && answer.choice === choiceId)
			return true
		else if (answer.answer_choices && answer.answer_choices.includes(choiceId))
			return true
		return false
	}

	return (
		<div>
			<h3 className="fw-medium mb-4 mt-4">{gettext('Réponses')}</h3>
			<div className="w-100 d-flex flex-wrap" style={{ gap: '2rem' }}>
				{/* Création d'une carte par question */}
				{answers.map((answer, index) => (
					<Card key={index} className="d-flex" style={{ width: '48%' }}>
						<Card.Body className="d-flex justify-content-between flex-column" style={{ gap: '32px' }}>
							<Card.Title className="mb-2">{answer.label}</Card.Title>
							{/* Affichage du détail*/}
							{showSolutionStates[index] ? (
								<>
									{/* Affichage de la bonne réponse et de la jauge associée à celle-ci */}
									{answer.choices
										.filter((choice) => (answer.answer_choice && choice.value === 4) || (!answer.answer_choice && choice.value > 0))
										.map((choice) => (
											<div className="d-flex flex-column" style={{ gap: '32px' }}>
												<Card.Subtitle key={choice.id} style={{ color: '#03A87C' }}>
													{gettext(choice.label)}
												</Card.Subtitle>
												<div
													className="w-100 progress-bar mb-1"
													style={{
														height: '20px',
														backgroundColor: convertHexToRgba('#03A87C', 0.1),
														borderRadius: '10px',
													}}
												>
													<div
														className="progress-bar-inner"
														style={{
															width: 50 + '%',
															height: '40px',
															backgroundColor: '#03A87C',
															borderRadius: '10px',
														}}
													></div>
												</div>
											</div>
										))}
									{/* Affichage du feedback en lien avec la question */}
									<Card.Text>
										<strong>{gettext('Feedback :')}</strong> <br />
										{gettext(answer.feedback)}
									</Card.Text>
									<Button variant="link" style={{ color: '#181B3D', textAlign: 'start' }} onClick={() => handleShowSolutionToggle(index)}>
										{gettext('Voir les réponses')}
									</Button>
								</>
							) : (
								// Affichage des choix multiples et de leurs résultats
								<>
									{answer.choices.map((choice) => {
										let textColor = '#181B3D';
										if ((answer.answer_choice && choice.value === 4) || (!answer.answer_choice && choice.value > 0)) {
											textColor = '#03A87C';
										} else if (choice.value <= 0 && checkUserAnswer(answer, choice.id)) {
											textColor = '#FF6F6F';
										}
										return (
											<div key={choice.id}>
												<Card.Subtitle
													className="d-flex justify-content-between"
													style={{
														padding: '10px',
														borderRadius: '5px',
														color: textColor,
													}}
												>
													{gettext(choice.label)}
													<strong style={{ marginLeft: '3rem' }}>{50 + '%'}</strong>
												</Card.Subtitle>
												{choice.value <= 0 && !checkUserAnswer(answer, choice.id) ? (
													<div
														className="w-100 progress-bar mb-1"
														style={{
															height: '20px',
															backgroundColor: '#E6E8EC',
															borderRadius: '10px',
														}}
													>
														<div
															className="progress-bar-inner"
															style={{
																width: 50 + '%',
																height: '40px',
																backgroundColor: textColor,
																borderRadius: '10px',
															}}
														></div>
													</div>
												) : (
													<div
														className="w-100 progress-bar mb-1"
														style={{
															height: '20px',
															backgroundColor: convertHexToRgba(textColor, 0.1),
															borderRadius: '10px',
														}}
													>
														<div
															className="progress-bar-inner"
															style={{
																width: 50 + '%',
																height: '40px',
																backgroundColor: textColor,
																borderRadius: '10px',
															}}
														></div>
													</div>
												)}
											</div>
										);
									})}
									{/* Affichage de la légende */}
									<Card.Text className="d-flex justify-content-between">
										{[
											{ color: '#03A87C', text: gettext('BONNE RÉPONSE') },
											{ color: '#181B3D', text: gettext('MAUVAISE RÉPONSE') },
											{ color: '#FF6F6F', text: gettext('MAUVAISE RÉPONSE SÉLECTIONNÉE') },
										].map((item, index) => (
											<div key={index} className="d-inline-flex align-items-center mb-3 mt-3">
												<div className="me-2">
													<div
														className="indic-score"
														style={{
															backgroundColor: item.color,
															width: '12px',
															height: '12px',
															borderRadius: item.color === '#FF6F6F' ? '5px' : '50%',
														}}
													></div>
												</div>
												<span className="mxt--small-bold">{item.text}</span>
											</div>
										))}
									</Card.Text>
									<Button className="d-flex" variant="link" style={{ color: '#181B3D' }} onClick={() => handleShowSolutionToggle(index)}>
										{gettext('Voir la solution')}
									</Button>
								</>
							)}
						</Card.Body>
					</Card>
				))}
			</div>
		</div>
	);
}
