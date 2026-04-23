import React, { Component } from 'react';
import { Breadcrumb, Form } from 'react-bootstrap';
import { Modal } from 'react-bootstrap';
import Header from '../../../mixity/dashboard/js/includes/Header';
import Nav from 'react-bootstrap/Nav';
import EntitiesSelect from './components/EntitiesSelect';
import UploadTemplateCollaboratorsCSV from './components/UploadTemplateCollaboratorsCSV';
import ImporterCollaboratorsCSV from './components/ImporterCollaboratorsCSV';
import UploadTemplateEntitiesCSV from './components/UploadTemplateEntitiesCSV';
import ImporterEntitiesCSV from './components/ImporterEntitiesCSV';
import NotificationLoader from '../../../mixity/dashboard/js/includes/NotificationLoader';
import SavePopup from './components/SavePopup';

class StructureUpdate extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to front-end display
			everythingLoaded: false,
			placeholder: gettext('Chargement'),

			show_error_modal: false,
			error_modal_message: '',

			is_staff: '',
			is_owner: '',

			activity_description: '',
			human_description: '',
			commitment_description: '',

			showAddCollaboratorBox: false,

			collaborators: [],
			current_delete_collaborator: {},
			show_collaborator_delete_validation: false,
			selected_entity: '',
			show_entities_modal: false,

			entities_list: [],

			emptyAddCollaboratorFields: {
				field_name: 'Email du collaborateur:',
				field_type: 'text',
				field_value: '',
				second_field_name: 'Entité(s) rattaché(es) au collaborateur:',
				second_field_type: 'entity-select',
				second_field_value: '',
				entities: [],
			},

			addCollaboratorsFields: [],

			currentCollaboratorsField: {
				field_name: 'Email du collaborateur:',
				field_type: 'text',
				field_value: '',
				second_field_name: 'Entité(s) rattaché(es) au collaborateur:',
				second_field_type: 'entity-select',
				second_field_value: '',
				entities: [],
			},

			activeKey: '',

			activeKeyMapping: {
				structure: 'link-1',
				entity: 'link-3',
				collaborators: 'link-4',
			},

			EntityInputsMappings: {
				social_name: 'entity_name',
				creation_year: 'creation_year',
				workforce: 'workforce',
				phone: 'phone',
			},

			InputsMappings: {
				juridic_name: 'juridic_name',
				category: 'category',
				logo: 'logo',
				workforce: 'workforce',
				business_line: 'business_line',
				secondary_business_lines: 'secondary_business_lines',
				website: 'website',
				phone: 'phone',
			},

			business_lines: [],

			category_key: {
				Entreprise: 'enterprise',
				Événement: 'event',
				Association: 'non_profit_organization',
				École: 'school',
				'Collectivité locale': 'public_institution',
				enterprise: 'Entreprise',
				event: 'Événement',
				non_profit_organization: 'Association',
				school: 'École',
				public_institution: 'Collectivité locale',
			},

			EntityInputs: [
				{
					field: 'social_name',
					field_name: gettext('Dénomination social'),
					field_type: 'text',
					base_value: '',
					value: '',
					url: '',
					placeholder: '',
					is_needed: true,
				},
				{
					field: 'creation_year',
					field_name: gettext('Année de création'),
					field_type: 'text',
					base_value: '',
					value: '',
					url: '',
					placeholder: '',
					is_needed: false,
				},
				{
					field: 'workforce',
					field_name: gettext('Effectifs'),
					field_type: 'text',
					base_value: '',
					value: '',
					url: '',
					placeholder: '',
					is_needed: true,
				},
				{
					field: 'phone',
					field_name: gettext('Téléphone'),
					field_type: 'text',
					base_value: '',
					value: '',
					url: '',
					placeholder: '',
					is_needed: true,
				},
			],

			Inputs: [
				{
					field: 'juridic_name',
					field_name: gettext('Dénomination sociale'),
					field_type: 'text',
					base_value: '',
					value: '',
					url: '',
					placeholder: '',
					is_needed: true,
				},
				{
					field: 'category',
					field_name: gettext('Catégorie'),
					field_type: 'select',
					base_value: '',
					value: '',
					url: '',
					field_list: [
						{ id: 1, name: 'Entreprise' },
						{ id: 2, name: 'Événement' },
						{ id: 3, name: 'Association' },
						{ id: 4, name: 'École' },
						{ id: 5, name: 'Collectivité locale' },
					],
					placeholder: '',
					is_needed: true,
				},
				{
					field: 'logo',
					field_name: gettext('Logo'),
					field_type: 'file',
					base_value: null,
					value: null,
					url: '',
					placeholder: gettext('Chemin du fichier'),
					is_needed: false,
				},
				{
					field: 'workforce',
					field_name: gettext('Effectifs'),
					field_type: 'text',
					base_value: '',
					value: '',
					url: '',
					placeholder: '',
					is_needed: true,
				},
				{
					field: 'business_line',
					field_name: gettext("Secteur d'activité"),
					field_type: 'select',
					base_value: '',
					value: '',
					url: '',
					field_list: [],
					placeholder: '',
					is_needed: true,
				},
				{
					field: 'secondary_business_lines',
					field_name: gettext("Secteurs d'activité secondaires"),
					field_type: 'multi-select',
					base_value: '',
					value: '',
					url: '',
					field_list: [],
					placeholder: '',
					is_needed: false,
				},
				{
					field: 'website',
					field_name: gettext('Site web'),
					field_type: 'text',
					base_value: '',
					value: '',
					url: '',
					placeholder: '',
					is_needed: true,
				},
				{
					field: 'phone',
					field_name: gettext('Téléphone'),
					field_type: 'text',
					base_value: '',
					value: '',
					url: '',
					placeholder: '',
					is_needed: true,
				},
			],
			showPopup: false,
			notification_is_active: false,
			csvFormData: null,
		};
	}

	async componentDidMount() {
		try {
			await this.userIsStaff();
			await this.getProfile();
			await this.getEntitiesList();
			await this.getBusinessLines();
			await this.getCollaborators();
			await this.getStructureDescription();
			this.setupBaseValues();
			this.setupEntitiesBaseValues();
			this.setState(() => {
				return {
					activeKey: this.state.activeKeyMapping[page_category],
				};
			});
			this.setState(() => {
				return {
					everythingLoaded: true,
					Inputs: this.state.Inputs.map((input) => {
						if (input.field === 'business_line' || input.field === 'secondary_business_lines') {
							return {
								...input,
								field_list: this.state.business_lines,
							};
						}
						return input;
					}),
				};
			});
		} catch (error) {
			console.error('>>>>> ERROR in StructureUpdate: ', error);
			this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext("Quelque chose s'est mal passé !"),
				};
			});
		}
	}

	handleNavSelect = (selectedKey) => {
		this.setState({ activeKey: selectedKey });
	};

	setupEntitiesBaseValues = (entity_name = this.state.selected_entity) => {
		let new_entities = this.state.EntityInputs;
		let entityData = this.state.collaborators.filter((entity) => entity.entity_name === entity_name)[0];
		Object.keys(this.state.EntityInputsMappings).forEach((key) => {
			new_entities = new_entities.map((input) => {
				if (input.field === key) {
					if (
						entityData[this.state.EntityInputsMappings[key]] !== 'None' &&
						entityData[this.state.EntityInputsMappings[key]] !== 'undefined' &&
						entityData[this.state.EntityInputsMappings[key]] !== null
					) {
						return {
							...input,
							base_value: entityData[this.state.EntityInputsMappings[key]],
							value: entityData[this.state.EntityInputsMappings[key]],
						};
					} else {
						return {
							...input,
							base_value: '',
							value: '',
						};
					}
				}
				return input;
			});
		});
		this.setState(() => {
			return {
				EntityInputs: new_entities,
			};
		});
	};

	setupBaseValues = () => {
		let new_inputs = this.state.Inputs;

		Object.keys(this.state.InputsMappings).forEach((key) => {
			new_inputs = new_inputs.map((input) => {
				if (input.field === key && structure_infos[key] !== 'None' && structure_infos[key] !== 'undefined') {
					if (key !== 'logo') {
						return {
							...input,
							base_value: structure_infos[key],
							value: structure_infos[key],
						};
					}
				}
				return input;
			});
		});

		new_inputs[1].value = this.state.category_key[structure_infos['category']];
		new_inputs[1].base_value = this.state.category_key[structure_infos['category']];

		new_inputs[3].base_value = structure_infos['workforce'].replace(/\xa0/g, '');
		new_inputs[3].value = structure_infos['workforce'].replace(/\xa0/g, '');

		new_inputs[5].value = '';
		new_inputs[5].base_value = '';

		this.setState(() => {
			return {
				Inputs: new_inputs,
			};
		});
	};

	setCollaboratorField = (index, value) => {
		this.setState(() => {
			return {
				addCollaboratorsFields: this.state.addCollaboratorsFields.map((field, i) => {
					if (i === index) {
						return {
							...field,
							field_value: value,
						};
					}
					return field;
				}),
			};
		});
	};

	setEntityInfos = (value) => {
		this.setState(() => {
			return {
				selected_entity: value,
			};
		});
		this.setupEntitiesBaseValues(value);
	};

	isEveryNeededFieldFilledEntity() {
		let isFilled = true;
		this.state.EntityInputs.forEach((input) => {
			if (input.is_needed && input.value === '') {
				isFilled = false;
			}
		});
		return isFilled;
	}

	UpdateEntityInfos = async () => {
		if (!this.isEveryNeededFieldFilledEntity()) {
			this.setShowErrorModal(true);
			return this.setState(() => {
				return {
					error_modal_message: gettext('Veuillez remplir tous les champs obligatoires.'),
				};
			});
		}
		try {
			const formData = new FormData();
			formData.append('siret', structure_infos['SIRET']);
			formData.append('duns', structure_infos['DUNS']);
			formData.append('entity_name', this.state.selected_entity);
			formData.append('social_name', this.state.EntityInputs[0].value);
			formData.append('creation_year', this.state.EntityInputs[1].value);
			formData.append('workforce', this.state.EntityInputs[2].value);
			formData.append('phone', this.state.EntityInputs[3].value);

			const response = await fetch(`/api/update_entity_infos/`, {
				method: 'POST',
				headers: {
					'X-CSRFToken': csrftoken,
				},
				body: formData,
			});
			this.fetchErrorMessage(response);
			const data = await response.json();
			alert(gettext("Les informations de l'entité ont été mises à jour avec succès."));
		} catch (error) {
			console.error('>>>>> ERROR in update_entity_infos: ', error);
			this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext("Quelque chose s'est mal passé !"),
				};
			});
		}
	};

	setEntityField = (field, value) => {
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
		if (field == 'workforce' && (value.length > 10 || /[^0-9]/.test(value))) {
			this.setShowErrorModal(true);
			return this.setState(() => {
				return {
					error_modal_message: gettext("L'effectifs doit être composé uniquement de chiffres."),
				};
			});
		}
		if (field == 'creation_year' && /[^0-9]/.test(value)) {
			this.setShowErrorModal(true);
			return this.setState(() => {
				return {
					error_modal_message: gettext("L'année de création doit être composée uniquement de chiffres."),
				};
			});
		}
		this.setState((prevState) => {
			return {
				EntityInputs: prevState.EntityInputs.map((input) => {
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
		if (field == 'workforce' && (value.length > 10 || /[^0-9]/.test(value))) {
			this.setShowErrorModal(true);
			return this.setState(() => {
				return {
					error_modal_message: gettext("L'effectifs doit être composé uniquement de chiffres."),
				};
			});
		}
		if (field == 'SIRET' && (value.length > 14 || /[^0-9]/.test(value))) {
			this.setShowErrorModal(true);
			return this.setState(() => {
				return {
					error_modal_message: gettext('Le SIRET doit être composé de 14 chiffres.'),
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

	setShowCollaboratorDeleteValidation = (value) => {
		this.setState(() => {
			return {
				show_collaborator_delete_validation: value,
			};
		});
	};

	setShowEntitiesModal = (value, currentCollaboratorsField) => {
		this.setState(() => {
			return {
				show_entities_modal: value,
				currentCollaboratorsField: currentCollaboratorsField,
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

	handleRadioChange = async (e, collaborator) => {
		if (e.target.value === 'owner') {
			collaborator.is_owner = true;
			collaborator.is_reader = false;
		} else if (e.target.value === 'member') {
			collaborator.is_owner = false;
			collaborator.is_reader = false;
		} else {
			collaborator.is_owner = false;
			collaborator.is_reader = true;
		}
		this.setState(() => {
			return {
				collaborators: this.state.collaborators.map((collaboratorSeek) => {
					if (collaboratorSeek.email === collaborator.email) {
						return collaborator;
					}
					return collaboratorSeek;
				}),
			};
		});
		try {
			const response = await fetch(`/api/update_collaborator/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': csrftoken,
				},
				body: JSON.stringify({
					email: collaborator.email,
					is_owner: collaborator.is_owner,
					is_reader: collaborator.is_reader,
					siret: structure_infos['SIRET'],
					duns: structure_infos['DUNS'],
					entity_name: this.state.selected_entity,
				}),
			});
			this.fetchErrorMessage(response);
			await response.json();
		} catch (error) {
			console.error('>>>>> ERROR in handleRadioChange: ', error);
			this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext("Quelque chose s'est mal passé !"),
				};
			});
		}
	};

	is_collaborators_in_entity = () => {
		let hasCollaborators = false;

		this.state.collaborators.forEach((entity) => {
			if (entity.entity_name === this.state.selected_entity) {
				if (entity.collaborators.length > 0) {
					hasCollaborators = true;
				}
			}
		});

		return hasCollaborators;
	};

	deleteCollaborator = async (collaborator) => {
		try {
			const response = await fetch(`/api/delete_collaborator/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': csrftoken,
				},
				body: JSON.stringify({
					email: collaborator.email,
					siret: structure_infos['SIRET'],
					duns: structure_infos['DUNS'],
					entity_name: this.state.selected_entity,
				}),
			});
			this.fetchErrorMessage(response);
			this.setState({ collaborators: [] });
			const data = await response.json();
			this.setState({ collaborators: data });
		} catch (error) {
			console.error('>>>>> ERROR in deleteCollaborator: ', error);
			this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext("Quelque chose s'est mal passé !"),
				};
			});
		}
	};

	userIsStaff = async () => {
		try {
			const response = await fetch(`/api/membership/`, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': csrftoken,
				},
			});
			this.fetchErrorMessage(response);
			const data = await response.json();
			this.setState(() => {
				return {
					is_staff: data.is_staff,
					is_owner: data.is_owner,
				};
			});
		} catch (error) {
			console.error('>>>>> ERROR in userIsStaff : ', error);
			this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext("Quelque chose s'est mal passé !"),
				};
			});
		}
	};

	getCollaborators = async () => {
		try {
			const response = await fetch(`/api/get_collaborators/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': csrftoken,
				},
				body: JSON.stringify({
					siret: structure_infos['SIRET'],
					duns: structure_infos['DUNS'],
				}),
			});
			this.fetchErrorMessage(response);
			const data = await response.json();
			this.setState(() => {
				return {
					selected_entity: data[0].entity_name,
					collaborators: data,
				};
			});
		} catch (error) {
			console.error('>>>>> ERROR in getCollaborators: ', error);
			this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext("Quelque chose s'est mal passé !"),
				};
			});
		}
	};

	getBusinessLines = async () => {
		try {
			const response = await fetch(`/api/get_business_lines/`, {
				method: 'GET',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': csrftoken,
				},
			});
			this.fetchErrorMessage(response);
			const data = await response.json();
			this.setState(() => {
				return {
					business_lines: data,
				};
			});
		} catch (error) {
			console.error('>>>>> ERROR in getBusinessLines: ', error);
			this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext("Quelque chose s'est mal passé !"),
				};
			});
		}
	};

	getEntitiesList = async () => {
		try {
			const siret = structure_infos['SIRET'];
			const duns = structure_infos['DUNS'];
			const response = await fetch(`/api/get_structure_entities/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'X-CSRFToken': csrftoken,
				},
				body: JSON.stringify({
					siret: siret,
					duns: duns,
				}),
			});
			this.fetchErrorMessage(response);
			const data = await response.json();
			this.setState(() => {
				return {
					entities_list: data[0],
				};
			});
		} catch (error) {
			console.error('>>>>> ERROR in getEntitiesList: ', error);
			this.setState(() => {
				return {
					show_error_modal: true,
					error_modal_message: gettext("Quelque chose s'est mal passé !"),
				};
			});
		}
	};

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

	deepCopy = (obj) => {
		if (typeof obj !== 'object' || obj === null) {
			return obj;
		}

		let copy;
		if (Array.isArray(obj)) {
			copy = [];
			for (let i = 0; i < obj.length; i++) {
				copy[i] = this.deepCopy(obj[i]);
			}
		} else {
			copy = {};
			for (let key in obj) {
				if (obj.hasOwnProperty(key)) {
					copy[key] = this.deepCopy(obj[key]);
				}
			}
		}
		return copy;
	};

	setAddCollaboratorDisplay = () => {
		const empty_collaboratorsFields = this.deepCopy(this.state.emptyAddCollaboratorFields);
		empty_collaboratorsFields.entities = this.deepCopy(this.state.entities_list);
		const new_addCollaboratorsFields = [empty_collaboratorsFields];
		this.setState(() => {
			return {
				showAddCollaboratorBox: !this.state.showAddCollaboratorBox,
				addCollaboratorsFields: new_addCollaboratorsFields,
			};
		});
	};

	addCollaboratorsFields = () => {
		const emptyAddCollaboratorFields_dup = this.deepCopy(this.state.emptyAddCollaboratorFields);
		emptyAddCollaboratorFields_dup.entities = this.deepCopy(this.state.entities_list);

		this.setState(() => {
			return {
				addCollaboratorsFields: [...this.state.addCollaboratorsFields, emptyAddCollaboratorFields_dup],
			};
		});
	};

	inviteCollaborators = async () => {
		const collaborators = this.state.addCollaboratorsFields;
		let collaboratorsToSend = [];
		collaborators.forEach((collaborator) => {
			let entities = this.getSelectedEntities([collaborator.entities]);
			if (collaborator.field_value === '' || entities.length === 0) {
				return;
			}
			collaboratorsToSend.push({
				email: collaborator.field_value,
				entity: entities[0],
			});
		});

		const response = await fetch(`/api/invite_collaborators/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': csrftoken,
			},
			body: JSON.stringify({
				collaborators: collaboratorsToSend,
				siret: structure_infos['SIRET'],
				duns: structure_infos['DUNS'],
			}),
		});
		this.fetchErrorMessage(response);
		const data = await response.json();
		this.setState(() => {
			return {
				showAddCollaboratorBox: false,
				addCollaboratorsFields: [],
			};
		});
		await this.getCollaborators();
	};

	inviteCollaboratorIsDisabled() {
		var return_value = false;
		this.state.addCollaboratorsFields.map((collab) => {
			if (collab.field_value === '' || this.getSelectedEntities([collab.entities]).length === 0) {
				return_value = true;
			}
		});
		return return_value;
	}

	handleStructureUpdate = async () => {
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
			formData.append('old_siret', structure_infos['SIRET']);
			formData.append('juridic_name', this.state.Inputs[0].value);
			formData.append('category', this.state.category_key[this.state.Inputs[1].value]);
			if (this.state.Inputs[2].value) {
				var picture = this.state.Inputs[2].value;
				const truncatedName = picture.name.substring(0, 60) + picture.name.substring(picture.name.length - 5);
				const newPicture = new File([picture], truncatedName, { type: picture.type });
				formData.append('logo', newPicture);
			}
			formData.append('workforce', this.state.Inputs[3].value);
			formData.append('business_line', this.state.Inputs[4].value);
			formData.append('secondary_business_lines', this.state.Inputs[5].value);
			formData.append('website', this.state.Inputs[6].value);
			formData.append('phone', this.state.Inputs[7].value);

			const response = await fetch(`/api/update_structure/`, {
				method: 'PATCH',
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
			console.error('>>>>> ERROR in handleStructureUpdate: ', error);
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

	unSelectAllEntities(field) {
		field.entities = [field.entities]
		const unselectAllChildrens = (childrens) => {
			childrens.forEach((child) => {
				child.selected = false;
				child.disabled = false;
				if (child.childrens && child.childrens.length > 0) {
					unselectAllChildrens(child.childrens);
				}
			});
		};

		for (let i = 0; i < field.entities.length; i++) {
			field.entities[i].selected = false;
			if (field.entities[i].childrens && field.entities[i].childrens.length > 0) {
				unselectAllChildrens(field.entities[i].childrens);
			}
		}

		this.setState(() => {
			return {
				Inputs: this.state.Inputs.map((input) => {
					if (input.field === field.field) {
						return {
							...input,
							entities: field.entities,
						};
					}
					return input;
				}),
			};
		});
	}

	unselectEntity = (field, entity_name) => {
		var entities = [field.entities]
		const disableChildrens = (childrens) => {
			childrens.forEach((child) => {
				child.selected = false;
				child.disabled = false;
				disableChildrens(child.childrens)
			})
		}
		const unselectChildrens = (childrens) => {
			childrens.forEach((child) => {
				if (child.label === entity_name) {
					child.selected = false;
					child.disabled = false;
					disableChildrens(child.childrens)
					return;
				}
				if (child.childrens && child.childrens.length > 0) {
					unselectChildrens(child.childrens);
				}
			});
		};
		for (let i = 0; i < entities.length; i++) {
			if (entities[i].label === entity_name) {
				entities[i].selected = false;
				entities[i].disabled = false;
				disableChildrens(entities[i].childrens)
			}
			if (entities[i].childrens && entities[i].childrens.length > 0) {
				unselectChildrens(entities[i].childrens);
			}
		}
		field.entities = entities[0]
		this.setState(() => {
			return {
				Inputs: this.state.Inputs.map((input) => {
					if (input.field === field.field) {
						return {
							...input,
							entities: field.entities,
						};
					}
					return input;
				}),
			};
		});
	};

	getSelectedEntities = (entities) => {
		var selectedEntities = [];

		entities.forEach((entity) => {
			if (entity.selected) {
				selectedEntities.push(entity.label);
			}
			if (entity.childrens && entity.childrens.length > 0) {
				selectedEntities = selectedEntities.concat(this.getSelectedEntities(entity.childrens));
			}
		});
		return selectedEntities;
	};

	SelectedEntitiesTags = ({ field }) => {
		var entities = [field.entities]
		if (!field.entities || entities.length === 0) {
			return null;
		}

		const selectedEntities = this.getSelectedEntities(entities);

		if (field.selected) {
			selectedEntities.push(field.label);
		}

		if (selectedEntities.length === 0) {
			return null;
		}
		return selectedEntities.map((entity, index) => (
			<div
				key={index}
				className="d-flex align-items-center justify-content-center"
				style={{
					whiteSpace: 'nowrap',
					width: 'fit-content',
					height: 'fit-content',
					padding: '8px 16px 8px 10px',
					backgroundColor: '#8888E219',
					color: '#8888E2',
					borderRadius: '4px',
				}}
			>
				<i
					onClick={() => {
						this.unselectEntity(field, entity);
					}}
					className="bi bi-x d-flex align-items-center"
					style={{ color: '#8888E2', padding: '0 0 0 0', margin: '0 12px 0 0', cursor: 'pointer' }}
				></i>
				<div>{entity}</div>
			</div>
		));
	};

	getStructureDescription = async () => {
		const response = await fetch(`/api/get_structure_description/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': csrftoken,
			},
			body: JSON.stringify({
				siret: structure_infos['SIRET'],
				duns: structure_infos['DUNS'],
			}),
		});
		this.fetchErrorMessage(response);
		const data = await response.json();
		this.setState(() => {
			return {
				activity_description: data.activity_description,
				human_description: data.human_description,
				commitment_description: data.commitment_description,
			};
		});
	};

	updateStructureDescription = async () => {
		const response = await fetch(`/api/update_structure_description/`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': csrftoken,
			},
			body: JSON.stringify({
				siret: structure_infos['SIRET'],
				duns: structure_infos['DUNS'],
				activity_description: this.state.activity_description,
				human_description: this.state.human_description,
				commitment_description: this.state.commitment_description,
			}),
		});
		this.fetchErrorMessage(response);
		await response.json();
		alert(gettext('Les descriptions ont été mises à jour avec succès.'));
	};

	selectedEntitiesCount = (entities) => {
		let count = 0;

		entities.forEach((entity) => {
			if (entity.selected) {
				count += 1;
			}
			if (entity.childrens && entity.childrens.length > 0) {
				count += this.selectedEntitiesCount(entity.childrens);
			}
		});
		return count;
	};

	handleCSVImport = (formData) => {
		this.setState({
			csvFormData: formData,
			notification_is_active: true,
		});
	};

	handleRequestComplete = (isActive) => {
		this.setState({ notification_is_active: isActive });
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
              a.nav-link.active {
                color: #181B3D;
                font-weight: 550;
                padding-left: 0;
                border-bottom: 3px solid #181B3D;
                margin-right: 1.5rem;
              }
              a.nav-link {
                color: #777E90;
                font-weight: 550;
                padding-left: 0;
                padding-right: 0;
                margin-right: 1.5rem;
              }
              a.nav-link:hover {
                color: #181B3D;
                font-weight: 550;
                padding-left: 0;
                padding-right: 0;
                margin-right: 1.5rem;
                border-bottom: 3px solid #181B3D;
              }
              .input-grid {
                display: grid;
                grid-template-columns: 4.8fr 4.8fr;
                column-gap: 35px;
              }
              .no-hover:hover {
                box-shadow: none !important;
              }
              .no-hover:active {
                box-shadow: none !important;
              }
              .collaborator_grid {
                display: grid;
                grid-template-columns: repeat(6, 1fr);
                width: 100%;
                margin: 0 auto;
                background-color: #FFF;
              }
              .collaborator_header_cell {
                background: #F6F7FB;
                padding: 8% 9% 8% 9%;
                text-align: left;
                font-weight: 500;
               }
              .collaborator_cell {
                border-bottom: 1px solid #E6E8EC;
                padding: 8% 9% 8% 9%;
                text-align: left;
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
							<strong>{gettext('Informations de la structure')}</strong>
						</Breadcrumb.Item>
					</Breadcrumb>
					<Header data={{ url: '/', languages: languages, language_code: language_code, enabled_website_languages: enabled_website_languages }} />
				</div>
				<Nav
					style={{ margin: '3%', width: 'auto', borderBottom: '2px solid #777E90' }}
					defaultActiveKey={this.state.activeKey}
					onSelect={this.handleNavSelect}
				>
					{structure_infos.is_owner && (
						<>
							<Nav.Item>
								<Nav.Link eventKey="link-1">{gettext('Structure')}</Nav.Link>
							</Nav.Item>
							<Nav.Item>
								<Nav.Link eventKey="link-2">{gettext('Fiche entreprise')}</Nav.Link>
							</Nav.Item>
						</>
					)}
					{this.state.collaborators.length > 0 && (
						<>
							<Nav.Item>
								<Nav.Link eventKey="link-3">{gettext('Entités')}</Nav.Link>
							</Nav.Item>
							<Nav.Item>
								<Nav.Link className="last-nav-link" eventKey="link-4">
									{gettext('Collaborateurs')}
								</Nav.Link>
							</Nav.Item>
						</>
					)}
				</Nav>

				{/* Notification pour les invitations collaborateurs */}
				<NotificationLoader
					apiUrl={'/api/upload_collaborators_csv/'}
					method="POST"
					is_active={this.state.notification_is_active}
					onRequestComplete={this.handleRequestComplete}
					formData={this.state.csvFormData}
				/>
				{this.state.activeKey === 'link-1' ? (
					<div>
						<p style={{ margin: '3%', fontWeight: 700, fontSize: '130%' }}>{gettext('Informations de la structure')}</p>
						<div style={{ margin: '3% 3% 0 3%' }}>
							<div style={{ width: '100%', backgroundColor: '#FFFFFF', marginBottom: '2.5%', borderRadius: '16px', border: '1px solid #DEDFEA' }}>
								<div style={{ margin: '3%' }}>
									<p style={{ fontWeight: 600 }}>{gettext('Modifier les informations de la structure')}</p>
									<div className="input-grid">
										{this.state.Inputs.map((input, index) => (
											<div className="mb-3" key={input.field}>
												<label style={{ fontWeight: 550 }} htmlFor={input.field} className="form-label d-flex">
													{input.field_name}
													{input.is_needed && <div style={{ color: 'red', margin: '0 0 0 3px', padding: 0 }}>*</div>}
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
															<input
																type="text"
																className="form-control"
																style={{ backgroundColor: '#F6F7FB', border: 0, color: '#777E90' }}
																value={input.value?.name}
																placeholder={input.placeholder}
																disabled
															/>
														</div>
														<input
															type="file"
															className="form-control"
															id={input.field}
															accept=".png, .jpg, .jpeg, .svg"
															onChange={(e) => {
																this.setField(input.field, e.target.files[0]);
																this.setUrl(input.field, URL.createObjectURL(e.target.files[0]));
															}}
														/>
													</div>
												) : input.field_type === 'multi-select' ? (
													<div className="d-flex" style={{ width: '100%', whiteSpace: 'nowrap' }}>
														<Form.Select
															style={{ borderRadius: '6px 0 0 6px' }}
															className="form-select"
															id={input.field}
															value={input.value}
															onChange={(e) => this.setField(input.field, e.target.value)}
														>
															<option key="default" value="">{gettext('--------------------')}</option>
															{input.field_list.map((option) => (
																<option key={option.pk} value={option.name}>
																	{option.name}
																</option>
															))}
														</Form.Select>
														<button
															type="button"
															style={{
																backgroundColor: '#8888E2',
																color: '#FFFFFF',
																borderRadius: '0 6px 6px 0',
																border: '1px solid #DEDFEA',
																padding: '0 3%',
															}}
															onClick={this.handleStructureUpdate}
														>
															{gettext('+ Ajouter')}
														</button>
													</div>
												) : input.field_type === 'select' ? (
													<Form.Select
														className="form-select"
														id={input.field}
														value={input.value}
														onChange={(e) => this.setField(input.field, e.target.value)}
													>
														<option key="default" value="">{gettext('--------------------')}</option>
														{input.field_list.map((option) => (
															<option key={option.pk} value={option.name}>
																{option.name}
															</option>
														))}
													</Form.Select>
												) : (
													<input
														type={input.field_type}
														className="form-control"
														id={input.field}
														value={input.value}
														placeholder={input.placeholder}
														onChange={(e) => this.setField(input.field, e.target.value)}
													/>
												)}
											</div>
										))}
									</div>
									<button
										type="button"
										className="btn"
										style={{
											backgroundColor: '#FFFFFF',
											color: '#000000',
											borderRadius: '6px',
											border: '1px solid #DEDFEA',
											margin: '1% 0 0 0',
										}}
										onClick={this.handleStructureUpdate}
									>
										{gettext('Valider les modifications')}
									</button>
								</div>
								{/* </div>
                    <Nav style={{ margin: "3%", width: "auto", borderBottom: "2px solid #777E90" }} defaultActiveKey={this.state.activeKey} onSelect={this.handleNavSelect}>
                        {structure_infos["is_owner"] &&
                            <>
                                <Nav.Item>
                                    <Nav.Link eventKey="link-1">{gettext("Structure")}</Nav.Link>
                                </Nav.Item>
                                <Nav.Item>
                                    <Nav.Link eventKey="link-2">{gettext("Fiche entreprise")}</Nav.Link>
                                </Nav.Item>
                            </>
                        }
                        {this.state.collaborators.length > 0 &&
                            <>
                                <Nav.Item>
                                    <Nav.Link eventKey="link-3">{gettext("Entitées")}</Nav.Link>
                                </Nav.Item>
                                <Nav.Item>
                                    <Nav.Link className="last-nav-link" eventKey="link-4">{gettext("Collaborateurs")}</Nav.Link>
                                </Nav.Item>
                            </>
                        }
                    </Nav>
                    {this.state.activeKey === "link-1" ?
                        <div>
                            <p style={{ margin: "3%", fontWeight: 700, fontSize: "130%" }}>{gettext("Informations de la structure")}</p>
                            <div style={{ margin: "3% 3% 0 3%" }}>
                                <div style={{ width: "100%", backgroundColor: "#FFFFFF", marginBottom: "2.5%", borderRadius: "16px", border: "1px solid #DEDFEA" }}>
                                    <div style={{ margin: "3%" }}>
                                        <p style={{ fontWeight: 600 }}>{gettext("Modifier les informations de la structure")}</p>
                                        <div className="input-grid">
                                            {this.state.Inputs.map((input, index) => (
                                                <div className="mb-3" key={input.field}>
                                                    <label style={{ fontWeight: 550 }} htmlFor={input.field} className="form-label d-flex">
                                                        {input.field_name}
                                                        {input.is_needed && <div style={{ color: "red", margin: "0 0 0 3px", padding: 0 }}>*</div>}
                                                    </label>
                                                    {input.field_type === "file" ? (
                                                        <div>
                                                            <div className="d-flex flex-row" style={{ whiteSpace: "nowrap" }}>
                                                                <label className="d-flex align-items-center" htmlFor={input.field} style={{ cursor: "pointer", backgroundColor: "#8888E2", border: "1px solid #8888E2", padding: ".2em .4em", borderRadius: "6px 0 0 6px", color: "#FFFF", height: "2.3rem" }}>
                                                                    {gettext("Choisir un fichier")}
                                                                </label>
                                                                <input type="text" className="form-control" style={{ backgroundColor: "#F6F7FB", border: 0, color: "#777E90" }} value={input.value?.name} placeholder={input.placeholder} disabled />
                                                            </div>
                                                            <input type="file" className="form-control" id={input.field} accept=".png, .jpg, .jpeg, .svg" onChange={(e) => { this.setField(input.field, e.target.files[0]); this.setUrl(input.field, URL.createObjectURL(e.target.files[0])); }} />
                                                        </div>
                                                    ) : input.field_type === "multi-select" ?
                                                        (
                                                            <div className="d-flex" style={{ width: "100%", whiteSpace: "nowrap" }}>
                                                                <Form.Select style={{ borderRadius: "6px 0 0 6px" }} className="form-select" id={input.field} value={input.value} onChange={(e) => this.setField(input.field, e.target.value)}>
                                                                    <option value="">{gettext("--------------------")}</option>
                                                                    {input.field_list.map((option) => (
                                                                        <option key={option.pk} value={option.name}>{option.name}</option>
                                                                    ))}
                                                                </Form.Select>
                                                                <button type="button" style={{ backgroundColor: "#8888E2", color: "#FFFFFF", borderRadius: "0 6px 6px 0", border: "1px solid #DEDFEA", padding: "0 3%" }} onClick={this.handleStructureUpdate}>{gettext("+ Ajouter")}</button>
                                                            </div>
                                                        ) : input.field_type === "select" ? (
                                                            <Form.Select className="form-select" id={input.field} value={input.value} onChange={(e) => this.setField(input.field, e.target.value)}>
                                                                <option value="">{gettext("--------------------")}</option>
                                                                {input.field_list.map((option) => (
                                                                    <option key={option.pk ? option.pk : option} value={option.name ? option.name : option}>{option.name ? option.name : option}</option>
                                                                ))}
                                                            </Form.Select>
                                                        ) : (
                                                            <input type={input.field_type} className="form-control" id={input.field} value={input.value} placeholder={input.placeholder} onChange={(e) => this.setField(input.field, e.target.value)} />
                                                        )}
                                                </div>
                                            ))}
                                        </div>
                                        <button type="button" className="btn" style={{ backgroundColor: "#FFFFFF", color: "#000000", borderRadius: "6px", border: "1px solid #DEDFEA", margin: "1% 0 0 0" }} onClick={this.handleStructureUpdate}>{gettext("Valider les modifications")}</button>
                                    </div> */}
							</div>
						</div>
					</div>
				) : this.state.activeKey === 'link-2' ? (
					<div>
						<div className="d-flex justify-content-between align-items-center" style={{ margin: '0 3% 0 0' }}>
							<p style={{ margin: '0 0 0 3%', fontWeight: 700, fontSize: '130%' }}>{gettext('Fiche entreprise')}</p>
						</div>
						<div className="d-flex justify-content-between" style={{ margin: '3% 3% 3% 3%' }}>
							<div style={{ width: '48%', height: 'auto', backgroundColor: '#FFFFFF', borderRadius: '16px', padding: '32px' }}>
								<div style={{ width: '100%', height: '100%' }}>
									<p style={{ fontWeight: 600 }}>{gettext('Modifier votre fiche entreprise')}</p>
									<div style={{ margin: '0 0 2% 0' }}>
										<p style={{ margin: 0 }}>{gettext("Description de l'activité")}</p>
										<textarea
											rows="4"
											style={{ width: '100%', borderRadius: '6px', borderColor: '#F6F7FB', backgroundColor: '#F6F7FB' }}
											className="form-control"
											id="activity_description"
											value={this.state.activity_description}
											onChange={(e) => this.setState({ activity_description: e.target.value })}
										/>
									</div>
									<div style={{ margin: '0 0 2% 0' }}>
										<p style={{ margin: 0 }}>{gettext('Description Mixity Human')}</p>
										<textarea
											rows="4"
											style={{ width: '100%', borderRadius: '6px', borderColor: '#F6F7FB', backgroundColor: '#F6F7FB' }}
											className="form-control"
											id="human_description"
											value={this.state.human_description}
											onChange={(e) => this.setState({ human_description: e.target.value })}
										/>
									</div>
									<div style={{ margin: '0 0 8% 0' }}>
										<p style={{ margin: 0 }}>{gettext('Témoignage diversité')}</p>
										<textarea
											rows="4"
											style={{ width: '100%', borderRadius: '6px', borderColor: '#F6F7FB', backgroundColor: '#F6F7FB' }}
											className="form-control"
											id="commitment_description"
											value={this.state.commitment_description}
											onChange={(e) => this.setState({ commitment_description: e.target.value })}
										/>
									</div>
									<button
										onClick={() => {
											this.updateStructureDescription();
										}}
										style={{ borderRadius: '6px', border: '1px solid #DEDFEA', backgroundColor: '#FFF', padding: '1%' }}
									>
										{gettext('Valider les modifications')}
									</button>
								</div>
							</div>
							<div style={{ width: '48%', height: 'auto', backgroundColor: '#FFFFFF', borderRadius: '16px', padding: '32px' }}>
								<div style={{ width: '100%', height: '100%' }}>
									<p style={{ fontWeight: 600 }}>{gettext('Aperçu de votre fiche entreprise')}</p>
									<div style={{ margin: '0 0 2% 0' }}>
										<p style={{ margin: 0, fontWeight: 550 }}>{gettext("Description de l'activité")}</p>
										<span>{this.state.activity_description.length == 0 ? 'Aucune description' : this.state.activity_description}</span>
									</div>
									<div style={{ margin: '0 0 2% 0' }}>
										<p style={{ margin: 0, fontWeight: 550 }}>{gettext('Description Mixity Human')}</p>
										<span>{this.state.human_description.length == 0 ? 'Aucune description' : this.state.human_description}</span>
									</div>
									<div style={{ margin: '0 0 2% 0' }}>
										<p style={{ margin: 0, fontWeight: 550 }}>{gettext('Témoignage diversité')}</p>
										<span>{this.state.commitment_description.length == 0 ? 'Aucune description' : this.state.commitment_description}</span>
									</div>
								</div>
							</div>
						</div>
					</div>
				) : this.state.activeKey === 'link-3' ? (
					<div className="d-flex flex-column" style={{ width: '100%' }}>
						<div style={{ margin: '0% 3% 0 3%' }}>
							{this.state.is_staff && (
								<div className="d-flex justify-content-between w-100 align-items-center" style={{ whiteSpace: 'nowrap', fontSize: '14px' }}>
									<p style={{ fontWeight: 700, fontSize: '150%' }}>{gettext('Informations sur les entités')}</p>
									<div className="d-flex" style={{ whiteSpace: 'nowrap', fontSize: '14px' }}>
										{this.state.entities_list.childrens.length === 0 && (
											<>
												<UploadTemplateEntitiesCSV />
												<ImporterEntitiesCSV />
											</>
										)}
									</div>
								</div>
							)}
							<div
								className="w-100"
								style={{ backgroundColor: '#FFFFFF', marginBottom: '2.5%', borderRadius: '16px', border: '1px solid #DEDFEA' }}
							>
								<div style={{ margin: '3%' }}>
									<div className="d-flex justify-content-between">
										<p style={{ fontWeight: 600 }}>{gettext("Modifier les informations de l'entité")}</p>
										<div className="d-flex" style={{ width: '25%' }}>
											<Form.Select
												style={{ border: '1px solid #DEDFEA', height: '89%', borderRadius: '6px' }}
												className="form-select no-hover"
												onChange={(e) => {
													this.setEntityInfos(e.target.value);
												}}
											>
												{this.state.collaborators.map((collaborator) => (
													<option key={collaborator.entity_name} value={collaborator.entity_name}>
														{collaborator.entity_name}
													</option>
												))}
											</Form.Select>
										</div>
									</div>
									<div className="input-grid">
										{this.state.EntityInputs.map((input, index) => (
											<div className="mb-3" key={input.field}>
												<label style={{ fontWeight: 550 }} htmlFor={input.field} className="form-label d-flex">
													{input.field_name}
													{input.is_needed && <div style={{ color: 'red', margin: '0 0 0 3px', padding: 0 }}>*</div>}
												</label>
												<input
													type={input.field_type}
													className="form-control"
													id={input.field}
													value={input.value}
													placeholder={input.placeholder}
													onChange={(e) => this.setEntityField(input.field, e.target.value)}
												/>
											</div>
										))}
									</div>
									<button
										type="button"
										className="btn"
										style={{
											backgroundColor: '#FFFFFF',
											color: '#000000',
											borderRadius: '6px',
											border: '1px solid #DEDFEA',
											margin: '1% 0 0 0',
										}}
										onClick={this.UpdateEntityInfos}
									>
										{gettext('Valider les modifications')}
									</button>
								</div>
							</div>
						</div>
					</div>
				) : this.state.activeKey === 'link-4' ? (
					<div>
						<style>
							{`
                        .modal-content {
                            border-radius: 16px;
                        }
                    `}
						</style>
						<Modal
							style={{ zIndex: 1200 }}
							show={this.state.show_entities_modal}
							size={'lg'}
							onHide={() => this.setShowEntitiesModal(false, this.state.currentCollaboratorsField)}
							title={gettext('Entités')}
							centered
						>
							<div style={{ margin: '2%', width: '100%', height: '100%' }}>
								<h5 style={{ fontWeight: 600 }}>{gettext('Choix des entités')}</h5>
								<div style={{ width: '100%', marginTop: '3%', marginBottom: '3%' }}>
									<EntitiesSelect entities={[this.state.currentCollaboratorsField?.entities]} />
								</div>
								<div>
									<button
										type="button"
										style={{
											backgroundColor: '#8888E2',
											height: '40px',
											color: '#FFFFFF',
											borderRadius: '6px',
											border: '1px solid #DEDFEA',
											margin: 0,
										}}
										onClick={() => this.setShowEntitiesModal(false, this.state.currentCollaboratorsField)}
									>
										{gettext('Valider')}
									</button>
									<button
										type="button"
										style={{
											backgroundColor: '#FFFFFF',
											height: '40px',
											color: '#000000',
											borderRadius: '6px',
											border: '1px solid #DEDFEA',
											margin: '0 0 0 1%',
										}}
										onClick={() => this.unSelectAllEntities(this.state.currentCollaboratorsField)}
									>
										<i className="bi bi-trash3" style={{ margin: '0 0.5rem 0 0', padding: 0 }}></i>
										{gettext('Supprimer la sélection')}
									</button>
								</div>
							</div>
						</Modal>
						<div style={{ margin: '3% 3% 0 3%' }}>
							<div className="d-flex justify-content-between align-items-center">
								<p style={{ fontWeight: 700, fontSize: '130%' }}>{gettext('Collaborateurs')}</p>
								{this.state.is_owner && (
									<div className="d-flex" style={{ whiteSpace: 'nowrap', fontSize: '14px' }}>
										<button
											onClick={() => {
												this.setAddCollaboratorDisplay();
											}}
											style={{
												padding: '10px, 16px, 10px, 0px',
												backgroundColor: '#FFFFFF',
												border: '1px solid #181B3D',
												borderRadius: '6px',
												margin: '8px 0px 8px 16px',
											}}
										>
											{gettext('+ Ajouter un collaborateur')}
										</button>
										<UploadTemplateCollaboratorsCSV />
										<ImporterCollaboratorsCSV onCSVImport={this.handleCSVImport} />
									</div>
								)}
							</div>
							{this.state.showAddCollaboratorBox ? (
								<div
									style={{
										width: '100%',
										backgroundColor: '#FFFFFF',
										marginBottom: '2.5%',
										borderRadius: '16px',
										border: '1px solid #DEDFEA',
									}}
								>
									<div style={{ margin: '3%' }}>
										<p style={{ fontWeight: 600 }}>{gettext('Ajouter un collaborateur')}</p>
										{this.state.addCollaboratorsFields.map((field, index) => (
											<div className="d-flex justify-content-between mb-4" key={index}>
												<div style={{ width: '48%' }}>
													<label style={{ fontWeight: 550 }} htmlFor={field.field_name} className="form-label d-flex">
														{field.field_name}
													</label>
													{field.field_type === 'entity-select' ? (
														<Form.Select
															className="form-select"
															id={field.field_name}
															value={field.field_value}
															onChange={(e) => this.setField(field.field_name, e.target.value)}
														>
															<option key="default" value="">{gettext('--------------------')}</option>
														</Form.Select>
													) : (
														<input
															type={field.field_type}
															className="form-control"
															id={field.field_name}
															value={field.field_value}
															placeholder={field.field_name}
															onChange={(e) => this.setCollaboratorField(index, e.target.value)}
														/> //fix
													)}
												</div>
												<div style={{ width: '48%' }}>
													<label style={{ fontWeight: 550 }} htmlFor={field.second_field_name} className="form-label d-flex">
														{field.second_field_name}
													</label>
													{field.second_field_type === 'entity-select' ? (
														<div style={{ width: '100%', height: '100%' }}>
															{this.selectedEntitiesCount([field.entities]) > 0 && (
																<div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: '3%' }}>
																	<this.SelectedEntitiesTags field={field} />
																</div>
															)}
															<button
																onClick={() => {
																	this.setShowEntitiesModal(true, field);
																}}
																type="button"
																style={{
																	backgroundColor: '#8888E2',
																	padding: '10px 16px',
																	color: '#FFFFFF',
																	borderRadius: '6px',
																	border: '1px solid #8888E2',
																	margin: 0,
																}}
															>
																{gettext('+ Ajouter entité')}
															</button>
														</div>
													) : (
														<input
															type={field.second_field_type}
															className="form-control"
															id={field.second_field_name}
															value={field.second_field_value}
															placeholder={field.second_field_name}
															onChange={(e) => this.setField(field.second_field_name, e.target.value)}
														/>
													)}
												</div>
											</div>
										))}
										<div>
											<button
												onClick={() => {
													this.addCollaboratorsFields();
												}}
												style={{
													border: '1px solid #181B3D',
													padding: '0.5rem',
													backgroundColor: '#FFFF',
													borderRadius: '6px',
													marginRight: '3%',
												}}
											>
												{gettext('+ Ajouter un autre collaborateur')}
											</button>
											<button
												disabled={this.inviteCollaboratorIsDisabled()}
												onClick={() => {
													this.inviteCollaborators();
												}}
												style={{
													border: this.inviteCollaboratorIsDisabled() ? '1px solid #E6E8EC' : '1px solid #8888E2',
													padding: '0.5rem',
													backgroundColor: this.inviteCollaboratorIsDisabled() ? '#E6E8EC' : '#8888E2',
													color: this.inviteCollaboratorIsDisabled() ? '#B1B5C3' : '#FFFF',
													borderRadius: '6px',
												}}
											>
												{this.state.addCollaboratorsFields.length > 1
													? gettext('Inviter les collaborateurs')
													: gettext('Inviter le collaborateur')}
											</button>
										</div>
									</div>
								</div>
							) : null}
							<div style={{ width: '100%', backgroundColor: '#FFFFFF', marginBottom: '2.5%', borderRadius: '16px', border: '1px solid #DEDFEA' }}>
								<div style={{ margin: '3%' }}>
									<div className="d-flex justify-content-between">
										<p style={{ fontWeight: 600 }}>{gettext('Administration')}</p>
										<div className="d-flex" style={{ width: '25%' }}>
											<Form.Select
												style={{ border: '1px solid #DEDFEA', height: '89%', borderRadius: '6px' }}
												className="form-select no-hover"
												onChange={(e) =>
													this.setState(() => {
														return { selected_entity: e.target.value };
													})
												}
												value={this.state.selected_entity}
											>
												{this.state.collaborators.map((collaborator) => (
													<option key={collaborator.entity_name} value={collaborator.entity_name}>
														{collaborator.entity_name}
													</option>
												))}
											</Form.Select>
										</div>
									</div>
									<Modal
										style={{ zIndex: 1200 }}
										show={this.state.show_collaborator_delete_validation}
										onHide={() => this.setShowCollaboratorDeleteValidation(false)}
										title={gettext("Suppression d'un collaborateur")}
										centered
									>
										<div className="d-flex flex-column justify-content-center align-items-center" style={{ padding: '4%' }}>
											<p>{gettext('Êtes-vous sûr de vouloir supprimer ce collaborateur ?')}</p>
											<p className="">
												{this.state.current_delete_collaborator.first_name + ' ' + this.state.current_delete_collaborator.last_name}
											</p>
											<div className="d-flex flex-row">
												<button
													onClick={() => {
														this.setShowCollaboratorDeleteValidation(false);
													}}
													style={{
														backgroundColor: '#FFFFFF',
														color: '#000000',
														borderRadius: '6px',
														border: '1px solid #DEDFEA',
														padding: '0.5rem',
														marginRight: '5%',
													}}
												>
													{gettext('Annuler')}
												</button>
												<button
													onClick={() => {
														this.setShowCollaboratorDeleteValidation(false);
														this.deleteCollaborator(this.state.current_delete_collaborator);
													}}
													style={{
														backgroundColor: '#8888E2',
														color: '#FFFFFF',
														border: '1px solid #8888E2',
														borderRadius: '6px',
														padding: '0.5rem',
													}}
												>
													{gettext('Supprimer')}
												</button>
											</div>
										</div>
									</Modal>
									<p style={{ fontWeight: 500, fontSize: '92%', marginTop: '2%' }}>
										{gettext(
											"Cette page vous permet de gérer les droits des collaborateurs appartenant à votre structure et/ou d'en inviter de nouveaux.",
										)}
									</p>
									{this.is_collaborators_in_entity() === false ? (
										<div className="d-flex justify-content-center align-items-center" style={{ marginTop: '2%' }}>
											<p>{gettext("Aucun collaborateur n'a été ajouté pour le moment.")}</p>
										</div>
									) : (
										<div className="collaborator_grid">
											<div className="collaborator_header_cell" style={{ borderRadius: '8px 0 0 8px' }}>
												{gettext('Collaborateur')}
											</div>
											<div className="collaborator_header_cell">{gettext('E-mail')}</div>
											<div className="collaborator_header_cell text-center">{gettext('Administrateur')}</div>
											<div className="collaborator_header_cell text-center">{gettext('Membre')}</div>
											<div className="collaborator_header_cell text-center">{gettext('Lecteur')}</div>
											<div className="collaborator_header_cell text-center" style={{ borderRadius: '0 8px 8px 0' }}>
												{gettext('Supprimer')}
											</div>
											{this.state.collaborators.map(
												(entity) =>
													this.state.selected_entity === entity.entity_name &&
													entity.collaborators.map((collaborator) => (
														<>
															<div key={collaborator.pk} className="collaborator_cell">
																{collaborator.first_name} {collaborator.last_name}
															</div>
															<div className="collaborator_cell">{collaborator.email}</div>
															<div className="collaborator_cell d-flex justify-content-center align-items-center">
																<input
																	style={{ borderRadius: '4px' }}
																	type="radio"
																	name={collaborator.email}
																	value={'owner'}
																	defaultChecked={collaborator.is_owner ? true : false}
																	onChange={(e) => this.handleRadioChange(e, collaborator)}
																/>
															</div>
															<div className="collaborator_cell d-flex justify-content-center align-items-center">
																<input
																	style={{ borderRadius: '4px' }}
																	type="radio"
																	name={collaborator.email}
																	value={'member'}
																	defaultChecked={!collaborator.is_owner && !collaborator.is_reader ? true : false}
																	onChange={(e) => this.handleRadioChange(e, collaborator)}
																/>
															</div>
															<div className="collaborator_cell d-flex justify-content-center align-items-center">
																<input
																	style={{ borderRadius: '4px' }}
																	type="radio"
																	name={collaborator.email}
																	value={'reader'}
																	defaultChecked={collaborator.is_reader ? true : false}
																	onChange={(e) => this.handleRadioChange(e, collaborator)}
																/>
															</div>
															<div className="collaborator_cell d-flex justify-content-center align-items-center">
																<img
																	onClick={() => {
																		this.setState(() => {
																			return { current_delete_collaborator: collaborator };
																		});
																		this.setShowCollaboratorDeleteValidation(true);
																	}}
																	src={'/static/icon/trash.svg'}
																	style={{ width: '18%', margin: 0, padding: 0, cursor: 'pointer' }}
																></img>
															</div>
														</>
													)),
											)}
										</div>
									)}
								</div>
							</div>
						</div>
					</div>
				) : (
					<div></div>
				)}
			</div>
		) : (
			<h4 className="d-flex justify-content-center align-items-middle" style={{ marginTop: '40%' }}>
				{this.state.placeholder}
			</h4>
		);
	}
}

export default StructureUpdate;
