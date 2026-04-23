//Ce composant permet de faire apparaître un bouton qui gère le call api pour la création d'options

import React, { Component } from 'react';

class FetchCreateOptionsButton extends Component {
	async fetchCreateOptions() {
		const { product, structure_id, setErrorModalMessage, setShowErrorModal, updateStepClass } = this.props;

		const formData = new FormData();
		formData.append('product', product);
		formData.append('structure_id', structure_id);

		try {
			const response = await fetch(`/api/create_options/`, {
				method: 'POST',
				headers: {
					'X-CSRFToken': csrftoken,
				},
				body: formData,
			});

			const data = await response.json();
			if (response.ok) {
				if (product === 'start') updateStepClass('startPaymentStepClass', '');
				else updateStepClass('thirdStepClass', '');
				updateStepClass('secondStepClass', 'd-none');
			} else {
				setShowErrorModal(true);
				setErrorModalMessage(gettext(`Une erreur est survenue : ${data.message}`));
			}
		} catch (error) {
			console.error('Error creating options:', error);
			setShowErrorModal(true);
			setErrorModalMessage(gettext("Une erreur est survenue lors de la création de l'option"));
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
				onClick={() => this.fetchCreateOptions()}
			>
				{gettext('Ajouter une option')}
			</button>
		);
	}
}

export default FetchCreateOptionsButton;
