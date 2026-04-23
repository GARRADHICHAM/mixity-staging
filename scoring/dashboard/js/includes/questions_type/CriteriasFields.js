import React, { useState, useEffect } from 'react';

export function CriteriasFields(props) {
	const [placeholder, setPlaceholder] = useState('');
	const [selectedChoices, setChoices] = useState({});

	useEffect(() => {
		// Réinitialiser les états quand les nouvelles props arrivent
		if (props.data.criterias && props.data.collaborators_info) {
			const initialChoices = {}; // Créer un objet vide pour initialiser selectedChoices
			Object.keys(props.data.criterias).forEach((key) => {
				initialChoices[key] = props.data.collaborators_info[key] || null;
				Object.keys(props.data.collaborators_info.criteria_choices).forEach((key2) => {
					if (props.data.collaborators_info.criteria_choices[key2][key])
						initialChoices[key] = props.data.collaborators_info.criteria_choices[key2][key] || null;
				})
			});
			setChoices(initialChoices); // Mettre à jour selectedChoices avec les nouvelles valeurs
		}
		setPlaceholder('');
	}, [props.data.criterias, props.data.collaborators_info]);

	const handleChange = (key, value) => {
		setChoices((prevChoices) => ({
			...prevChoices,
			[key]: value !== '' ? value : null, // Assigner null si aucune option sélectionnée
		}));
	};

	function checkAllFieldsAreFilled() {
		if (Object.keys(selectedChoices).length === 0)
			return true;

		for (let key in selectedChoices) {
			if (selectedChoices[key] === null)
				return true;
		}
		return false;
	}

	function disabledFieldsOrNot(key) {
		let disabled = false
		if (selectedChoices[key] != null && (selectedChoices[key] === props.data.collaborators_info[key]))
			disabled = true
		else {
			Object.keys(props.data.collaborators_info.criteria_choices).forEach((key2) => {
				if (selectedChoices[key] != null && selectedChoices[key] === props.data.collaborators_info.criteria_choices[key2][key])
					disabled = true;
			})
		}
		return disabled
	}

	function translateMandatoryCriteria(key) {
		if (key === "age")
			return gettext("Âge")
		if (key === "civility")
			return gettext("Genre")
		if (key === "job")
			return gettext("Position")
		return key.charAt(0).toUpperCase() + key.slice(1)
	}

	return (
		props.data.criterias && props.data.collaborators_info &&
		<React.Fragment>
			<div className="d-flex justify-content-between"
				 style={{ justifySelf: 'center', flexWrap: 'wrap', width: '100%', marginLeft: '5%' }}>
				{Object.keys(props.data.criterias).map((key) => (
					<div key={key} className="w-50 py-4">
						<div className="w-75 profile-form-dropdown">
							<label htmlFor={key} className="mb-2"
								   style={{ display: 'block', fontWeight: 'bold' }}>{translateMandatoryCriteria(key)}</label>
							<select id={key} name={key} value={selectedChoices[key] || ''}
									className="profile-form-dropbtn button button--circle px-1"
									style={{ backgroundColor: 'white' }}
									onChange={(e) => handleChange(key, e.target.value)}
									disabled={disabledFieldsOrNot(key)}
							>
								<option value="" disabled hidden>
									Select {translateMandatoryCriteria(key)}
								</option>
								{props.data.criterias[key].map((subArray, index) => (
									<option key={index} value={subArray[0]}>
										{subArray[1]}
									</option>
								))}
							</select>
						</div>
					</div>
				))}
			</div>
			<div className="d-flex justify-content-center pt-4">
				<button type="button" className="d-flex align-self-center" name="start_survey"
						style={{
							borderRadius: '6px',
							padding: '10px 16px 10px 16px',
							borderColor: '#181B3D',
							backgroundColor: '#F6F7FB',
							border: '1px',
						}}
						onClick={() => {
							props.data.saveInfo(selectedChoices);
						}}
						disabled={checkAllFieldsAreFilled()}
				>
					{gettext('Commencer le questionnaire')}
				</button>
			</div>
		</React.Fragment>
	);
}
