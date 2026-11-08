import React, { Component } from 'react';
import Loading from '../../mixity/dashboard/js/includes/Loading';
import { Breadcrumb, Card, Modal, Form } from 'react-bootstrap';
import moment from 'moment';
import Header from '../../mixity/dashboard/js/includes/Header';

class Overview extends Component {
	constructor(props) {
		super(props);
		this.state = {
			entity: {},
			entities: [],
			user: {},
			structure: {},
			categories: [],
			objectives: [],
			kpis: [],
			savedKpis: [],
			genericKpis: [],
			actions: [],
			savedActions: [],
			entityFilter: [],
			referentFilter: [],
			activeFilter: true,
			all_possible_referent: [],
			showEntityModal: false,
			filterKpis: [],
			months: [],
			monthsShort: [],
			todayDate: new Date(),
			yearDate: null,
			activeMonth: '',
			filteredKpis: [],
			actionsPercentage: 0,
			actionCount: 0,
			actionsBudget: 0,
			url: '',
			scoresShown: 0,
			categoriesLoaded: false,
			objectivesLoaded: false,
			entityLoaded: false,
			genericKpisLoaded: false,
			entitiesLoaded: true,
			actionStatusChoices: [
				{ value: 'reflection', name: gettext('Action en réflexion') },
				{ value: 'planned', name: gettext('Action planifiée') },
				{ value: 'in_progress', name: gettext('Action en cours') },
				{ value: 'operation', name: gettext('Action pilote') },
				{ value: 'deployed', name: gettext('Action déployée') },
			],
			placeholder: gettext('Chargement'),
		};
	}

	/* Fetch all the datas needed once when loading the page */
	componentDidMount() {
		moment.locale(language_code);
		fetch('api/url/')
			.then((response) => {
				if (response.status > 400) {
					return this.setState(() => {
						return { placeholder: gettext("Quelque chose s'est mal passé !") };
					});
				}
				return response.json();
			})
			.then((data) => {
				if (window.location.pathname.split('/').filter(Boolean)[0]) data += '/' + window.location.pathname.split('/').filter(Boolean)[0];
				this.setState(
					() => {
						return {
							url: window.location.protocol + '//' + data,
						};
					},
					() => {
						fetch(this.state.url + '/api/category/')
							.then((response) => {
								if (response.status > 400) {
									return this.setState(() => {
										return { placeholder: gettext("Quelque chose s'est mal passé !") };
									});
								}
								return response.json();
							})
							.then((data) => {
								var catLabels = [];
								data.filter((cat) => cat.slug !== 'your-suggestions').map((cat) => {
									catLabels.push(cat.name);
								});
								this.setState(
									() => {
										return {
											categories: data.filter((cat) => cat.slug !== 'your-suggestions'),
											categoriesLoaded: true,
										};
									},
									() => {
										fetch(this.state.url + '/api/user/')
											.then((response) => {
												if (response.status > 400) {
													return this.setState(() => {
														return { placeholder: gettext("Quelque chose s'est mal passé !") };
													});
												}
												return response.json();
											})
											.then((data) => {
												this.setState(() => {
													return {
														user: data[0],
														filterKpis: data[0].kpis_tracked,
													};
												});
											});
										fetch(this.state.url + '/api/generickpi/')
											.then((response) => {
												if (response.status > 400) {
													return this.setState(() => {
														return { placeholder: gettext("Quelque chose s'est mal passé !") };
													});
												}
												return response.json();
											})
											.then((data) => {
												this.setState(
													() => {
														return {
															genericKpis: data,
															genericKpisLoaded: true,
														};
													},
													() => {
														fetch(this.state.url + '/api/objective/')
															.then((response) => {
																if (response.status > 400) {
																	return this.setState(() => {
																		return { placeholder: gettext("Quelque chose s'est mal passé !") };
																	});
																}
																return response.json();
															})
															.then((data) => {
																this.setState(
																	() => {
																		return {
																			objectives: data,
																		};
																	},
																	() => {
																		this.setUpValues(data);
																	},
																);
															});
													},
												);
											});
									},
								);
							});
						fetch(this.state.url + '/api/entity/')
							.then((response) => {
								if (response.status > 400) {
									return this.setState(() => {
										return { placeholder: gettext("Quelque chose s'est mal passé !") };
									});
								}
								return response.json();
							})
							.then((data) => {
								this.setState(
									() => {
										return {
											entity: data[0],
											structure: data[0].structure,
											entityLoaded: true,
										};
									},
									() => {
										fetch(this.state.url + '/api/entities/')
											.then((response) => {
												if (response.status > 400) {
													return this.setState(() => {
														return { placeholder: gettext("Quelque chose s'est mal passé !") };
													});
												}
												return response.json();
											})
											.then((data) => {
												var filterList = [];
												data.map((entity) => {
													filterList.push(entity.pk);
												});
												var refList = [];
												var refNameList = [];
												this.state.structure.members.map((member) => {
													refList.push(member.pk);
													member.membership = gettext('Structure Admin');
													refNameList.push(member);
												});
												data.map((entity) => {
													entity.members.map((member) => {
														if (!refList.includes(member.pk)) {
															refList.push(member.pk);
															member.membership = entity.name;
															refNameList.push(member);
														}
													});
												});
												this.setState(() => {
													return {
														entities: data,
														entityFilter: filterList,
														entitiesLoaded: true,
														referentFilter: [...refList, null],
														all_possible_referent: refNameList,
													};
												});
											});
									},
								);
							});
					},
				);
			});
	}

	kpisTrackedManagement(filterList) {
		// Seule la liste des indicateurs suivis est envoyée : un PUT du profil complet était refusé
		// (400) quand le prénom ou le nom est vide, et la réponse d'erreur remplaçait l'utilisateur.
		const user = { ...this.state.user, kpis_tracked: filterList };
		const requestOptions = {
			credentials: 'include',
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
			body: JSON.stringify({ kpis_tracked: filterList }),
		};
		fetch(this.state.url + '/api/user/' + user.pk + '/', requestOptions)
			.then((response) => {
				if (!response.ok) console.log('error while saving tracked kpis');
			})
			.finally(() => {
				this.setState({ user: user, lgShow: false }, () => {
					this.applyFiltersOnKeysIndicator();
				});
			});
	}

	setUpValues(data) {
		var categories = this.state.categories;
		var actions_budget = 0;
		var kpis = [];
		var savedKpis = [];
		var savedActions = [];
		var actions = [];

		//Créer la liste d'actions
		data.map((objective) => {
			actions_budget += objective.total_budget;
			savedActions.push.apply(savedActions, JSON.parse(JSON.stringify(objective)).actions);
			actions.push.apply(actions, objective.actions);
		});

		actions = actions.filter((action) => action.action_date).sort((a, b) => a.action_date.localeCompare(b.action_date));
		savedActions = JSON.parse(JSON.stringify(actions.filter((action) => action.action_date).sort((a, b) => a.action_date.localeCompare(b.action_date))));
		var actions_count = actions.filter((act) => act.status !== 'reflection').length;
		actions.map((action) => {
			action.action_date = new Date(action.action_date);
			action.category = data.find((objective) => objective.pk === action.objective).category;
		});

		savedActions.map((action) => {
			action.action_date = new Date(action.action_date);
			action.category = data.find((objective) => objective.pk === action.objective).category;
		});

		//Créer la liste de kpis
		actions
			.filter((action) => action.status !== 'reflection')
			.map((action) => {
				savedKpis.push.apply(savedKpis, JSON.parse(JSON.stringify(action)).kpis);
				kpis.push.apply(kpis, action.kpis);
			});

		// Additionne les valeurs atteintes des kpis utilisant le même KPI générique
		kpis.map((kpi) => {
			if (kpi.generic_kpi) {
				var same_kpis = kpis.filter((kp) => kp != kpi && kp.generic_kpi === kpi.generic_kpi);
				var pk = kpi.pk;
				kpi.pk = [pk];
				same_kpis.map((addkpi) => {
					kpi.value += addkpi.value;
					kpi.pk.push(addkpi.pk);
					kpis.splice(kpis.indexOf(addkpi), 1);
				});
			}
		});
		kpis.map((kpi) => {
			if (!kpi.label) kpi.label = this.state.genericKpis.find((genkpi) => genkpi.pk === kpi.generic_kpi).label;
		});
		savedKpis.map((kpi) => {
			if (!kpi.label) kpi.label = this.state.genericKpis.find((genkpi) => genkpi.pk === kpi.generic_kpi).label;
		});
		// Aucun indicateur choisi : tous sont affichés, et cochés dans la fenêtre « Indicateurs ».
		const tracked = this.state.user.kpis_tracked || [];
		const filtered = tracked.length ? kpis.filter((kpi) => [].concat(kpi.pk).some((pk) => tracked.includes(pk))) : kpis;
		const filterKpis = tracked.length ? tracked : kpis.flatMap((kpi) => [].concat(kpi.pk));

		//Créer les valeurs supplémentaires nécessaire dans les categories
		categories.map((cat) => {
			cat['number_actions'] = actions.filter((action) => action.status !== 'reflection' && action.category === cat.pk).length;
			cat['actionsBudget'] = 0;
			actions
				.filter((act) => act.category === cat.pk)
				.map((act) => {
					cat['actionsBudget'] += act.budget;
				});
			if (cat['number_actions'] != 0)
				cat['actions_deployed'] =
					(actions.filter((action) => action.status === 'deployed' && action.category === cat.pk).length / cat['number_actions']) * 100;
			else cat['actions_deployed'] = 0;
		});

		var actionsPercentage = 0;
		if (actions_count != 0) actionsPercentage = (actions.filter((act) => act.status === 'deployed').length / actions_count) * 100;

		this.setState({
			categories: categories,
			actionCount: actions_count,
			actionsPercentage: actionsPercentage,
			actionsBudget: actions_budget,
			kpis: kpis,
			savedActions: savedActions,
			savedKpis: savedKpis,
			filteredKpis: filtered,
			filterKpis: filterKpis,
			actions: actions,
			monthsShort: moment.monthsShort(),
			months: moment.months(),
			activeMonth: moment(this.state.todayDate).format('MMM'),
			yearDate: new Date(this.state.todayDate.getFullYear(), 1, 1).toLocaleString(language_code, { year: 'numeric' }),
			objectivesLoaded: true,
		});
	}

	activateMonth(month) {
		this.setState({ activeMonth: month });
	}

	/* Displaying or not the filters modal */
	setLgShow(boolean) {
		this.setState({ lgShow: boolean });
	}

	/* Front filter management */
	handleFilterKpis(pk) {
		var filterList = this.state.filterKpis;
		if (pk[0] && filterList.includes(pk[0])) {
			pk.map((i) => {
				filterList = filterList.filter((kpi) => kpi !== i);
			});
		} else if (filterList.includes(pk)) filterList = this.state.filterKpis.filter((kpi) => kpi !== pk);
		else if (pk[0]) filterList = filterList.concat(pk);
		else filterList.push(pk);
		this.setState({ filterKpis: filterList });
	}

	/* Apply all filters */
	applyFilters() {
		var filterList = this.state.filterKpis;

		if (filterList.length === 0) {
			this.state.savedKpis.map((kpi) => {
				filterList.push(kpi.pk);
			});
		}

		this.kpisTrackedManagement(filterList);
	}

	/* Displaying or not the filters modal */
	setshowEntityModal(boolean) {
		this.setState({ showEntityModal: boolean });
	}

	/* Front filter management */
	handleFilterByEntity(pk) {
		var filterList = this.state.entityFilter;
		if (filterList.includes(pk)) filterList = this.state.entityFilter.filter((kpi) => kpi !== pk);
		else filterList.push(pk);
		this.setState({ entityFilter: filterList }, () => {
			this.applyFiltersOnKeysIndicator();
		});
	}

	/* Front filter management */
	FillFilterByEntity() {
		var filterList = this.state.entityFilter;
		this.state.entities.map((entity) => {
			if (!filterList.includes(entity.pk)) filterList.push(entity.pk);
		});
		this.setState({ entityFilter: filterList }, () => {
			this.applyFiltersOnKeysIndicator();
		});
	}

	/* Front filter management */
	handleFilterByReferent(pk) {
		var filterList = this.state.referentFilter;
		if (filterList.includes(pk)) filterList = this.state.referentFilter.filter((kpi) => kpi !== pk);
		else filterList.push(pk);
		this.setState({ referentFilter: filterList }, () => {
			this.applyFiltersOnKeysIndicator();
		});
	}

	/* Front filter management */
	FillFilterByReferent() {
		var filterList = [];
		this.state.structure.members.map((member) => {
			filterList.push(member.pk);
		});
		filterList.push(null);
		this.state.entities.map((entity) => {
			entity.members.map((member) => {
				if (!filterList.includes(member.pk)) filterList.push(member.pk);
			});
		});
		this.setState({ referentFilter: filterList }, () => {
			this.applyFiltersOnKeysIndicator();
		});
	}

	applyFiltersOnKeysIndicator() {
		let actions = this.state.savedActions
			.filter(({ creation_entity }) => this.state.entityFilter.includes(creation_entity))
			.filter(({ referent }) => this.state.referentFilter.includes(referent));
		let kpis = JSON.parse(
			JSON.stringify(
				this.state.savedKpis
					.filter((kpi) => actions.flatMap((action) => action.kpis.map((kpi) => kpi.pk)).includes(kpi.pk))
					.filter((kpi) => !this.state.user.kpis_tracked.length || this.state.user.kpis_tracked.includes(kpi.pk)),
			),
		);

		// Additionne les valeurs atteintes des kpis utilisant le même KPI générique
		kpis.map((kpi) => {
			if (kpi.generic_kpi) {
				kpi.value = this.state.savedKpis.find((savedkpi) => savedkpi.pk === kpi.pk).value;
				var same_kpis = kpis.filter((kp) => kp != kpi && kp.generic_kpi === kpi.generic_kpi);
				same_kpis.map((addkpi) => {
					kpi.value += addkpi.value;
					kpis.splice(kpis.indexOf(addkpi), 1);
				});
			}
		});

		var actions_budget = 0;
		actions.map((action) => {
			actions_budget += action.budget;
		});

		var actions_count = actions.filter((act) => act.status !== 'reflection').length;

		//Créer les valeurs supplémentaires nécessaire dans les categories
		this.state.categories.map((cat) => {
			cat['number_actions'] = actions.filter((action) => action.status !== 'reflection' && action.category === cat.pk).length;
			cat['actionsBudget'] = 0;
			actions
				.filter((act) => act.category === cat.pk)
				.map((act) => {
					cat['actionsBudget'] += act.budget;
				});
			if (cat['number_actions'] != 0)
				cat['actions_deployed'] =
					(actions.filter((action) => action.status === 'deployed' && action.category === cat.pk).length / cat['number_actions']) * 100;
			else cat['actions_deployed'] = 0;
		});

		var actionsPercentage = 0;
		if (actions_count != 0) actionsPercentage = (actions.filter((act) => act.status === 'deployed').length / actions_count) * 100;

		this.setState({
			filteredKpis: kpis,
			actionCount: actions_count,
			actionsPercentage: actionsPercentage,
			actionsBudget: actions_budget,
			actions: actions,
		});
	}

	convertToRGB(hexa) {
		hexa = hexa.slice(1);
		if (hexa.length != 6) {
			return 'rgba(255, 255, 255, 0.5)';
		}

		var aRgbHex = hexa.match(/.{1,2}/g);
		var aRgb = `rgba(${parseInt(aRgbHex[0], 16)},${parseInt(aRgbHex[1], 16)},${parseInt(aRgbHex[2], 16)},0.5)`;
		return aRgb;
	}

	checkKpi(kpi) {
		if (kpi.generic_kpi && this.state.filterKpis.includes(kpi.pk[0])) return true;
		else if (this.state.filterKpis.includes(kpi.pk)) return true;
		return false;
	}

	render() {
		return this.state.objectivesLoaded &&
			this.state.categoriesLoaded &&
			this.state.entityLoaded &&
			this.state.genericKpisLoaded &&
			this.state.entitiesLoaded ? (
			<div style={{ fontFamily: 'DM Sans' }}>
				<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
					<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
						<Breadcrumb.Item underline="hover" color="inherit" href={'/' + this.state.entity.slug}>
							{gettext('Accueil')}
						</Breadcrumb.Item>
						<Breadcrumb.Item active>{gettext('Piloter')}</Breadcrumb.Item>
						<Breadcrumb.Item underline="hover" color="inherit" active>
							{gettext('Aperçu')}
						</Breadcrumb.Item>
					</Breadcrumb>
					<Header
						data={{ url: this.state.url, languages: languages, language_code: language_code, enabled_website_languages: enabled_website_languages }}
					/>
				</div>
				<div className="p-4">
					<div className="pb-4">
						<div className="d-flex justify-content-between">
							<h4 className="ps-4">{gettext('Indicateurs clés')}</h4>
							<h5 style={{ width: '15%', cursor: 'pointer' }} onClick={() => this.setshowEntityModal(true)}>
								{gettext('Filtres')}
								<i className="bi bi-funnel-fill"></i>
							</h5>
							<button
								className="button border p-2 mx-3 align-middle"
								style={{ borderRadius: '6px', backgroundColor: '#fff' }}
								onClick={() => this.setLgShow(true)}
							>
								<i className="bi bi-sliders2 pe-4"></i>
								{gettext('Indicateurs')}
							</button>
						</div>
						<div className="px-3 d-flex justify-content-between flex-wrap">
							{this.state.filteredKpis.map((kpi) => {
								return (
									<Card key={kpi.pk} className="p-3 my-3 border" style={{ width: '32%', borderRadius: '16px', borderColor: '#DEDFEA' }}>
										<Card.Title style={{ fontSize: '10px', lineHeight: '15px', textAlign: 'center', marginBottom: '0px' }}>
											{
												this.state.categories
													.find((cat) => cat.pk === this.state.savedActions.find((act) => act.pk === kpi.action).category)
													.subcategories.find((subcat) => subcat.pk === kpi.subcategory).name
											}
										</Card.Title>
										<Card.Body className="p-0 py-2 d-flex justify-content-between align-items-center">
											<div className="d-flex justify-content-start" style={{ width: '70%' }}>
												<img
													className="p-2"
													alt=""
													src="/static/img/subcategories/aim.png"
													style={{
														height: '5vh',
														width: 'auto',
														marginRight: '2%',
														backgroundColor: `${this.convertToRGB(this.state.categories.find((cat) => cat.pk === this.state.savedActions.find((act) => act.pk === kpi.action).category).color)}`,
													}}
												/>
												<h6 style={{ fontSize: '14px', lineHeight: '20px', color: '#9094AA' }}>{kpi.label}</h6>
											</div>
											<Card.Title className="px-3" style={{ fontSize: '32px', lineHeight: '40px' }}>
												{Math.round(kpi.value)} {kpi.unit === 'percent' && '%'}
											</Card.Title>
										</Card.Body>
									</Card>
								);
							})}
						</div>
					</div>
					<div className="pb-4">
						<div className="w-50 d-flex justify-content-between pe-2">
							<h4 className="ps-4">{gettext("Plan d'action")}</h4>
							<select
								defaultValue={this.state.scoresShown}
								onChange={(e) => this.setState({ scoresShown: parseInt(e.target.value) })}
								className="selector ms-2 me-4 border"
							>
								<option key={0} value={0}>
									{gettext('Total')}
								</option>
								{this.state.categories.map((cat) => {
									return (
										<option key={cat.pk} value={cat.pk}>
											{gettext(cat.name)}
										</option>
									);
								})}
							</select>
						</div>
						<div className="p-3 d-flex justify-content-between">
							<div className="py-3" style={{ width: '48%' }}>
								<Card
									className="p-3 mb-3 border"
									style={{
										height: '20vh',
										borderRadius: '16px',
										borderColor: 'rgba(255, 111, 111, 0.3)',
										backgroundColor: 'rgba(255, 111, 111, 0.1)',
									}}
								>
									<Card.Body className="p-0 py-2">
										<Card.Title className="px-3" style={{ fontSize: '12px', lineHeight: '20px' }}>
											{gettext('Budget Total')}
										</Card.Title>
										{this.state.categories.find((cat) => cat.pk === this.state.scoresShown) ? (
											<Card.Title className="px-3" style={{ fontSize: '40px', lineHeight: '40px' }}>
												{this.state.categories.find((cat) => cat.pk === this.state.scoresShown).actionsBudget} €
											</Card.Title>
										) : (
											<Card.Title className="px-3" style={{ fontSize: '40px', lineHeight: '40px' }}>
												{this.state.actionsBudget} €
											</Card.Title>
										)}
										<Card.Img
											style={{
												position: 'absolute',
												right: '0px',
												top: '0px',
												borderRadius: '6px',
												height: '100%',
												width: 'fit-content',
											}}
											src="/static/img/total_budget_style.png"
										/>
									</Card.Body>
								</Card>
								<Card
									className="p-3 my-3 border"
									style={{
										height: '20vh',
										borderRadius: '16px',
										borderColor: 'rgba(136, 136, 226, 0.3)',
										backgroundColor: 'rgba(136, 136, 226, 0.1)',
									}}
								>
									<Card.Body className="p-0 py-2">
										<Card.Title className="px-3" style={{ fontSize: '12px', lineHeight: '20px' }}>
											{gettext('Progrès Global')}
										</Card.Title>
										{this.state.categories.find((cat) => cat.pk === this.state.scoresShown) ? (
											<div>
												<Card.Title className="px-3 pb-2" style={{ fontSize: '40px', lineHeight: '40px' }}>
													{Math.round(this.state.categories.find((cat) => cat.pk === this.state.scoresShown).actions_deployed)} %
												</Card.Title>
												<Card.Title className="p-3" style={{ fontSize: '16px', lineHeight: '24px' }}>
													{Math.round(
														this.state.categories.find((cat) => cat.pk === this.state.scoresShown).actions_deployed *
															(this.state.categories.find((cat) => cat.pk === this.state.scoresShown).number_actions / 100),
													)}
													/{this.state.categories.find((cat) => cat.pk === this.state.scoresShown).number_actions}{' '}
													{gettext('actions planifiée complétées')}
												</Card.Title>
											</div>
										) : (
											<div>
												<Card.Title className="px-3 pb-2" style={{ fontSize: '40px', lineHeight: '40px' }}>
													{Math.round(this.state.actionsPercentage)} %
												</Card.Title>
												<Card.Title className="p-3" style={{ fontSize: '16px', lineHeight: '24px' }}>
													{Math.round(this.state.actionCount * (this.state.actionsPercentage / 100))}/{this.state.actionCount}{' '}
													{gettext('actions planifiée complétées')}
												</Card.Title>
											</div>
										)}
										<Card.Img
											style={{
												position: 'absolute',
												right: '0px',
												top: '0px',
												borderRadius: '6px',
												height: '100%',
												width: 'fit-content',
											}}
											src="/static/img/overall_progress_style.png"
										/>
									</Card.Body>
								</Card>
							</div>
							<div className="py-3" style={{ width: '48%' }}>
								<Card className="p-3 border" style={{ borderRadius: '16px', borderColor: '#DEDFEA', backgroundColor: '#fff' }}>
									<Card.Body className="p-0 py-2">
										<Card.Title className="px-2" style={{ fontSize: '20px', lineHeight: '28px' }}>
											{gettext('Dimensions')}
										</Card.Title>
										{this.state.categories.map((category) => {
											return (
												<div key={category.pk} className="p-2">
													<div className="d-flex justify-content-between">
														<div className="w-75 d-flex justify-content-start">
															<h6 style={{ color: '#9094AA' }}>{gettext(category.name)}</h6>
															<div
																className="border text-center ms-2 px-1"
																style={{
																	fontSize: '12px',
																	lineHeight: '16px',
																	borderRadius: '24px',
																	width: 'fit-content',
																	height: 'fit-content',
																	background: '#FAFAFA',
																}}
															>
																<b>
																	{category.number_actions} {gettext('actions')}
																</b>
															</div>
														</div>
														<div>
															<h6 style={{ color: '#9094AA' }}>{Math.round(category.actions_deployed) + '%'}</h6>
														</div>
													</div>
													<div className="progress" style={{ height: '1.5vh' }}>
														<div
															className="progress-bar justify-content-center"
															role="progressbar"
															style={{ width: category.actions_deployed + '%', backgroundColor: `${category.color}` }}
															aria-valuenow={category.actions_deployed}
															aria-valuemin="0"
															aria-valuemax="100"
														></div>
													</div>
												</div>
											);
										})}
									</Card.Body>
								</Card>
							</div>
						</div>
					</div>
					<div className="pb-4">
						<h4 className="ps-4">{gettext('Planning')}</h4>
						<div className="p-4 m-3 border" style={{ background: '#ffffff', borderColor: '#DEDFEA', borderRadius: '16px' }}>
							<div className="p-3">
								<h4>{gettext('Calendrier')}</h4>
								<h6 style={{ fontSize: '12px', lineHeight: '20px', color: '#9094AA' }}>{gettext('Votre planning pour les 12 mois à venir')}</h6>
								<nav className="py-3 tab-menu">
									<div className="nav nav-tabs d-flex justify-content-between" style={{ border: 'none' }} id="nav-tab" role="tablist">
										{this.state.monthsShort.map((month) => {
											return (
												<button
													key={month}
													data-bs-toggle="tab"
													className="border p-3"
													style={{
														textTransform: 'capitalize',
														width: '4vw',
														backgroundColor: `${month === this.state.activeMonth ? '#181B3D' : '#FAFAFA'}`,
														borderColor: '#F0F0F0',
														color: `${month === this.state.activeMonth ? '#fff' : '#9094AA'}`,
														borderRadius: '6px',
													}}
													onClick={() => this.activateMonth(month)}
												>
													<b>
														{
															this.state.actions.filter(
																(action) =>
																	action.action_date.toLocaleString(language_code, { month: 'short' }) === month &&
																	action.action_date.toLocaleString(language_code, { year: 'numeric' }) ===
																		this.state.yearDate,
															).length
														}
													</b>
													<br />
													{month}
												</button>
											);
										})}
									</div>
								</nav>
								<h5 style={{ textTransform: 'capitalize' }}>{this.state.months[this.state.monthsShort.indexOf(this.state.activeMonth)]}</h5>
								<div className="d-flex justify-content-between flex-wrap">
									{this.state.actions
										.filter(
											(action) =>
												action.action_date.toLocaleString(language_code, { month: 'short' }) === this.state.activeMonth &&
												action.action_date.toLocaleString(language_code, { year: 'numeric' }) >= this.state.yearDate,
										)
										.map((action) => {
											return (
												<div key={action.pk} className="py-2 w-50">
													<div
														className="ps-3"
														style={{
															borderLeft: 'solid',
															borderWidth: '3px',
															borderColor: `${this.state.categories.find((cat) => cat.pk === action.category).color}`,
														}}
													>
														<Card.Title
															className="p-0 m-0"
															style={{
																fontSize: '16px',
																lineHeight: '32px',
																color: `${action.action_date >= this.state.todayDate ? '#000' : '#9094AA'}`,
															}}
														>
															{action.label}
														</Card.Title>
														<Card.Text className="p-0 m-0" style={{ fontSize: '12px', color: '#9094AA' }}>
															{this.state.actionStatusChoices.find((st) => st.value === action.status).name +
																' - ' +
																moment(action.action_date).format('DD/MM/YYYY')}
														</Card.Text>
													</div>
												</div>
											);
										})}
								</div>
							</div>
						</div>
					</div>
				</div>
				<Modal
					size="lg"
					show={this.state.lgShow}
					onHide={() => this.setLgShow(false)}
					aria-labelledby="contained-modal-title-vcenter"
					style={{ zIndex: '1050', width: '100%' }}
					className="m-0 p-0"
				>
					<Modal.Header closeButton>
						<Modal.Title id="contained-modal-title-vcenter">{gettext('Indicateurs')}</Modal.Title>
					</Modal.Header>
					<Modal.Body>
						<Form>
							{this.state.kpis.map((kpi) => (
								<div key={kpi.pk} className="mb-3">
									<Form.Check
										type={'checkbox'}
										checked={this.checkKpi(kpi)}
										value={kpi.pk}
										label={
											kpi.label +
											'  /  ' +
											this.state.categories.find(
												(cat) => cat.pk === this.state.savedActions.find((act) => act.pk === kpi.action).category,
											).name
										}
										onChange={() => this.handleFilterKpis(kpi.pk)}
									/>
								</div>
							))}
						</Form>
					</Modal.Body>
					<Modal.Footer className="d-flex justify-content-between">
						<button
							className="button border m-2"
							style={{ background: '#fff', borderColor: '#000', color: '#000', borderRadius: '6px' }}
							onClick={() => this.setState({ filterKpis: [] })}
						>
							{gettext('Vider les filtres')}
						</button>
						<button
							className="button border m-2"
							style={{ background: '#8785BB', borderColor: '#8785BB', color: '#fff', borderRadius: '6px' }}
							onClick={() => this.applyFilters()}
						>
							{gettext('Appliquer')}
						</button>
					</Modal.Footer>
				</Modal>
				{/* Modal to filter entity and referent */}
				<Modal
					size="lg"
					show={this.state.showEntityModal}
					onHide={() => this.setshowEntityModal(false)}
					aria-labelledby="contained-modal-title-vcenter"
					style={{ zIndex: '1050', width: '100%' }}
					className="m-0 p-0"
				>
					<Modal.Header closeButton>
						<nav className="tab-menu">
							<div className="nav nav-tabs d-flex justify-content-start" id="nav-tab" role="tablist">
								<button
									data-bs-toggle="tab"
									className={`nav-link ${this.state.activeFilter ? 'active' : ''}`}
									style={{ border: 'none', fontSize: `${this.state.activeFilter ? '1.2rem' : '0.8rem'}` }}
									onClick={() => this.setState({ activeFilter: true })}
								>
									{gettext('Entités')}
								</button>
								<button
									data-bs-toggle="tab"
									className={`nav-link ${!this.state.activeFilter ? 'active' : ''}`}
									style={{ border: 'none', fontSize: `${!this.state.activeFilter ? '1.2rem' : '0.8rem'}` }}
									onClick={() => this.setState({ activeFilter: false })}
								>
									{gettext('Référents')}
								</button>
							</div>
						</nav>
					</Modal.Header>
					{this.state.activeFilter ? (
						<div>
							<Modal.Body>
								<Form>
									{this.state.entities.map((entity) => (
										<div key={entity.pk} className="mb-3">
											<Form.Check
												type={'checkbox'}
												checked={this.state.entityFilter.includes(entity.pk) ? true : false}
												value={entity.pk}
												label={entity.name}
												onChange={() => this.handleFilterByEntity(entity.pk)}
											/>
										</div>
									))}
								</Form>
							</Modal.Body>
							<Modal.Footer className="d-flex justify-content-between">
								<button
									className="button border m-2"
									style={{ background: '#fff', borderColor: '#000', color: '#000', borderRadius: '6px' }}
									onClick={() =>
										this.setState({ entityFilter: [] }, () => {
											this.applyFiltersOnKeysIndicator();
										})
									}
								>
									{gettext('Vider les filtres')}
								</button>
								<button
									className="button border m-2"
									style={{ background: '#fff', borderColor: '#000', color: '#000', borderRadius: '6px' }}
									onClick={() => this.FillFilterByEntity()}
								>
									{gettext('Tout sélectionner')}
								</button>
							</Modal.Footer>
						</div>
					) : (
						<div>
							<Modal.Body>
								<Form>
									{this.state.all_possible_referent.map((member) => (
										<div key={member.pk} className="mb-3">
											<Form.Check
												type={'checkbox'}
												checked={this.state.referentFilter.includes(member.pk) ? true : false}
												value={member.pk}
												label={
													member.first_name
														? member.first_name + ' ' + member.last_name + ' / ' + member.membership
														: member.username + ' / ' + member.membership
												}
												onChange={() => this.handleFilterByReferent(member.pk)}
											/>
										</div>
									))}
								</Form>
							</Modal.Body>
							<Modal.Footer className="d-flex justify-content-between">
								<button
									className="button border m-2"
									style={{ background: '#fff', borderColor: '#000', color: '#000', borderRadius: '6px' }}
									onClick={() =>
										this.setState({ referentFilter: [] }, () => {
											this.applyFiltersOnKeysIndicator();
										})
									}
								>
									{gettext('Vider les filtres')}
								</button>
								<button
									className="button border m-2"
									style={{ background: '#fff', borderColor: '#000', color: '#000', borderRadius: '6px' }}
									onClick={() => this.FillFilterByReferent()}
								>
									{gettext('Tout sélectionner')}
								</button>
							</Modal.Footer>
						</div>
					)}
				</Modal>
			</div>
		) : (
			<Loading message={this.state.placeholder} />
		);
	}
}

export default Overview;
