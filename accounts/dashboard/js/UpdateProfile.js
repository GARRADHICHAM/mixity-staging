import React, { Component } from 'react';
import { Breadcrumb } from 'react-bootstrap';
import { Modal } from 'react-bootstrap';
import Header from '../../../mixity/dashboard/js/includes/Header';
import SavePopup from './components/SavePopup';

class UpdateProfile extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to front-end display
			everythingLoaded: false,
			placeholder: gettext('Chargement'),

			show_error_modal: false,
			error_modal_message: '',

			InputsMappings: {
				picture: 'foto',
				last_name: 'last_name',
				first_name: 'first_name',
				job: 'job',
				phone: 'phone',
			},

			Inputs: [
				{
					field: 'picture',
					field_name: gettext('Photo'),
					field_type: 'file',
					base_value: null,
					value: null,
					url: '',
					placeholder: gettext('Chemin du fichier'),
					is_needed: false,
				},
				{
					field: 'last_name',
					field_name: gettext('Nom'),
					field_type: 'text',
					base_value: '',
					value: '',
					url: '',
					placeholder: 'Tapez votre nom',
					is_needed: true,
				},
				{
					field: 'first_name',
					field_name: gettext('Prénom'),
					field_type: 'text',
					base_value: '',
					value: '',
					url: '',
					placeholder: 'Tapez votre prénom',
					is_needed: true,
				},
				{
					field: 'job',
					field_name: gettext('Fonction'),
					field_type: 'text',
					base_value: '',
					value: '',
					url: '',
					placeholder: "Taper l'intitulé de votre poste",
					is_needed: true,
				},
				{
					field: 'phone',
					field_name: gettext('Téléphone'),
					field_type: 'text',
					base_value: '',
					value: '',
					url: '',
					placeholder: 'Taper votre numéro de téléphone',
					is_needed: false,
				},
			],
			showPopup: false,
		};
	}

	async componentDidMount() {
		try {
			await this.getProfile();
			this.setState(() => {
				return {
					everythingLoaded: true,
				};
			});
		} catch (error) {
			console.error('>>>>> ERROR in UpdateProfile: ', error);
			this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext("Quelque chose s'est mal passé !"),
				};
			});
		}
	}

	setField = (field, value) => {
		if (field == 'phone' && (value.length > 10 || /[^0-9]/.test(value))) {
			this.setShowErrorModal(true);
			return this.setState(() => {
				return {
					error_modal_message: gettext(
						'Le numéro de téléphone doit être composé de 10 chiffres, et ne doit pas contenir de lettres ou de caractères spéciaux.',
					),
				};
			});
		}
		if (value.length > 40) {
			this.setShowErrorModal(true);
			return this.setState(() => {
				return {
					error_modal_message: gettext('La taille maximale est de 40 caractères.'),
				};
			});
		}
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

	getProfile = async () => {
		try {
			const response = await fetch(`/api/get_profile/`, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': csrftoken,
				},
			});
			this.fetchErrorMessage(response);
			const data = await response.json();
			const updatedInputs = this.state.Inputs.map((input) => {
				const mappedField = this.state.InputsMappings[input.field];
				if (mappedField !== undefined) {
					return {
						...input,
						value: data[mappedField],
						url: data[mappedField],
						base_value: data[mappedField],
					};
				}
				return input;
			});
			updatedInputs[0].value = '';
			updatedInputs[0].base_value = '';
			this.setState({
				Inputs: updatedInputs,
			});
		} catch (error) {
			console.error('>>>>> ERROR in getProfile: ', error);
			this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext("Quelque chose s'est mal passé !"),
				};
			});
		}
	};

	resetInputs = () => {
		this.setState(() => {
			return {
				Inputs: this.state.Inputs.map((input) => {
					return {
						...input,
						value: input.base_value,
						url: input.base_value,
					};
				}),
			};
		});
	};

	handleUpdateProfile = async () => {
		if (!this.isEveryNeededFieldFilled()) {
			this.setShowErrorModal(true);
			return this.setState(() => {
				return {
					error_modal_message: gettext('Veuillez remplir tous les champs obligatoires.'),
				};
			});
		}
		try {
			const formData = new FormData();
			formData.append('foto', this.state.Inputs[0].value);
			formData.append('last_name', this.state.Inputs[1].value);
			formData.append('first_name', this.state.Inputs[2].value);
			formData.append('job', this.state.Inputs[3].value);
			formData.append('phone', this.state.Inputs[4].value);

			const response = await fetch(`/api/update_profile/`, {
				method: 'POST',
				headers: {
					'X-CSRFToken': csrftoken,
				},
				body: formData,
			});
			this.fetchErrorMessage(response);
			const data = await response.json();
			this.setState({ showPopup: true });
			// Masquer la popup après 2 secondes
			setTimeout(() => {
				this.setState({ showPopup: false });
			}, 3000);
		} catch (error) {
			console.error('>>>>> ERROR in handleUpdateProfile: ', error);
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

	getInputLabel(input, value) {
		let label = '';
		this.state.Inputs.forEach((inputSeek) => {
			if (input === inputSeek) {
				inputSeek.field_list.forEach((option) => {
					if (option.value === value) {
						label = option.label;
					}
				});
			}
		});
		return label;
	}

	handleImageChange = (event, input) => {
		const errMess = document.getElementById('error_message');
		const file = event.target.files[0];
		errMess.innerText = '';
		if (file) {
			if (file.type.startsWith('image/')) {
				this.setField(input.field, event.target.files[0]);
				this.setUrl(input.field, URL.createObjectURL(file));
			} else {
				errMess.innerText = gettext('Sélectionnez une image');
			}
		}
	};

	render() {
		return this.state.everythingLoaded ? (
			<div style={{ height: '100%', width: '100%' }}>
				{this.state.showPopup && <SavePopup message="Informations sauvegardées" />}
				<style>
					{`
              input[type="file"] {
                display: none;
              }
            `}
				</style>
				<Modal
					style={{ zIndex: 1200 }}
					show={this.state.show_error_modal}
					onHide={() => this.setShowErrorModal(false)}
					title={gettext('Erreur')}
					centered
				>
					<p className="text-center">{this.state.error_modal_message}</p>
				</Modal>
				{/*header block*/}
				<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
					<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
						<Breadcrumb.Item href={'/'}>{gettext('Accueil')}</Breadcrumb.Item>
						<Breadcrumb.Item active>{gettext('Mon compte')}</Breadcrumb.Item>
						<Breadcrumb.Item active>
							<strong>{gettext('Mes informations personnelles')}</strong>
						</Breadcrumb.Item>
					</Breadcrumb>
					<Header data={{ url: '/', languages: languages, language_code: language_code, enabled_website_languages: enabled_website_languages }} />
				</div>
				<p style={{ margin: '3%', fontWeight: 700, fontSize: '130%' }}>{gettext('Mes informations personnelles')}</p>
				<div className="d-flex justify-content-between" style={{ margin: '3% 3% 0 3%' }}>
					<div style={{ width: '700px', backgroundColor: '#FFFFFF', marginBottom: '2.5%', borderRadius: '16px', border: '1px solid #DEDFEA' }}>
						<div style={{ margin: '3%' }}>
							<p style={{ fontWeight: 600 }}>{gettext('Modifier vos information personnelles')}</p>
							{this.state.Inputs.map((input) => {
								return (
									<div className="mb-3" key={input.field}>
										<label style={{ fontWeight: 550 }} htmlFor={input.field} className="form-label d-flex">
											{input.field_name}
											{input.is_needed ? <p style={{ color: 'red', margin: '0 0 0 3px' }}>*</p> : null}
										</label>
										{input.field_type === 'file' ? (
											<div>
												<div className="d-flex flex-row" style={{ whiteSpace: 'nowrap' }}>
													<label
														className="d-flex align-items-center"
														htmlFor={input.field}
														style={{
															cursor: 'pointer',
															backgroundColor: '#8888E2',
															border: '1px solid #8888E2',
															padding: '.2em .4em',
															borderRadius: '6px 0 0 6px',
															color: '#FFFF',
															height: '2.3rem',
														}}
													>
														{gettext('Choisir un fichier')}
													</label>
													{input.name && (
														<input
															type="text"
															className="form-control"
															style={{ backgroundColor: '#F6F7FB', border: 0, color: '#777E90' }}
															value={input.name}
															placeholder={input.placeholder}
															disabled
														/>
													)}
												</div>
												<input
													type="file"
													className="form-control"
													id={input.field}
													accept="image/*"
													onChange={(e) => {
														this.handleImageChange(e, input);
													}}
												/>
												<h6 id="error_message"></h6>
											</div>
										) : (
											<input
												type="text"
												className="form-control"
												style={{ backgroundColor: '#F6F7FB', border: 0, color: '#777E90' }}
												id={input.field}
												value={input.value}
												placeholder={input.placeholder}
												onChange={(e) => this.setField(input.field, e.target.value)}
											/>
										)}
									</div>
								);
							})}
						</div>
						<div className="d-flex align-items-center justify-content-center">
							<button
								type="button"
								className="btn"
								style={{ backgroundColor: '#FFFFFF', color: '#000000', borderRadius: '6px', border: '1px solid #DEDFEA', margin: '0 0 3% 0' }}
								onClick={this.resetInputs}
							>
								{gettext('Annuler')}
							</button>
							<button
								type="button"
								className="btn"
								style={{ backgroundColor: '#FFFFFF', color: '#000000', borderRadius: '6px', border: '1px solid #DEDFEA', margin: '0 3% 3% 3%' }}
								onClick={this.handleUpdateProfile}
							>
								{gettext('Enregistrer')}
							</button>
						</div>
					</div>
					<div
						style={{
							width: '35%',
							height: 'fit-content',
							backgroundColor: '#FFFFFF',
							marginBottom: '2.5%',
							borderRadius: '16px',
							border: '1px solid #DEDFEA',
						}}
					>
						<div className="d-flex flex-column justify-content-center align-items-center" style={{ margin: '5%' }}>
							<p style={{ fontWeight: 600 }}>{gettext('Aperçu de vos informations')}</p>
							<img
								src={
									this.state.Inputs[0].url != '' && this.state.Inputs[0].url != null
										? this.state.Inputs[0].url
										: '/static/icon/basic_profile_pic.svg'
								}
								alt="profile_picture"
								style={{ width: '125px', height: '125px', marginTop: '6%', marginBottom: '8%', borderRadius: '90px' }}
							/>
							<p style={{ margin: '1%', fontWeight: 550 }}>
								{this.state.Inputs[1].value} {this.state.Inputs[2].value}
							</p>
							<p style={{ margin: '1%' }}>
								{this.state.Inputs[3].value != null && this.state.Inputs[3].value != '' ? this.state.Inputs[3].value : 'N/A'}
							</p>
							<p style={{ margin: '1%' }}>
								{this.state.Inputs[4].value != null && this.state.Inputs[4].value != ''
									? this.state.Inputs[4].value.match(/.{1,2}/g).join(' ')
									: 'N/A'}
							</p>
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

export default UpdateProfile;
