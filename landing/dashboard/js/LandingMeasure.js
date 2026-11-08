import React, { Component, useState } from 'react';
import Loading from '../../../mixity/dashboard/js/includes/Loading';
import { Breadcrumb } from 'react-bootstrap';
import Header from '../../../mixity/dashboard/js/includes/Header';
import { openMarketingPage } from './marketing';

import Background from '../../../mixity/static/img/background/bg_header.svg';

class LandingMeasure extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to front-end display
			everythingLoaded: true,
			placeholder: gettext('Chargement'),
		};
	}

	async componentDidMount() {}

	fetchErrorMessage(response) {
		if (response.status > 400) {
			return this.setState(() => {
				return { placeholder: gettext("Quelque chose s'est mal passé !") };
			});
		}
		return;
	}

	render() {
		return this.state.everythingLoaded ? (
			<div style={{ height: '100%', width: '100%' }}>
				{/*header block*/}
				<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
					<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
						<Breadcrumb.Item href={'/'}>{gettext('Accueil')}</Breadcrumb.Item>
						<Breadcrumb.Item active>{gettext('Mesurer')}</Breadcrumb.Item>
						<Breadcrumb.Item active>
							<strong>{gettext('Mixity Human')}</strong>
						</Breadcrumb.Item>
					</Breadcrumb>
					<Header data={{ url: '/', languages: languages, language_code: language_code, enabled_website_languages: enabled_website_languages }} />
				</div>
				<div className="d-flex flex-row space-between" style={{ justifyContent: 'space-between', margin: '3%', marginBottom: '2%' }}>
					<div className="d-flex flex-row align-items-center" style={{ whiteSpace: 'nowrap' }}>
						<div className="align-self-center" style={{ fontWeight: 700, fontSize: '120%', marginRight: '20px' }}>
							{gettext('Abonnement 360 DEI')}
						</div>
					</div>
					<div className="d-flex flex-row align-items-center" style={{ whiteSpace: 'nowrap' }}>
						<button
							style={{ borderRadius: '6px', backgroundColor: '#FFFFFF', border: '2px solid', padding: '4px 12px 4px 12px', marginRight: '12px' }}
							onClick={() => openMarketingPage('measure360')}
						>
							{gettext("Qu'est ce que 360 DEI ?")}
						</button>
						<button
							style={{ borderRadius: '6px', backgroundColor: '#FFFFFF', border: '2px solid', padding: '4px 12px 4px 12px', marginRight: '12px' }}
						onClick={() => openMarketingPage('example')}
						>
							{gettext('Voir un exemple')}
						</button>
						<button
							style={{
								borderRadius: '6px',
								backgroundColor: '#8888E2',
								border: '2px solid',
								borderColor: '#8888E2',
								color: '#FFFFFF',
								padding: '4px 12px 4px 12px',
							}}
							onClick={() => openMarketingPage('demo')}
						>
							{gettext('Demander une demo')}
						</button>
					</div>
				</div>
				<div className="d-flex justify-content-between" style={{ margin: '3%', height: 'auto', marginTop: 0 }}>
					<div style={{ width: '74%' }}>
						<div style={{ backgroundColor: '#FFFFFF', height: 'auto', marginBottom: '2.5%', borderRadius: '16px', border: '1px solid #DEDFEA' }}>
							<div className="d-flex flex-row align-items-center" style={{ height: '100%' }}>
								<div style={{ marginLeft: '4%' }}>
									<div
										style={{ fontWeight: 700, fontSize: '80%', marginTop: '8%', marginBottom: '4%' }}
										className="d-flex align-items-center"
									>
										<img src={'/static/icon/diag.svg'} style={{ width: '3%', margin: '0 5px 2px 0', padding: 0 }}></img>
										{gettext('MIXITY DIAG')}
									</div>
									<p style={{ fontWeight: 500, fontSize: '140%' }}>{gettext('Mesurez vos pratiques...')}</p>
									<p style={{ fontSize: '90%' }}>
										{gettext('Bénéficiez d’un état des lieux complet des process, données RH et actions de votre organisation.')}
									</p>
									<p style={{ fontSize: '90%' }}>
										{gettext('Obtenez vos scores de maturité, vos indicateurs de pilotage et votre empreinte sociale.')}
									</p>
									<p style={{ fontSize: '90%' }}>
										{gettext(
											'Identifiez vos points forts, obtenez des recommandations pour développer votre politique et mesurez vos progrès toute l’année.',
										)}
									</p>
									<div style={{ marginTop: '8%', marginBottom: '8%' }}>
										<button
											style={{
												borderRadius: '6px',
												backgroundColor: '#FFFFFF',
												border: '2px solid',
												padding: '4px 12px 4px 12px',
												marginRight: '12px',
											}}
											onClick={() => openMarketingPage('diag')}
										>
											{gettext("Qu'est-ce que Mixity Diag ?")}
										</button>
										<button
											style={{
												borderRadius: '6px',
												backgroundColor: '#FFFFFF',
												border: '2px solid',
												padding: '4px 12px 4px 12px',
												marginRight: '12px',
											}}
										onClick={() => openMarketingPage('example')}
										>
											{gettext('Voir un exemple')}
										</button>
									</div>
								</div>
								<img src={'/static/img/solo_footprint.svg'} style={{ width: '80%', margin: '0 0 0 0', padding: 0 }}></img>
							</div>
						</div>
						<div style={{ backgroundColor: '#FFFFFF', height: 'auto', borderRadius: '16px', border: '1px solid #DEDFEA' }}>
							<div className="d-flex flex-row align-items-center" style={{ height: '100%' }}>
								<img src={'/static/img/solo_footprint_human.svg'} style={{ width: '70%', margin: '0 0 0 0', padding: 0 }}></img>
								<div style={{ marginRight: '4%' }}>
									<div
										style={{ fontWeight: 700, fontSize: '80%', marginTop: '8%', marginBottom: '4%' }}
										className="d-flex align-items-center"
									>
										<img src={'/static/icon/human.svg'} style={{ width: '3%', margin: '0 5px 2px 0', padding: 0 }}></img>
										{gettext('MIXITY HUMAN')}
									</div>
									<p style={{ fontWeight: 500, fontSize: '140%' }}>{gettext('...et sondez vos équipes')}</p>
									<p style={{ fontSize: '90%' }}>
										{gettext(
											'Recueillez le sentiment d’engagement, de satisfaction et d’inclusion des collaborateurs et collaboratrices sur les sujets DE&I.',
										)}
									</p>
									<p style={{ fontSize: '90%' }}>
										{gettext(
											'Obtenez des scores de ressenti, des indicateurs modulables par filtres et une empreinte de votre organisation.',
										)}
									</p>
									<div style={{ marginTop: '8%', marginBottom: '8%' }}>
										<button
											style={{
												borderRadius: '6px',
												backgroundColor: '#FFFFFF',
												border: '2px solid',
												padding: '4px 12px 4px 12px',
												marginRight: '12px',
											}}
											onClick={() => openMarketingPage('human')}
										>
											{gettext("Qu'est-ce que Mixity Human ?")}
										</button>
										<button
											style={{
												borderRadius: '6px',
												backgroundColor: '#FFFFFF',
												border: '2px solid',
												padding: '4px 12px 4px 12px',
												marginRight: '12px',
											}}
										onClick={() => openMarketingPage('example')}
										>
											{gettext('Voir un exemple')}
										</button>
									</div>
								</div>
							</div>
						</div>
					</div>
					<div
						className="d-flex align-items-center flex-column"
						style={{ backgroundColor: '#FFFFFF', width: '23%', borderRadius: '16px', border: '1px solid #DEDFEA' }}
					>
						<div style={{ width: '70%', marginTop: '7%' }}>
							<p style={{ fontWeight: 500 }}>{gettext('Mais également...')}</p>
							<p style={{ fontSize: '80%', fontWeight: 550 }}>
								<img src={'/static/img/logos/namsor.png'} style={{ width: '10%', margin: '0 0 2px 0', padding: 0 }}></img>
								{gettext('MESURE ETHNIQUE PERÇUE')}
							</p>
							<p style={{ fontSize: '80%' }}>
								{gettext(
									"Analyser les origines perçues de vos collaborateurs (f/h/nb) permet de mesurer leur représentation dans l'organisation et d’identifier les obstacles au recrutement auxquels vos collaborateurs peuvent faire face(f/h/nb)",
								)}
							</p>
							<p style={{ fontSize: '80%' }}>{gettext('Les résultats sont présentés de manière anonyme et agrégée')}</p>
							<p style={{ fontSize: '80%', fontWeight: 550 }}>
								<img src={'/static/img/logos/namsor.png'} style={{ width: '10%', margin: '0 0 2px 0', padding: 0 }}></img>
								{gettext('CONNECTEUR SIRH')}
							</p>
							<p style={{ fontSize: '80%' }}>
								{gettext('Mixity vous permet de compléter automatiquement des données DE&I depuis votre logiciel SIRH.')}
							</p>
							<p style={{ fontSize: '80%' }}>
								{gettext(
									'Grâce à Mixity, vous avez désormais accès en un clic à un ensemble d’indicateurs de diversité et d’inclusion avec des mises à jour automatiques et régulières.',
								)}
							</p>
						</div>
					</div>
				</div>
			</div>
		) : (
			<Loading message={this.state.placeholder} />
		);
	}
}

export default LandingMeasure;
