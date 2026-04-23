import React, { Component } from 'react';

import { Modal, Alert } from 'react-bootstrap';

class CollaboratorLogin extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to front-end display
			everythingLoaded: true,
			placeholder: gettext('Chargement'),

			//related to /api/url/ request
			emptyurl: '',
			url: '',
			urlEvaluation: '',
			dashboardUrl: '',

			//related to /api/assess-evaluation/ request
			slug: '',
			evaluation: null,
			version: '',

			//related to /api/login/ request
			encrypted_email: '',
			password: '',
			show_error_modal: false,
			error_modal_message: '',
		};
	}

	async componentDidMount() {
		try {
			const response_url = await fetch('api/url/');
			this.fetchErrorMessage(response_url);
			const data_url = await response_url.json();
			let url = 'https://' + data_url;
			let emptyurl = url;
			let url_evaluation = 'https://' + data_url;
			let dashboard_url = 'https://' + data_url + '/';
			let version_slug = segments[segments.length - 1];

			if (window.location.pathname.split('/').filter(Boolean)[1]) url += '/' + window.location.pathname.split('/').filter(Boolean)[1];
			dashboard_url += '/' + window.location.pathname.split('/').filter(Boolean)[1];
			if (window.location.pathname.split('/').filter(Boolean)[2])
				url_evaluation += '/' + window.location.pathname.split('/').filter(Boolean)[1] + '/' + window.location.pathname.split('/').filter(Boolean)[2];

			this.setState(() => {
				return {
					emptyurl: emptyurl,
					url: url,
					urlEvaluation: url_evaluation,
					dashboardUrl: dashboard_url,
					slug: window.location.pathname.split('/').filter(Boolean)[4],
					version: version_slug,
				};
			});
		} catch (error) {
			console.error('>>>>> ERROR in evaluation criterias: ', error);
		}

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

	async fetchEvaluation() {
		try {
			const response_evaluation = await fetch(this.state.urlEvaluation + '/' + this.state.slug + '/human/api/assess-evaluation/' + version);
			this.fetchErrorMessage(response_evaluation);
			const data_evaluation = await response_evaluation.json();
			this.setState(() => {
				return {
					evaluation: data_evaluation[0],
				};
			});
		} catch (error) {
			console.error('>>>>> ERROR in fetch_evaluation: ', error);
		}
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
			await this.fetchEvaluation();
			const evaluation_url = 'https://' + window.location.host + this.state.evaluation.collaborator_url;
			window.location.href = evaluation_url;
		} catch (error) {
			console.error('>>>>> ERROR in fetchLoginRequest: ', error);
		}
	}

	async handleLogin() {
		if (this.state.password.length >= 8) {
			this.fetchLoginRequest();
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
								<img className="" style={{}} src={laptop_img} alt="Présentation questionnaire Mixity" />
							</article>
						</div>
						<div className="grid-column-2 py-5">
							<article className="card-light">
								<h2 className="title--h2">{gettext('Connectez-vous')}</h2>
								<div>
									<label className="field__label">{gettext('Mot de passe : ')}</label>
									<input type="password" onBlur={(e) => this.setState({ password: e.target.value })} />
								</div>
								<div className="d-flex flex-row justify-content-center mt-4 mb-2">
									<button className="btn btn-secondary" style={{ width: '100%' }} onClick={() => this.handleLogin()}>
										{gettext("Se connecter et accéder à l'évaluation")}
									</button>
								</div>
								<a href="/user/password-reset" className="field__label mb-2" style={{ fontWeight: 600 }}>
									{gettext('Mot de passe oublié ?')}{' '}
								</a>
							</article>
						</div>
					</div>
					<div className="grid-column-2 py-5">
						<article className="card-light">
							<h2 className="title--h2">{gettext('Connectez-vous')}</h2>
							<div>
								<p className="field__label">{gettext('Mot de passe:')}</p>
								<input type="password" onBlur={(e) => this.setState({ password: e.target.value })} />
							</div>
							<div className="d-flex flex-row justify-content-center mt-4 mb-2">
								<button className="btn btn-secondary" style={{ width: '100%' }} onClick={() => this.handleLogin()}>
									{gettext("Se connecter et accéder à l'évaluation")}
								</button>
							</div>
							<a href="/user/password-reset" className="field__label mb-2" style={{ fontWeight: 600 }}>
								{gettext('Mot de passe oublié ?')}{' '}
							</a>
						</article>
					</div>
				</section>
			</div>
		) : (
			<h4 className="d-flex justify-content-center align-items-middle" style={{ marginTop: '40%' }}>
				{this.state.placeholder}
			</h4>
		);
	}
}

export default CollaboratorLogin;
