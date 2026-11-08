import React, { Component } from 'react';

import Loading from '../../../mixity/dashboard/js/includes/Loading';
import { Modal } from 'react-bootstrap';

class ForgottenPasswordChange extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to front-end display
			everythingLoaded: true,
			placeholder: gettext('Chargement'),

			show_error_modal: false,
			error_modal_message: '',

			Inputs: [
				{
					field: 'new_password',
					field_name: gettext('Mot de passe'),
					value: '',
					placeholder: 'Tapez votre nouveau mot de passe',
					hide_value: true,
					is_needed: true,
				},
				{
					field: 'password_confirmation',
					field_name: gettext('Confirmer mot de passe'),
					value: '',
					placeholder: 'Tapez votre nouveau mot de passe',
					hide_value: true,
					is_needed: true,
				},
			],
		};
	}

	checkPasswordValidity(password) {
		if (password.length < 8) {
			this.setShowErrorModal(true);
			this.setState(() => {
				return {
					error_modal_message: gettext('Le mot de passe doit contenir au moins 8 caractères.'),
				};
			});
			return false;
		}
		if (/^\d+$/.test(password)) {
			this.setShowErrorModal(true);
			this.setState(() => {
				return {
					error_modal_message: gettext('Le mot de passe ne peut pas être entièrement numérique.'),
				};
			});
			return false;
		}
		return true;
	}

	handlePasswordChange = async () => {
		if (!this.isEveryNeededFieldFilled()) {
			this.setShowErrorModal(true);
			return this.setState(() => {
				return {
					error_modal_message: gettext('Veuillez remplir tous les champs obligatoires.'),
				};
			});
		}
		if (this.state.Inputs[0].value !== this.state.Inputs[1].value) {
			this.setShowErrorModal(true);
			return this.setState(() => {
				return {
					error_modal_message: gettext('Les deux mots de passe ne correspondent pas.'),
				};
			});
		}
		if (!this.checkPasswordValidity(this.state.Inputs[0].value)) {
			return;
		}
		try {
			const formData = new FormData();
			formData.append('new_password', this.state.Inputs[0].value);
			formData.append('uuid', uuid);

			const response = await fetch(`/api/forgotten_password_change/`, {
				method: 'POST',
				headers: {
					'X-CSRFToken': csrftoken,
				},
				body: formData,
			});
			this.fetchErrorMessage(response);
			const data = await response.json();
			this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext('Mot de passe changé avec succès !'),
				};
			});
			setTimeout(() => {
				window.location.href = '/account/login';
			}, 2000);
		} catch (error) {
			console.error('>>>>> ERROR in handlePasswordChange: ', error);
			this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext("Quelque chose s'est mal passé !"),
				};
			});
		}
	};

	setShowInput = (input) => {
		this.setState(() => {
			return {
				Inputs: this.state.Inputs.map((input_loop) => {
					if (input_loop.field === input.field) {
						return {
							...input_loop,
							hide_value: !input_loop.hide_value,
						};
					} else {
						return input_loop;
					}
				}),
			};
		});
	};

	setField = (field, value) => {
		this.setState((prevState) => {
			return {
				Inputs: prevState.Inputs.map((input) => {
					if (input.field === field) {
						return {
							...input,
							value: value,
						};
					}
					return input;
				}),
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

	handleSubmit = (e) => {
		e.preventDefault();
		this.handlePasswordChange();
	};
	isEveryNeededFieldFilled() {
		let isFilled = true;
		this.state.Inputs.forEach((input) => {
			if (input.is_needed && input.value === '') {
				isFilled = false;
			}
		});
		return isFilled;
	}

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
					style={{ width: '45%', minWidth: '300px', height: '45vh', borderRadius: '16px' }}
				>
					<p className="text-center" style={{ marginBottom: '5vh', fontWeight: 570, fontSize: '22px' }}>
						{gettext('Mot de passe oublié ?')}
					</p>
					{this.state.Inputs.map((input) => {
						return (
							<div style={{ width: '85%', marginBottom: '2%' }} key={input.field}>
								<label className="mb-1" htmlFor={input.field} style={{ fontWeight: 520, fontSize: '14px' }}>
									{input.field_name}
								</label>
								<div
									id={input.field}
									className="d-flex flex-rows align-items-center justify-content-center"
									style={{ width: '100%', maxHeight: '30px' }}
								>
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
										type={input.hide_value ? 'password' : 'text'}
										value={input.value}
										placeholder={input.placeholder}
										onChange={(e) => this.setField(input.field, e.target.value)}
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
										onClick={() => this.setShowInput(input)}
									>
										<i
											className={input.hide_value ? 'bi bi-eye-slash' : 'bi bi-eye'}
											style={{ color: '#00000', padding: '5px', margin: 0 }}
										></i>
									</button>
								</div>
							</div>
						);
					})}
					<ul>
						<li style={{ marginBottom: '2%', marginTop: '8%' }}>{gettext('Votre mot de passe doit contenir au minimum 8 caractères.')}</li>
						<li style={{ marginBottom: '2%' }}>{gettext('Votre mot de passe ne peut pas être entièrement numérique.')}</li>
					</ul>
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
							{gettext('Changer de mot de passe')}
						</button>
					</div>
				</div>
			</form>
		) : (
			<Loading message={this.state.placeholder} />
		);
	}
}

export default ForgottenPasswordChange;
