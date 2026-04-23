import React, { Component } from 'react';
import { Card } from 'react-bootstrap';
import Footprint from '../../../mixity/dashboard/js/includes/Footprint';
import AssessCategoryScore from '../../dashboard/js/includes/AssessCategoryScore';
import AssessSubCategoryScore from '../../dashboard/js/includes/AssessSubCategoryScore';
import AssessIndicators from '../../dashboard/js/EvaluationIndicator';
import StrengthsAndWeaknesses from '../../dashboard/js/includes/StrengthsAndWeaknesses';

import { Skeleton } from '@mui/material';
import { json } from 'd3';

class AssessPagePDF extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to /api/url/ request

			emptyurl: '',
			url: '',
			urlEvaluation: '',
			isDiagPage: false,

			//related to /api/entity/ request
			entity: {},
			entityLoaded: false,

			//related to /api/assess-evaluation/ request
			evaluation: null,
			evaluationLoaded: false,
			CommentsLoaded: false,

			//related to /api/human-collaborators-count/ request
			nbCollaborators: null,
			nbCollaboratorsLoaded: false,
			nbWorkforce: null,
			nbWorkforceLoaded: false,
			HumanCollaboratorInfoLoaded: false,
			DefaultHumanCollaboratorFilter: '{"default":{"age":[],"civility":[]},"human_criteria":[]}',

			//related to /api/assess-category-score/ request
			scoreCategories: null,
			scoreCategoriesLoaded: false,

			//related to /api/assess-subcategory-score/ request
			SubScoreByCat: {},

			//related to /api/assess-indicators/ request
			Indicatorsloaded: false,
			Indicators: {},
			linkedWithList: [],

			nbCollaboratorsWithFilterMin: 10,
			placeholder: gettext('Chargement'),
		};
	}

	async getUrl() {
		let adaptedurl = '';
		if (window.location.href.includes('/?filter=')) {
			adaptedurl = window.location.href.substring(0, window.location.href.slice(0, -1).lastIndexOf('/?filter='));
			adaptedurl = adaptedurl.substring(0, adaptedurl.slice(0, -1).lastIndexOf('/'));
			console.log(`adaptedurl : ${adaptedurl}`);
		} else {
			adaptedurl = window.location.href.substring(0, window.location.href.slice(0, -1).lastIndexOf('/'));
		}
		const response_url = await fetch(`${adaptedurl}/api/url/`);
		this.fetchErrorMessage(response_url);
		const data_url = await response_url.json();

		let url = 'https://' + data_url;
		let emptyurl = url;
		let url_evaluation = 'https://' + data_url;
		if (window.location.pathname.split('/').filter(Boolean)[0])
			url_evaluation += '/' + window.location.pathname.split('/').filter(Boolean)[0] + '/' + window.location.pathname.split('/').filter(Boolean)[1];
		const is_diag_page = window.location.href.includes('diag');
		let version_slug = segments[segments.length - 1];
		this.setState(() => {
			return {
				emptyurl: emptyurl,
				url: url,
				urlEvaluation: url_evaluation,
				isDiagPage: is_diag_page,
			};
		});
		return;
	}

	async componentDidMount() {
		try {
			//  URL
			await this.getUrl();
			if (window.location.search !== '') {
				let args = window.location.search.slice(8);
				args = JSON.parse(decodeURIComponent(args));
				this.setState(() => {
					return {
						DefaultHumanCollaboratorFilter: JSON.stringify(args),
					};
				});
			}
			//evaluation
			const response_evaluation = await fetch(this.state.urlEvaluation + '/api/assess-evaluation/' + version_slug);
			this.fetchErrorMessage(response_evaluation);
			const data_evaluation = await response_evaluation.json();
			this.setState(() => {
				return {
					evaluation: data_evaluation[0],
					evaluationLoaded: true,
					CommentsLoaded: true,
				};
			});

			// entity
			const response_entity = await fetch(this.state.url + '/' + window.location.pathname.split('/').filter(Boolean)[0] + '/api/entity/');
			this.fetchErrorMessage(response_entity);
			const data_entity = await response_entity.json();
			this.setState(() => {
				return {
					entity: data_entity[0],
					entityLoaded: true,
				};
			});

			if (this.state.evaluation.is_human) {
				this.setState(() => {
					return {
						HumanCollaboratorInfoLoaded: true,
						nbCollaborators: this.state.evaluation.answer_count,
						nbWorkforce: this.state.evaluation.get_workforce_from_evaluation,
						nbCollaboratorsLoaded: true,
						nbWorkforceLoaded: true,
					};
				});

				//human collaborators info
				const responseHumanCollaboratorInfo = await fetch(
					`${this.state.urlEvaluation}/api/human-collaborators-infos/?filter=${this.state.DefaultHumanCollaboratorFilter}`,
				);
				this.fetchErrorMessage(responseHumanCollaboratorInfo);
				const dataHumanCollaboratorInfo = await responseHumanCollaboratorInfo.json();
				this.setState(() => {
					return {
						CollaboratorsIndicators: dataHumanCollaboratorInfo,
						HumanCollaboratorInfoLoaded: true,
					};
				});
			} else {
				this.setState({
					HumanCollaboratorInfoLoaded: true,
				});
			}

			//score categories
			const response_score_categories = await fetch(this.state.urlEvaluation + '/api/assess-score-categories/');
			this.fetchErrorMessage(response_score_categories);
			const data_score_categories = await response_score_categories.json();
			this.setState(() => {
				return {
					scoreCategories: data_score_categories,
					scoreCategoriesLoaded: true,
				};
			});
			const requestOptions = {
				credentials: 'include',
				method: 'GET',
				headers: {
					'Content-Type': 'application/json;charset=utf-8',
					'X-CSRFToken': csrftoken,
				},
			};
			await Object.values(data_score_categories).map(async (cat) => {
				console.log(cat.category.slug);
				let bodyOptions = JSON.parse(this.state.DefaultHumanCollaboratorFilter);
				bodyOptions['score_cat_slug'] = cat.category.slug;
				requestOptions.Body = JSON.stringify(bodyOptions);
				const subscorecat = await fetch(`${this.state.urlEvaluation}/api/${cat.pk}/subcategory-scores/`, requestOptions);
				this.fetchErrorMessage(subscorecat);
				let formattedsubscorecat = await subscorecat.json();
				let newSubScoreByCat = this.state.SubScoreByCat;
				newSubScoreByCat[cat.category.slug] = formattedsubscorecat['subcategories_scores'];
				this.setState(() => {
					return {
						SubScoreByCat: newSubScoreByCat,
					};
				});
				const response_indicator = await fetch(
					`${this.state.urlEvaluation}/api/indicators/?page=${cat.category.slug}&filter=${this.state.DefaultHumanCollaboratorFilter}`,
				);
				this.fetchErrorMessage(response_indicator);
				var jsonHumanIndicator = await response_indicator.json();
				let updated_humanindicator = this.state.Indicators;
				updated_humanindicator[cat.category.slug] = jsonHumanIndicator;
				var linkedIds = [];
				jsonHumanIndicator.map((indicator) => {
					var duplicate = false;
					var canAdd = false;
					if (indicator.scores_json.display_params.linked_with) {
						var linked = indicator.scores_json.display_params.linked_with;
						linked.push(indicator.scores_json.id);
						linked = linked.sort();
						linkedIds.map((element) => {
							duplicate = element.every((element, index) => element === linked[index]);
							if (duplicate) canAdd = true;
						});
						if (!canAdd) linkedIds.push(linked);
					} else {
						linkedIds.push([indicator.scores_json.id]);
					}
				});
				let newLinkedIds = this.state.linkedWithList;
				newLinkedIds = newLinkedIds.concat(linkedIds);
				this.setState(() => {
					return {
						Indicators: updated_humanindicator,
						Indicatorsloaded: true,
						linkedWithList: newLinkedIds,
					};
				});
			});
		} catch (error) {
			console.log(error);
		}
	}

	globalScoresDescItem(color, value, isEntity = false) {
		return (
			<div className="d-inline-flex align-items-center mb-3">
				<div>
					<div className="indic-score" style={{ backgroundColor: `${color}` }}></div>
				</div>
				{isEntity ? <strong>{value}</strong> : <span>{value}</span>}
			</div>
		);
	}

	fetchErrorMessage(response) {
		if (response.status > 400) {
			return this.setState(() => {
				return { placeholder: gettext("Quelque chose s'est mal passé !") };
			});
		}
		return;
	}

	getYear(evaluationDate) {
		let evaluationDate_ = new Date(evaluationDate);
		return evaluationDate_.getFullYear();
	}

	collaboratorsCountItem(title, count) {
		return (
			<div className="d-flex flex-column my-3">
				<div className="assess_human_collab_count_title">{title}</div>
				<div className="assess_human_collab_count_number">{count}</div>
			</div>
		);
	}

	display_indicators(currentCategorySlug) {
		try {
			return this.state.linkedWithList.map((linked) => {
				if (this.state.Indicators[currentCategorySlug].find((element) => element.scores_json.id === linked[0]) && linked.length > 1)
					return (
						<div className="d-flex flex-row flex-wrap justify-content-between card" style={{ margin: '1rem', borderRadius: '25px', width: '95vw' }}>
							{this.state.Indicators[currentCategorySlug]
								.filter((element) => linked.includes(element.scores_json.id))
								.map((element, index) => {
									return (
										<AssessIndicators
											key={element.title}
											category={currentCategorySlug}
											json={element.scores_json}
											index={index}
											isCriteria={false}
											svg={
												element.scores_json.indicator_type === 'TextChart' && index === linked.length - 1
													? this.state.Indicators[currentCategorySlug].find((element) => linked[0] === element.scores_json.id)
															.scores_json.display_params.svg
													: ''
											}
											isHuman={!this.state.isDiagPage}
										/>
									);
								})}
						</div>
					);
				else {
					{
						var indicator = this.state.Indicators[currentCategorySlug].find((element) => linked[0] === element.scores_json.id);
						if (indicator && indicator.scores_json.indicator_type === 'MultipleBarChart')
							return (
								<div className="d-flex flex-row justify-content-between card" style={{ margin: '1rem', borderRadius: '25px', width: '95vw' }}>
									<AssessIndicators
										key={indicator.title}
										category={currentCategorySlug}
										json={indicator.scores_json}
										index={0}
										isCriteria={false}
									/>
								</div>
							);
						else if (indicator)
							return (
								<AssessIndicators
									key={indicator.title}
									category={currentCategorySlug}
									json={indicator.scores_json}
									index={0}
									isCriteria={false}
								/>
							);
					}
				}
			});
		} catch (error) {
			console.error('>>>>>>>> ERROR in assess page in function display_indicators : ', error);
		}
	}

	render() {
		return this.state.evaluationLoaded && this.state.entityLoaded ? (
			<div style={{ fontFamily: 'DM Sans', width: '100vw' }}>
				<div className="col py-3 dashboard-assess-indicator-font-size">
					<div className="row">
						{/* Footprint Block */}
						<div className="col" style={{ maxWidth: '50%', marginLeft: '25%' }} id="footprint-block">
							<h3 className="mxt--large-bold">
								{this.state.evaluation && this.state.evaluation.is_validated_by_admin
									? gettext('Votre empreinte') + ' ' + this.getYear(this.state.evaluation.modified_by_user_date)
									: gettext('Votre empreinte')}{' '}
							</h3>
							{this.state.evaluation && this.state.evaluation.is_validated_by_admin ? (
								<Card style={{ borderRadius: '25px' }}>
									<Card.Header className="m-0 p-0" style={{ background: 'none', border: 'none' }}>
										{/* Structure name & Global Score */}
										<div className="d-flex flex-row relative">
											{this.state.evaluation.is_human ? (
												<Card.Title>
													<span style={{ marginRight: '10px' }} className="icon-footprint-human"></span>Mixity Human
												</Card.Title>
											) : (
												<Card.Title>
													<span style={{ marginRight: '10px' }} className="mxt-icon--32 icon-offer-diag color-diag"></span>Mixity Diag
												</Card.Title>
											)}
											<Card.Title className="mxt--small m-0 radar_top-right" style={{ color: 'rgba(144, 148, 170, 1)' }}>
												{gettext('Score Diversité & Inclusion')}
											</Card.Title>
										</div>
										<div className="d-flex flex-row relative">
											<Card.Subtitle style={{ fontSize: '14px', marginLeft: '43px' }}>{this.state.entity.name}</Card.Subtitle>
											<Card.Text className="mxt--large-bold m-0 radar_top-right" style={{ color: '#181B3D' }}>
												{Math.round(this.state.evaluation.get_global_score_delta)}
												<span className="mxt--small-bold" style={{ color: '#181B3D' }}>
													/100
												</span>
											</Card.Text>
										</div>
									</Card.Header>
									<Card.Body className="m-0 p-0">
										{/* Footprint Body */}
										<Footprint
											data={{
												id: 'radar_' + this.state.evaluation.pk,
												isCategoryEvaluation: this.state.evaluation.is_category_evaluation,
												measures: this.state.evaluation.radar_data,
												mirror: {},
												enableLegend: true,
												enableLinks: false,
												horizontal: true,
											}}
										/>
									</Card.Body>
									<Card.Footer className="m-0 py-4" style={{ background: 'none', border: 'none' }}>
										{/* Mixity Watermark  */}
										<div className="relative">
											<img src={'/static/img/logo-mixity.svg'} alt="Logo Mixity" className="radar_watermark" />
										</div>
									</Card.Footer>
								</Card>
							) : (
								<div>
									<img src={'/static/img/footprint_not_available.png'} alt="Image Empreinte non disponible" />
								</div>
							)}
						</div>
						{/* end of footprint begining of human repartition */}
						{this.state.evaluation.is_human && (
							<div className="m-3 p-3 w-100">
								{/* Human Filters Form Block */}
								<div id="human_repartition_all" style={{ display: 'block' }}>
									<div id="repartition_block" className="row p-3 w-100">
										<h3 className="mxt--large-bold" style={{ marginBottom: '1.5em' }}>
											{gettext('Caractéristiques des collaborateurs (f/h/nb)')}
										</h3>
										{/* Collaborators Counts Block */}
										<div className="d-flex flex-column w-100" style={{ gap: '2rem' }}>
											<div className="d-flex flex-row" style={{ gap: '2rem' }}>
												{/* Collaborators Counts Block */}
												<div className="col" style={{ maxWidth: '50%' }}>
													<Card className="d-flex flex-row align-items-center assess_human_collab_count">
														<div className="col">
															<div className="d-flex flex-column">
																{/* Collborators Count */}
																{this.state.nbWorkforceLoaded ? (
																	this.collaboratorsCountItem(gettext('Effectif Total'), this.state.nbWorkforce)
																) : (
																	<Skeleton variant="text" width={52} />
																)}
																{this.state.nbCollaboratorsLoaded ? (
																	this.collaboratorsCountItem(
																		gettext('Total des réponses collectées'),
																		this.state.nbCollaborators,
																	)
																) : (
																	<Skeleton variant="text" width={52} />
																)}
																{this.state.nbWorkforceLoaded && this.state.nbCollaboratorsLoaded ? (
																	this.collaboratorsCountItem(
																		gettext('Ratio des réponses collectées'),
																		`${Math.round((this.state.nbCollaborators / this.state.nbWorkforce) * 100)}%`,
																	)
																) : (
																	<Skeleton variant="text" width={52} />
																)}
															</div>
														</div>
														<div className="col d-flex justify-content-end">
															<div style={{ width: '70%' }}>
																<img
																	src={'/static/img/assess/human_collab_counts.png'}
																	alt="Graphique des collaborateurs Human"
																/>
															</div>
														</div>
													</Card>
												</div>
												{this.state.HumanCollaboratorInfoLoaded && this.state.CollaboratorsIndicators ? (
													<React.Fragment>
														<div className="col" style={{ maxWidth: '50%' }}>
															<div className="d-flex flex-row justify-content-between card" style={{ borderRadius: '25px' }}>
																{this.state.CollaboratorsIndicators.slice(0, 2).map((indicator) => {
																	indicator.display_params.linked_with.push(indicator.id);
																	return (
																		<AssessIndicators
																			key={indicator.title}
																			category={'all'}
																			json={indicator}
																			index={indicator.id}
																			isCriteria={true}
																		/>
																	);
																})}
															</div>
														</div>
													</React.Fragment>
												) : (
													<div style={{ maxWidth: '50%' }}>
														<p>{gettext("Chargement de la répartition de l'âge et du genre des collaborateurs (f/h/nb)")}</p>
													</div>
												)}
											</div>
											{this.state.HumanCollaboratorInfoLoaded && this.state.CollaboratorsIndicators ? (
												<React.Fragment>
													<div className="d-flex justify-content-center flex-wrap w-100 p-0 mt-5" style={{ gap: '2rem' }}>
														{this.state.CollaboratorsIndicators.slice(2, this.state.CollaboratorsIndicators.length).map(
															(indicator) => {
																return (
																	<AssessIndicators
																		key={indicator.title}
																		category={'all'}
																		json={indicator}
																		index={indicator.id}
																		isCriteria={true}
																		isHuman={!this.state.isDiagPage}
																	/>
																);
															},
														)}
													</div>
												</React.Fragment>
											) : (
												<div>
													<p>{gettext('Chargement de la repartition selon les autres filtres')}</p>
												</div>
											)}
										</div>
									</div>
								</div>
							</div>
						)}
						{this.state.evaluation.is_validated_by_admin && this.state.scoreCategoriesLoaded && (
							<div className="row m-3 p-3 w-100">
								<h3 className="mxt--large-bold d-flex justify-content-center align-items-middle">{gettext('Mon évaluation')}</h3>
								{Object.values(this.state.scoreCategories).map((cat) => {
									return (
										<>
											<Card style={{ borderRadius: '25px', width: '97vw' }} key={cat.category.slug}>
												<Card.Body className="assess_global_scores">
													{/* Rendering global scores in function of current score category */}
													<div id={`assess_global_scores_desc_${cat.slug}`} className="assess_global_scores_desc">
														<h3 className="mxt--large-bold">{cat.category.name}</h3>

														<div className="d-flex flex-column flex-start">
															{this.globalScoresDescItem(cat.category.color, this.state.entity.name, true)}
															{this.globalScoresDescItem('#863C63', gettext('Score moyen dans mon secteur'))}
															{this.globalScoresDescItem('#F2A71B', gettext('Score moyen dans toutes les entreprises'))}
														</div>
													</div>

													<div id={`assess_global_scores_category_${cat.slug}`} className="assess_global_scores_category">
														<AssessCategoryScore
															innerPercent={Math.round(cat.inner_percent)}
															innerColor={cat.category.color}
															betweenPercent={Math.round(cat.between_percent)}
															outterPercent={Math.round(cat.outter_percent)}
														/>
													</div>
													<div id="assess_global_scores_subcategories" className="assess_global_scores_subcategories">
														{this.state.SubScoreByCat[cat.category.slug] &&
															Object.values(this.state.SubScoreByCat[cat.category.slug]).map((subscore) => {
																return (
																	<AssessSubCategoryScore
																		subCatPercent={Math.round(subscore[1])}
																		subCatName={subscore[0]}
																		subCatColor={cat.category.color}
																	/>
																);
															})}
													</div>
												</Card.Body>
											</Card>
											{
												this.state.evaluation.is_human && this.state.nbCollaborators <= this.state.nbCollaboratorsWithFilterMin ? (
													<div style={{ textAlign: '-webkit-center', margin: '50px 0' }}>
														<div className="item_pb item_s50 item_c stretched_item">
															<h3 className="txt_line content-strong" style={{ margin: 'auto' }}>
																{gettext(
																	"Le nombre de répondants (f/h/nb) dans cette catégorie n'est pas assez important pour visualiser les résultats",
																)}
															</h3>
														</div>
													</div>
												) : (
													// Indicators Block
													<h3 className="mxt--large-bold" style={{ marginTop: '40px', marginBottom: '24px' }}>
														{gettext('Indicateurs')}
													</h3>
												)
												// Strength and Weaknesses Block
											}
											{this.state.Indicatorsloaded && this.state.Indicators[cat.category.slug] ? (
												this.display_indicators(cat.category.slug)
											) : (
												<p>{this.state.placeholder}</p>
											)}
											{/* put the margin bottom as important */}

											<div className="row">
												<StrengthsAndWeaknesses
													key={cat.category.slug}
													strengths={this.state.evaluation.strengths.filter((strength) => strength.category === cat.category.slug)}
													weaknesses={this.state.evaluation.weaknesses.filter((weakness) => weakness.category === cat.category.slug)}
													aims={this.state.evaluation.aims.filter((aim) => aim.category === cat.category.slug)}
													CommentsLoaded={this.state.CommentsLoaded}
												/>
											</div>
										</>
									);
								})}
							</div>
						)}
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

export default AssessPagePDF;
