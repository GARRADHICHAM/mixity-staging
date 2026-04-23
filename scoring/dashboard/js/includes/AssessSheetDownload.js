import React, { Component } from 'react';

class AssessSheetDownload extends Component {
	constructor(props) {
		super();
		this.state = {
			numberOfFilter: 1,
			filterpage: [1],
			acutalfilterpage: 1,
			document_human_is_downloading: false,
			downloading_human_finished: false,
			downloading_human_error: false,
			is_download_human_message: false,
			download_human_message: '',
			default_human_language: '',
			selected_human: 'fr',

			document_diag_is_downloading: false,
			downloading_diag_finished: false,
			downloading_diag_error: false,
			is_download_diag_message: false,
			download_diag_message: '',
			default_diag_language: '',
			selected_diag: 'fr',
			selected_filter_diag: 'classique',
			diag_selected_entities: [],
			diag_accessible_entities: [],
			diag_entities_found: false,
			is_diag_one_entity_eval: false,
			diag_possible_choice: [
				{
					classique: `${gettext('Toutes les questions')}`,
					key_figures: `${gettext('Les chiffres clés uniquement')}`,
					to_review: `${gettext('Les questions à vérifier')}`,
				},
			],
			//, "to_review": `${gettext("Les questions à vérifier")}`

			direct_download: false,

			error: false,
			error_message: gettext("Quelque chose s'est mal passé !"),
		};
		this.add_one_filter_human = this.add_one_filter_human.bind(this);
		this.gotofilter = this.gotofilter.bind(this);
		this.delete_this_filter_human = this.delete_this_filter_human.bind(this);
		this.validate_react_form_human = this.validate_react_form_human.bind(this);
		this.validate_react_form_diag = this.validate_react_form_diag.bind(this);
		this.reset_human_form_state = this.reset_human_form_state.bind(this);
	}

	handleChange_diag = (event) => {
		this.setState({ selected_diag: event.target.value });
	};

	handleChange_human = (event) => {
		this.setState({ selected_human: event.target.value });
	};

	handleFilterChange_diag = (event) => {
		this.setState({ selected_filter_diag: event.target.value });
	};

	handleEntityChange_diag = (event) => {
		if (event.target.checked) {
			this.setState({ diag_selected_entities: this.state.diag_selected_entities.concat([event.target.value]) });
		} else {
			const index = this.state.diag_selected_entities.indexOf(event.target.value);
			const temp = this.state.diag_selected_entities;
			temp.splice(index, 1);
			this.setState({ diag_selected_entities: temp });
		}
	};

	fetchErrorMessage(response) {
		if (response.status > 400) {
			return this.setState(() => {
				return {
					error: true,
				};
			});
		}
		return;
	}

	getCookie(cookieName) {
		let cookie = {};
		document.cookie.split(';').forEach(function (el) {
			let [key, value] = el.split('=');
			cookie[key.trim()] = value;
		});
		return cookie[cookieName];
	}

	async componentDidMount() {
		const response_url = await fetch('api/url/');
		this.fetchErrorMessage(response_url);
		const data_url = await response_url.json();

		let url = 'https://' + data_url + '/api/' + this.props.entity_pk + '/get_children_tree/';

		const response_children_tree = await fetch(url);
		this.fetchErrorMessage(response_children_tree);
		const data_children_tree = await response_children_tree.json();

		const cookieValue = this.getCookie('language_code');

		this.setState(() => {
			return {
				default_language: cookieValue,
				selected_human: cookieValue,
				selected_diag: cookieValue,
				is_diag_one_entity_eval: data_children_tree.length == 1,
				diag_accessible_entities: data_children_tree,
				diag_entities_found: true,
			};
		});
		if (this.state.is_diag_one_entity_eval) {
			this.setState(() => {
				return {
					diag_selected_entities: data_children_tree,
				};
			});
		}
	}

	scrollToTopHuman() {
		document.getElementById('excel_human_filters_Modal').scroll({ top: 0, behavior: 'smooth' });
	}

	scrollToTopDiag() {
		document.getElementById('excel_diag_filters_Modal').scroll({ top: 0, behavior: 'smooth' });
	}

	gotofilter(index) {
		this.scrollToTopHuman();
		this.setState(() => {
			return {
				acutalfilterpage: index,
			};
		});
	}
	createfilterbutton_human(index) {
		if (index == this.state.acutalfilterpage) return;
		return (
			<button
				type="button"
				className="btn btn-primary"
				id={'filter ' + index}
				key={index}
				onClick={() => {
					this.gotofilter(index);
				}}
			>
				{gettext('Aller au filtre n°')}
				{index}
			</button>
		);
	}

	reset_human_form_state() {
		this.setState(() => {
			return {
				document_human_is_downloading: false,
				downloading_human_finished: false,
				downloading_human_error: false,
				is_download_human_message: false,
				download_human_message: '',
				numberOfFilter: 1,
				filterpage: [1],
				acutalfilterpage: 1,
			};
		});
		document.getElementById('close_btn_excel_human_filters').click();
	}

	async download_diag_human_sheet(language_code) {
		const directdownloadbutton = document.getElementById('direct_download_button');
		const directdownloadelement = document.getElementById('direct_download_element');
		const directdownloadmsg = document.getElementById('direct_download_msg');

		directdownloadbutton.setAttribute('aria-expanded', 'false');
		directdownloadbutton.style.opacity = '0.5';
		directdownloadbutton.style.pointerEvents = 'none';
		directdownloadelement.style.display = 'block';
		directdownloadmsg.textContent = gettext('chargement en cours ...');
		await fetch(`/scoring/evaluation/${this.props.evaluation.pk}/download_diag_human_sheet/`, {
			credentials: 'include',
			method: 'POST',
			headers: {
				'Content-Type': 'application/json;charset=utf-8',
				'X-CSRFToken': csrftoken,
			},
			body: JSON.stringify({ language_code: language_code }),
		})
			.then((response) => response.json())
			.then((data) => {
				directdownloadelement.style.display = 'block';
				if (data.code == 200) {
					directdownloadelement.style.backgroundColor = 'rgb(50, 255, 50, 50)';
					directdownloadmsg.textContent = data.message;
				} else if (data.code == 404) {
					directdownloadelement.style.backgroundColor = 'rgb(255, 15, 0, 50)';
					directdownloadmsg.textContent = data.message;
				} else {
					directdownloadelement.style.backgroundColor = 'rgb(255, 127, 0, 50)';
					directdownloadmsg.textContent = gettext('une erreur interne est survenue merci de réessayer plus tard');
				}
				setTimeout(() => {
					directdownloadelement.style.backgroundColor = 'rgb(255, 255, 255, 0)';
					directdownloadelement.style.display = 'none';
					directdownloadmsg.textContent = '';
				}, 5000);
			})
			.catch((error) => {
				directdownloadelement.style.backgroundColor = 'rgb(255, 127, 0, 50)';
				directdownloadmsg.textContent = gettext('une erreur interne est survenue merci de réessayer plus tard');
			});
		setTimeout(async () => {
			directdownloadelement.style.backgroundColor = 'rgb(255, 255, 255, 0)';
			directdownloadelement.style.display = 'none';
			directdownloadmsg.textContent = '';
			directdownloadbutton.style = { opacity: '1', cursor: 'pointer' };
		}, 5000);
	}

	delete_this_filter_human() {
		this.scrollToTopHuman();
		let newfilterpage = this.state.filterpage;

		const index = newfilterpage.indexOf(this.state.acutalfilterpage);
		newfilterpage.splice(index, 1);

		this.setState(() => {
			return {
				numberOfFilter: this.state.numberOfFilter - 1,
				acutalfilterpage: 1,
				filterpage: newfilterpage,
			};
		});
	}
	add_one_filter_human() {
		this.scrollToTopHuman();
		let newfilterpage = this.state.filterpage;
		newfilterpage.push(this.state.numberOfFilter + 1);
		this.setState(() => {
			return {
				numberOfFilter: this.state.numberOfFilter + 1,
				acutalfilterpage: newfilterpage.length,
				filterpage: newfilterpage,
			};
		});
	}
	async validate_react_form_human() {
		// Getting filters
		let human_selected_filters = { pk: 0, language_code: '', filterlist: {} };
		let All_filters = document.querySelectorAll('.excel_collab_filter');
		let All_human_criteria = document.querySelectorAll('.excel_collab_human_criteria');

		human_selected_filters['pk'] = document.getElementById('human_excel_pk').getAttribute('data-pk');

		// Collab Filters
		await All_filters.forEach(function (f) {
			let checked_values = f.children[2].querySelectorAll('input[type="checkbox"]:checked');
			let filterid = f.id;
			let slug = f.children[1].id;
			if (human_selected_filters['filterlist'][filterid] == undefined) human_selected_filters['filterlist'][filterid] = {};

			if (human_selected_filters['filterlist'][filterid]['collab_filters'] == undefined)
				human_selected_filters['filterlist'][filterid]['collab_filters'] = {};

			if (human_selected_filters['filterlist'][filterid]['collab_filters'][slug] == undefined)
				human_selected_filters['filterlist'][filterid]['collab_filters'][slug] = [];
			checked_values.forEach(function (value) {
				let current_label = value.getAttribute('choice-value');
				let current_value = value.getAttribute('choice-key');
				human_selected_filters['filterlist'][filterid]['collab_filters'][slug].push({ slug: current_value, label: current_label });
			});
		});
		// Collab Human Criteria
		await All_human_criteria.forEach(function (f) {
			let checked_values = f.children[2].querySelectorAll('input[type="checkbox"]:checked');
			let filterid = f.id;
			let slug = f.children[1].textContent;
			if (human_selected_filters['filterlist'][filterid] == undefined && checked_values.length > 0) human_selected_filters['filterlist'][filterid] = {};
			if (human_selected_filters['filterlist'][filterid]['collab_human_criteria'] == undefined)
				human_selected_filters['filterlist'][filterid]['collab_human_criteria'] = {};
			if (human_selected_filters['filterlist'][filterid]['collab_human_criteria'][slug] == undefined && checked_values.length > 0) {
				human_selected_filters['filterlist'][filterid]['collab_human_criteria'][slug] = [];
			}
			checked_values.forEach(function (value) {
				let current_choice = value.getAttribute('choice-id');

				human_selected_filters['filterlist'][filterid]['collab_human_criteria'][slug].push(current_choice);
			});
		});

		// get the selected language
		let language_code = document.querySelector('.excel_human_languages').querySelector('input[type="radio"]:checked');
		if (language_code) {
			human_selected_filters['language_code'] = language_code.getAttribute('choice-id');
		}

		if (human_selected_filters['language_code']) {
			// Sending filters to APIView
			this.scrollToTopHuman();
			this.setState(() => {
				return {
					document_human_is_downloading: true,
				};
			});
			return fetch(`/scoring/evaluation/${this.props.evaluation.pk}/react_human_filtered_excel/`, {
				credentials: 'include',
				method: 'POST',
				headers: {
					'Content-Type': 'application/json;charset=utf-8',
					'X-CSRFToken': csrftoken,
				},
				body: JSON.stringify(human_selected_filters),
			})
				.then((response) => response.json())
				.then((data) => {
					if (data.result === 'failure') {
						if (data.reason == 'not_enough_collaborators' && data.filter_index != undefined) {
							let errormsg = gettext("Il n'y a pas assez de collaborateurs pour le filtre n°") + data.filter_index;
							this.setState(() => {
								return {
									downloading_human_finished: true,
									download_human_message: errormsg,
									is_download_human_message: true,
									downloading_human_error: true,
								};
							});
							setTimeout(() => {
								this.reset_human_form_state();
							}, 5000);
						}
					} else if (data.result === 'close') {
						this.setState(() => {
							return {
								downloading_human_finished: true,
								is_download_human_message: true,
								download_human_message: gettext(
									"Votre fichier a fini d'être généré, vous devriez avoir reçu un email avec le fichier en pièce jointe.",
								),
							};
						});
						setTimeout(() => {
							this.reset_human_form_state();
						}, 5000);
					} else {
						this.setState(() => {
							return {
								downloading_human_finished: true,
								is_download_human_message: true,
								downloading_human_error: true,
								download_human_message: gettext("Une erreur s'est produite merci de réessayer plus tard."),
							};
						});
						setTimeout(() => {
							this.reset_human_form_state();
						}, 5000);
					}
				})
				.catch((error) => {
					this.setState(() => {
						return {
							downloading_human_finished: true,
							is_download_human_message: true,
							downloading_human_error: true,
							download_human_message: gettext("Une erreur s'est produite merci de réessayer plus tard."),
						};
					});
					setTimeout(() => {
						this.reset_human_form_state();
					}, 5000);
				});
		} else {
			alert(gettext('Veuillez choisir une langue !'));
		}
		setTimeout(() => {
			this.reset_human_form_state();
		}, 5000);
	}

	reset_diag_form_state() {
		this.setState(() => {
			return {
				document_diag_is_downloading: false,
				downloading_diag_finished: true,
				downloading_diag_error: false,
				is_download_diag_message: false,
				download_diag_message: '',
				diag_selected_entities: [],
			};
		});
		document.getElementById('close_btn_excel_diag_filters').click();
	}

	async validate_react_form_diag() {
		const error_info = document.getElementById('error_info');

		if (!this.state.is_diag_one_entity_eval && this.state.diag_selected_entities.length == 0) {
			error_info.innerText = gettext('Sélectionnez vos entités');
			return;
		}

		error_info.innerText = '';

		const filterselected = this.state.selected_filter_diag;
		const language_selected = document.querySelector('.excel_diag_languages').querySelector('input[type="radio"]:checked');
		console.log(`validate_react_form_diag with ${this.state.selected_filter_diag} and lang ${this.state.selected_diag}`);

		if (language_selected != null) {
			this.scrollToTopDiag();
			this.setState(() => {
				return {
					document_diag_is_downloading: true,
					downloading_diag_finished: false,
				};
			});
			var pk_list = this.state.diag_selected_entities;
			if (this.state.is_diag_one_entity_eval) pk_list = [];
			return fetch(`/scoring/evaluation/${this.props.evaluation.pk}/react_diag_excel/`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json;charset=utf-8',
					'X-CSRFToken': csrftoken,
				},
				body: JSON.stringify({ filter: filterselected, language_code: this.state.selected_diag, pk_list: pk_list }),
			})
				.then((response) => response.json())
				.then((data) => {
					if (data.status === 'success') {
						this.setState(() => {
							return {
								downloading_diag_finished: true,
								is_download_diag_message: true,
								download_diag_message: gettext(
									"Votre fichier a fini d'être généré, vous devriez avoir reçu un email avec le fichier en pièce jointe.",
								),
							};
						});
					} else if (data.status === 'error') {
						this.setState(() => {
							return {
								downloading_diag_finished: true,
								is_download_diag_message: true,
								downloading_diag_error: true,
								download_diag_message: gettext("une erreur s'est produite lors de la génération de votre fichier"),
							};
						});
					}
					setTimeout(() => {
						this.reset_diag_form_state();
					}, 5000);
				})
				.catch((error) => {
					this.setState(() => {
						return {
							downloading_diag_finished: true,
							is_download_diag_message: true,
							downloading_diag_error: true,
							download_diag_message: gettext(
								"une erreur interne s'est produite lors de la génération de votre fichier, merci de réessayer plus tard",
							),
						};
					});
					setTimeout(() => {
						this.reset_diag_form_state();
					}, 5000);
				});
		}
	}

	render() {
		return (
			<>
				<meta id="human_excel_pk" data-pk={this.props.evaluation.pk} />
				<div className="d-flex flex-row align-items-center">
					{this.props.evaluation.is_human ? (
						// HUMAN DOWNLOAD ELEMENT
						<>
							<button
								type="button"
								className="mxt--small button border assess_white_btn p-0 px-1"
								data-bs-toggle="modal"
								data-bs-target="#excel_human_filters_Modal"
							>
								<i className="bi bi-cloud-download"></i>
								{this.props.evaluation.is_validated_by_user ? `${gettext('Excel avec filtres')}` : `${gettext('Excel avec filtres en cours')}`}
							</button>
							<div>
								<div
									className="modal fade"
									id="excel_human_filters_Modal"
									tabIndex="-1"
									aria-labelledby="excel_human_filters_label"
									aria-hidden="true"
								>
									<div className="modal-dialog">
										<div className="modal-content">
											{this.state.document_human_is_downloading ? (
												<>
													<div className="modal-header" style={{ marginBottom: '100px' }}>
														<h5 className="modal-title" id="excel_human_filters_label">
															{gettext('Création du fichier ...')}
														</h5>
														<button
															type="button"
															id="close_btn_excel_human_filters"
															className="btn-close"
															data-bs-dismiss="modal"
															aria-label="Close"
														></button>
													</div>
													<div
														className="modal-body"
														id="top_download_elem"
														data-bs-target="#top_download_elem"
														style={{ paddingBottom: '150px' }}
													>
														{this.state.downloading_human_finished ? (
															<>
																{this.state.downloading_human_error ? (
																	<>
																		<h5> {gettext("Une erreur s'est produite")}</h5>
																		<h6> {this.state.download_human_message}</h6>
																	</>
																) : (
																	<>
																		<h5> {gettext('Votre fichier est prêt')}</h5>
																		<h6> {this.state.download_human_message}</h6>
																	</>
																)}
															</>
														) : (
															<>
																<h5> {gettext('génération en cours...')}</h5>
																<h6> {gettext("Cela devrait durer moins d'une minute")}</h6>
															</>
														)}
													</div>
												</>
											) : (
												<>
													<div className="modal-header">
														<h5 className="modal-title" id="excel_human_filters_label">
															{gettext('Choisir vos filtres')}
														</h5>
														<button
															type="button"
															id="close_btn_excel_human_filters"
															className="btn-close"
															data-bs-dismiss="modal"
															aria-label="Close"
														></button>
													</div>
													<div className="modal-body">
														<div style={{ display: this.state.acutalfilterpage != 1 ? 'none' : 'block' }}>
															<h5 className="mb-4">{gettext('Langues')}</h5>
															<form className="d-flex flex-column flex-wrap">
																<div className="excel_human_languages">
																	{this.props.languages.map((language) => {
																		if (this.props.evaluation.is_human && this.props.google_sheet_lang.includes(language)) {
																			return (
																				<div className="form-check" key={language.code}>
																					<input
																						className="form-check-input"
																						name="execl_filtered_languages"
																						type="radio"
																						value={language.code}
																						id={`${language.code}__radio`}
																						choice-id={language.code}
																						onChange={this.handleChange_human}
																						checked={this.state.selected_human == language.code}
																					/>
																					<label className="form-check-label" htmlFor={`${language.code}__radio`}>
																						<span className={`icon-flag-${language.code}`}></span>
																						{language.slug}({language.code.toUpperCase()})
																					</label>
																				</div>
																			);
																		}
																		return null;
																	})}
																</div>
															</form>
														</div>

														{Object.entries(this.state.filterpage).map(([main_key, main_value]) => {
															return (
																<div
																	key={main_key}
																	style={{ display: main_value != this.state.acutalfilterpage ? 'none' : 'block' }}
																>
																	<hr
																		className="solid"
																		style={{
																			borderColor: '#DEDFEA',
																			display: this.state.acutalfilterpage != 1 ? 'none' : 'block',
																		}}
																	/>
																	<h5 className="mb-4">Filtres n°{parseInt(main_value)}</h5>
																	{Object.entries(this.props.filters).map(([key, value]) => {
																		if (value.is_human_criteria) {
																			return (
																				<div className="excel_collab_human_criteria" id={main_value} key={key}>
																					<hr className="solid" style={{ borderColor: '#DEDFEA' }} />
																					<h6 className="mb-4">{value.label}</h6>
																					<form className="d-flex flex-column flex-wrap">
																						{value.choices.map((choice) =>
																							Object.entries(choice).map(([choiceKey, choiceValue]) => (
																								<div className="form-check" key={choiceValue}>
																									<input
																										className="form-check-input"
																										type="checkbox"
																										value=""
																										id={`${choiceValue}__check`}
																										choice-id={choiceValue}
																										choice-value={choiceKey}
																									/>
																									<label
																										className="form-check-label"
																										htmlFor={`${choiceValue}__check`}
																									>
																										{choiceKey}
																									</label>
																								</div>
																							)),
																						)}
																					</form>
																				</div>
																			);
																		} else {
																			return (
																				<div className="excel_collab_filter" id={main_value} key={key}>
																					<hr className="solid" style={{ borderColor: '#DEDFEA' }} />
																					<h6 id={key} className="mb-4">
																						{value.label}
																					</h6>
																					<form className="d-flex flex-column flex-wrap">
																						{value.choices.map((choice) =>
																							Object.entries(choice).map(([choiceKey, choiceValue]) => (
																								<div className="form-check" key={choiceKey}>
																									<input
																										className="form-check-input"
																										type="checkbox"
																										value=""
																										id={`${choiceKey}__check`}
																										choice-key={choiceKey}
																										choice-value={choiceValue}
																									/>
																									<label
																										className="form-check-label"
																										id={`${choiceKey}__label`}
																										htmlFor={`${choiceKey}__check`}
																									>
																										{choiceValue}
																									</label>
																								</div>
																							)),
																						)}
																					</form>
																				</div>
																			);
																		}
																	})}
																</div>
															);
														})}
													</div>
													{/* creatign a button for every filter using the filternumber*/}
													<div className="modal-footer">
														{Object.entries(this.state.filterpage).map(([key, value]) => {
															return this.createfilterbutton_human(parseInt(key) + 1);
														})}
														{this.state.numberOfFilter > 1 && this.state.acutalfilterpage != 1 ? (
															<button
																type="button"
																className="btn btn-primary"
																onClick={() => {
																	this.delete_this_filter_human();
																}}
															>
																{gettext('supprimer ce filtre')}
															</button>
														) : (
															<></>
														)}
														<button
															type="button"
															className="btn btn-primary"
															onClick={() => {
																this.add_one_filter_human();
															}}
														>
															{gettext('Ajouter un filtre')}
														</button>
														<button
															type="button"
															className="btn btn-primary"
															onClick={() => {
																this.validate_react_form_human();
															}}
														>
															{gettext('Valider')}
														</button>
													</div>
												</>
											)}
										</div>
									</div>
								</div>
							</div>
						</>
					) : (
						// DIAG DOWNLOAD ELEMENT
						<>
							<>
								<button
									type="button"
									className="mxt--small button border assess_white_btn p-0 px-3"
									data-bs-toggle="modal"
									data-bs-target="#excel_diag_filters_Modal"
								>
									<i className="bi bi-cloud-download"></i>
									{this.props.evaluation.is_validated_by_user
										? `${gettext('Télécharger le questionnaire')}`
										: `${gettext('Questionnaire en cours')}`}
								</button>
								<div>
									<div
										className="modal fade"
										id="excel_diag_filters_Modal"
										tabIndex="-1"
										aria-labelledby="excel_diag_filters_label"
										aria-hidden="true"
									>
										<div className="modal-dialog">
											<div className="modal-content">
												{this.state.document_diag_is_downloading ? (
													<>
														<div className="modal-header" style={{ marginBottom: '100px' }}>
															<h5 className="modal-title" id="excel_diag_filters_label">
																{gettext('Création du fichier ...')}
															</h5>
															<button
																type="button"
																id="close_btn_excel_diag_filters"
																className="btn-close"
																data-bs-dismiss="modal"
																aria-label="Close"
															></button>
														</div>
														<div
															className="modal-body"
															id="top_download_elem"
															data-bs-target="#top_download_elem"
															style={{ paddingBottom: '150px' }}
														>
															{this.state.downloading_diag_finished ? (
																<>
																	{this.state.downloading_diag_error ? (
																		<>
																			<h5> {gettext("Une erreur s'est produite")}</h5>
																			<h6> {this.state.download_diag_message}</h6>
																		</>
																	) : (
																		<>
																			<h5> {gettext('Votre fichier est prêt')}</h5>
																			<h6> {this.state.download_diag_message}</h6>
																		</>
																	)}
																</>
															) : (
																<>
																	<h5> {gettext('génération en cours...')}</h5>
																	<h6> {gettext("Cela devrait durer moins d'une minute")}</h6>
																</>
															)}
														</div>
													</>
												) : (
													<>
														<div className="modal-header">
															<h4 className="modal-title" id="excel_diag_filters_label">
																{gettext('Questionnaire')}
															</h4>
															<button
																type="button"
																id="close_btn_excel_diag_filters"
																className="btn-close"
																data-bs-dismiss="modal"
																aria-label="Close"
															></button>
														</div>
														{this.state.error || !this.state.diag_entities_found ? (
															<div>
																{this.state.error ? (
																	<h5 className="m-4">{gettext(this.state.error_message)}</h5>
																) : (
																	<h5 className="m-4">{gettext('Chargement')}</h5>
																)}
															</div>
														) : (
															<div className="modal-body">
																<div>
																	<h5 className="mb-4">{gettext('Langues')}</h5>
																	<form className="d-flex flex-column flex-wrap">
																		<div className="excel_diag_languages">
																			{this.props.languages.map((language) => {
																				if (
																					!this.props.evaluation.is_human &&
																					this.props.enabled_lang.includes(language)
																				) {
																					return (
																						<div className="form-check" key={language.code}>
																							<input
																								className="form-check-input"
																								name="execl_filtered_languages"
																								type="radio"
																								value={language.code}
																								id={`${language.code}__radio`}
																								choice-id={language.code}
																								onChange={this.handleChange_diag}
																								checked={this.state.selected_diag == language.code}
																							/>
																							<label
																								className="form-check-label"
																								htmlFor={`${language.code}__radio`}
																							>
																								<span className={`icon-flag-${language.code}`}></span>
																								{language.slug}({language.code.toUpperCase()})
																							</label>
																						</div>
																					);
																				}
																				return null;
																			})}
																		</div>
																	</form>
																</div>
																<div style={{ marginBottom: '10px' }}>
																	<hr className="solid" style={{ borderColor: 'rgb(222, 223, 234)', display: 'block' }}></hr>

																	<h5>{gettext('Choisir le questionnaire')}</h5>
																	<form className="d-flex flex-column flex-wrap">
																		{this.state.diag_possible_choice.map((choice) =>
																			Object.entries(choice).map(([choiceKey, choiceValue]) => (
																				<div className="form-check" key={choiceKey}>
																					<input
																						className="form-check-input"
																						type="checkbox"
																						value={choiceKey}
																						choice-value={choiceKey}
																						onChange={this.handleFilterChange_diag}
																						checked={this.state.selected_filter_diag == choiceKey}
																					/>
																					<label className="form-check-label">{choiceValue}</label>
																				</div>
																			)),
																		)}
                                    									{this.props.csrd_tag_is_on &&
                                    										<div className="form-check" key="csrd">
                                    											<input
                                    												className="form-check-input"
                                    												type="checkbox"
                                    												value="csrd"
                                    												choice-value="csrd"
                                    												onChange={this.handleFilterChange_diag}
                                    												checked={this.state.selected_filter_diag == "csrd"}
                                    											/>
                                    											<label
                                    												className="form-check-label"
                                    											>
                                    												{gettext("Les questions de la catégorie CSRD uniquement")}
                                    											</label>
                                    										</div>
                                    									}
																	</form>
																</div>
																{this.props.evaluation && !this.state.is_diag_one_entity_eval && (
																	<div style={{ marginBottom: '10px' }}>
																		<hr
																			className="solid"
																			style={{ borderColor: 'rgb(255, 223, 234)', display: 'block' }}
																		></hr>

																		<h5>{gettext('Choisir les entités')}</h5>
																		<form className="d-flex flex-column flex-wrap">
																			{this.state.diag_accessible_entities.map((entity) => (
																				<div className="form-check" key={entity.pk}>
																					<input
																						className="form-check-input"
																						type="checkbox"
																						value={entity.pk}
																						choice-value={entity.pk}
																						onChange={this.handleEntityChange_diag}
																					/>
																					<label className="form-check-label">{entity.name}</label>
																				</div>
																			))}
																		</form>
																	</div>
																)}
															</div>
														)}

														{/* creatign a button for every filter using the filternumber*/}
														{!this.state.error && this.state.diag_entities_found && (
															<div className="modal-footer">
																<div>
																	<h6 className="mr-3" id="error_info"></h6>
																</div>
																<button type="button" className="btn btn-primary" onClick={this.validate_react_form_diag}>
																	{gettext('Valider')}
																</button>
															</div>
														)}
													</>
												)}
											</div>
										</div>
									</div>
								</div>
							</>
							{/* <>  FOR LATER
                <button
                  type="button"
                  className="mxt--small button border assess_white_btn p-0 px-1"
                  data-bs-toggle="modal"
                  data-bs-target="#excel_diag_filters_Modal"
                >
                  <i className="bi bi-cloud-download"></i>
                  {this.props.evaluation.is_validated_by_user
                    ? `${gettext("Excel avec filtres")}`
                    : `${gettext("Excel avec filtres en cours")}`}
                </button>
                <div>
                  <div
                    className="modal fade"
                    id="excel_diag_filters_Modal"
                    tabIndex="-1"
                    aria-labelledby="excel_diag_filters_label"
                    aria-hidden="true"
                  >
                    <div className="modal-dialog">
                      <div className="modal-content">
                        {this.state.document_diag_is_downloading ?
                          <>
                            <div className="modal-header" style={{ marginBottom: "100px" }}>
                              <h5 className="modal-title" id="excel_diag_filters_label">{gettext("Création du fichier ...")}</h5>
                              <button type="button" id="close_btn_excel_diag_filters" className="btn-close" data-bs-dismiss="modal" aria-label="Close">
                              </button>
                            </div>
                            <div className="modal-body" id="top_download_elem" data-bs-target="#top_download_elem" style={{ paddingBottom: "150px" }}>
                              {this.state.downloading_diag_finished ?
                                <>
                                  {this.state.downloading_diag_error ?
                                    <>
                                      <h5> {gettext("Une erreur s'est produite")}</h5>
                                      <h6> {this.state.download_diag_message}</h6>

                                    </>
                                    :
                                    <>
                                      <h5> {gettext("Votre fichier est prêt")}</h5>
                                      <h6> {this.state.download_diag_message}</h6>

                                    </>
                                  }
                                </>
                                :
                                <>
                                  <h5> {gettext("génération en cours...")}</h5>
                                  <h6> {gettext("Cela devrait durer moins d'une minute")}</h6>

                                </>
                              }
                            </div>
                          </>
                          :
                          <>
                            <div className="modal-header">
                              <h5 className="modal-title" id="excel_diag_filters_label">
                                {gettext("Choisir vos filtres")}
                              </h5>
                              <button
                                type="button"
                                id="close_btn_excel_diag_filters"
                                className="btn-close"
                                data-bs-dismiss="modal"
                                aria-label="Close"
                              ></button>
                            </div>
                            <div className="modal-body">
                              <div>
                                <h5 className="mb-4">{gettext("Langues")}</h5>
                                <form className="d-flex flex-column flex-wrap">
                                  <div className="excel_diag_languages">
                                    {this.props.languages.map((language) => {
                                      if (
                                        !this.props.evaluation.is_human && this.props.enabled_lang.includes(language)) {
                                        return (
                                          <div className="form-check" key={language.code}>
                                            <input
                                              className="form-check-input"
                                              name="execl_filtered_languages"
                                              type="radio"
                                              value={language.code}
                                              id={`${language.code}__radio`}
                                              choice-id={language.code}
                                              onChange={this.handleChange_diag}
                                              checked={this.state.selected_diag == language.code}
                                            />
                                            <label
                                              className="form-check-label"
                                              htmlFor={`${language.code}__radio`}
                                            >
                                              <span
                                                className={`icon-flag-${language.code}`}
                                              ></span>
                                              {language.slug}
                                              ({language.code.toUpperCase()})
                                            </label>
                                          </div>
                                        );
                                      }
                                      return null;
                                    })}
                                  </div>
                                </form>
                              </div>
                              <div style={{ marginBottom: '10px' }}>
                                <hr className="solid" style={{ borderColor: "rgb(222, 223, 234)", display: "block" }}></hr>

                                <h4>{gettext("Questionnaire")}</h4>
                                <form className="d-flex flex-column flex-wrap">
                                  {this.state.diag_possible_choice.map((choice) => (
                                    Object.entries(choice).map(([choiceKey, choiceValue]) => (
                                      <div className="form-check" key={choiceKey}>
                                        <input
                                          className="form-check-input"
                                          type="checkbox"
                                          value={choiceKey}
                                          choice-value={choiceKey}
                                          onChange={this.handleFilterChange_diag}
                                          checked={this.state.selected_filter_diag == choiceKey}
                                        />
                                        <label
                                          className="form-check-label"
                                        >
                                          {choiceValue}
                                        </label>
                                      </div>
                                    ))
                                  ))}
                                </form>

                              </div>
                            </div>


                            <div className="modal-footer">
                              <button
                                type="button"
                                className="btn btn-primary"
                                onClick={this.validate_react_form_diag}
                              >
                                {gettext("Valider")}
                              </button>

                            </div>
                          </>
                        }
                      </div>
                    </div>
                  </div>
                </div>

              </> */}
						</>
					)}
				</div>
			</>
		);
	}
}

export default AssessSheetDownload;
