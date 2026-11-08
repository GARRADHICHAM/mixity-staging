import React, { Component, createRef } from 'react';
import Loading from '../../mixity/dashboard/js/includes/Loading';
import { Breadcrumb, Modal } from 'react-bootstrap';
import Header from '../../mixity/dashboard/js/includes/Header';
// https://0.0.0.0:8080/dashboard/maaf/sirh/status/
// TODO: Manual update button (to trigger a gathering of data), form update (auto update + update frequency. This need to be updated everytime the user change something)
class ADPStatus extends Component {
	constructor(props) {
		super(props);
		this.vocabulary = {
			pending: gettext('En attente'),
			ongoing: gettext('En cours'),
			partial: gettext('Terminé partiellement'),
			success: gettext('Terminé'),
			failed: gettext('Echec'),
		};
		this.adpPicture = createRef();
		this.state = {
			pk: null,
			user: {},
			url: '',
			steps: {
				connection: { name: gettext('Demande de connexion'), status: 'pending', message: this.vocabulary['pending'] },
				gathering: { name: gettext('Récupération des données'), status: 'pending', message: this.vocabulary['pending'] },
				processing: { name: gettext('Traitement des données'), status: 'pending', message: this.vocabulary['pending'] },
			},
			hasSubmittedConnectionRequest: false,
			canUpdate: false,
			lastUpdated: null,
			dataProcessed: 0,
			dataUnprocessed: 0,
			dataPartial: 0,
			placeholder: gettext('Chargement'),
			userLoaded: false,
			statusLoaded: false,
			lgShow: false,
			updateFrequency: 1,
			updateAutomatically: false,
			responseStatus: 200,
			errorMessage: '',
			isProcessing: false,
			isSent: false,
		};
	}

	resizeAdpPicture(context) {
		if (context.adpPicture.current !== null) {
			context.adpPicture.current.style.height = `${(context.adpPicture.current.offsetWidth * 6) / 16}px`;
		}
	}

	componentDidUpdate(prevProps, prevState, snapshot) {
		this.resizeAdpPicture(this);
	}

	/* Fetch all the datas needed once when loading the page */
	componentDidMount() {
		window.addEventListener('resize', () => this.resizeAdpPicture(this));
		fetch('../api/status/')
			.then((response) => {
				if (response.status >= 400) {
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
						statusLoaded: this.state.responseStatus < 400,
					};
				});
				if (data.length > 0) {
					data = data[0];
					Object.keys(data.steps).forEach((e) => {
						this.state.steps[e].status = data.steps[e].status;
						this.state.steps[e].message = this.vocabulary[data.steps[e].status];
						this.state.steps[e].date = data.steps[e].date;
					});
					this.setState(() => {
						return {
							hasSubmittedConnectionRequest: true,
							pk: data.pk,
							updateFrequency: data.update_frequency,
							updateAutomatically: !data.update_automatically,
							canUpdate: data.can_update,
							dataProcessed: data.processed_indicators.length,
							dataPartial: data.partial_indicators.length,
							dataUnprocessed: data.unprocessed_indicator_types.length,
						};
					});
				}
			});
	}

	changeFrequency(context, event) {
		const status = {
			pk: this.state.pk,
			update_frequency: event.target.value,
		};
		const requestOptions = {
			credentials: 'include',
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
			body: JSON.stringify(status),
		};
		context.setState({ isProcessing: true });
		fetch(`../api/status/` + status.pk + '/', requestOptions)
			.then((response) => {
				if (response.status >= 400) {
					return context.setState(() => {
						return { errorMessage: gettext("Quelque chose s'est mal passé ! Prenez contact avec le support Mixity"), isProcessing: false };
					});
				}
				return response.json();
			})
			.then((data) => {
				console.log(data);
				this.setState(() => {
					return {
						updateFrequency: data.update_frequency,
						isProcessing: false,
					};
				});
			});
	}

	changeAutoUpdate(context) {
		const status = {
			pk: this.state.pk,
			update_automatically: this.state.updateAutomatically,
		};
		const requestOptions = {
			credentials: 'include',
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
			body: JSON.stringify(status),
		};
		context.setState({ isProcessing: true });
		fetch(`../api/status/` + status.pk + '/', requestOptions)
			.then((response) => {
				if (response.status >= 400) {
					return context.setState(() => {
						return { errorMessage: gettext("Quelque chose s'est mal passé ! Prenez contact avec le support Mixity"), isProcessing: false };
					});
				}
				return response.json();
			})
			.then((data) => {
				console.log(data);
				this.setState(() => {
					return {
						updateAutomatically: !data.update_automatically,
						isProcessing: false,
					};
				});
			});
	}

	sendForm(context) {
		context.setState({ isProcessing: true });
		fetch(`../api/indicators-update/`).then((response) => {
			if (response.status >= 400) {
				return context.setState(() => {
					return { errorMessage: gettext("Quelque chose s'est mal passé ! Prenez contact avec le support Mixity"), isProcessing: false };
				});
			} else {
				context.setState(() => {
					return {
						isProcessing: false,
						isSent: true,
					};
				});
				setTimeout(() => (window.location = '../indicators/'), 2000);
			}
		});
	}

	render() {
		return this.state.statusLoaded ? (
			<div style={{ fontFamily: 'DM Sans' }}>
				<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
					<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
						<Breadcrumb.Item underline="hover" color="inherit" href={'/' + entity_slug}>
							{gettext('Accueil')}
						</Breadcrumb.Item>
						<Breadcrumb.Item color="inherit" active>
							{gettext('Mesurer')}
						</Breadcrumb.Item>
						<Breadcrumb.Item active>{gettext('ADP')}</Breadcrumb.Item>
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
				<div className="row p-4 flex-grow-1">
					<div className="d-flex col-xl-4 col-12 gap-3 flex-column justify-content-evenly align-items-stretch">
						<div className="d-flex flex-grow-1 flex-column align-items-start justify-content-evenly gap-3 w-100 mb-0 p-4 border dashboard-main-container">
							<h3 className="fw-medium text-center" style={{ fontSize: '1.2rem', marginBottom: '2vh' }}>
								{gettext('Etapes')}
							</h3>
							<div className="adp-steps d-flex">
								<div className="d-flex flex-column mx-2 gap-3 justify-content-evenly position-relative overflow-hidden">
									<div className="position-absolute w-100 h-100 d-flex justify-content-center">
										<div className="color-bg-lowkey-grey" style={{ width: '3px', height: '200px' }}></div>
									</div>
									{Object.values(this.state.steps).map((e, i) => {
										let color =
											e.status == 'success'
												? 'secondary-dark'
												: e.status == 'failed'
													? 'red'
													: e.status == 'partial'
														? 'yellow'
														: e.status == 'ongoing'
															? 'primary-light'
															: '';
										let icon =
											e.status == 'success'
												? 'check'
												: e.status == 'failed'
													? 'times'
													: e.status == 'partial'
														? 'exclamation-triangle'
														: '';

										return (
											<div
												className={`bg-white d-flex justify-content-center align-items-center ${color == '' ? 'border border-secondary' : ''} p-3 bg--${color}`}
												style={{ zIndex: 1, borderRadius: '50%', height: '55px', width: '55px' }}
											>
												<span className={`fw-medium ${e.status == 'ongoing' ? 'color--white' : ''}`}>
													{e.status == 'pending' || e.status == 'ongoing' ? (
														i + 1
													) : (
														<span style={{ filter: 'brightness(50%)' }} className={`fa fa-${icon} color--${color}`}></span>
													)}
												</span>
											</div>
										);
									})}
								</div>
								<div className="d-flex flex-column ms-2 gap-3 justify-content-evenly position-relative overflow-hidden">
									{Object.values(this.state.steps).map((e, i) => {
										let color =
											e.status == 'success'
												? 'secondary-dark'
												: e.status == 'failed'
													? 'red'
													: e.status == 'partial'
														? 'yellow'
														: e.status == 'ongoing'
															? 'primary-light'
															: '';
										return (
											<div style={{ height: '55px' }} className="d-flex flex-column justify-content-center">
												<span className="fw-medium" style={{ fontSize: '1.1rem' }}>
													{e.name}
												</span>
												{e.message ? <span className={`fw-medium mxt--small color--${color}`}>{e.message}</span> : ''}
											</div>
										);
									})}
								</div>
							</div>
						</div>

						<div className="d-flex flex-grow-1 flex-column align-items-start justify-content-evenly gap-3 w-100 mb-0 p-4 border dashboard-main-container">
							<h3 className="fw-medium text-center" style={{ fontSize: '1.2rem', marginBottom: '2vh' }}>
								{gettext('Données traitées')}
							</h3>
							<h6 className="fw-medium">
								{this.state.dataProcessed} {gettext('données traitées,')} {this.state.dataPartial}{' '}
								{gettext('données traitées partiellement et')} {this.state.dataUnprocessed} {gettext('données non-traitées')}.
							</h6>
							{this.state.dataProcessed ? (
								<a href="../indicators" className={'mxt--small button button_nasmor border assess_white_btn px-3 mt-2'}>
									{gettext('Voir mon tableau de bord')}
								</a>
							) : (
								''
							)}
						</div>

						<div className="d-flex flex-grow-1 flex-column align-items-start justify-content-evenly gap-3 w-100 mb-0 p-4 border dashboard-main-container">
							<h3 className="fw-medium text-center" style={{ fontSize: '1.2rem' }}>
								{gettext('Mises à jour')}
							</h3>
							{this.state.lastUpdated ? (
								<div className="adp-steps d-flex">
									<div className="d-flex flex-column mx-2 justify-content-evenly position-relative overflow-hidden">
										<div
											className={`bg-white d-flex justify-content-center align-items-center bg--secondary-dark`}
											style={{ borderRadius: '50%', height: '55px', width: '55px' }}
										>
											<span className={`fw-medium`}>
												<span style={{ filter: 'brightness(50%)' }} className={`fa fa-check color--secondary-dark`}></span>
											</span>
										</div>
									</div>
									<div className="d-flex flex-column ms-2 gap-3 justify-content-evenly position-relative overflow-hidden">
										<div style={{ height: '55px' }} className="d-flex flex-column justify-content-center">
											<span className="fw-medium" style={{ fontSize: '1.1rem' }}>
												{gettext('Vous êtes à jour')}
											</span>
											<span className={`fw-medium mxt--small color--secondary-dark`}>
												{gettext('Complété le')} {new Date(this.state.lastUpdated * 1000).toLocaleString()}
											</span>
										</div>
									</div>
								</div>
							) : (
								''
							)}
							<h6 className="fw-medium">{gettext('Fréquence des mises à jour souhaitée :')}</h6>
							<select
								className={`w-100 ${this.state.isProcessing ? 'disabled' : ''}`}
								style={{ pointerEvents: `${this.state.isProcessing ? 'none' : ''}` }}
								onChange={(e) => this.changeFrequency(this, e)}
								value={`${this.state.updateFrequency}`}
							>
								<option value="1">1 {gettext('mois')}</option>
								<option value="2">2 {gettext('mois')}</option>
								<option value="3">3 {gettext('mois')}</option>
								<option value="6">6 {gettext('mois')}</option>
							</select>
							<div
								className={`d-flex gap-2 ${this.state.isProcessing ? 'disabled' : ''}`}
								style={{ pointerEvents: `${this.state.isProcessing ? 'none' : ''}` }}
								onClick={() => this.changeAutoUpdate(this)}
							>
								<input type="checkbox" checked={this.state.updateAutomatically} />
								<label for="">{gettext('Ne pas mettre à jour les données automatiquement')}</label>
							</div>
							{this.state.canUpdate && this.state.dataProcessed === 0 ? (
								<button
									onClick={() => this.sendForm(this)}
									className={`mxt--small button button_nasmor border assess_white_btn px-3 mt-2 ${this.state.isProcessing ? 'disabled' : ''}`}
								>
									{this.state.isProcessing ? gettext('Mises à jour des données...') : gettext('Mettre à jour les données')}
								</button>
							) : (
								''
							)}
							{this.state.errorMessage ? <span className="text-danger">{this.state.errorMessage}</span> : ''}
						</div>
					</div>
					<div className="d-flex col-xl-8 col-12 gap-3 flex-column justify-content-start align-items-stretch">
						<div className="d-flex flex-grow-1 flex-column align-items-start justify-content-start gap-3 w-100 mb-0 p-4 border dashboard-main-container">
							<h3 className="fw-medium text-center" style={{ fontSize: '1.2rem', marginBottom: '2vh' }}>
								{gettext('ADP')}
							</h3>
							<div
								ref={this.adpPicture}
								className="w-100"
								style={{
									backgroundImage: "url('/static/img/drawings/adp.svg')",
									backgroundPosition: 'center',
									backgroundRepeat: 'no-repeat',
									backgroundSize: 'cover',
									borderRadius: '1rem',
									border: '#dedfea 1px solid',
								}}
							/>
							<span>
								{gettext('Mixity vous permet de compléter automatiquement des données DE&I depuis votre logiciel SIRH.')}
								<br />
								{gettext("L'objectif de cette fonctionnalité est de vous permettre de :")}
								<ul>
									<li>{gettext('Remplir automatiquement une partie des données du questionnaire Mixity Diag')}</li>
									<li>{gettext('Obtenir des indicateurs de performance au sein d’un dashboard interactif')}</li>
									<li>{gettext("Suivre la mise à jour et l'évolution des données")}</li>
								</ul>
								{gettext(
									'Grâce à Mixity, vous avez désormais accès en un clic à un ensemble d’indicateurs DE&I avec des mises à jour automatiques et régulières.',
								)}
								<br />
								{gettext(
									'Mesurez et pilotez votre politique diversité, équité et inclusion avec facilité et précision grâce au connecteur SIRH de Mixity.',
								)}
							</span>
							<div className="w-100">
								<a
									className="collapsed button border position-relative assess_white_btn px-3 w-100 border-1 adp-connection-status mw-100 justify-content-start gap-2"
									data-toggle="collapse"
									href="#adpConnectionStatus"
									role="button"
									aria-expanded="false"
									aria-controls="adpConnectionStatus"
									style={{ pointerEvents: this.state.hasSubmittedConnectionRequest && 'none' }}
								>
									<div
										className={`d-flex justify-content-center align-items-center ${this.state.hasSubmittedConnectionRequest ? 'border--secondary-dark' : 'border--primary'} border-3`}
										style={{ borderRadius: '50%', height: '30px', width: '30px', borderStyle: 'solid' }}
									>
										<span className="fw-medium">
											{this.state.hasSubmittedConnectionRequest ? (
												<span style={{ fontSize: '9pt' }} className={`fa fa-check color--secondary-dark mx-0`}></span>
											) : (
												''
											)}
										</span>
									</div>
									<span>{gettext('Demande de connexion')}</span>
									<span className="fa fa-chevron-up position-absolute adp-connection-status-arrow" style={{ right: '10px' }}></span>
								</a>
							</div>
							<div className="w-100 collapse multi-collapse" id="adpConnectionStatus" style={{ marginTop: '-24px', zIndex: 2 }}>
								<div className="card card-body bg--white border-top-0" style={{ borderTopLeftRadius: '0px', borderTopRightRadius: '0px' }}>
									<h3 className="fw-medium">{gettext('Demande de connexion')}</h3>
									Anim pariatur cliche reprehenderit, enim eiusmod high life accusamus terry richardson ad squid. Nihil anim keffiyeh
									helvetica, craft beer labore wes anderson cred nesciunt sapiente ea proident.
									{!this.state.hasSubmittedConnectionRequest ? (
										<a className="mxt--small button button_nasmor border assess_white_btn px-3 mt-2" href="../request/">
											{gettext('Faire une demande de connexion')}
										</a>
									) : (
										''
									)}
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		) : (
			<Loading message={this.state.placeholder} />
		);
	}
}

export default ADPStatus;
