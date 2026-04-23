import React, { Component } from 'react';
import { Breadcrumb, Modal } from 'react-bootstrap';
import Header from '../../../mixity/dashboard/js/includes/Header';
import NamsorIndicator from '../../../theme/src/js/indicators/NamsorIndicator';

class NameAnalyzerComponent extends Component {
	constructor(props) {
		super(props);
		this.state = {
			placeholder: gettext('Chargement'),
			responseStatus: 200,
			collaboratorStatistics: [],
			collaboratorStatisticsLoaded: false,
			showWhatIsNamsor: false,
			showWhyNamsor: false,
			namsorIndicatorContent: [],
			namsorIndicatorContentLoaded: false,
			evaluationVersionsList: [],
			currentVersionSlugified: '',
			currentVersion: '',
		};
	}

	updateCollaboratorStatistics(data) {
		return this.setState(() => {
			return { collaboratorStatistics: data };
		});
	}

	getNamsorIndicatorContent() {
		fetch('/api/' + eval_id + '/namsor-indicator-content/?version=' + this.state.currentVersionSlugified)
			.then((response) => {
				if (response.status != 200) {
					console.log('error with django namsor indicator content');
				}
				return response.json();
			})
			.then((data) => {
				this.setState(() => {
					return {
						namsorIndicatorContent: data,
						namsorIndicatorContentLoaded: true,
					};
				});
			});
	}

	async getCollaboratorStatistics() {
		fetch('/' + entity_slug + '/api/collaboratorstatistics/?version=' + this.state.currentVersionSlugified)
			.then((response) => {
				if (response.status > 400) {
					return this.setState(() => {
						return {
							placeholder: gettext("Quelque chose s'est mal passé !"),
							responseStatus: response.status,
						};
					});
				}
				return response.json();
			})
			.then((data) => {
				let reload = false;
				data.forEach((element) => {
					if (element.status === 'processing') {
						reload = true;
					}
				});
				if (reload) {
					setTimeout(() => this.getCollaboratorStatistics(), 5000);
				}
				this.setState(() => {
					return {
						collaboratorStatistics: data,
						collaboratorStatisticsLoaded: this.state.responseStatus < 400,
					};
				});
			});
	}

	fetchData() {
		this.setState(() => {
			return {
				collaboratorStatistics: [],
				collaboratorStatisticsLoaded: false,
				namsorIndicatorContent: [],
				namsorIndicatorContentLoaded: false,
			}
		})
		setTimeout(() => {
			this.getCollaboratorStatistics().then(() => {this.getNamsorIndicatorContent()});
		}, 500);
	}

	/* Displaying or not the 'what' modal */
	setShowWhatIsNamsorModal(boolean) {
		this.setState({ showWhatIsNamsor: boolean });
	}

	/* Displaying or not the 'why' modal */
	setShowWhyNamsorModal(boolean) {
		this.setState({ showWhyNamsor: boolean });
	}

	slugify(text) {
		return text
			.toLowerCase()
			.normalize('NFD') // Normaliser les caractères
			.replace(/[\u0300-\u036f]/g, '') // Enlever les accents
			.replace(/[^a-z0-9 -]/g, ''); // Enlever les caractères non autorisés
	}

	/* Fetch all the datas needed once when loading the page */
	componentDidMount() {
		fetch(window.location + 'api/evaluations-versions-list/')
			.then((response) => {
				if (response.status > 400) {
					return this.setState(() => {
						return {
							placeholder: gettext("Quelque chose s'est mal passé !"),
							responseStatus: response.status,
						};
					});
				}
				return response.json();
			})
			.then((data) => {
				this.setState(() => {
					return {
						currentVersion: data[0].display_version,
						currentVersionSlugified: this.slugify(data[0].display_version),
						evaluationVersionsList: data,
					};
				});
			})
			.then(() => {
				this.fetchData();
			});
	}

	handleVersion(version) {
		const newVersionSlugified = this.slugify(version);

		if (newVersionSlugified == this.state.currentVersionSlugified) return;

		this.setState(() => {
			return {
				currentVersionSlugified: newVersionSlugified,
				currentVersion: version,
			};
		});
		this.fetchData();
	}

	render() {
		return this.state.collaboratorStatisticsLoaded ? (
			<div style={{ fontFamily: 'DM Sans' }}>
				<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
					<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
						<Breadcrumb.Item underline="hover" color="inherit" href={'/' + entity_slug}>
							{gettext('Accueil')}
						</Breadcrumb.Item>
						<Breadcrumb.Item color="inherit">{gettext('Mesurer')}</Breadcrumb.Item>
						<Breadcrumb.Item active>{gettext('Mesure ethnique (Namsor)')}</Breadcrumb.Item>
					</Breadcrumb>
					<Header
						data={{
							languages: languages,
							language_code: language_code,
							enabled_website_languages: enabled_website_languages,
						}}
					/>
				</div>
				<div className="w-100" style={{ minHeight: 'fit-content' }}>
					<div className="d-flex flex-column gap-5 m-5">
						<div className="w-100 d-flex justify-content-between align-items-center">
							<h3 className="mxt--h3">{gettext('Mesure ethnique perçue')}</h3>
							<div className="d-flex justify-content-end gap-3">
								<button
									className="button button_nasmor border--strong assess_white_btn px-3"
									onClick={() => this.setShowWhatIsNamsorModal(true)}
								>
									{gettext("Qu'est-ce que Namsor ?")}
								</button>
								<button className="button button_nasmor border--strong assess_white_btn px-3" onClick={() => this.setShowWhyNamsorModal(true)}>
									{gettext('Pourquoi mesurer ?')}
								</button>
								{this.state.evaluationVersionsList != [] && (
									<select
										defaultValue={this.state.currentVersion}
										onChange={(e) => this.handleVersion(e.target.value)}
										className="selector border d-flex"
									>
										{this.state.evaluationVersionsList.map((evaluation) => (
											<option key={evaluation.display_version} value={evaluation.display_version}>
												{evaluation.display_version}
											</option>
										))}
									</select>
								)}
							</div>
						</div>
						<div className="w-100 d-flex flex-column gap-3">
							<h3 className="fw-medium-2">{gettext('Importer un CSV')}</h3>
							<div className="row row-cols-2 g-3">
								{this.state.collaboratorStatistics.map((statObj, i) => {
									var btnClass = ['mxt--small', 'button', 'button_nasmor_csv', 'assess_white_btn', 'mw-100', 'text-center', 'border--strong'];
									if (!has_evaluation) btnClass.push('namsor_btn_disabled');
									var textBtnClass = btnClass.join(' ');
									return (
										<div class="col">
											<button
												key={i}
												className={textBtnClass}
												style={{
													zIndex: '0',
													padding: '2vh 2rem',
													fontSize: '0.8rem',
													backgroundColor:
														!has_evaluation
															? '#FAFAFA'
															: statObj.status === 'nodata'
															? '#FFFFFF'
															: statObj.status === 'processing'
															? 'rgba(71, 212, 255, 0.1)'
															: statObj.status === 'finished'
															? 'rgba(24, 255, 195, 0.1)'
															: 'rgba(255, 111, 111, 0.1)',
												}}
												onClick={() => {
													window.location += statObj.type + '/' + this.state.currentVersionSlugified;
												}}
												disabled={!has_evaluation}
											>
												{statObj.name}
											</button>
										</div>
									);
								})}
							</div>
							{!has_evaluation && (
								<div
									className="d-flex dashboard-main-container justify-content-between align-items-center border p-4"
									style={{ flexGrow: '1' }}
								>
									<div>
										<h4 className="fw-medium-2" style={{ fontSize: '1.2rem', marginBottom: '2vh' }}>
											{gettext('Evaluation non démarrée')}
										</h4>
										<p className="m-0">
											{gettext("Afin de pouvoir réaliser votre analyse, vous devez passer par l'étape de création votre évaluation.")}
										</p>
									</div>
									<a
										className="mxt--normal button button_nasmor border assess_white_btn p-4"
										style={{ fontSize: '1rem' }}
										href={'/diag/landing/'}
									>
										{gettext('Créer mon évaluation')}
									</a>
								</div>
							)}
						</div>
						<div className="w-100 d-flex flex-column gap-3">
							<h3 className="fw-medium-2">{gettext('Consulter les résultats')}</h3>
							{has_evaluation && this.state.collaboratorStatistics.some((obj) => obj.status === 'finished') ? (
								this.state.namsorIndicatorContentLoaded ? (
									<div className="border p-4 dashboard-main-container">
										<div className="d-flex flex-row flex-wrap justify-content-between p-3">
											<NamsorIndicator results={this.state.namsorIndicatorContent} />
										</div>
									</div>
								) : (
									<div className="border p-4 dashboard-main-container">
										<div class="mx-auto" style={{ width: 'fit-content', marginTop: '10rem', marginBottom: '10rem' }}>
											<div class="spinner-border" role="status">
												<span class="visually-hidden">Loading...</span>
											</div>
										</div>
									</div>
								)
							) : (
								<div
									className="w-100 d-flex flex-column justify-content-center align-items-center gap-4"
									style={{ marginTop: '10rem', marginBottom: '10rem' }}
								>
									<img src="/static/img/empty_namsor_results.svg" alt="Pas de résultats" style={{ width: '70px' }}></img>
									<div className="text-center">
										<p className="mb-0" style={{ fontWeight: '400', fontSize: '13px', lineHeight: '16.25px', color: '#909090' }}>
											{gettext('Pas de résultats disponibles.')}
										</p>
										<p className="mb-0" style={{ fontWeight: '400', fontSize: '13px', lineHeight: '16.25px', color: '#909090' }}>
											{gettext('Analysez les noms de vos collaborateurs en important un CSV pour découvrir vos résultats.')}
										</p>
									</div>
								</div>
							)}
						</div>
					</div>
				</div>
				<Modal
					size="lg"
					show={this.state.showWhatIsNamsor}
					onHide={() => this.setShowWhatIsNamsorModal(false)}
					aria-labelledby="contained-modal-title-vcenter"
					style={{ zIndex: '1050' }}
					className="m-0 p-0 w-100 namsor_modal"
				>
					<Modal.Header closeButton>
						<Modal.Title id="contained-modal-title-vcenter" className="d-flex align-items-end justify-content-center w-100">
							{gettext('Qu’est-ce que')}
							<img className="namsor_img mb-1" style={{ marginRight: '0.15rem' }} src="/static/img/logos/namsor.png" />
							<span className="namsor_span pe-2">{'amsor'}</span>
							{gettext('?')}
						</Modal.Title>
					</Modal.Header>
					<Modal.Body>
						<h3 id="contained-modal-title-vcenter" className="mb-4">
							{gettext("L'outil Namsor")}
						</h3>
						<p className="mb-3" style={{ fontSize: '12px' }}>
							{gettext(
								'Namsor est un outil basé sur l’Intelligence Artificielle et le Machine Learning*. En tant que logiciel onomastique**, il permet, à partir des prénoms et noms de naissance des collaborateurs (f/h/nb), de présumer comment une personne va être perçue sur son genre, son pays d’origine ou encore son ethnie.',
							)}
						</p>
						<p className="mb-3" style={{ fontSize: '12px' }}>
							{gettext(
								"Fort d'une base de données de plus de 8 milliards de noms et prénoms, en permanence maintenue et enrichie par des data scientists, des historiens (f/h/nb), linguistes et développeurs (f/h/nb), l’outil Namsor utilise la morphologie des noms et prénoms pour déterminer leur origine perçue.",
							)}
						</p>
						<p className="mb-3" style={{ fontSize: '12px' }}>
							{gettext(
								'La solution Namsor est largement utilisée par la communauté scientifique qui, en complément de son usage dans le cadre de la recherche sur les discriminations, renforce et valide également sa méthodologie. Des universités renommées, telles que Harvard, Berkeley et Science Po, mais également des groupes scientifiques, comme Elsevier, ou des institutions internationales, comme l’ONU et la Commission Européenne, ont mobilisé les ressources de Namsor pour mener leurs recherches.',
							)}
						</p>
						<p className="fst-italic" style={{ fontSize: '12px' }}>
							{gettext(
								"*Le Machine Learning permet aux machines de tirer des enseignements des données, d'identifier des tendances et de s'améliorer avec l'expérience, et ce avec un minimum d'intervention humaine.",
							)}
						</p>
						<p className="fst-italic mb-5" style={{ fontSize: '12px' }}>
							{gettext("**L'onomastique a pour sujet l’étude des noms propres.")}
						</p>
						<h3 id="contained-modal-title-vcenter" className="mb-4">
							{gettext('La méthodologie')}
						</h3>
						<p className="mb-3" style={{ fontSize: '12px' }}>
							{gettext('Le modèle sélectionné pour cette analyse est le modèle ')}
							<a href="https://namsor.app/features/name-origin#name-us-race-batch">{gettext('Diaspora')}</a>
							{gettext(
								"*, qui permet d'estimer l’origine ethnique des noms et prénoms. Ce modèle comprenant 22 régions du monde, 249 pays, 142 ethnies et 22 alphabets, la mesure est pleinement applicable à l’international.",
							)}
						</p>
						<p className="mb-3" style={{ fontSize: '12px' }}>
							{gettext(
								"Cette classification, basée sur l'expression culturelle et le lieu d'origine, définit les ethnies comme de grands groupes de personnes classés en fonction de la perception de leur origine ou de leur milieu « ethno-racial », national, tribal, religieux, linguistique ou culturel commun.",
							)}
						</p>
						<p className="fst-italic mb-5" style={{ fontSize: '12px' }}>
							{gettext('*Pour les organisations aux États-Unis, le modèle utilisé est ')}
							<a href="https://www.census.gov/topics/population/race/about.html">{gettext("l'US Census Taxonomy.")}</a>
						</p>
						<h3 id="contained-modal-title-vcenter" className="mb-4">
							{gettext('La politique de protection des données')}
						</h3>
						<p className="mb-3" style={{ fontSize: '12px' }}>
							{gettext(
								'Les données importées sont instantanément cryptées et automatiquement supprimées. Ce processus garantit la confidentialité et la protection des données personnelles. La solution Namsor utilise le même principe et présente des résultats agrégés aux organisations.',
							)}
						</p>
						<p className="mb-5" style={{ fontSize: '12px' }}>
							{gettext('Vous pouvez consulter ')}
							<a href="https://namsor.app/privacy-policy">{gettext('ici')}</a>
							{gettext(' la politique de confidentialité de Namsor et ')}
							<a href="https://namsor.app/files_to_download_p/NamSor_Data_Processing_Agreement_v007.pdf">{gettext('télécharger')}</a>
							{gettext(' leur accord relatif au traitement des données.')}
						</p>
					</Modal.Body>
					<Modal.Footer className="d-flex justify-content-center">
						<a className="mxt--small button border assess_white_btn py-0 px-3 mb-3" href={'https://namsor.app/'}>
							{gettext('Visiter le site de Namsor')}
							<i className="d-flex align-items-center w-100 namsor_img mb-0">
								<img className="namsor_icon" src="/static/img/logos/namsor.png" />
							</i>
						</a>
					</Modal.Footer>
				</Modal>
				<Modal
					size="lg"
					show={this.state.showWhyNamsor}
					onHide={() => this.setShowWhyNamsorModal(false)}
					aria-labelledby="contained-modal-title-vcenter"
					style={{ zIndex: '1050' }}
					className="m-0 p-0 w-100 namsor_modal"
				>
					<Modal.Header closeButton>
						<Modal.Title id="contained-modal-title-vcenter" className="d-flex align-items-end justify-content-center w-100">
							{gettext('Pourquoi utiliser ')}
							<img className="namsor_img mb-1" style={{ marginRight: '0.15rem' }} src="/static/img/logos/namsor.png" />
							<span className="namsor_span pe-2">{'amsor'}</span>
							{gettext('?')}
						</Modal.Title>
					</Modal.Header>
					<Modal.Body>
						<div className="d-flex justify-content-between m-3 pt-3">
							<h4 className="fw-medium" style={{ fontSize: '1.4rem' }}>
								{gettext("Analyser l'origine ethnique perçue de vos collaborateurs (f/h/nb)")}
							</h4>
						</div>
						<div className="w-100 px-3" style={{ lineHeight: '24px', fontSize: '0.8rem' }}>
							<div className="mb-3">
								{gettext(
									'Nos origines ethniques et culturelles sont des éléments importants de notre identité. Ils influencent la manière dont les autres personne nous perçoivent et nous traitent et peuvent donc entrainer des privilèges ou, au contraire, des discriminations.',
								)}
							</div>
							<div>
								{gettext("Pour vous accompagner sur cet enjeu, nous vous proposons l'outil de notre partenaire ")}
								<a target="_blank" href="https://namsor.app/about-us">
									Namsor
								</a>
								{gettext(
									". Cet outil permet de supposer l'origine ethnique perçue d'une personne par étude onomastique, c'est-à-dire par l'analyse de son nom et prénom.",
								)}
							</div>
						</div>
						<div className="d-flex justify-content-between m-3 pt-3">
							<h4 className="fw-medium mxt--h4" style={{ fontSize: '1.2rem' }}>
								{gettext('Objectifs')}
							</h4>
						</div>
						<div className="w-100 px-3" style={{ lineHeight: '24px', fontSize: '0.8rem' }}>
							<div className="mb-3">{gettext('Analyser les origines perçues de vos collaborateurs (f/h/nb) permet :')}</div>
							<ul>
								<li>{gettext("De mesurer la représentation des origines perçues dans l'organisation")}</li>
								<li>{gettext('D’identifier des obstacles au recrutement en fonction des origines perçues des collaborateurs (f/h/nb)')}</li>
							</ul>
							<div>{gettext('Les résultats sont présentés de manière anonyme et agrégée.')}</div>
						</div>
					</Modal.Body>
					<Modal.Footer className="d-flex justify-content-center">
						<a className="mxt--small button border assess_white_btn py-0 px-3 mb-3" href={'https://namsor.app/'}>
							{gettext('Visiter le site de Namsor')}
							<i className="d-flex align-items-center w-100 namsor_img mb-0">
								<img className="namsor_icon" src="/static/img/logos/namsor.png" />
							</i>
						</a>
					</Modal.Footer>
				</Modal>
			</div>
		) : (
			<h4 className="d-flex justify-content-center align-items-middle">{this.state.placeholder}</h4>
		);
	}
}

export default NameAnalyzerComponent;
