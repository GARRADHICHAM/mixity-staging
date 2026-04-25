import React, { Component } from 'react';
import { Modal } from 'react-bootstrap';
import CreateStructureForm from './components/CreateStructureForm';
import FetchCreateStructureButton from './components/FetchCreateStructureButton';
import CreateSubOptionForm from './components/CreateSubOptionForm';
import FetchCreateOptionsButton from './components/FetchCreateOptionsButton';
import FetchCheckCoupon from './components/FetchCheckCoupon';

class CreateStructure extends Component {
	constructor(props) {
		super(props);
		this.state = {
			// variables globales
			everythingLoaded: true,
			placeholder: gettext('Chargement'),
			show_error_modal: false,
			error_modal_message: '',
			user_name: '',
			// gestion de l'affichage de l'étape
			firstStepClass: '',
			secondStepClass: 'd-none',
			startPaymentStepClass: 'd-none',
			thirdStepClass: 'd-none',
			// variables utilisées pour le step1
			structure_pk: -1,
			entity_slug: '',
			fields: {
				organisation_name: '',
				siret: '',
				category: 'enterprise',
				country: '',
				phone: '',
				activity: '',
				employees: '',
				website: '',
			},
			coupon: '',
			// variables utilisées pour le step2
			product: 'diag',
		};
	}

	async componentDidMount() {
		await this.fetchGetUserName();
		this.setState({ everythingLoaded: true });
	}

	setErrorModalMessage = (message) => {
		this.setState({ error_modal_message: message });
	};

	setShowErrorModal = (value) => {
		this.setState({ show_error_modal: value });
	};

	fetchErrorMessage = (response) => {
		if (response.status > 400) {
			this.setState({ placeholder: gettext("Quelque chose s'est mal passé !") });
		}
	};

	fetchGetUserName = async () => {
		const response = await fetch(`/api/get_user_name/`, {
			method: 'GET',
			headers: {
				'Content-Type': 'application/json',
			},
		});
		if (response.status === 200) {
			const data = await response.json();
			this.setState({ user_name: data.first_name });
		} else {
			this.fetchErrorMessage(response);
		}
	};

	handleFieldsChange = (newFields) => {
		this.setState({ fields: newFields });
	};

	updateProduct = (product) => {
		this.setState({ product });
	};

	updateStepClass = (stepClass, value) => {
		this.setState({ [stepClass]: value });
	};

	setStructurePK = (pk) => {
		this.setState({ structure_pk: pk, firstStepClass: 'd-none', secondStepClass: '' });
	};
	setEntitySlug = (slug) => {
		this.setState({ entity_slug: slug });
	};

	render() {
		// const { everythingLoaded, firstStepClass, secondStepClass, startPaymentStepClass, thirdStepClass, show_error_modal, error_modal_message, user_name, fields, structure_pk, entity_slug, placeholder, product } = this.state;

		return this.state.everythingLoaded ? (
			<>
				{/* First Step */}
				<div className={`d-flex justify-content-center align-items-center ${this.state.firstStepClass}`} style={{ height: 'auto' }}>
					<Modal
						style={{ zIndex: 1200 }}
						show={this.state.show_error_modal}
						onHide={() => this.setShowErrorModal(false)}
						title={gettext('Erreur')}
						centered
					>
						<p className="text-center">{gettext(this.state.error_modal_message)}</p>
						<p className="text-center">
							{gettext("Si l'erreur persiste, veuillez ")}
							<a href={'https://www.mixity.io/contact'}>{gettext('prendre contact avec notre équipe')}</a>
						</p>
					</Modal>
					<div
						className="bg-white d-flex align-items-center flex-column"
						style={{ width: '55%', minWidth: '400px', height: 'auto', borderRadius: '16px' }}
					>
						<p className="text-center" style={{ marginBottom: '5px', fontWeight: 570, fontSize: '22px' }}>
							{gettext('Bonjour ')}
							{this.state.user_name}
							{' !'}
						</p>
						<p className="text-center mb-3" style={{ margin: 0, fontWeight: 520, fontSize: '12px' }}>
							{gettext('Renseignez les informations de la structure')}
						</p>
						<CreateStructureForm
							onFieldsChange={this.handleFieldsChange}
							fields={this.state.fields}
							csrftoken={csrftoken}
							setShowErrorModal={this.setShowErrorModal}
							setErrorModalMessage={this.setErrorModalMessage}
						/>
						<div className="d-flex align-items-center justify-content-center flex-column" style={{ height: '100%', width: '100%', margin: '3%' }}>
							<FetchCreateStructureButton
								fields={this.state.fields}
								csrftoken={csrftoken}
								buttonName={gettext('Créer la structure')}
								setShowErrorModal={this.setShowErrorModal}
								setErrorModalMessage={this.setErrorModalMessage}
								setStructurePK={this.setStructurePK}
								setEntitySlug={this.setEntitySlug}
								fetchErrorMessage={this.fetchErrorMessage}
							/>
						</div>
					</div>
				</div>
				{/* Second Step */}
				<div className={`d-flex justify-content-center align-items-center ${this.state.secondStepClass}`} style={{ height: 'auto' }}>
					<div
						className="bg-white d-flex align-items-center flex-column"
						style={{ width: '55%', minWidth: '400px', height: 'auto', borderRadius: '16px' }}
					>
						<p className="text-center" style={{ marginBottom: '5px', fontWeight: 570, fontSize: '22px' }}>
							{gettext('Bonjour ')}
							{this.state.user_name}
							{' !'}
						</p>
						<p className="text-center mb-3" style={{ margin: 0, fontWeight: 520, fontSize: '12px' }}>
							{gettext("Choisissez le.les option.s à appliquer au pack d'abonnement de la structure.")}
						</p>
						{/* Ici on affiche le formulaire de création d'options */}
						<CreateSubOptionForm product={this.state.product} updateProduct={this.updateProduct} />
						<div className="d-flex align-items-center justify-content-center flex-column" style={{ height: '100%', width: '100%', margin: '3%' }}>
							<FetchCreateOptionsButton
								product={this.state.product}
								structure_id={this.state.structure_pk}
								entity_slug={this.state.entity_slug}
								setShowErrorModal={this.setShowErrorModal}
								setErrorModalMessage={this.setErrorModalMessage}
								updateStepClass={this.updateStepClass}
							/>
						</div>
					</div>
				</div>
				{/* Start Payment Step */}
				<div className={`d-flex justify-content-center align-items-center ${this.state.startPaymentStepClass}`} style={{ height: 'auto' }}>
					<div
						className="bg-white d-flex align-items-center flex-column"
						style={{ width: '55%', minWidth: '400px', height: 'auto', borderRadius: '16px' }}
					>
						<p className="text-center" style={{ marginBottom: '5px', fontWeight: 570, fontSize: '22px' }}>
							{gettext('Bonjour ')}
							{this.state.user_name}
							{' !'}
						</p>
						<p className="text-center mb-3" style={{ margin: 0, fontWeight: 520, fontSize: '12px' }}>
							{gettext("Entrez votre coupon afin d'activer votre abonnement Mixity Start.")}
						</p>
						<div className="d-flex justify-content-between mb-3" style={{ width: '92%' }}>
							<label className="mb-1 d-flex flex-row align-items-center" style={{ fontWeight: 520, fontSize: '14px' }}>
								{gettext('Code Coupon')}
								<span style={{ color: '#DE3838', fontWeight: 520, fontSize: '14px', margin: 0 }}>*</span>
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
									onChange={(e) => this.setState({ coupon: e.target.value })}
								/>
							</div>
						</div>
						<div className="d-flex align-items-center justify-content-center flex-column" style={{ height: '100%', width: '100%', margin: '3%' }}>
							<FetchCheckCoupon
								coupon={this.state.coupon}
								structure_id={this.state.structure_pk}
								entity_slug={this.state.entity_slug}
								setShowErrorModal={this.setShowErrorModal}
								setErrorModalMessage={this.setErrorModalMessage}
								updateStepClass={this.updateStepClass}
							/>
						</div>
					</div>
				</div>
				{/* Third Step */}
				<div className={`d-flex justify-content-center align-items-center ${this.state.thirdStepClass}`} style={{ height: 'auto' }}>
					<div
						className="bg-white d-flex align-items-center flex-column"
						style={{ width: '55%', minWidth: '400px', height: 'auto', borderRadius: '16px' }}
					>
						<p className="text-center" style={{ marginBottom: '5px', fontWeight: 570, fontSize: '22px' }}>
							{gettext('Félicitations ')}
							{this.state.user_name}
							{' !'}
						</p>
						<p className="text-center mb-3" style={{ margin: 0, fontWeight: 520, fontSize: '12px' }}>
							{gettext('La création de la structure et de ses options est terminée.')}
						</p>
						<p className="mb-1 d-flex flex-row w-100 p-2" style={{ fontWeight: 520, fontSize: '14px' }}>
							<a className=" w-100 text-center mb-3" style={{ margin: 0, fontWeight: 520, fontSize: '12px' }} href={'/' + this.state.entity_slug}>
								{gettext('Retourner sur le dashboard')}
							</a>
						</p>
					</div>
				</div>
			</>
		) : (
			<h4 className="d-flex justify-content-center align-items-middle" style={{ marginTop: '40%' }}>
				{this.state.placeholder}
			</h4>
		);
	}
}

export default CreateStructure;
