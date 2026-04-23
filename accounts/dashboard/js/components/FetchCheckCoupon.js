//Ce composant permet de faire apparaître un bouton qui gère le call api pour la création d'options

import React, { Component } from 'react';

class FetchCheckCoupon extends Component {
	async fetchCheckCoupon() {
		const { coupon, structure_id, setErrorModalMessage, setShowErrorModal, updateStepClass } = this.props;

		const formData = new FormData();
		formData.append('coupon', coupon);
		formData.append('structure_id', structure_id);

		try {
			const response = await fetch(`/api/validate_coupon/`, {
				method: 'POST',
				headers: {
					'X-CSRFToken': csrftoken,
				},
				body: formData,
			});

			const data = await response.json();
			if (response.ok) {
				updateStepClass('startPaymentStepClass', 'd-none');
				updateStepClass('thirdStepClass', '');
			} else {
				setShowErrorModal(true);
				setErrorModalMessage(gettext(`Une erreur est survenue : ${data.message}`));
			}
		} catch (error) {
			console.error('Error validating coupon:', error);
			setShowErrorModal(true);
			setErrorModalMessage(gettext('Une erreur est survenue lors de la vérification du coupon'));
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
				onClick={() => this.fetchCheckCoupon()}
			>
				{gettext('Valider le coupon')}
			</button>
		);
	}
}

export default FetchCheckCoupon;
