import React, { Component } from 'react';

import { Modal } from 'react-bootstrap';

class ForgottenPasswordMail extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to front-end display
			everythingLoaded: true,
			placeholder: gettext('Chargement'),

			show_error_modal: false,
			error_modal_message: '',

			fields: {
				email: '',
			},
		};
	}

	isEmailFormatValid(email) {
		let re = /\S+@\S+\.\S+/;
		return re.test(email);
	}

	setField = (field, value) => {
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

	async fetchLogUser() {
		if (!this.isEmailFormatValid(this.state.fields.email)) {
			return this.setState(() => {
				return { show_error_modal: true, error_modal_message: gettext("L'adresse mail n'est pas valide") };
			});
		}
		const response = await fetch(`/api/forgotten_password_mail/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': csrftoken,
			},
			body: JSON.stringify({
				email: this.state.fields.email,
			}),
		});
		if (response.status === 200) {
			this.fetchErrorMessage(response);
			this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext('Mail envoyé ! Veuillez vérifier vos emails.'),
				};
			});
		} else {
			this.fetchErrorMessage(response);
			this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext("Cette adresse mail n'est liée à aucun compte"),
				};
			});
		}
	}

	handleSubmit = (e) => {
		e.preventDefault();
		this.fetchLogUser();
	};

	render() {
		return this.state.everythingLoaded ? (
			<form onSubmit={this.handleSubmit} className="d-flex justify-content-center align-items-center" style={{ height: '80vh' }}>
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
					style={{ width: '32%', minWidth: '300px', height: '35vh', borderRadius: '16px' }}
				>
					<p className="text-center" style={{ marginBottom: '10vh', fontWeight: 570, fontSize: '22px' }}>
						{gettext('Mot de passe oublié ?')}
					</p>
					<div style={{ width: '85%' }}>
						<label className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext('Adresse mail')}
						</label>
						<input
							style={{ background: '#F6F7FB', borderColor: '#F6F7FB', margin: 0, borderRadius: '8px', whiteSpace: 'nowrap', boxShadow: 'none' }}
							name="email"
							type="text"
							onBlur={(e) => this.setField('email', e.target.value)}
						/>
					</div>
					<div className="d-flex align-items-center justify-content-center flex-column" style={{ height: '100%', width: '100%' }}>
						<button
							className="d-flex align-items-center justify-content-center text-white"
							style={{
								border: '1px solid #000000',
								height: '20%',
								minHeight: '30px',
								maxHeight: '35px',
								width: '85%',
								borderColor: '#8888E2',
								backgroundColor: '#8888E2',
								borderRadius: '4px',
								fontWeight: 505,
								fontSize: '12px',
							}}
							type="submit"
						>
							{gettext('Envoyer le mail de changement de mot de passe')}
						</button>
					</div>
				</div>
			</form>
		) : (
			<h4 className="d-flex justify-content-center align-items-middle" style={{ marginTop: '40%' }}>
				{this.state.placeholder}
			</h4>
		);
	}
}

export default ForgottenPasswordMail;
