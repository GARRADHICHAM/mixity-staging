// Ce composant représente les champs permettant de créer une nouvelle structure. Il gère l'import des BusinessLine et la mise à jour des valeurs des champs du formulaire.

import React, { Component } from 'react';
import CountriesList from './CountriesList'; // Assurez-vous que le chemin est correct

class CreateStructureForm extends Component {
	constructor(props) {
		super(props);
		this.state = {
			categories: {
				enterprise: gettext('Entreprise'),
				event: gettext('Événement'),
				non_profit_organization: gettext('Association'),
				school: gettext('École'),
				public_institution: gettext('Collectivité locale'),
			},
			activityType: [],
			fields: { ...props.fields },
			selectedCountryCode: '',
		};
	}

	async componentDidMount() {
		await this.fetchActivityType();
	}

	setField = (field, value) => {
		const { setShowErrorModal } = this.props;
		const { fields } = this.state;
		if (field === 'phone' && (value.length > 15 || /[^0-9]/.test(value))) {
			setShowErrorModal(true);
			this.setState({
				error_modal_message: gettext(
					"Le numéro de téléphone doit être composé d'au maximum 15 chiffres, et ne doit pas contenir de lettres ou de caractères spéciaux.",
				),
			});
			return;
		}

		const newFields = { ...fields, [field]: value };
		this.setState({ fields: newFields }, () => {
			this.props.onFieldsChange(newFields);
		});
	};

	async fetchActivityType() {
		try {
			const response = await fetch(`/api/get_business_lines/`, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': this.props.csrftoken,
				},
			});
			if (response.ok) {
				const data = await response.json();
				this.setState({
					activityType: data,
					fields: { ...this.state.fields, activity: data[0]?.name },
				});
			} else {
				fetchErrorMessage(response);
			}
		} catch (error) {
			console.error('Error fetching activity types:', error);
			setErrorModalMessage(gettext('Une erreur est survenue lors de la création du formulaire.'));
		}
	}

	render() {
		const { categories, fields, activityType } = this.state;

		return (
			<>
				<div className="d-flex justify-content-between mb-3" style={{ width: '92%' }}>
					<div style={{ width: '47%' }}>
						<label className="mb-1 d-flex flex-row align-items-center" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext("Nom de l'organisation")}
							<span style={{ color: '#DE3838', fontWeight: 520, fontSize: '14px', margin: 0 }}>*</span>
						</label>
						<div className="d-flex flex-rows align-items-center justify-content-center" style={{ width: '100%', maxHeight: '30px' }}>
							<input
								style={{
									background: '#F6F7FB',
									borderColor: '#F6F7FB',
									margin: 0,
									borderRadius: '8px',
									whiteSpace: 'nowrap',
									boxShadow: 'none',
								}}
								type="text"
								onBlur={(e) => this.setField('organisation_name', e.target.value)}
							/>
						</div>
					</div>
					<div style={{ width: '47%' }}>
						<label className="mb-1 d-flex flex-row align-items-center" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext('SIRET / DUNS')}
							<span style={{ color: '#DE3838', fontWeight: 520, fontSize: '14px', margin: 0 }}>*</span>
						</label>
						<div className="d-flex flex-rows align-items-center justify-content-center" style={{ width: '100%', maxHeight: '30px' }}>
							<input
								style={{
									background: '#F6F7FB',
									borderColor: '#F6F7FB',
									margin: 0,
									borderRadius: '8px',
									whiteSpace: 'nowrap',
									boxShadow: 'none',
								}}
								type="text"
								onBlur={(e) => this.setField('siret', e.target.value)}
							/>
						</div>
					</div>
				</div>
				<div className="d-flex justify-content-between mb-3" style={{ width: '92%' }}>
					<div style={{ width: '47%' }}>
						<label className="mb-1 d-flex flex-row align-items-center" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext('Catégorie')}
							<span style={{ color: '#DE3838', fontWeight: 520, fontSize: '14px', margin: 0 }}>*</span>
						</label>
						<div className="d-flex flex-rows align-items-center justify-content-center" style={{ width: '100%', maxHeight: '30px' }}>
							<select
								style={{
									background: '#F6F7FB',
									borderColor: '#F6F7FB',
									margin: 0,
									borderRadius: '8px',
									whiteSpace: 'nowrap',
									boxShadow: 'none',
								}}
								value={fields.category}
								onChange={(e) => this.setField('category', e.target.value)}
							>
								{Object.keys(categories).map((key) => (
									<option key={key} value={key}>
										{categories[key]}
									</option>
								))}
							</select>
						</div>
					</div>
					<div style={{ width: '47%' }}>
						<label className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext('Pays')}
						</label>
						<div className="d-flex flex-rows align-items-center justify-content-center" style={{ width: '100%', maxHeight: '30px' }}>
							<CountriesList onCountryChange={(selectedCountryCode) => this.setField('country', selectedCountryCode)} />
						</div>
					</div>
				</div>
				<div className="d-flex justify-content-between mb-3" style={{ width: '92%' }}>
					<div style={{ width: '47%' }}>
						<label className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext('Téléphone')}
						</label>
						<div className="d-flex flex-rows align-items-center justify-content-center" style={{ width: '100%', maxHeight: '30px' }}>
							<input
								style={{
									background: '#F6F7FB',
									borderColor: '#F6F7FB',
									margin: 0,
									borderRadius: '8px',
									whiteSpace: 'nowrap',
									boxShadow: 'none',
								}}
								type="text"
								onBlur={(e) => this.setField('phone', e.target.value)}
							/>
						</div>
					</div>
					<div style={{ width: '47%' }}>
						<label className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext("Secteur d'activité")}
							<span style={{ color: '#DE3838', fontWeight: 520, fontSize: '14px', margin: 0 }}>*</span>
						</label>
						<div className="d-flex flex-rows align-items-center justify-content-center" style={{ width: '100%', maxHeight: '30px' }}>
							<select
								style={{
									background: '#F6F7FB',
									borderColor: '#F6F7FB',
									margin: 0,
									borderRadius: '8px',
									whiteSpace: 'nowrap',
									boxShadow: 'none',
								}}
								value={fields.activity}
								onChange={(e) => this.setField('activity', e.target.value)}
							>
								{this.state.activityType.map((activity) => (
									<option key={activity.name} value={activity.name}>
										{activity.name}
									</option>
								))}
							</select>
						</div>
					</div>
				</div>
				<div className="d-flex justify-content-between" style={{ width: '92%' }}>
					<div style={{ width: '47%' }}>
						<label className="mb-1 d-flex flex-row align-items-center" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext('Effectif')}
							<span style={{ color: '#DE3838', fontWeight: 520, fontSize: '14px', margin: 0 }}>*</span>
						</label>
						<div className="d-flex flex-rows align-items-center justify-content-center" style={{ width: '100%', maxHeight: '30px' }}>
							<input
								style={{
									background: '#F6F7FB',
									borderColor: '#F6F7FB',
									margin: 0,
									borderRadius: '8px',
									whiteSpace: 'nowrap',
									boxShadow: 'none',
								}}
								type="text"
								onBlur={(e) => this.setField('employees', e.target.value)}
							/>
						</div>
					</div>
					<div style={{ width: '47%' }}>
						<label className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext('Site web')}
							<span style={{ color: '#DE3838', fontWeight: 520, fontSize: '14px', margin: 0 }}>*</span>
						</label>
						<div className="d-flex flex-rows align-items-center justify-content-center" style={{ width: '100%', maxHeight: '30px' }}>
							<input
								style={{
									background: '#F6F7FB',
									borderColor: '#F6F7FB',
									margin: 0,
									borderRadius: '8px',
									whiteSpace: 'nowrap',
									boxShadow: 'none',
								}}
								type="text"
								onBlur={(e) => this.setField('website', e.target.value)}
							/>
						</div>
					</div>
				</div>
			</>
		);
	}
}

export default CreateStructureForm;
