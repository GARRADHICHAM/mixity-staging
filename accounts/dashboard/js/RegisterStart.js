import React, { Component } from 'react';
import { Modal } from 'react-bootstrap';
import CreateStructureForm from './components/CreateStructureForm';
import FetchCreateStructure from './components/FetchCreateStructureButton';

class RegisterStart extends Component {
	constructor(props) {
		super(props);
		this.state = {
			everythingLoaded: false,
			placeholder: gettext('Chargement'),
			show_error_modal: false,
			error_modal_message: '',
			user_name: '',
			structure_pk: -1,
			fields: {
				organisation_name: '',
				siret: '',
				category: '',
				address: '',
				phone: '',
				activity: '',
				employees: '',
				website: '',
			},
		};
	}

	async componentDidMount() {
		await this.fetchGetUserName();
		this.setState({ everythingLoaded: true });
	}

	setShowErrorModal = (value) => {
		this.setState({ show_error_modal: value });
	};

	setErrorModalMessage = (message) => {
		this.setState({ error_modal_message: message });
	};

	fetchErrorMessage(response) {
		if (response.status > 400) {
			this.setState({ placeholder: gettext("Quelque chose s'est mal passé !") });
		}
	}

	async fetchGetUserName() {
		try {
			const response = await fetch(`/api/get_user_name/`, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
				},
			});
			if (response.ok) {
				const data = await response.json();
				this.setState({ user_name: data.first_name });
			} else {
				this.fetchErrorMessage(response);
			}
		} catch (error) {
			console.error('Error fetching user name:', error);
			this.fetchErrorMessage(error);
		}
	}

	handleFieldsChange = (newFields) => {
		this.setState({ fields: newFields });
	};

	setStructurePK = (structureId) => {
		this.setState({ structure_pk: structureId }, () => {
			this.fetchCreateSubscriptionOption();
		});
	};

	async fetchCreateSubscriptionOption() {
		try {
			const { structure_pk, fields } = this.state;
			const subOptionResponse = await fetch(`/api/create_sub_start_option/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': csrftoken,
				},
				body: JSON.stringify({ siret: fields.siret, structure_pk }),
			});

			if (subOptionResponse.ok) {
				// Utilisez structure_pk pour la redirection
				window.location.href = '/payments/' + structure_pk + '/pay/';
			} else {
				this.fetchErrorMessage(subOptionResponse);
			}
		} catch (error) {
			console.error('Error creating subscription option:', error);
			this.setShowErrorModal(true);
			this.setErrorModalMessage(gettext("Une erreur est survenue lors de la création de l'option d'abonnement."));
		}
	}

	render() {
		const { everythingLoaded, user_name, fields, show_error_modal, error_modal_message, placeholder } = this.state;

		return everythingLoaded ? (
			<div className="d-flex justify-content-center align-items-center" style={{ height: 'auto' }}>
				<Modal style={{ zIndex: 1200 }} show={show_error_modal} onHide={() => this.setShowErrorModal(false)} title={gettext('Erreur')} centered>
					<p className="text-center">{error_modal_message}</p>
				</Modal>
				<div
					className="bg-white d-flex align-items-center flex-column"
					style={{ width: '55%', minWidth: '400px', height: 'auto', borderRadius: '16px' }}
				>
					<p className="text-center" style={{ marginBottom: '5px', fontWeight: 570, fontSize: '22px' }}>
						{gettext('Bonjour ')}
						{user_name}
						{' !'}
					</p>
					<p className="text-center mb-3" style={{ margin: 0, fontWeight: 520, fontSize: '12px' }}>
						{gettext('Pourriez-vous nous décrire votre organisation ?')}
					</p>
					<CreateStructureForm
						onFieldsChange={this.handleFieldsChange}
						fields={this.state.fields}
						csrftoken={csrftoken}
						setShowErrorModal={this.setShowErrorModal}
						setErrorModalMessage={this.setErrorModalMessage}
					/>
					<div className="d-flex align-items-center justify-content-center flex-column" style={{ height: '100%', width: '100%', margin: '3%' }}>
						<FetchCreateStructure
							fields={fields}
							csrftoken={csrftoken}
							buttonName={gettext('Payer avec Stripe')}
							setShowErrorModal={this.setShowErrorModal}
							setErrorModalMessage={this.setErrorModalMessage}
							setStructurePK={this.setStructurePK}
							fetchErrorMessage={this.fetchErrorMessage}
						/>
					</div>
				</div>
			</div>
		) : (
			<h4 className="d-flex justify-content-center align-items-middle" style={{ marginTop: '40%' }}>
				{placeholder}
			</h4>
		);
	}
}

export default RegisterStart;
