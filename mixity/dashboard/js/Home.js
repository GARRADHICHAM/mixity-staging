import React, { Component, useEffect } from 'react';
import Loading from './includes/Loading';
import { Chart as ChartJS, RadialLinearScale, PointElement, LineElement, Filler, CategoryScale, LinearScale, BarElement, Title, Legend } from 'chart.js';
import { Bar } from 'react-chartjs-2';
import pattern from 'patternomaly';
import { Breadcrumb, Card } from 'react-bootstrap';
import { CircularProgressbarWithChildren, buildStyles } from 'react-circular-progressbar';
import Footprint from './includes/Footprint';
import Header from './includes/Header';
import GlobalScores from './includes/GlobalScores';

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, CategoryScale, LinearScale, BarElement, Title, Legend);

const ACTION_STATUS_LABELS = {
	reflection: gettext('Action en réflexion'),
	planned: gettext('Action planifiée'),
	in_progress: gettext('Action en cours'),
	operation: gettext('Action pilote'),
	deployed: gettext('Action déployée'),
};

class Home extends Component {
	constructor(props) {
		super(props);
		this.state = {
			structure: {},
			entity: {},
			categories: [],
			categoriesWithSuggestions: [],
			categoryLabels: [],
			barDatasets: [],
			diag: {},
			human: {},
			actions: [],
			actionPercentage: null,
			solutions: [],
			barData: {},
			url: '',
			user: {},
			radarDiagData: {},
			radarHumanData: {},
			categoriesLoaded: false,
			diagLoaded: false,
			humanLoaded: false,
			actionsLoaded: false,
			solutionsLoaded: false,
			entityLoaded: false,
			scoresShown: 'diag',
			placeholder: gettext('Chargement'),

			//related to /api/human-form-choices/ request
			formChoicesLoaded: false,
			human_selected_filters: {},

			//related to /api/language/ request
			languages: [],
			enabled_lang: [],
			google_sheet_lang: [],
			languagesLoaded: false,

			subscription_pack: '',
			current_human: false,
			current_diag: false,
		};
	}

	/* Fetch all the datas needed once when loading the page */
	componentDidMount() {
		// L'adresse de l'API est celle de la page elle-même (même protocole, même hôte) : inutile de la
		// demander au serveur, ce qui supprime un aller-retour et évite d'écrire "https://" en dur.
		Promise.resolve(window.location.host)
			.then((base_url) => {
				let url = base_url;
				if (window.location.pathname.split('/').filter(Boolean)[0]) {
					url = `${base_url}/${window.location.pathname.split('/').filter(Boolean)[0]}`;
				}
				this.setState(
					{
						url: `${window.location.protocol}//${url}`,
					},
					() => {
						fetch(`${this.state.url}/api/category/`)
							.then((response) => {
								if (response.status > 400) {
									return this.setState({ placeholder: gettext("Quelque chose s'est mal passé !") });
								}
								return response.json();
							})
							.then((data) => {
								const catLabels = [];
								data.filter((cat) => cat.slug !== 'your-suggestions' && cat.slug !== 'csrd').map((cat) => {
									catLabels.push(cat.name);
								});
								this.setState(
									{
										categoriesWithSuggestions: data.filter((cat) => cat.slug !== 'csrd'),
										categories: data.filter((cat) => cat.slug !== 'your-suggestions' && cat.slug !== 'csrd'),
										categoryLabels: catLabels,
										categoriesLoaded: true,
									},
									() => {
										// Fetch entity first
										fetch(`${this.state.url}/api/entity/`)
											.then((response) => {
												if (response.status > 400) {
													return this.setState({ placeholder: gettext("Quelque chose s'est mal passé !") });
												}
												return response.json();
											})
											.then((data) => {
												this.setState(
													{
														entity: data[0],
														structure: data[0].structure,
														entityLoaded: true,
													},
													() => {
														// Fetch subscription-pack after structure is set
														fetch(`${this.state.url}/api/${this.state.structure.pk}/subscription-pack`)
															.then((response) => {
																if (response.status > 400) {
																	return this.setState({ placeholder: gettext("Quelque chose s'est mal passé !") });
																}
																return response.json();
															})
															.then((data) => {
																for (let option of data.options) {
																	if (option.product.slug == 'diag' && option.is_current) {
																		this.setState({ current_diag: true });
																	} else if (option.product.slug == 'human' && option.is_current) {
																		this.setState({ current_human: true });
																	}
																}
																this.setState({ subscription_pack: data });
															});
														// Fetch last-diag-evaluation after entity
														fetch(`${this.state.url}/api/last-diag-evaluation/`)
															.then((response) => {
																if (response.status > 400) {
																	return this.setState({ placeholder: gettext("Quelque chose s'est mal passé !") });
																}
																return response.json();
															})
															.then((data) => {
																let diag_values = [100, 100, 100, 100, 100, 100];
																let diag_color_list = 'rgba(136, 136, 226, 0.1)';
																const datasets = [...this.state.barDatasets];
																let evaluation = {};
																if (data[0] && data[0].is_validated_by_admin) {
																	evaluation = data[0];
																	diag_values = [];
																	diag_color_list = [];
																	this.state.categories.map((cat) => {
																		const scoreCategory = evaluation.scores_categories.find((sc) => sc.category === cat.pk);
																		if (scoreCategory) {
																			diag_color_list.push(cat.color);
																			diag_values.push(scoreCategory.display_value);
																		}
																	});
																}
																datasets.push({
																	label: 'Diag',
																	data: diag_values,
																	backgroundColor: diag_color_list,
																	borderRadius: 20,
																	borderSkipped: false,
																	categoryPercentage: 0.7,
																});
																this.setState(
																	() => {
																		return {
																			// On récupère les données de la dernière évaluation diag dans diag.
																			diag: data[0],
																			barDatasets: datasets,
																		};
																	},
																	() => {
																		this.setUpCharts('diag'),
																			fetch(this.state.url + '/api/last-human-evaluation/')
																				.then((response) => {
																					if (response.status > 400) {
																						return this.setState(() => {
																							return { placeholder: gettext("Quelque chose s'est mal passé !") };
																						});
																					}
																					return response.json();
																				})
																				.then((data) => {
																					var human_values = [100, 100, 100, 100, 100, 100];
																					var human_color_list = 'rgba(136, 136, 226, 0.1)';
																					var datasets = this.state.barDatasets;
																					var evaluation = {};
																					if (data[0] && data[0].is_validated_by_admin) {
																						evaluation = data[0];
																						data[0].collaborator_url = base_url + data[0].collaborator_url;
																						human_values = [];
																						human_color_list = [];
																						this.state.categories.map((cat) => {
																							let foundValue = evaluation.scores_categories.find(
																								(sc) => sc.category === cat.pk,
																							);
																							if (foundValue) {
																								human_color_list.push(pattern.draw('diagonal', cat.color));
																								human_values.push(foundValue.display_value);
																							}
																						});
																					}
																					datasets.push({
																						label: 'Human',
																						data: human_values,
																						backgroundColor: human_color_list,
																						borderRadius: 20,
																						borderSkipped: false,
																						categoryPercentage: 0.7,
																					});
																					this.setState(
																						() => {
																							// On récupère les données de la dernière évaluation human dans human
																							return {
																								human: data[0],
																								barDatasets: datasets,
																							};
																						},
																						() => {
																							this.setUpCharts('human');
																						},
																					);
																				});
																	},
																);
															});
													},
												);
											});
									},
								);
							});
						fetch(this.state.url + '/api/first-five-actions/')
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
											actions: data,
										};
									},
									() => {
										var actions_count = data.filter((action) => action.status !== 'reflection').length;
										if (actions_count) actions_count = (data.filter((action) => action.status === 'deployed').length / actions_count) * 100;
										this.setState({
											actionPercentage: actions_count,
											actionsLoaded: true,
										});
									},
								);
							});
						fetch(this.state.url + '/api/first-five-solutions/')
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
										solutions: data,
										solutionsLoaded: true,
									};
								});
							});
						fetch(this.state.url + '/api/membership/')
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
										user: data,
									};
								});
							});
						if (this.state.human.is_validated_by_admin) {
							fetch(this.state.url + '/api/language/')
								.then((response) => {
									if (response.status > 400) {
										return this.setState(() => {
											return { placeholder: gettext("Quelque chose s'est mal passé !") };
										});
									}
									return response.json();
								})
								.then((data_languages) => {
									this.setState(() => {
										return {
											//language
											languages: data_languages,
											enabled_lang: Object.values(data_languages.filter((lang) => lang.is_enabled)),
											google_sheet_lang: Object.values(data_languages.filter((lang) => lang.is_google_sheet_lang)),
											languagesLoaded: true,
										};
									});
								});
							fetch(this.state.url + '/api/human-form-choices/')
								.then((response) => {
									return response.json();
								})
								.then((data_form) => {
									const old_data_form = data_form['old'];
									this.setState(() => {
										return {
											formChoicesLoaded: true,
											human_selected_filters: old_data_form,
										};
									});
								});
						}
					},
				);
			});
	}

	setUpCharts(type) {
		const data = {
			labels: this.state.categoryLabels,
			datasets: this.state.barDatasets,
		};

		const config = {
			type: 'bar',
			data: data,
			options: {
				responsive: true,
				plugins: {
					legend: { display: false },
					title: { display: false, text: '' },
				},
				scales: {
					x: { display: false },
					y: { display: false, beginAtZero: true, max: 100 },
				},
			},
		};
		var radarName = 'radar' + type.charAt(0).toUpperCase() + type.slice(1) + 'Data';

		const radarData = this.setUpRadar(type);
		this.setState({
			barData: {
				data: data,
				config: config,
			},
			[radarName]: radarData,
			[type + 'Loaded']: true,
		});
	}

	setUpRadar(name) {
		var values = [];
		var colors = [];
		var labels = this.state.categoryLabels;
		if (this.state[name] && this.state[name].scores_categories.length !== 0) {
			this.state.categories.map((cat) => {
				colors.push(cat.color);
			});
			if (name === 'human') {
				colors = this.convertToRGB(this.state.categories.find((cat) => cat.pk === 1).color, 0.7);
				this.state.human.scores_categories
					.filter((sc) => sc.category !== this.state.categoriesWithSuggestions.find((cat1) => cat1.slug === 'your-suggestions').pk)
					.map((sc) => {
						values.push(sc.display_value);
					});
			} else {
				this.state.diag.scores_categories.map((sc) => {
					values.push(sc.display_value);
				});
				colors.shift();
			}
			values.shift();
		}

		const data = {
			labels: labels,
			datasets: [
				{
					label: name.charAt(0).toUpperCase() + name.slice(1),
					data: values,
					backgroundColor: colors,
				},
			],
		};

		const config = {
			type: 'radar',
			data: data,
			options: {
				plugins: {
					legend: { display: false },
					'samples-filler-analyser': { target: 'chart-analyser' },
					title: { display: false, text: '' },
				},
				scales: {
					r: {
						ticks: { beginAtZero: true, max: 100, min: 0, stepSize: 50 },
						angleLines: { display: false },
						suggestedMin: 0,
						suggestedMax: 100,
					},
				},
			},
		};
		return { data: data, config: config };
	}

	convertToRGB(hexa, alpha) {
		hexa = hexa.slice(1);
		if (hexa.length != 6) {
			return 'rgba(255, 255, 255, 0.1)';
		}

		var aRgbHex = hexa.match(/.{1,2}/g);
		var aRgb = `rgba(${parseInt(aRgbHex[0], 16)},${parseInt(aRgbHex[1], 16)},${parseInt(aRgbHex[2], 16)},${alpha})`;
		return aRgb;
	}

	handleScoresShown(e) {
		this.setState({
			scoresShown: e.target.value,
		});
	}

	getScoresCategoriesList(name, type) {
		var measures = [];
		this.state[name].scores_categories
			.filter(
				(sc) =>
					sc.category !== this.state.categoriesWithSuggestions.find((cat1) => cat1.slug === 'your-suggestions').pk &&
					sc.category !== this.state.categories.find((cat1) => cat1.slug === 'all').pk,
			)
			.map((sc) => {
				measures.push({
					key: this.state.categories.find((cat) => cat.pk === sc.category).slug,
					value: sc.display_value,
					label: this.state.categories.find((cat) => cat.pk === sc.category).name,
					color: this.state.categories.find((cat) => cat.pk === sc.category).color,
					fake: 0,
				});
			});
		var data = {
			society: this.state.structure.juridic_name.replace("'", ' '),
			type: type,
			footprint_type: 'standard',
			measures: measures,
		};
		return JSON.stringify(data);
	}

	async startEvaluation() {
		const requestOptions = {
			credentials: 'include',
			method: 'POST',
			headers: { 'Content-Type': 'application/json;charset=utf-8', 'X-CSRFToken': csrftoken },
		};
		const response = await fetch(this.state.url + '/api/' + this.state.human.pk + '/start-evaluation/', requestOptions);
		const data = await response.json();
		alert(gettext('Votre évaluation a bien été lancée. Vous pouvez désormais répondre aux questions.'));
	}

	render() {
		return (
			// NAV BARRE
			this.state.actionsLoaded &&
				this.state.diagLoaded &&
				this.state.solutionsLoaded &&
				this.state.humanLoaded &&
				this.state.categoriesLoaded &&
				this.state.entityLoaded ? (
				<div style={{ fontFamily: 'DM Sans' }}>
					<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
						<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
							<Breadcrumb.Item underline="hover" color="inherit" active>
								{gettext('Accueil')}
							</Breadcrumb.Item>
						</Breadcrumb>
						<Header
							data={{
								url: this.state.url,
								languages: languages,
								language_code: language_code,
								enabled_website_languages: enabled_website_languages,
							}}
						/>
					</div>
					{/*                      Titre de la page*/}
					<div className="p-4 d-flex flex-column">
						<div className="pb-4">
							<h4>{gettext('Aperçu')}</h4>
							{/* Diagramme en barres : comparatif resultats diag/human */}
							<div className="p-3 d-flex justify-content-between">
								<Card
									className="px-3 py-4 border"
									style={{ width: '45%', borderRadius: '16px', borderColor: '#DEDFEA', backgroundColor: '#fff' }}
								>
									<Card.Body className="d-flex flex-column justify-content-between p-0 py-2">
										<Card.Title className="px-2" style={{ fontSize: '20px', lineHeight: '32px' }}>
											{gettext('Diag vs Human')}
										</Card.Title>
										<Bar options={this.state.barData.config.options} data={this.state.barData.data}></Bar>
										<div className="text-center py-2 row" style={{ paddingLeft: '0.8vw', paddingRight: '0.8vw' }}>
											<h6 className="col-2" style={{ color: '#9094AA', fontSize: '12px', textOverflow: 'ellipsis' }}>
												{gettext('Transversal')}
											</h6>
											<h6 className="col-2" style={{ color: '#9094AA', fontSize: '12px' }}>
												{gettext('Genre')}
											</h6>
											<h6 className="col-2" style={{ color: '#9094AA', fontSize: '12px' }}>
												{gettext('Handicap')}
											</h6>
											<h6 className="col-2" style={{ color: '#9094AA', fontSize: '12px' }}>
												{gettext('Multi-culturel')}
											</h6>
											<h6 className="col-2" style={{ color: '#9094AA', fontSize: '12px' }}>
												{gettext('Multi-générationnel')}
											</h6>
											<h6 className="col-2" style={{ color: '#9094AA', fontSize: '12px' }}>
												{gettext('LGBTQIA+')}
											</h6>
										</div>
										<div className="d-flex justify-content-center pt-2">
											<h5 className="pe-2">
												<b>
													<img alt="" src="/static/img/legend_diag.png" style={{ height: '4vh', width: 'auto' }} />
													DIAG
												</b>
											</h5>
											<h5 className="ps-2">
												<b>
													<img alt="" src="/static/img/legend_human.png" style={{ height: '4vh', width: 'auto' }} />
													HUMAN
												</b>
											</h5>
										</div>
									</Card.Body>
								</Card>
								{/* Graphique DIAG */}
								{/* Affichage si l'entité n'a pas encore d'évaluation diag */}
								{!this.state.diag ? (
									<Card
										className="p-4 border"
										style={{
											width: '25%',
											borderRadius: '16px',
											borderColor: 'rgba(136, 136, 226, 0.3)',
											backgroundColor: 'rgba(136, 136, 226, 0.1)',
										}}
									>
										<Card.Body className="px-0 py-2 d-flex justify-content-between flex-column">
											<div className="d-flex align-items-center text-center justify-content-between">
												<Card.Title className="card__title__no-subscription">
													{gettext('Obtenez votre évaluation Mixity Diag')}
												</Card.Title>
											</div>
											<div className="text-center d-flex flex-column align-items-center">
												<Card.Img
													className="my-2 col-8"
													style={{ borderRadius: '6px', height: 'auto', width: '75%' }}
													variant="top"
													src="/static/img/locked_evaluation.png"
												/>
												<br />
												<a href={'/diag/landing/'} className="mxt--small button border dashboard_white_btn p-0 px-3 mb-2">
													{gettext('En savoir plus')}
												</a>
											</div>
										</Card.Body>
									</Card>
								) : (
									<Card
										className="p-4 border"
										style={{ width: '25%', borderRadius: '16px', borderColor: '#DEDFEA', backgroundColor: '#fff' }}
									>
										<Card.Body className="px-0 py-2 d-flex justify-content-between flex-column">
											{this.state.diag.is_validated_by_admin ? (
												<>
													<Card.Title className="p-0 m-0" style={{ fontSize: '20px', lineHeight: '32px' }}>
														<img alt="" className="me-2" src="/static/img/icon_diag.png" style={{ height: '3vh', width: 'auto' }} />
														Mixity Diag
													</Card.Title>
													<Card.Text className="p-1 m-0">{gettext('Score Diversité, Équité et Inclusion')}</Card.Text>
													<Card.Title className="p-0 mb-3" style={{ fontSize: '1.75rem' }}>
														{Math.round(this.state.diag.get_global_score_delta)}/100
													</Card.Title>
													<Footprint
														data={{
															id: 'radar_' + this.state.diag.pk,
															isCategoryEvaluation: this.state.diag.is_category_evaluation,
															measures: this.state.diag.radar_data,
															mirror: {},
															enableLegend: 0,
															enableLinks: -1,
															isHomePage: true,
														}}
													/>
													<a
														href={'/' + this.state.entity.slug + '/diag/assess/' + this.state.diag.display_version_slugified}
														className="mxt--small button border dashboard_white_btn p-0 px-3 mb-2"
													>
														{gettext('Consulter mes évaluations')}
													</a>
												</>
											) : // Si l'évaluation n'est pas validé par l'admin, ni validée par l'utilisateur :
											!this.state.diag.is_validated_by_user ? (
												<>
													<div className="d-flex justify-content-between flex-wrap flex-column">
														<Card.Text className="p-1 m-0 dashboard_status_evaluation">{gettext('En cours')}</Card.Text>
														<Card.Title className="p-0 m-0" style={{ fontSize: '20px', lineHeight: '32px' }}>
															<img
																alt=""
																className="me-2"
																src="/static/img/icon_diag.png"
																style={{ height: '3vh', width: 'auto' }}
															/>
															Mixity Diag
														</Card.Title>
													</div>
													<div className="text-center d-flex justify-content-end align-items-center flex-column pt-3">
														<Card.Img
															className="my-2 p-2 col-8"
															style={{ borderRadius: '6px', height: 'auto', width: '90%' }}
															src="/static/img/locked_evaluation.png"
														/>
														{this.state.current_diag && (
															<a
																href={'/scoring/evaluation/' + this.state.diag.pk + '/confirm/'}
																className="mxt--small button border dashboard_secondary_btn p-0 px-3 mb-2"
															>
																{gettext('Reprendre le questionnaire')}
															</a>
														)}
														<a
															href={'/' + this.state.entity.slug + '/diag/assess/' + this.state.diag.display_version_slugified}
															className="mxt--small button border dashboard_white_btn p-0 px-3 mb-2"
														>
															{gettext('Consulter mes évaluations')}
														</a>
													</div>
												</>
											) : (
												// Si l'évaluation n'est pas validé par l'admin, mais elle est validée par l'utilisateur :
												<>
													<div className="d-flex justify-content-between flex-wrap flex-column">
														<Card.Text className="p-1 m-0 dashboard_status_evaluation">{gettext("En cours d'analyse")}</Card.Text>
														<Card.Title className="p-0 m-0" style={{ fontSize: '20px', lineHeight: '32px' }}>
															<img
																alt=""
																className="me-2"
																src="/static/img/icon_diag.png"
																style={{ height: '3vh', width: 'auto' }}
															/>
															Mixity Diag
														</Card.Title>
													</div>
													<div className="text-center d-flex justify-content-start align-items-center flex-column pt-3">
														<Card.Img
															className="my-2 p-2 col-8"
															style={{ borderRadius: '6px', height: 'auto', width: '90%' }}
															src="/static/img/locked_evaluation.png"
														/>
														<a
															href={'/' + this.state.entity.slug + '/diag/assess/' + this.state.diag.display_version_slugified}
															className="mxt--small button border dashboard_white_btn p-0 px-3 mb-2"
														>
															{gettext('Consulter mes évaluations')}
														</a>
													</div>
												</>
											)}
										</Card.Body>
									</Card>
								)}
								{/* Graphique HUMAN */}
								{/* Affichage si l'entité n'a pas encore d'évaluation human */}
								{!this.state.human ? (
									<Card
										className="p-4 border"
										style={{
											width: '25%',
											borderRadius: '16px',
											borderColor: 'rgba(136, 136, 226, 0.3)',
											backgroundColor: 'rgba(136, 136, 226, 0.1)',
										}}
									>
										<Card.Body className="px-0 py-2 d-flex justify-content-between flex-column">
											<div className="d-flex align-items-center text-center justify-content-between">
												<Card.Title className="card__title__no-subscription">
													{gettext('Obtenez votre évaluation Mixity Human')}
												</Card.Title>
											</div>
											<div className="text-center d-flex flex-column align-items-center">
												<Card.Img
													className="my-2 col-8"
													style={{ borderRadius: '6px', height: 'auto', width: '75%' }}
													variant="top"
													src="/static/img/locked_evaluation.png"
												/>
												<br />
												<a href={'/human/landing/'} className="mxt--small button border dashboard_white_btn p-0 px-3 mb-2">
													{gettext('En savoir plus')}
												</a>
											</div>
										</Card.Body>
									</Card>
								) : (
									// Affichage si l'entité a un produit human :
									<Card
										className="p-4 border"
										style={{ width: '25%', borderRadius: '16px', borderColor: '#DEDFEA', backgroundColor: '#fff' }}
									>
										<Card.Body className="px-0 py-2 d-flex justify-content-between flex-column">
											{/* Si l'évaluation est validée par l'admin : */}
											{this.state.human.is_validated_by_admin ? (
												<>
													<Card.Title className="p-0 m-0" style={{ fontSize: '20px', lineHeight: '32px' }}>
														<img
															alt=""
															className="me-2"
															src="/static/img/icon_human.png"
															style={{ height: '3vh', width: 'auto' }}
														/>
														Mixity Human
													</Card.Title>
													<Card.Text className="p-1 m-0">{gettext('Score Diversité, Équité et Inclusion')}</Card.Text>
													<Card.Title className="p-0 mb-3" style={{ fontSize: '1.75rem' }}>
														{Math.round(this.state.human.get_global_score_delta)}/100
													</Card.Title>
													<Footprint
														data={{
															id: 'radar_' + this.state.human.pk,
															isCategoryEvaluation: this.state.human.is_category_evaluation,
															measures: this.state.human.radar_data,
															mirror: {},
															enableLegend: 0,
															enableLinks: -1,
															isHomePage: true,
														}}
													/>
													<div className="text-center d-flex justify-content-center align-items-center pt-3">
														<a
															href={'/' + this.state.entity.slug + '/human/assess/' + this.state.human.display_version_slugified}
															className="mxt--small button border dashboard_white_btn p-0 px-3 mb-2"
														>
															{gettext('Consulter mes évaluations')}
														</a>
													</div>
												</>
											) : // Si l'évaluation n'est pas validé par l'admin, ni validée par l'utilisateur :
											!this.state.human.is_validated_by_user ? (
												this.state.human.is_started ? (
													<>
														<div className="d-flex justify-content-between flex-wrap flex-column">
															<Card.Text className="p-1 m-0 dashboard_status_evaluation">{gettext('En cours')}</Card.Text>
															<Card.Title className="p-0 m-0" style={{ fontSize: '20px', lineHeight: '32px' }}>
																<img
																	alt=""
																	className="me-2"
																	src="/static/img/icon_human.png"
																	style={{ height: '3vh', width: 'auto' }}
																/>
																Mixity Human
															</Card.Title>
														</div>
														<div className="text-center d-flex justify-content-start align-items-center flex-column pt-3">
															<Card.Img
																className="my-2 p-2 col-8"
																style={{ borderRadius: '6px', height: 'auto', width: '90%' }}
																src="/static/img/locked_evaluation.png"
															/>
															{this.state.current_human && (
																<a
																	onClick={() => {
																		navigator.clipboard.writeText(window.location.origin + this.state.human.collaborator_url);
																	}}
																	className="mxt--small button border dashboard_secondary_btn p-0 px-3 mb-2"
																>
																	{gettext('Copier le lien du sondage')}
																</a>
															)}
															<a
																href={
																	'/' + this.state.entity.slug + '/human/assess/' + this.state.human.display_version_slugified
																}
																className="mxt--small button border dashboard_white_btn p-0 px-3 mb-2"
															>
																{gettext('Consulter mes évaluations')}
															</a>
														</div>
													</>
												) : (
													<>
														<div className="d-flex justify-content-between flex-wrap flex-column">
															<Card.Text className="p-1 m-0 dashboard_status_evaluation">{gettext('Inactif')}</Card.Text>
															<Card.Title className="p-0 m-0" style={{ fontSize: '20px', lineHeight: '32px' }}>
																<img
																	alt=""
																	className="me-2"
																	src="/static/img/icon_human.png"
																	style={{ height: '3vh', width: 'auto' }}
																/>
																Mixity Human
															</Card.Title>
														</div>
														<div className="text-center d-flex justify-content-start align-items-center flex-column pt-3">
															<Card.Img
																className="my-2 p-2 col-8"
																style={{ borderRadius: '6px', height: 'auto', width: '90%' }}
																src="/static/img/locked_evaluation.png"
															/>
															{this.state.current_human && (
																<button
																	className="mxt--small button border dashboard_secondary_btn p-0 px-3 mb-2"
																	onClick={() => this.startEvaluation()}
																>
																	{gettext("Lancer l'évaluation")}
																</button>
															)}
															<a
																href={
																	'/' + this.state.entity.slug + '/human/assess/' + this.state.human.display_version_slugified
																}
																className="mxt--small button border dashboard_white_btn p-0 px-3 mb-2"
															>
																{gettext('Consulter mes évaluations')}
															</a>
														</div>
													</>
												)
											) : (
												// Si l'évaluation n'est pas validé par l'admin, mais elle est validée par l'utilisateur :
												<>
													<div className="d-flex justify-content-between flex-wrap flex-column">
														<Card.Text className="p-1 m-0 dashboard_status_evaluation">{gettext("En cours d'analyse")}</Card.Text>
														<Card.Title className="p-0 m-0" style={{ fontSize: '20px', lineHeight: '32px' }}>
															<img
																alt=""
																className="me-2"
																src="/static/img/icon_human.png"
																style={{ height: '3vh', width: 'auto' }}
															/>
															Mixity Human
														</Card.Title>
													</div>
													<div className="text-center d-flex justify-content-start align-items-center flex-column pt-3">
														<Card.Img
															className="my-2 p-2 col-8"
															style={{ borderRadius: '6px', height: 'auto', width: '90%' }}
															src="/static/img/locked_evaluation.png"
														/>
														<a
															href={'/' + this.state.entity.slug + '/human/assess/' + this.state.human.display_version_slugified}
															className="mxt--small button border dashboard_white_btn p-0 px-3 mb-2"
														>
															{gettext('Consulter mes évaluations')}
														</a>
													</div>
												</>
											)}
										</Card.Body>
									</Card>
								)}
							</div>
						</div>
						<div className="pb-4">
							<div className="d-flex justify-content-between">
								<h4>{gettext('Scores globaux')}</h4>
								<select
									defaultValue={this.state.scoresShown}
									onChange={(e) => this.handleScoresShown(e)}
									className="selector ms-2 me-4 border"
									style={{ width: '8%' }}
								>
									<option key="1" value="diag">
										Diag
									</option>
									<option key="2" value="human">
										Human
									</option>
								</select>
							</div>
							<div className="p-3 d-flex flex-wrap justify-content-center text-center">
								{this.state.scoresShown === 'diag' && this.state.diag && this.state.diag.is_validated_by_admin
									? this.state.diag.scores_categories
											.filter(
												(sc) =>
													sc.category !== this.state.categoriesWithSuggestions.find((cat1) => cat1.slug === 'your-suggestions').pk,
											)
											.map((scoresCategories) => {
												return (
													<GlobalScores
														key={scoresCategories.pk}
														data={{
															category: this.state.categories.find((cat) => cat.pk === scoresCategories.category),
															scoresCategories: scoresCategories,
														}}
													/>
												);
											})
									: this.state.scoresShown === 'human' && this.state.human && this.state.human.is_validated_by_admin
									? this.state.human.scores_categories
											.filter(
												(sc) =>
													sc.category !== this.state.categoriesWithSuggestions.find((cat1) => cat1.slug === 'your-suggestions').pk,
											)
											.map((scoresCategories) => {
												return (
													<GlobalScores
														key={scoresCategories.pk}
														data={{
															category: this.state.categories.find((cat) => cat.pk === scoresCategories.category),
															scoresCategories: scoresCategories,
														}}
													/>
												);
											})
									: this.state.categories.map((cat) => {
											return <GlobalScores key={cat.pk} data={{ category: cat, scoresCategories: '' }} />;
									  })}
							</div>
						</div>
						<div className="pb-4">
							<h4>{gettext("Plan d'action")}</h4>
							<div className="p-3 d-flex justify-content-between">
								<Card className="p-3 border" style={{ width: '58%', borderRadius: '16px', borderColor: '#DEDFEA', backgroundColor: '#fff' }}>
									<Card.Body className="px-0 py-2">
										<div>
											<div className="d-flex justify-content-between">
												<div className="mb-3 w-50">
													<div style={{ width: '13%', float: 'left', marginRight: '5%' }}>
														<CircularProgressbarWithChildren
															value={this.state.actionPercentage}
															strokeWidth={8}
															styles={buildStyles({
																pathColor: '#000',
																trailColor: 'rgba(240, 243, 240, 1)',
															})}
														>
															<Card.Text className="m-0" style={{ fontSize: '14px' }}>
																<b>{Math.round(this.state.actionPercentage)}%</b>
															</Card.Text>
														</CircularProgressbarWithChildren>
													</div>
													<div className="ps-3">
														<Card.Title className="p-0 m-0" style={{ fontSize: '20px', lineHeight: '32px' }}>
															{gettext('Actions')}
														</Card.Title>
														<span className="tooltip tooltip__dashboard">
															<div className="tooltip__icon">?</div>
															<span className="tooltip__text">
																{gettext(
																	"L'outil de pilotage Mixity permet de suivre sa politique DEI toute l'année sur l'ensemble des dimensions et à plusieurs niveaux. Avec cet outil, il vous suffit de définir des objectifs, planifier des actions et suivre des indicateurs afin de garder une vision claire de votre stratégie DEI. Cet outil collaboratif est essentiel pour permettre aux équipes de partager les actions déployées et de contribuer à l'amélioration de la politique DEI.",
																)}
															</span>
														</span>
														<Card.Text className="p-0 m-0" style={{ fontSize: '12px', color: '#9094AA' }}>
															{gettext('Le top des priorités à venir')}
														</Card.Text>
													</div>
												</div>
												<a
													href={'/' + this.state.entity.slug + '/lead'}
													className="button border my-1 me-5"
													style={{
														background: '#fff',
														borderColor: '#000',
														color: '#000',
														borderRadius: '6px',
														height: 'fit-content',
													}}
												>
													{gettext('Tout voir')}
												</a>
											</div>
										</div>
										{this.state.actions.map((action) => {
											return (
												<div key={action.pk} className="py-2">
													<div className="ps-3" style={{ borderLeft: 'solid', borderWidth: '3px', borderColor: '#FF6F6F' }}>
														<Card.Title className="p-0 m-0" style={{ fontSize: '16px', lineHeight: '32px' }}>
															{action.label}
														</Card.Title>
														<Card.Text className="p-0 m-0" style={{ fontSize: '12px', color: '#9094AA' }}>
															{(ACTION_STATUS_LABELS[action.status] || action.status) + ' - ' + new Date(action.action_date).toLocaleDateString(language_code)}
														</Card.Text>
													</div>
												</div>
											);
										})}
									</Card.Body>
								</Card>
								<Card className="p-3 border" style={{ width: '40%', borderRadius: '16px', borderColor: '#DEDFEA', backgroundColor: '#fff' }}>
									<Card.Body className="px-0 py-2 row">
										{/* <div className="d-flex justify-content-between"> */}
										<div className="mb-3">
											<Card.Title className="p-0 m-0" style={{ fontSize: '20px', lineHeight: '32px' }}>
												{gettext('Solutions')}
											</Card.Title>
											<span className="tooltip tooltip__dashboard px-2">
												<div className="tooltip__icon">?</div>
												<span className="tooltip__text">
													{gettext(
														"Le catalogue de solutions est un annuaire diversité, équité et inclusion qui rassemble de nombreux partenaires engagés et qui permet aux organisations de trouver facilement une offre adaptée à leurs besoins. Identifier un sujet, consulter une solution et entrer directement en contact avec les experts référencés. Il existe toute sorte de solutions alors n'hésitez pas à les rencontrer pour en savoir plus.",
													)}
												</span>
											</span>
											<Card.Text className="p-0 m-0" style={{ fontSize: '12px', color: '#9094AA' }}>
												{gettext('Trouver des solutions pour compléter vos actions')}
											</Card.Text>
										</div>
										{/* <button className="button border m-2" style={{ background:"#fff", borderColor:"#000", color:"#000", borderRadius:"6px", height:"fit-content" }}>{gettext("My favorites")}</button>
                    </div> */}
										{this.state.solutions.map((solution) => {
											return (
												<div key={solution.pk} className="pt-2 row">
													<Card.Title style={{ fontSize: '16px', lineHeight: '32px' }}>
														<img
															alt=""
															className="me-2"
															src={solution.photo ? solution.photo : '/static/solvers_catalog/solution.jpg'}
															style={{ height: '4vh', width: '4vw', objectFit: 'cover' }}
														/>
														{solution.title}
													</Card.Title>
												</div>
											);
										})}
									</Card.Body>
									<Card.Footer style={{ backgroundColor: '#fff' }}>
										<a
											href={'/' + this.state.entity.slug + '/take-action/search-solutions'}
											className="button border p-2 m-0"
											style={{ background: '#fff', borderColor: '#000', color: '#000', borderRadius: '6px' }}
										>
											{gettext('Voir toutes les solutions')}
										</a>
									</Card.Footer>
								</Card>
							</div>
						</div>
					</div>
				</div>
			) : (
				<Loading message={this.state.placeholder} />
			)
		);
	}
}

export default Home;
