import React, { Component } from 'react';

import { Modal } from 'react-bootstrap';

class RegisterStartConfirmed extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to front-end display
			everythingLoaded: true,
			placeholder: gettext('Chargement'),

			show_error_modal: false,
			error_modal_message: '',

			fields: {
				last_name: '',
				firstname: '',
				job: '',
				phone: '',
			},
		};
	}

	setField = (field, value) => {
		if (field === 'phone' && (value.length > 15 || /[^0-9]/.test(value))) {
			this.setShowErrorModal(true);
			this.setState(() => {
				return {
					error_modal_message: gettext(
						"Le numéro de téléphone doit être composé d'au maximum 15 chiffres, et ne doit pas contenir de lettres ou de caractères spéciaux.",
					),
				};
			});
			return;
		}
		this.setState((prevState) => {
			return {
				fields: {
					...prevState.fields,
					[field]: value,
				},
			};
		});
	};

	setShowErrorModal = (value) => {
		this.setState(() => {
			return {
				show_error_modal: value,
			};
		});
	};

	fetchErrorMessage(response) {
		if (response.status > 400) {
			return this.setState(() => {
				return { placeholder: gettext("Quelque chose s'est mal passé !") };
			});
		}
		return;
	}

	async fetchCreateUser() {
		if (this.state.fields.phone.length > 15 || /[^0-9]/.test(this.state.fields.phone)) {
			this.setShowErrorModal(true);
			this.setState(() => {
				return {
					error_modal_message: gettext(
						"Le numéro de téléphone doit être composé d'au maximum 15 chiffres, et ne doit pas contenir de lettres ou de caractères spéciaux.",
					),
				};
			});
			return;
		}
		if (this.state.fields.last_name === '' || this.state.fields.firstname === '' || this.state.fields.job === '' || this.state.fields.phone === '') {
			this.setShowErrorModal(true);
			this.setState(() => {
				return {
					error_modal_message: gettext('Veuillez remplir tous les champs.'),
				};
			});
			return;
		}
		const response = await fetch(`/api/update_user/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': csrftoken,
			},
			body: JSON.stringify({
				first_name: this.state.fields.firstname,
				last_name: this.state.fields.last_name,
				commercial_name: this.state.fields.job,
				phone: this.state.fields.phone,
			}),
		});
		if (response.status === 200) {
			window.location.href = '/account/register/start/step3';
		} else {
			this.fetchErrorMessage(response);
		}
	}

	render() {
		return this.state.everythingLoaded ? (
			<div className="d-flex justify-content-center align-items-center" style={{ height: '80vh' }}>
				<Modal
					style={{ zIndex: 1200 }}
					show={this.state.show_error_modal}
					onHide={() => this.setShowErrorModal(false)}
					title={gettext('Erreur')}
					centered
				>
					<p className="text-center">{this.state.error_modal_message}</p>
				</Modal>
				<div
					className="bg-white d-flex align-items-center flex-column"
					style={{ width: '55%', minWidth: '400px', height: '60%', borderRadius: '16px' }}
				>
					<p className="text-center" style={{ marginBottom: '5px', fontWeight: 570, fontSize: '22px' }}>
						{gettext('Inscription confirmée !')}
					</p>
					<p className="text-center mb-3" style={{ margin: 0, fontWeight: 520, fontSize: '12px' }}>
						{gettext('Pourriez-vous nous donner quelques détails sur vous ?')}
					</p>
					<div className="d-flex justify-content-between mb-3" style={{ width: '92%' }}>
						<div style={{ width: '47%' }}>
							<label className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
								{gettext('Nom')}
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
									onBlur={(e) => this.setField('last_name', e.target.value)}
								/>
							</div>
						</div>
						<div style={{ width: '47%' }}>
							<label className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
								{gettext('Prénom')}
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
									onBlur={(e) => this.setField('firstname', e.target.value)}
								/>
							</div>
						</div>
					</div>
					<div className="d-flex justify-content-between" style={{ width: '92%' }}>
						<div style={{ width: '47%' }}>
							<label className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
								{gettext('Fonction')}
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
									onBlur={(e) => this.setField('job', e.target.value)}
								/>
							</div>
						</div>
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
					</div>
					<div className="d-flex justify-content-between flex-column" style={{ width: '92%', height: '100%' }}>
						<div className="d-flex align-items-center justify-content-center flex-column" style={{ height: '100%', width: '100%' }}>
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
								onClick={() => this.fetchCreateUser()}
							>
								{gettext('Suivant')}
							</button>
						</div>
					</div>
				</div>
			</div>
		) : (
			<h4 className="d-flex justify-content-center align-items-middle" style={{ marginTop: '40%' }}>
				{this.state.placeholder}
			</h4>
		);
	}
}

export default RegisterStartConfirmed;
