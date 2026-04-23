import React, { Component } from 'react';
import { Breadcrumb } from 'react-bootstrap';
import { Modal } from 'react-bootstrap';
import Header from '../../../mixity/dashboard/js/includes/Header';

class PasswordChange extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to front-end display
			everythingLoaded: true,
			placeholder: gettext('Chargement'),

			show_error_modal: false,
			error_modal_message: '',

			InputsMappings: {
				picture: 'foto',
				last_name: 'last_name',
				first_name: 'first_name',
				job: 'commercial_name',
				phone: 'phone',
			},

			Inputs: [
				{
					field: 'old_password',
					field_name: gettext('Ancien mot de passe'),
					value: '',
					placeholder: gettext('Taper votre ancien mot de passe'),
					hide_value: true,
					is_needed: true,
				},
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

	setUrl = (field, url) => {
		this.setState((prevState) => {
			return {
				Inputs: prevState.Inputs.map((input) => {
					if (input.field === field) {
						return {
							...input,
							url: url,
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
		if (password === this.state.Inputs[0].value) {
			this.setShowErrorModal(true);
			this.setState(() => {
				return {
					error_modal_message: gettext("Le nouveau mot de passe doit être différent de l'ancien."),
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
		if (this.state.Inputs[1].value !== this.state.Inputs[2].value) {
			this.setShowErrorModal(true);
			return this.setState(() => {
				return {
					error_modal_message: gettext('Les deux mots de passe ne correspondent pas.'),
				};
			});
		}
		if (!this.checkPasswordValidity(this.state.Inputs[1].value)) {
			return;
		}
		try {
			const formData = new FormData();
			formData.append('old_password', this.state.Inputs[0].value);
			formData.append('new_password', this.state.Inputs[1].value);

			const response = await fetch(`/api/password_change/`, {
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
					error_modal_message: data.message,
				};
			});
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
			<div style={{ height: '100%', width: '100%' }}>
				<Modal
					aria-labelledby="contained-modal-title-vcenter"
					style={{ zIndex: '1050' }}
					className="criteria_modal m-0 p-0"
					centered
					show={this.state.show_error_modal}
					onHide={() => this.setShowErrorModal(false)}
					title={gettext('Erreur')}
				>
					<div className="text-center" style={{ fontWeight: 500, fontSize: '110%' }}>
						{this.state.error_modal_message}
					</div>
				</Modal>
				{/*header block*/}
				<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
					<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
						<Breadcrumb.Item href={'/'}>{gettext('Accueil')}</Breadcrumb.Item>
						<Breadcrumb.Item active>{gettext('Mon compte')}</Breadcrumb.Item>
						<Breadcrumb.Item active>
							<strong>{gettext('Mes identifiants')}</strong>
						</Breadcrumb.Item>
					</Breadcrumb>
					<Header data={{ url: '/', languages: languages, language_code: language_code, enabled_website_languages: enabled_website_languages }} />
				</div>
				<p style={{ margin: '3%', fontWeight: 700, fontSize: '130%' }}>{gettext('Mes identifiants')}</p>
				<div className="d-flex justify-content-between" style={{ margin: '3% 3% 0 3%' }}>
					<div style={{ width: '47%', backgroundColor: '#FFFFFF', marginBottom: '2.5%', borderRadius: '16px', border: '1px solid #DEDFEA' }}>
						<div style={{ margin: '5%' }}>
							<p style={{ fontWeight: 600, marginBottom: '6%' }}>{gettext('Changer de mot de passe')}</p>
							{this.state.Inputs.map((input) => {
								return (
									<div className="mb-3" key={input.field}>
										<label style={{ fontWeight: 550 }} htmlFor={input.field} className="form-label d-flex">
											{input.field_name}
											{input.is_needed ? <p style={{ color: 'red', margin: '0 0 0 3px' }}>*</p> : null}
										</label>
										<div className="d-flex flex-row">
											<input
												type={input.hide_value ? 'password' : 'text'}
												className="form-control"
												style={{ backgroundColor: '#F6F7FB', borderRadius: '6px 0 0 6px', border: 0, color: '#777E90' }}
												id={input.field}
												value={input.value}
												placeholder={input.placeholder}
												onChange={(e) => this.setField(input.field, e.target.value)}
											/>
											<button
												style={{
													borderRadius: '0 6px 6px 0',
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
						</div>
						<div className="d-flex align-items-center justify-content-center" style={{ margin: '5%', marginTop: '8%' }}>
							<button
								type="button"
								className="btn"
								style={{ backgroundColor: '#FFFFFF', color: '#000000', borderRadius: '6px', border: '1px solid #DEDFEA', margin: '0 3% 3% 3%' }}
								onClick={this.handlePasswordChange}
							>
								{gettext('Valider les modifications')}
							</button>
						</div>
					</div>
					<div className="d-flex flex-column justify-content-between" style={{ width: '47%', marginBottom: '2.5%' }}>
						<div style={{ backgroundColor: '#FFFFFF', borderRadius: '16px', border: '1px solid #DEDFEA' }}>
							<div style={{ margin: '5%' }}>
								<p style={{ fontWeight: 600, marginBottom: '6%' }}>{gettext('Mes identifiants')}</p>
								<label style={{ fontWeight: 550 }}>{gettext('Adresse mail')}</label>
								<p style={{ marginBottom: '4%' }}>{user_mail}</p>
								<label style={{ fontWeight: 550 }}>{gettext('Mot de passe')}</label>
								<p>xxxxxxxxxxxxxxxx</p>
							</div>
						</div>
						<div style={{ backgroundColor: '#FFFFFF', borderRadius: '16px', border: '1px solid #DEDFEA' }}>
							<div style={{ margin: '5%', fontSize: '100%' }}>
								<ul>
									<li style={{ marginBottom: '2%' }}>{gettext('Votre mot de passe doit contenir au minimum 8 caractères.')}</li>
									<li style={{ marginBottom: '2%' }}>{gettext('Votre mot de passe ne peut pas être entièrement numérique.')}</li>
								</ul>
							</div>
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

export default PasswordChange;
