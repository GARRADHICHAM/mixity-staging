import React, { Component } from 'react';

import { Modal } from 'react-bootstrap';

class RegisterConfirmed extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to front-end display
			everythingLoaded: true,
			placeholder: gettext('Chargement'),

			email: '',
			newsletter: false,

			show_error_modal: false,
			error_modal_message: '',

			show_password: false,
			show_password_confirmation: false,

			fields: {
				last_name: '',
				firstname: '',
				job: '',
				phone: '',
			},

			jobsType: [
				gettext('CEO'),
				gettext('DRH/RH/CRHO'),
				gettext('RSE'),
				gettext('Diversité & Inclusion ou QVT'),
				gettext('Formation'),
				gettext('Communication RH/RSE'),
				gettext('Autre'),
			],

			cards: [
				{
					title: gettext('Mesure instantanée de votre politique DE&I'),
					description: gettext('Audit et plan d’actions instantanés avec l’offre Start'),
					redirect: '/account/register/start/step3',
					selected: false,
				},
				{
					title: gettext('Mesure approfondie de votre politique DE&I'),
					description: gettext('Évaluation complète accompagnée de nos experts avec l’offre 360 DEI ou Campus'),
					redirect: '/measure/landing/',
					selected: false,
				},
				{
					title: gettext('Proposer des solutions'),
					description: gettext('Faire découvrir des solutions aux utilisateurs de la plateforme'),
					redirect: '/solver/landing/',
					selected: false,
				},
				{
					title: gettext('Chercher une solution'),
					description: gettext('Trouver une solution ou de bonnes pratiques pour vos problèmes'),
					redirect: '/pilot/landing/',
					selected: false,
				},
			],
		};
	}

	setSelectedCard = (index) => {
		let cards = this.state.cards;

		for (let i = 0; i < cards.length; i++) {
			cards[i].selected = false;
		}
		cards[index].selected = !cards[index].selected;
		this.setState(() => {
			return {
				cards: cards,
			};
		});
	};

	getSelectedCard = () => {
		for (let i = 0; i < this.state.cards.length; i++) {
			if (this.state.cards[i].selected) {
				return i;
			}
		}
		return -1;
	};

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

	getCookie = (name) => {
		let value = '; ' + document.cookie;
		let parts = value.split('; ' + name + '=');
		if (parts.length === 2) return parts.pop().split(';').shift();
	};

	async componentDidMount() {
		const currentUrl = window.location.href;
		const url = new URL(currentUrl);
		const params = new URLSearchParams(url.search);
		const email = params.get('email');
		this.setState(() => {
			return {
				email: email,
			};
		});

		this.fetchNewsletterUser();
	}

	async fetchHubspotForm() {
		const hutk = this.getCookie('hubspotutk');
		const formData = {
			submittedAt: Date.now(),
			fields: [
				{ objectTypeId: '0-1', name: 'email', value: this.state.email },
				{ objectTypeId: '0-1', name: 'firstname', value: this.state.fields.firstname },
				{ objectTypeId: '0-1', name: 'lastname', value: this.state.fields.last_name },
				{ objectTypeId: '0-1', name: 'phone', value: this.state.fields.phone },
				{ objectTypeId: '0-1', name: 'intitule_de_poste', value: this.state.fields.job },
			],
			context: {
				hutk: hutk,
				pageUri: 'https://share.hsforms.com/1Fla_8QZSSvGappoSKgWyDg43j1b',
				pageName: 'Form',
			},
		};

		// le premier id est l'id du portail, le deuxième est l'id du formulaire (à changer si le formulaire est modifié / portail supprimé)
		const response = await fetch('https://api.hsforms.com/submissions/v3/integration/submit/6883103/1656bff1-0652-4af1-9aa6-9a122a05b20e', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
			},
			body: JSON.stringify(formData),
		});
		if (response.status !== 200) {
			this.fetchErrorMessage(response);
		}
	}

	async fetchNewsletterUser() {
		const response = await fetch(`/api/user_newsletter/`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': csrftoken,
			},
		});
		if (response.status !== 200) {
			this.fetchErrorMessage(response);
		}
		const data = await response.json();
		this.setState(() => {
			return {
				newsletter: data.subscribed_to_newsletter,
			};
		});
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
		if (this.state.fields.last_name === '' || this.state.fields.firstname === '' || this.state.fields.job === '') {
			this.setShowErrorModal(true);
			this.setState(() => {
				return {
					error_modal_message: gettext('Veuillez remplir tous les champs.'),
				};
			});
			return;
		}
		if (this.getSelectedCard() === -1) {
			this.setShowErrorModal(true);
			this.setState(() => {
				return {
					error_modal_message: gettext('Veuillez sélectionner une carte.'),
				};
			});
			return;
		}
		if (this.state.newsletter === true) {
			this.fetchHubspotForm();
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
				job: this.state.fields.job,
				phone: this.state.fields.phone,
			}),
		});
		if (response.status === 200) {
			window.location.href = this.state.cards[this.getSelectedCard()].redirect;
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
					style={{ width: '55%', minWidth: '400px', height: '95%', borderRadius: '16px' }}
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
								<span style={{ color: 'red', marginLeft: '3px' }}>*</span>
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
									onChange={(e) => this.setField('last_name', e.target.value)}
								/>
							</div>
						</div>
						<div style={{ width: '47%' }}>
							<label className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
								{gettext('Prénom')}
								<span style={{ color: 'red', marginLeft: '3px' }}>*</span>
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
									onChange={(e) => this.setField('firstname', e.target.value)}
								/>
							</div>
						</div>
					</div>
					<div className="d-flex justify-content-between" style={{ width: '92%' }}>
						<div style={{ width: '47%' }}>
							<label className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
								{gettext('Fonction')}
								<span style={{ color: 'red', marginLeft: '3px' }}>*</span>
							</label>
							<div className="d-flex flex-rows align-items-center justify-content-center" style={{ width: '100%', maxHeight: '30px' }}>
								<select
									style={{
										background: '#F6F7FB',
										borderColor: '#F6F7FB',
										margin: 0,
										borderRadius: '8px',
										whiteSpace: 'nowrap',
										boxShadow: 'none',
									}}
									onChange={(e) => this.setField('job', e.target.value)}
								>
									<option value="">{gettext('Sélectionnez une fonction')}</option>
									{this.state.jobsType.map((job, index) => {
										return (
											<option key={index} value={job}>
												{gettext(job)}
											</option>
										);
									})}
								</select>
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
									onChange={(e) => this.setField('phone', e.target.value)}
								/>
							</div>
						</div>
					</div>
					<p style={{ fontSize: '14px', fontWeight: 600, color: '#00000', marginTop: '6%', marginBottom: '4%' }}>
						{gettext('Ce que vous souhaitez faire sur la plateforme')}
					</p>
					<div className="d-flex justify-content-between flex-column" style={{ width: '92%', height: '100%' }}>
						<div className="d-flex justify-content-between flex-row" style={{ width: '100%', height: '100%' }}>
							{this.state.cards.map((card, index) => {
								return (
									<div
										key={index}
										className="d-flex align-items-center, flex-column"
										style={{
											width: '22%',
											border: card.selected ? '1px solid #564592' : '1px solid #DEDFEA',
											margin: '3px',
											borderRadius: '8px',
											cursor: 'pointer',
										}}
										onClick={() => this.setSelectedCard(index)}
									>
										<p className="align-self-center justify-self-center" style={{ fontWeight: 650, fontSize: '12px', width: '90%' }}>
											{gettext(card.title)}
										</p>
										<p
											className="align-self-center justify-self-center"
											style={{ fontWeight: 600, fontSize: '11px', color: '#777E90', width: '90%', marginTop: 0 }}
										>
											{gettext(card.description)}
										</p>
									</div>
								);
							})}
						</div>
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

export default RegisterConfirmed;
