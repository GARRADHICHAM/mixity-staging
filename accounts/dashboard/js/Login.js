import React, { Component } from 'react';

import Loading from '../../../mixity/dashboard/js/includes/Loading';
import { Modal } from 'react-bootstrap';

class Login extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to front-end display
			everythingLoaded: true,
			placeholder: gettext('Chargement'),

			show_error_modal: false,
			error_modal_message: '',

			show_password: false,

			fields: {
				email: '',
				password: '',
			},
		};
	}

	isEmailFormatValid(email) {
		let re = /\S+@\S+\.\S+/;
		return re.test(email);
	}

	setShowPassword = () => {
		this.setState(() => {
			return {
				show_password: !this.state.show_password,
			};
		});
	};

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
		const response = await fetch(`/api/login/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': csrftoken,
			},
			body: JSON.stringify({
				email: this.state.fields.email,
				password: this.state.fields.password,
			}),
		});
		if (response.status === 200) {
			window.location.href = '/';
		} else {
			this.fetchErrorMessage(response);
			this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext("L'adresse mail ou le mot de passe est incorrect"),
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
			<form onSubmit={this.handleSubmit} className="d-flex justify-content-center align-items-center" style={{ minHeight: '80vh', maxHeight: 'fit-content' }}>
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
					<p className="text-center" style={{ marginBottom: '20%', fontWeight: 570, fontSize: '22px' }}>
						{gettext('Connexion')}
					</p>
					<div style={{ width: '85%' }}>
						<label className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext('Adresse mail')}
						</label>
						<input
							style={{ background: '#F6F7FB', borderColor: '#F6F7FB', margin: 0, borderRadius: '8px', whiteSpace: 'nowrap', boxShadow: 'none' }}
							name="email"
							type="text"
							onChange={(e) => this.setField('email', e.target.value)}
						/>
					</div>
					<div style={{ width: '85%' }}>
						<label className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext('Mot de passe')}
						</label>
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
								name="password"
								type={this.state.show_password ? 'text' : 'password'}
								onChange={(e) => this.setField('password', e.target.value)}
							/>
							<button
								type="button"
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
					{/*<div className="d-flex align-items-center justify-content-center" style={{width: "85%", height: "30%", marginTop: "4%"}}>*/}
					{/*  <div style={{border: "1px solid #000000", width: "50%", borderColor: "#B1B5C3"}}/>*/}
					{/*  <p style={{fontSize: "12px", fontWeight: 520, color: "#B1B5C3"}} className="mx-2">{gettext("ou")}</p>*/}
					{/*  <div style={{border: "1px solid #000000", width: "50%", borderColor: "#B1B5C3"}}/>*/}
					{/*</div>*/}
					<div className="d-flex align-items-center justify-content-center flex-column" style={{ height: '100%', width: '100%' }}>
						{/*<button type="button" className="bg-white d-flex align-items-center justify-content-center" style={{border: "1px solid #000000", height: "20%", minHeight: "30px", maxHeight: "35px", width: "85%", borderColor: "#FFFFF", borderRadius: "4px", fontWeight: 520, fontSize: "12px"}} onClick={() => alert("login Google")}>*/}
						{/*  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/c/c1/Google_%22G%22_logo.svg/1024px-Google_%22G%22_logo.svg.png" style={{height: "20px", width: "20px", marginRight: "7px"}} alt="Google logo" />*/}
						{/*  {gettext("Se connecter avec Google")}*/}
						{/*</button>*/}
						{/*<button type="button" className="bg-white d-flex align-items-center justify-content-center mt-2 mb-4" style={{border: "1px solid #000000", height: "20%", minHeight: "30px", maxHeight: "35px", width: "85%", borderColor: "#FFFFF", borderRadius: "4px", fontWeight: 520, fontSize: "12px"}} onClick={() => alert("login Facebook")}>*/}
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
							type="submit"
						>
							{gettext('Se connecter')}
						</button>
						<a
							href="/account/register"
							className="bg-white d-flex align-items-center justify-content-center mt-2"
							style={{
								border: '1px solid #000000',
								height: '20%',
								minHeight: '30px',
								maxHeight: '35px',
								width: '85%',
								borderColor: '#FFFFF',
								borderRadius: '4px',
								fontWeight: 520,
								fontSize: '12px',
							}}
						>
							{gettext('Créer un compte')}
						</a>
						<p className="mb-5" style={{ fontSize: '12px', fontWeight: 'light' }}>
							<a href="/user/password-reset/">{gettext('Mot de passe oublié ?')}</a>
						</p>
					</div>
				</div>
			</form>
		) : (
			<Loading message={this.state.placeholder} />
		);
	}
}

export default Login;
