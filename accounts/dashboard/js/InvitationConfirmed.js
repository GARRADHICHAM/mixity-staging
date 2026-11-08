import React, { Component } from 'react';

import Loading from '../../../mixity/dashboard/js/includes/Loading';
import { Modal } from 'react-bootstrap';

class InvitationConfirmed extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to front-end display
			everythingLoaded: true,
			placeholder: gettext('Chargement'),

			email: '',
			company: '',
			newsletter: false,

			show_error_modal: false,
			error_modal_message: '',
			fields: {
				first_name: '',
				last_name: '',
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

	async fetchEmail() {
		const response = await fetch(`/api/get_email/${window.location.pathname.split('/').filter(Boolean)[4]}/`, {
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
				email: data.email,
			};
		});
	}

	async fetchCompany() {
		const response = await fetch(`/api/get_company_name/`, {
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
				company: data.company,
			};
		});
	}

	async componentDidMount() {
		this.fetchNewsletterUser();
		this.fetchEmail();
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

	getCookie = (name) => {
		let value = '; ' + document.cookie;
		let parts = value.split('; ' + name + '=');
		if (parts.length === 2) return parts.pop().split(';').shift();
	};

	async fetchHubspotForm() {
		const hutk = this.getCookie('hubspotutk');
		const formData = {
			submittedAt: Date.now(),
			fields: [
				{ objectTypeId: '0-1', name: 'email', value: this.state.email },
				{ objectTypeId: '0-1', name: 'firstname', value: this.state.fields.first_name },
				{ objectTypeId: '0-1', name: 'lastname', value: this.state.fields.last_name },
				{ objectTypeId: '0-1', name: 'phone', value: this.state.fields.phone },
				{ objectTypeId: '0-1', name: 'company', value: this.state.company },
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

	async fetchUpdateUser() {
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
		const response = await fetch(`/api/update_user/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': csrftoken,
			},
			body: JSON.stringify({
				first_name: this.state.fields.first_name,
				last_name: this.state.fields.last_name,
				commercial_name: this.state.fields.job,
				phone: this.state.fields.phone,
			}),
		});
		if (response.status === 200) {
			if (this.state.newsletter === true) {
				this.fetchHubspotForm();
			}
			window.location.href = '/';
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
					className="bg-white d-flex align-items-center justify-content-between flex-column"
					style={{ width: '32%', minWidth: '300px', height: '85%', borderRadius: '16px' }}
				>
					<p className="text-center" style={{ marginBottom: '5px', fontWeight: 570, fontSize: '22px' }}>
						{gettext('Inscription confirmée !')}
					</p>
					<p className="text-center mb-3" style={{ margin: 0, fontWeight: 520, fontSize: '12px' }}>
						{gettext('Pourriez-vous nous donner quelques détails sur vous ?')}
					</p>
					<div style={{ width: '85%', marginBottom: '4%' }}>
						<p className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext('Nom')}
						</p>
						<input
							style={{
								width: '100%',
								height: '14%',
								minHeight: '30px',
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
						<p className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext('Prénom')}
						</p>
						<input
							style={{
								width: '100%',
								height: '14%',
								minHeight: '30px',
								background: '#F6F7FB',
								borderColor: '#F6F7FB',
								margin: 0,
								borderRadius: '8px',
								whiteSpace: 'nowrap',
								boxShadow: 'none',
							}}
							type="text"
							onChange={(e) => this.setField('first_name', e.target.value)}
						/>
						<p className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext('Job')}
						</p>
						<select
							style={{ background: '#F6F7FB', borderColor: '#F6F7FB', margin: 0, borderRadius: '8px', whiteSpace: 'nowrap', boxShadow: 'none' }}
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
						<p className="mb-1" style={{ fontWeight: 520, fontSize: '14px' }}>
							{gettext('Téléphone')}
						</p>
						<input
							style={{
								width: '100%',
								height: '14%',
								minHeight: '30px',
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
					<div className="d-flex align-items-center justify-content-center flex-column" style={{ height: '100%', width: '100%' }}>
						<button
							className="d-flex align-items-center justify-content-center text-white"
							style={{
								border: '1px solid #000000',
								height: '20%',
								minHeight: '35px',
								maxHeight: '35px',
								width: '85%',
								borderColor: '#8888E2',
								backgroundColor: '#8888E2',
								borderRadius: '4px',
								fontWeight: 505,
								fontSize: '12px',
							}}
							onClick={() => this.fetchUpdateUser()}
						>
							{gettext('Accéder au Dashboard')}
						</button>
					</div>
				</div>
			</div>
		) : (
			<Loading message={this.state.placeholder} />
		);
	}
}

export default InvitationConfirmed;
