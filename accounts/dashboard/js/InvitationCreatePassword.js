import React, { Component } from 'react';

import { Modal } from 'react-bootstrap';

class InvitationCreatePassword extends Component {
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

			show_password: false,
			show_password_confirmation: false,
			cgu_accepted: false,
			subscribed_to_newsletter: false,
		};
	}

	setShowPassword = () => {
		this.setState(() => {
			return {
				show_password: !this.state.show_password,
			};
		});
	};

	setShowPasswordConfirmation = () => {
		this.setState(() => {
			return {
				show_password_confirmation: !this.state.show_password_confirmation,
			};
		});
	};

	async componentDidMount() {
		this.setState(() => {
			return {
				encrypted_email: window.location.pathname.split('/').filter(Boolean)[4],
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

	async fetchLoginRequest() {
		const response = await fetch(`/api/collaborator_login/`, {
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
		if (response.status === 200) {
			window.location.href = window.location.href.replace('create_password', 'confirmed');
		} else {
			this.fetchErrorMessage(response);
		}
	}

	async fetchPasswordRequest() {
		if (!this.state.cgu_accepted) {
			return this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext("Veuillez accepter les conditions générales d'utilisation."),
				};
			});
		}
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
					subscribed_to_newsletter: this.state.subscribed_to_newsletter,
				}),
			});
			this.fetchErrorMessage(response);
			const data = await response.json();
			this.fetchLoginRequest();
		} catch (error) {
			console.error('>>>>> ERROR in fetchPasswordRequest: ', error);
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
					style={{ width: '32%', minWidth: '300px', height: '95%', borderRadius: '16px' }}
				>
					<p className="text-center" style={{ marginBottom: '20px', fontWeight: 570, fontSize: '22px' }}>
						{gettext("Commencez l'aventure dès maintenant")}
					</p>
					<p className="text-center mb-3" style={{ margin: 0, fontWeight: 520, fontSize: '12px' }}>
						{gettext("Bienvenue, créez votre compte pour commencer l'expérience Mixity")}
					</p>
					<div style={{ width: '85%', marginTop: '15%' }}>
						<p className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext('Mot de passe')}
						</p>
						<div className="d-flex flex-rows align-items-center justify-content-center" style={{ width: '100%', maxHeight: '30px' }}>
							<input
								style={{
									background: '#F6F7FB',
									borderColor: '#F6F7FB',
									margin: 0,
									borderRadius: '8px 0 0 8px',
									whiteSpace: 'nowrap',
									boxShadow: 'none',
								}}
								type={this.state.show_password ? 'text' : 'password'}
								onChange={(e) => this.setState({ password: e.target.value })}
							/>
							<button
								style={{
									borderRadius: '0 8px 8px 0',
									borderRight: 'none',
									margin: 0,
									borderColor: '#F6F7FB',
									backgroundColor: '#F6F7FB',
									boxShadow: 'none',
									border: 'none',
								}}
								className="d-flex align-self-center"
								onClick={() => this.setShowPassword()}
							>
								<i
									className={this.state.show_password ? 'bi bi-eye-slash' : 'bi bi-eye'}
									style={{ color: '#00000', padding: '5px', margin: 0 }}
								></i>
							</button>
						</div>
					</div>
					<div style={{ width: '85%' }}>
						<p className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext('Confirmez votre mot de passe')}
						</p>
						<div className="d-flex flex-rows align-items-center justify-content-center" style={{ width: '100%', maxHeight: '30px' }}>
							<input
								style={{
									background: '#F6F7FB',
									borderColor: '#F6F7FB',
									margin: 0,
									borderRadius: '8px 0 0 8px',
									whiteSpace: 'nowrap',
									boxShadow: 'none',
								}}
								type={this.state.show_password_confirmation ? 'text' : 'password'}
								onChange={(e) => this.setState({ password_confirmation: e.target.value })}
							/>
							<button
								style={{
									borderRadius: '0 8px 8px 0',
									borderRight: 'none',
									margin: 0,
									borderColor: '#F6F7FB',
									backgroundColor: '#F6F7FB',
									boxShadow: 'none',
									border: 'none',
								}}
								className="d-flex align-self-center"
								onClick={() => this.setShowPasswordConfirmation()}
							>
								<i
									className={this.state.show_password_confirmation ? 'bi bi-eye-slash' : 'bi bi-eye'}
									style={{ color: '#00000', padding: '5px', margin: 0 }}
								></i>
							</button>
						</div>
					</div>
					<div className="mt-2 d-flex align-items-center">
						<input
							className="mx-2"
							style={{ borderRadius: '4px', border: '1px solid #000000', width: '22px', height: '22px' }}
							type="checkbox"
							onClick={() => this.setState({ cgu_accepted: !this.state.cgu_accepted })}
							checked={this.state.cgu_accepted}
						/>
						<p style={{ fontSize: '14px', fontWeight: 520 }}>
							{gettext("J'accepte les ")}
							<a href="/cgu">{gettext("conditions générales d'utilisation")}</a>
						</p>
					</div>
					<div className="d-flex align-items-center" style={{ marginTop: '-15px' }}>
						<input
							className="mx-2"
							style={{ borderRadius: '4px', border: '1px solid #000000', width: '22px', height: '22px' }}
							type="checkbox"
							onClick={() => this.setState({ subscribed_to_newsletter: !this.state.subscribed_to_newsletter })}
							checked={this.state.subscribed_to_newsletter}
						/>
						<p style={{ fontSize: '14px', fontWeight: 520 }}>{gettext("Je m'inscris à la newsletter")}</p>
					</div>
					{/*<div className="d-flex align-items-center justify-content-center" style={{width: "85%", margin: "3%"}}>*/}
					{/*  <div style={{border: "1px solid #000000", width: "50%", borderColor: "#B1B5C3"}}/>*/}
					{/*  <p style={{fontSize: "12px", fontWeight: 520, color: "#B1B5C3"}} className="mx-2">{gettext("ou")}</p>*/}
					{/*  <div style={{border: "1px solid #000000", width: "50%", borderColor: "#B1B5C3"}}/>*/}
					{/*</div>*/}
					<div className="d-flex align-items-center justify-content-center flex-column" style={{ height: '100%', width: '100%' }}>
						{/*<button className="bg-white d-flex align-items-center justify-content-center" style={{border: "1px solid #000000", height: "20%", minHeight: "30px", maxHeight: "35px", width: "85%", borderColor: "#FFFFF", borderRadius: "4px", fontWeight: 520, fontSize: "12px"}} onClick={() => alert("login Google")}>*/}
						{/*  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_%22G%22_logo.svg/1024px-Google_%22G%22_logo.svg.png" style={{height: "20px", width: "20px", marginRight: "7px"}} alt="Google logo" />*/}
						{/*  {gettext("Se connecter avec Google")}*/}
						{/*</button>*/}
						{/*<button className="bg-white d-flex align-items-center justify-content-center mt-3 mb-4" style={{border: "1px solid #000000", height: "20%", minHeight: "30px", maxHeight: "35px", width: "85%", borderColor: "#FFFFF", borderRadius: "4px", fontWeight: 520, fontSize: "12px"}} onClick={() => alert("login Facebook")}>*/}
						{/*  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/51/Facebook_f_logo_%282019%29.svg/1024px-Facebook_f_logo_%282019%29.svg.png" style={{height: "20px", width: "20px", marginRight: "7px"}} alt="Facebook logo" />*/}
						{/*  {gettext("Se connecter avec Facebook")}*/}
						{/*</button>*/}
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
							onClick={() => this.fetchPasswordRequest()}
						>
							{gettext("S'inscrire")}
						</button>
						<p style={{ fontSize: '12px', fontWeight: 'light' }}>
							{gettext('Déjà un compte ? ')}
							<a href="/user/login/">{gettext('Se connecter')}</a>
						</p>
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

export default InvitationCreatePassword;
