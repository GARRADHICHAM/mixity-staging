//Ce composant permet de faire apparaître un bouton qui gère le call api pour la création d'une structure et de son pack

import React, { Component } from 'react';

class FetchCreateStructureButton extends Component {
	async fetchCreateStructure() {
		if (this.props.fields.phone.length > 15 || /[^0-9]/.test(this.props.fields.phone)) {
			this.props.setShowErrorModal(true);
			this.props.setErrorModalMessage(
				gettext("Le numéro de téléphone doit être composé d'au maximum 15 chiffres, et ne doit pas contenir de lettres ou de caractères spéciaux."),
			);
			return;
		}
		if (
			this.props.fields.organisation_name === '' ||
			this.props.fields.siret === '' ||
			this.props.fields.employees === '' ||
			this.props.fields.website === '' ||
			this.props.fields.activity === ''
		) {
			this.props.setShowErrorModal(true);
			this.props.setErrorModalMessage(gettext('Veuillez remplir tous les champs.'));
			return;
		}
		if (this.props.fields.siret.length !== 9 && this.props.fields.siret.length !== 14) {
			this.props.setShowErrorModal(true);
			this.props.setErrorModalMessage(gettext('Veuillez renseigner un SIRET ou un DUNS valide.'));
			return;
		}

		try {
			const response = await fetch(`/api/create_structure/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': this.props.csrftoken,
				},
				body: JSON.stringify(this.props.fields),
			});
			const data = await response.json();
			if (response.ok) {
				this.props.setStructurePK(data.pk);
				this.props.setEntitySlug(data.entity_slug);
			} else {
				this.props.setShowErrorModal(true);
				this.props.setErrorModalMessage(gettext(`Une erreur est survenue : ${data.message}`));
			}
		} catch (error) {
			console.error('Error creating structure:', error);
			this.props.setShowErrorModal(true);
			this.props.setErrorModalMessage(gettext('Une erreur est survenue lors de la création de la structure.'));
		}
	}

	render() {
		return (
			<button
				className="d-flex align-items-center justify-content-center text-white"
				style={{
					border: '1px solid #000000',
					height: '20%',
					minHeight: '30px',
					maxHeight: '35px',
					width: '95%',
					borderColor: '#8888E2',
					backgroundColor: '#8888E2',
					borderRadius: '4px',
					fontWeight: 505,
					fontSize: '12px',
				}}
				onClick={() => this.fetchCreateStructure()}
			>
				{this.props.buttonName}
			</button>
		);
	}
}

export default FetchCreateStructureButton;
