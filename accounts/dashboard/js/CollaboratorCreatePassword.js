import React, { Component } from 'react';

import Loading from '../../../mixity/dashboard/js/includes/Loading';
import { Modal } from 'react-bootstrap';

class CollaboratorCreatePassword extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to front-end display
			everythingLoaded: true,
			placeholder: gettext('Chargement'),

			//related to /api/create_password/ request
			encrypted_email: '',
			password: '',
			password_confirmation: '',
			show_error_modal: false,
			error_modal_message: '',
		};
	}

	async componentDidMount() {
		this.setState(() => {
			return {
				encrypted_email: window.location.pathname.split('/').filter(Boolean)[5],
			};
		});
	}

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

	onlyContainsNumbers(str) {
		return /^\d+$/.test(str);
	}

	async fetchLoginRequest() {
		try {
			const response = await fetch(`/api/login/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': csrftoken,
				},
				body: JSON.stringify({
					encrypted_email: this.state.encrypted_email,
					password: this.state.password,
				}),
			});
			this.fetchErrorMessage(response);
			const data = await response.json();
		} catch (error) {
			console.error('>>>>> ERROR in fetchLoginRequest: ', error);
		}
	}

	async fetchPasswordRequest() {
		try {
			const response = await fetch(`/api/create_password/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': csrftoken,
				},
				body: JSON.stringify({
					encrypted_email: this.state.encrypted_email,
					password: this.state.password,
				}),
			});
			this.fetchErrorMessage(response);
			const data = await response.json();
			await this.fetchLoginRequest();
			window.location.href = '/';
		} catch (error) {
			console.error('>>>>> ERROR in fetchPasswordRequest: ', error);
		}
	}

	async checkValidPassword() {
		if (this.state.password === this.state.password_confirmation && this.state.password.length >= 8 && !this.onlyContainsNumbers(this.state.password)) {
			await this.fetchPasswordRequest();
		} else {
			this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext('Le mot de passe ne respecte pas les conditions requises. Veuillez réessayer.'),
				};
			});
		}
	}

	render() {
		return this.state.everythingLoaded ? (
			<div className="bg-gradient-multicolor full-height">
				<Modal size="lg" style={{ zIndex: 1050 }} show={this.state.show_error_modal} onHide={() => this.setShowErrorModal(false)} centered>
					<Modal.Body>
						<p className="text-center">{this.state.error_modal_message}</p>
					</Modal.Body>
				</Modal>
				<section className="mxt-container bg--radar">
					<div className="col col--2">
						<div className="grid-column-1">
							<article className="margin padding">
								<img className="" src="/static/img/laptop.png" alt="Présentation questionnaire Mixity" />
							</article>
						</div>
						<div className="grid-column-2 py-5">
							<article className="card-light">
								<h2 className="title--h2">{gettext('Créer votre mot de passe')}</h2>
								<div>
									<p className="field__label" style={{}}>
										{gettext('Mot de passe:')}
									</p>
									<input type="password" onBlur={(e) => this.setState({ password: e.target.value })} />
									<div className="d-flex flex-column align-items-center">
										<div className="d-flex flex-column pt-3" style={{ fontSize: '75%' }}>
											<span style={{ margin: 0, padding: 0 }}>
												{gettext('Votre mot de passe doit contenir au minimum 8 caractères.')}
											</span>
											<span style={{ margin: 0, padding: 0 }}>
												{gettext('Votre mot de passe ne peut pas être entièrement numérique.')}
											</span>
										</div>
									</div>
								</div>
								<div>
									<p className="field__label">{gettext('Confirmer le mot de passe:')}</p>
									<input type="password" onBlur={(e) => this.setState({ password_confirmation: e.target.value })} />
									<span style={{ fontSize: '75%' }}>{gettext('Saisissez le même mot de passe que précédemment, pour vérification.')}</span>
								</div>
								<div className="d-flex flex-row justify-content-center pt-3">
									<button className="btn btn-secondary" style={{ width: '100%' }} onClick={() => this.checkValidPassword()}>
										{gettext('Valider le mot de passe')}
									</button>
								</div>
							</article>
						</div>
					</div>
				</section>
			</div>
		) : (
			<Loading message={this.state.placeholder} />
		);
	}
}

export default CollaboratorCreatePassword;
