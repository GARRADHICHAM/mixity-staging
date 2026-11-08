import React, { Component } from 'react';
import Loading from './includes/Loading';
import { Breadcrumb, Card, Form, Modal } from 'react-bootstrap';
import Header from '../../../mixity/dashboard/js/includes/Header';
import CSVImporter from './includes/CSVImporter';
import NamsorIndicatorComponent from '../../../theme/src/js/NamsorIndicatorComponent';

class NameAnalyzerUploadComponent extends Component {
	constructor(props) {
		super(props);
		this.state = {
			user: {},
			collaboratorStatistics: [],
			placeholder: gettext('Chargement'),
			userLoaded: false,
			collaboratorStatisticsLoaded: false,
			responseStatus: 200,
			namsorIndicatorContent: {},
			namsorIndicatorContentLoaded: false,
			showMoreErrors: false,
		};
	}

	updateCollaboratorStatistics(data) {
		return this.setState(() => {
			return { collaboratorStatistics: data };
		});
	}

	getNamsorIndicatorContent() {
		var INDICATOR_LABELS = {
			"contracts": gettext(
				"Répartition des origines ethniques perçues des personnes en CDD/CDI"
			),
			"interns": gettext(
				"Répartition des origines ethniques perçues des personnes en stage/alternance"
			),
			"hired_contracts": gettext(
				"Répartition des origines ethniques perçues des personnes recrutées en CDD/CDI dans les 12 derniers mois"
			),
			"hired_interns": gettext(
				"Répartition des origines ethniques perçues des personnes recrutées en stage/alternance dans les 12 derniers mois"
			),
		}
		fetch('/api/' + eval_id + '/namsor-indicator-content/')
			.then((response) => {
				if (response.status != 200) {
					console.log("error with django namsor indicator content")
				}
				return response.json();
			})
			.then((data) => {
				data.filter((x) => x.label === INDICATOR_LABELS[csvType])
					.forEach((obj) => {
						this.setState(() => {
							return {
								namsorIndicatorContent: obj,
								namsorIndicatorContentLoaded: true,
							};
						});
					});
			});
	}

	getCollaboratorStatistics() {
		fetch('/' + entity_slug + '/api/collaboratorstatistics/?version=' + currentVersion)
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
				data.filter((x) => x.type === csvType)
					.forEach((statObj) => {
						if (statObj.status != 'finished')
							return;
						this.getNamsorIndicatorContent();
					});
			});
	}

	toggleShowMoreErrors() {
		var newValue = !this.state.showMoreErrors;

		this.setState(() => {
			return {
				showMoreErrors: newValue,
			};
		});
	}

	/* Fetch all the datas needed once when loading the page */
	componentDidMount() {
		fetch('/' + entity_slug + '/api/membership/')
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
						user: data,
						userLoaded: this.state.responseStatus < 400,
					};
				});
			});

		this.getCollaboratorStatistics();
	}

	goBack() {
		const anchor = document.getElementById("goBackAnchor");
		anchor.click()
	}

	render() {
		return this.state.userLoaded && this.state.collaboratorStatisticsLoaded ? (
			<div style={{ fontFamily: 'DM Sans' }}>
				<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
					<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
						<Breadcrumb.Item underline="hover" color="inherit" href={'/' + entity_slug}>
							{gettext('Accueil')}
						</Breadcrumb.Item>
						<Breadcrumb.Item color="inherit">{gettext('Mesurer')}</Breadcrumb.Item>
						<Breadcrumb.Item underline="hover" color="inherit" href={'/' + entity_slug + '/name-analyzer/'}>
							{gettext('Mesure ethnique (Namsor)')}
						</Breadcrumb.Item>
						<Breadcrumb.Item active>
							{this.state.collaboratorStatistics
								.filter((x) => x.type === csvType)
								.map((statObj, i) => {
									return statObj.name;
								})}
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
				<a href={'/' + entity_slug + '/name-analyzer/'} style={{ display: "none" }} id="goBackAnchor"></a>
				<button className="button p-4 pb-0 pt-3" style={{ backgroundColor: 'transparent' }} onClick={() => this.goBack()}>
					<i className="bi bi-arrow-left"></i>
					{gettext('Retour')}
				</button>
				{this.state.collaboratorStatistics
					.filter((x) => x.type === csvType)
					.map((statObj, i) => {
						return (
							<div className="d-flex flex-column">
								<div
									key={i}
									className="m-4 px-4 pb-4 dashboard-main-container"
									style={{
										backgroundColor:
											statObj.status === 'nodata'
												? '#FFFFFF'
												: statObj.status === 'processing'
												? 'rgba(71, 212, 255, 0.1)'
												: statObj.status === 'finished'
												? 'rgba(24, 255, 195, 0.1)'
												: 'rgba(255, 111, 111, 0.1)',
										borderColor:
											statObj.status === 'nodata'
												? '#DEDFEA'
												: statObj.status === 'processing'
												? 'rgba(71, 212, 255, 0.3)'
												: statObj.status === 'finished'
												? 'rgba(24, 255, 195, 0.3)'
												: 'rgba(255, 111, 111, 0.3)',
									}}
								>
									<div className="w-100">
										<CSVImporter
											stats={statObj}
											key={statObj.type}
											slug={entity_slug}
											callback={(data) => {
												this.updateCollaboratorStatistics(data);
												setTimeout(() => this.getCollaboratorStatistics(), 5000);
											}}
											toggleShowMoreErrors={() => this.toggleShowMoreErrors()}
										/>
									</div>
								</div>
								{statObj.status === 'finished' && (
									<>
										{this.state.namsorIndicatorContentLoaded && (
											<div className="border m-4 px-4 dashboard-main-container">
												<div className="d-flex flex-row flex-wrap justify-content-between p-3">
													<NamsorIndicatorComponent result={this.state.namsorIndicatorContent} data={null} />
												</div>
											</div>
										)}
										<div className="border m-4 px-4 dashboard-main-container">
											<div className="d-flex justify-content-between align-items-center p-3">
												<h4 className="fw-medium text-center mb-0">{gettext('Voir les résultats')}</h4>
												<a
													className="mxt--small button border assess_white_btn py-0 px-2"
													href={'/' + entity_slug + '/diag/assess/' + currentVersion + '/#evaluation-tabs'}
												>
													{gettext("Voir l'évaluation Mixity Diag")}
												</a>
											</div>
										</div>
									</>
								)}
								<Modal size="lg" style={{ zIndex: 1050 }} show={this.state.showMoreErrors} onHide={() => this.toggleShowMoreErrors()} centered>
									<Modal.Body>
									<div className="w-100">
										<div className="m-3 p-3">
											<div
												className="d-flex justify-content-between align-items-center"
											>
												<h4 className="fw-medium">{gettext('Vos erreurs dans le fichier')}</h4>
											</div>
											{this.state.showMoreErrors && (
												<div className="d-flex justify-content-start gap-3">
													<span className="w-100 d-block pt-3" style={{ lineHeight: '32px' }}>
														<ul>
															{statObj.status_label.split('/').splice(1).map((error, i) => {
																return (
																	<li>{error}</li>
																)
															})}
														</ul>
													</span>
												</div>
											)}
										</div>
									</div>
									</Modal.Body>
								</Modal>
							</div>
						);
					})}
			</div>
		) : (
			<Loading message={this.state.placeholder} />
		);
	}
}

export default NameAnalyzerUploadComponent;
