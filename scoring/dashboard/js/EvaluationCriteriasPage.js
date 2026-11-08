import React, { Component, useState } from 'react';
import Loading from '../../../mixity/dashboard/js/includes/Loading';
import { Breadcrumb } from 'react-bootstrap';
import Accordion from 'react-bootstrap/Accordion';
import AccordionButton from 'react-bootstrap/AccordionButton';
import Header from '../../../mixity/dashboard/js/includes/Header';
import CollaboratorsImporter from './includes/CollaboratorsImporter';

class EvaluationCriteriasPage extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to front-end display
			new_filter_name: '',
			_is_csv_imported: false,
			human_criterias_csv: [],
			human_criterias: [],
			everythingLoaded: false,
			placeholder: gettext('Chargement'),
			csvNeedReload: false,
			recentlySavedPersonalFilters: false,
			successAlertTimer: null,

			//related to /api/url/ request
			emptyurl: '',
			url: '',
			urlEvaluation: '',

			//related to /api/human-form-choices/ request
			human_selected_filters: {},

			//related to /api/human-collaborators-count/ request
			nbAnswers: 0,

			//related to /api/assess-evaluation/ request
			evaluation: null,
			version: '',
			product: '',
		};
	}

	async componentDidMount() {
		try {
			const is_human_page = window.location.href.includes('human');
			if (is_human_page) {
				this.setState({ product: 'human' });
			} else {
				this.setState({ product: 'scan' });
			}

			const response_url = await fetch('api/url/');
			this.fetchErrorMessage(response_url);
			const data_url = await response_url.json();
			let url = window.location.protocol + '//' + data_url;
			let emptyurl = url;
			let url_evaluation = window.location.protocol + '//' + data_url;

			if (window.location.pathname.split('/').filter(Boolean)[0])
				url_evaluation += '/' + window.location.pathname.split('/').filter(Boolean)[0] + '/' + window.location.pathname.split('/').filter(Boolean)[1];

			let segments = window.location.pathname.split('/').filter(Boolean);
			let version_slug = segments[segments.length - 1];
			this.setState(() => {
				return {
					emptyurl: emptyurl,
					url: url,
					urlEvaluation: url_evaluation,
					version: version_slug,
				};
			});
			const response_evaluation = await fetch(url_evaluation + '/api/assess-evaluation/' + version_slug);
			this.fetchErrorMessage(response_evaluation);
			const data_evaluation = await response_evaluation.json();
			this.setState(() => {
				return {
					evaluation: data_evaluation,
				};
			});
			this.getAllHumanCriterias().then(() => {
				this.setState(() => {
					return {
						everythingLoaded: true,
					};
				});
			});

			if (this.state.nbAnswers > 0) {
				window.history.back();
			}
		} catch (error) {
			console.error('>>>>> ERROR in evalution criterias: ', error);
		}
	}

	downloadCriteriasTemplate() {
		const csvContent = `email;nom;prenom\nexample1@email.com;Dupont;Jean`;

		const blob = new Blob([csvContent], { type: 'text/csv' });

		const a = document.createElement('a');
		const url = window.URL.createObjectURL(blob);
		a.href = url;
		a.download = 'CriteriasTemplate.csv';
		document.body.appendChild(a);
		a.click();

		window.URL.revokeObjectURL(url);
		document.body.removeChild(a);
	}

	async getAllHumanCriterias() {
		if (this.state.evaluation.is_human) {
			const [response_form, response_counts] = await Promise.all([
				fetch(this.state.urlEvaluation + '/api/human-form-choices/'),
				fetch(this.state.urlEvaluation + '/api/human-collaborators-count/'),
			]);
			this.fetchErrorMessage(response_form);
			this.fetchErrorMessage(response_counts);
			const data_form = await response_form.json();
			const data_counts = await response_counts.json();
			const old_data_form = data_form['old'];
			this.setState(() => {
				return {
					human_selected_filters: old_data_form,
					//answer
					nbAnswers: data_counts['nb_collaborator_answers'],
				};
			});
		}
		const criterias_from_csv = [];
		const criterias = [];
		for (const criteriaKey in this.state.human_selected_filters) {
			const criteria = this.state.human_selected_filters[criteriaKey];
			if (criteria.is_csv_imported) {
				criterias_from_csv.push(criteria);
			} else if (criteria.is_human_criteria) {
				criterias.push(criteria);
			}
		}
		this.setState(() => {
			return {
				human_criterias_csv: criterias_from_csv,
				human_criterias: criterias,
				_is_csv_imported: criterias_from_csv.length > 0,
			};
		});
	}

	createListFromKeys(keysList) {
		let result = {};
		keysList.forEach((key) => (result[key] = []));
		return result;
	}

	fetchErrorMessage(response) {
		if (response.status > 400) {
			return this.setState(() => {
				return { placeholder: gettext("Quelque chose s'est mal passé !") };
			});
		}
		return;
	}

	handleCollaboratorsImporterSuccess = () => {
		this.setState(() => {
			return {
				csvNeedReload: true,
			};
		});
	};

	startSuccessAlert = () => {
		this.setState(() => {
			return {
				recentlySavedPersonalFilters: true,
			};
		});
		clearTimeout(this.state.successAlertTimer);
		this.setState(() => {
			return {
				successAlertTimer: setTimeout(this.stopSuccessAlert, 2500),
			};
		});
	};

	stopSuccessAlert = () => {
		this.setState(() => {
			return {
				recentlySavedPersonalFilters: false,
			};
		});
	};

	async handleDeleteFilter(criteria) {
		const response = await fetch(this.state.url + '/api/' + this.state.evaluation.pk + '/delete-filter/', {
			credentials: 'include',
			method: 'POST',
			headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
			body: JSON.stringify({
				human_criteria: criteria.label,
			}),
		});
		this.fetchErrorMessage(response);
		const data = await response.json();
		if (data.error) {
			return;
		}

		let new_human_criterias = this.state.human_criterias.filter((criteria_loop) => {
			return criteria_loop.label !== criteria.label;
		});
		this.setState(() => {
			return {
				human_criterias: new_human_criterias,
			};
		});
		this.startSuccessAlert();
	}

	async handleDeleteFilterChoice(criteria, choice) {
		let prev_choice;
		let choice_index;
		this.state.human_criterias.forEach((criteria_loop) => {
			if (criteria_loop.label === criteria.label) {
				criteria.choices.forEach((choice_loop, index) => {
					if (choice_loop === choice) {
						choice_index = index;
						prev_choice = JSON.parse(JSON.stringify(choice_loop));
					}
				});
			}
		});

		if (criteria.choices[choice_index][Object.keys(criteria.choices[choice_index])[0]] != -1) {
			const response = await fetch(this.state.url + '/api/' + this.state.evaluation.pk + '/delete-filter-choice/', {
				credentials: 'include',
				method: 'POST',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
				body: JSON.stringify({
					human_criteria: criteria.label,
					choice: Object.keys(prev_choice)[0],
				}),
			});
			this.fetchErrorMessage(response);
			const data = await response.json();
			if (data.error) {
				return;
			}
		}

		criteria.choices.splice(choice_index, 1);
		this.setState(() => {
			return {
				human_criterias: this.state.human_criterias,
			};
		});
		this.startSuccessAlert();
	}

	async handleChoiceModification(criteria, choice, event) {
		if (event.target.value === '') {
			return;
		}
		const new_choice_name = event.target.value;
		let prev_choice;

		this.state.human_criterias.forEach((criteria_loop) => {
			if (criteria_loop.label === criteria.label) {
				criteria.choices.forEach((choice_loop) => {
					if (choice_loop === choice) {
						prev_choice = choice_loop;
					}
				});
			}
		});

		choice[Object.keys(choice)[0]] = 1;

		const response = await fetch(this.state.url + '/api/' + this.state.evaluation.pk + '/modify-filter-choice/', {
			credentials: 'include',
			method: 'POST',
			headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
			body: JSON.stringify({
				human_criteria: criteria.label,
				choice: Object.keys(prev_choice)[0],
				new_choice: new_choice_name,
			}),
		});
		this.fetchErrorMessage(response);
		const data = await response.json();
		if (data.error) {
			return;
		}

		prev_choice[new_choice_name] = choice[Object.keys(choice)[0]];
		delete prev_choice[Object.keys(choice)[0]];

		event.target.value = '';

		this.setState(() => {
			return {
				human_criterias: this.state.human_criterias,
			};
		});
		this.startSuccessAlert();
	}

	handleNewChoice = (filter_index) => {
		const choice_name = 'Choix ' + (this.state.human_criterias[filter_index].choices.length + 1);
		const choice = { [choice_name]: -1 };

		this.setState((prevState) => ({
			human_criterias: prevState.human_criterias.map((criteria, index) => {
				if (index === filter_index) {
					return {
						...criteria,
						choices: [...criteria.choices, choice],
					};
				}
				return criteria;
			}),
		}));
	};

	async handleNewFilter() {
		if (this.state.new_filter_name === '') {
			return;
		}

		for (const criteria of this.state.human_criterias) {
			if (criteria.label === this.state.new_filter_name) {
				return;
			}
		}

		const response = await fetch(this.state.url + '/api/' + this.state.evaluation.pk + '/add-filter/', {
			credentials: 'include',
			method: 'POST',
			headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
			body: JSON.stringify({
				human_criteria: this.state.new_filter_name,
			}),
		});
		this.fetchErrorMessage(response);
		const data = await response.json();

		if (data.error) {
			return;
		}

		const new_filter = {
			label: this.state.new_filter_name,
			choices: [{ 'Choix 1': -1 }],
		};

		this.setState((prevState) => ({
			human_criterias: [...prevState.human_criterias, new_filter],
		}));

		this.setState(() => {
			return {
				new_filter_name: '',
			};
		});
		this.startSuccessAlert();
	}

	render() {
		return this.state.everythingLoaded ? (
			<div>
				{/*header block*/}
				<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
					<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
						<Breadcrumb.Item href={'/'}>{gettext('Accueil')}</Breadcrumb.Item>
						<Breadcrumb.Item active>{gettext('Mesurer')}</Breadcrumb.Item>
						{this.state.product === 'human' ? (
							<Breadcrumb.Item active>
								<strong>{gettext('Mixity Human')}</strong>
							</Breadcrumb.Item>
						) : (
							<Breadcrumb.Item active>
								<strong>{gettext('Mixity Scan')}</strong>
							</Breadcrumb.Item>
						)}
					</Breadcrumb>
					<Header data={{ url: '/', languages: languages, language_code: language_code, enabled_website_languages: enabled_website_languages }} />
				</div>
				{/*description text*/}
				<div
					className="border m-4 pl-5 pr-5"
					style={{ borderRadius: '16px', borderColor: '#DEDFEA', background: '#FFFFFF', boxShadow: '0px 4px 6px 0px #181B3D0D' }}
				>
					<div className="d-flex mx-3 pt-3 flex-column">
						<h5 className="pb-1" style={{ fontWeight: '900' }}>
							{gettext('Filtres personnalisés')}
						</h5>
						<div style={{ fontSize: '75%' }}>
							<p>
								{gettext(
									'Vous pouvez ci-dessous ajouter des filtres avec des choix personnalisés, ces filtres vont permettre de consulter les réponses au sondage en fonction des caractéristiques des répondants (entités, statut, métiers...)',
								)}
							</p>
							<p>{gettext("Le genre et l'âge sont les deux caractéristiques déjà présentes au sein du sondage.")}</p>
							<p>{gettext('Vous pouvez ajouter autant de filtres et de choix que vous souhaitez ou ne pas en ajouter du tout.')}</p>
							<p style={{ fontWeight: 700 }}>
								{gettext('Attention : ')}
								<span style={{ fontWeight: 'normal' }}>
									{gettext(
										"Si la population de répondants n'est pas assez importante au sein des différents choix de filtres, vous ne pourrez pas visualiser les résultats filtrés.",
									)}
								</span>
							</p>
						</div>
					</div>
				</div>
				{/*filters block*/}
				<div className="d-flex justify-content-center">
					{/*Personnal filters*/}
					<div
						className="border mx-3 px-3 pt-3"
						style={{
							width: '46.5%',
							height: 'auto',
							borderRadius: '16px',
							borderColor: '#DEDFEA',
							background: '#FFFFFF',
							boxShadow: '0px 4px 6px 0px #181B3D0D',
						}}
					>
						{this.state.recentlySavedPersonalFilters && (
							<div
								className="d-flex flex-row align-items-center py-2 px-3 mb-3"
								style={{
									backgroundColor: 'rgba(3, 168, 124, 0.1)',
									borderRadius: '4px',
									border: '1px solid',
									borderColor: 'rgba(3, 168, 124, 0.3)',
								}}
							>
								<span style={{ color: '#03A87C', fontWeight: 500, width: '100%' }}>{gettext('Changements sauvegardés')}</span>
								<div className="d-flex flex-column align-items-end" style={{ width: '100%' }}>
									<i className="fas bi-check-circle fa-sm" style={{ color: '#03A87C', padding: 0, margin: 0 }}></i>
								</div>
							</div>
						)}
						<p style={{ fontWeight: 900 }}>{gettext('Filtres personnalisés')}</p>
						<div className="d-flex justify-content-center flex-column align-items-center" style={{ height: '100%' }}>
							{!(this.state.human_criterias.length > 0) ? (
								<div className="d-flex justify-content-center flex-column align-items-center" style={{ width: '100%', height: '100%' }}>
									<p
										className="text-center d-flex justify-content-center flex-column align-items-center"
										style={{
											width: '100%',
											height: '100%',
											fontSize: '95%',
											fontWeight: '500',
											color: '#B1B5C3',
										}}
									>
										{gettext('Pas de filtres trouvés')}
									</p>
								</div>
							) : (
								<Accordion style={{ width: '90%', marginTop: '2em' }} flush>
									{this.state.human_criterias.map((criteria, index) => {
										return (
											<Accordion.Item eventKey={index} key={index} className="accordion-item" bsPrefix="personal_filters_accordion-item">
												<h2 className="d-flex flex-rows" style={{ width: '100%' }}>
													<AccordionButton
														className="accordion-button"
														bsPrefix="personal_filters_accordion-button"
														style={{ fontWeight: 700, fontSize: '55%' }}
													>
														{criteria.label}
													</AccordionButton>
													<button
														style={{ borderColor: '#FFF', backgroundColor: '#FFF', boxShadow: 'none', border: 'none' }}
														className="d-flex align-self-center"
														onClick={() => this.handleDeleteFilter(criteria)}
													>
														<i className="bi bi-trash3" style={{ color: '#FF6F6F', padding: 0, margin: 0 }}></i>
													</button>
												</h2>
												<Accordion.Body className="accordion-body">
													<ul style={{ margin: 0, padding: 0, paddingLeft: '20px' }}>
														{criteria.choices.map((choice, choice_index) => {
															const key = Object.keys(choice)[0];
															if (key === '') {
																return;
															}
															return (
																<div key={choice_index} className="pb-3" style={{ width: '100%' }}>
																	<p style={{ fontWeight: 700, margin: 0 }} key={choice_index}>
																		{gettext('Choix ' + (choice_index + 1))}
																	</p>
																	<div
																		className="d-flex flex-rows align-items-center justify-content-center"
																		style={{ height: '100%', width: '100%' }}
																	>
																		<input
																			placeholder={key}
																			style={{
																				background: '#F6F7FB',
																				borderColor: '#F6F7FB',
																				margin: 0,
																				borderRadius: '8px 0 0 8px',
																				whiteSpace: 'nowrap',
																				boxShadow: 'none',
																			}}
																			onBlur={(event) => this.handleChoiceModification(criteria, choice, event)}
																			onKeyDown={(event) => {
																				if (event.key === 'Enter') {
																					event.target.blur();
																				}
																			}}
																		/>
																		<button
																			style={{
																				borderRadius: '0 8px 8px 0',
																				borderRight: 'none',
																				margin: 0,
																				borderColor: '#8888E2',
																				backgroundColor: '#8888E2',
																				boxShadow: 'none',
																				border: 'none',
																			}}
																			className="d-flex align-self-center"
																			onClick={() => this.handleDeleteFilterChoice(criteria, choice)}
																		>
																			<i
																				className="bi bi-trash3"
																				style={{ color: '#FFFFFF', padding: '5px', margin: 0 }}
																			></i>
																		</button>
																	</div>
																</div>
															);
														})}
														<button
															className="button border"
															style={{
																width: '100%',
																background: '#FFF',
																borderColor: '#000',
																color: '#000',
																borderRadius: '8px',
																whiteSpace: 'nowrap',
															}}
															onClick={() => this.handleNewChoice(index)}
														>
															{gettext('Ajouter un choix')}
														</button>
													</ul>
												</Accordion.Body>
											</Accordion.Item>
										);
									})}
								</Accordion>
							)}
							<div
								className="d-flex justify-content-center align-items-end"
								style={{ height: '100%', width: '100%', marginBottom: this.state.recentlySavedPersonalFilters ? '7.5rem' : '4em' }}
							>
								<div className="d-flex flex-column justify-content-center align-items-center" style={{ width: '100%' }}>
									<p className="text-left" style={{ fontWeight: 700, width: '90%', margin: 0 }}>
										{gettext('Nom du filtre')}
									</p>
									<input
										className="mb-3"
										style={{
											width: '90%',
											background: '#F6F7FB',
											borderColor: '#F6F7FB',
											borderRadius: '8px',
											whiteSpace: 'nowrap',
											boxShadow: 'none',
										}}
										value={this.state.new_filter_name}
										maxLength="35"
										onChange={(event) => this.setState({ new_filter_name: event.target.value })}
									/>
									<button
										className="button border"
										style={{
											width: '90%',
											background: '#8888E2',
											borderColor: '#8888E2',
											color: '#fff',
											borderRadius: '8px',
											whiteSpace: 'nowrap',
										}}
										onClick={() => this.handleNewFilter()}
									>
										{gettext('Ajouter un filtre')}
									</button>
								</div>
							</div>
						</div>
					</div>
					{/*CSV filters*/}
					<div
						className="border mx-3 px-3 pt-3"
						style={{
							width: '47%',
							height: 'auto',
							borderRadius: '16px',
							borderColor: '#DEDFEA',
							background: '#FFFFFF',
							boxShadow: '0px 4px 6px 0px #181B3D0D',
						}}
					>
						<p style={{ fontWeight: 900 }}>{gettext('Collaborateurs')}</p>
						{this.state._is_csv_imported && !this.state.csvNeedReload ? (
							<div className="d-flex justify-content-center flex-column align-items-center" style={{ height: '100%' }}>
								<Accordion className="pt-4 pb-0" style={{ width: '90%' }} flush>
									{this.state.human_criterias_csv.map((criteria, index) => {
										return (
											<Accordion.Item eventKey={index} key={index} className="accordion-item" bsPrefix="csv_filters_accordion-item">
												<h2>
													<AccordionButton
														className="accordion-button"
														bsPrefix="csv_filters_accordion-button"
														style={{ fontWeight: 700, fontSize: '55%' }}
													>
														{criteria.label}
													</AccordionButton>
												</h2>
												<Accordion.Body className="accordion-body">
													<ul>
														{criteria.choices.map((choice, index) => {
															const key = Object.keys(choice)[0];
															if (key === '') {
																return;
															}
															return <p key={index}>{key}</p>;
														})}
													</ul>
												</Accordion.Body>
											</Accordion.Item>
										);
									})}
								</Accordion>
								<div className="d-flex justify-content-center align-items-end" style={{ height: '100%', width: '100%', marginBottom: '4em' }}>
									<button
										className="button border"
										style={{
											width: '90%',
											background: '#FFFFFF',
											borderColor: '#DEDFEA',
											color: '#DEDFEA',
											borderRadius: '8px',
											whiteSpace: 'nowrap',
										}}
										disabled={true}
									>
										<i className="fas bi-box-arrow-in-down fa-lg align-self-center"></i>
										{gettext('Importer un CSV')}
									</button>
								</div>
							</div>
						) : this.state.csvNeedReload ? (
							<div className="d-flex justify-content-center flex-column align-items-center" style={{ height: '100%' }}>
								<p
									className="text-center d-flex justify-content-center flex-column align-items-center"
									style={{
										width: '100%',
										height: '100%',
										fontSize: '95%',
										fontWeight: '500',
										color: '#B1B5C3',
									}}
								>
									{gettext('Les collaborateurs ont été importés avec succès, veuillez rafraîchir la page pour les visualiser.')}
								</p>
								<div className="d-flex justify-content-center align-items-end" style={{ width: '100%', marginBottom: '4em' }}>
									<CollaboratorsImporter
										className="button border"
										evaluation_pk={this.state.evaluation.pk}
										logo_style="fas bi-box-arrow-in-down fa-lg align-self-center"
										text={gettext('Importer un CSV')}
										style={{
											width: '90%',
											background: '#8888E2',
											borderColor: '#8888E2',
											color: '#fff',
											borderRadius: '8px',
											whiteSpace: 'nowrap',
										}}
										onSuccess={this.handleCollaboratorsImporterSuccess}
										needModal={false}
									/>
								</div>
							</div>
						) : !this.state.csvNeedReload ? (
							<div className="d-flex justify-content-center flex-column align-items-center" style={{ height: '100%' }}>
								<p
									className="text-center d-flex justify-content-center flex-column align-items-center"
									style={{
										width: '100%',
										height: '100%',
										fontSize: '95%',
										fontWeight: '500',
										color: '#B1B5C3',
									}}
								>
									{gettext('Veuillez télécharger le fichier csv exemple pour importer vos collaborateurs.')}
									<button
										className="button border"
										style={{
											background: '#8888E2',
											borderColor: '#8888E2',
											color: '#fff',
											borderRadius: '8px',
											whiteSpace: 'nowrap',
											marginTop: '2.5%',
										}}
									>
										<a onClick={this.downloadCriteriasTemplate} style={{ color: '#fff', fontSize: '90%', textDecoration: 'none' }}>
											{gettext('Télécharger le fichier exemple')}
										</a>
									</button>
								</p>
								<div className="d-flex justify-content-center align-items-end" style={{ width: '100%', marginBottom: '4em' }}>
									<CollaboratorsImporter
										className="button border"
										logo_style="fas bi-box-arrow-in-down fa-lg align-self-center"
										evaluation_pk={this.state.evaluation.pk}
										text={gettext('Importer un CSV')}
										style={{
											width: '90%',
											background: '#8888E2',
											borderColor: '#8888E2',
											color: '#fff',
											borderRadius: '8px',
											whiteSpace: 'nowrap',
										}}
										onSuccess={this.handleCollaboratorsImporterSuccess}
										needModal={false}
									/>
								</div>
							</div>
						) : (
							<div className="d-flex align-items-center justify-content-center pt-3">
								<div class="spinner-border" role="status">
									<span class="visually-hidden">{gettext('Chargement...')}</span>
								</div>
							</div>
						)}
					</div>
				</div>
				{/*Return button*/}
				<div className="d-flex justify-content-center m-3">
					<a
						className="button border m-2"
						style={{
							width: '90%',
							background: '#8888E2',
							borderColor: '#8888E2',
							color: '#fff',
							borderRadius: '8px',
							whiteSpace: 'nowrap',
						}}
						href={this.state.urlEvaluation + '/assess/' + this.state.version}
					>
						{gettext('Sauvegarder les filtres')}
					</a>
				</div>
			</div>
		) : (
			<Loading message={this.state.placeholder} />
		);
	}
}

export default EvaluationCriteriasPage;
