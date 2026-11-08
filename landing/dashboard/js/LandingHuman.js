import React, { Component, useState } from 'react';
import Loading from '../../../mixity/dashboard/js/includes/Loading';
import { Breadcrumb } from 'react-bootstrap';
import Header from '../../../mixity/dashboard/js/includes/Header';
import { openMarketingPage } from './marketing';

import Background from '../../../mixity/static/img/background/bg_header.svg';

class LandingHuman extends Component {
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
						<div style={{ fontWeight: 700, fontSize: '80%' }}>
							<img src={'/static/icon/human.svg'} style={{ width: '10%', margin: '0 5px 2px 0', padding: 0 }}></img>
							{gettext('MIXITY HUMAN')}
						</div>
					</div>
					<div className="d-flex flex-row align-items-center" style={{ whiteSpace: 'nowrap' }}>
						<button
							style={{ borderRadius: '6px', backgroundColor: '#FFFFFF', border: '2px solid', padding: '4px 12px 4px 12px', marginRight: '12px' }}
							onClick={() => openMarketingPage('human')}
						>
							{gettext("Qu'est-ce que Mixity Human ?")}
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
							onClick={() => openMarketingPage('pricing')}
						>
							{gettext('Prendre un abonnement')}
						</button>
					</div>
				</div>
				<div className="d-flex justify-content-between" style={{ margin: '3%', height: 'auto', marginTop: 0 }}>
					<div style={{ width: '74%' }}>
						<div style={{ backgroundColor: '#FFFFFF', height: '48%', marginBottom: '2.5%', borderRadius: '16px', border: '1px solid #DEDFEA' }}>
							<div className="d-flex flex-row align-items-center" style={{ height: '100%' }}>
								<img src={'/static/img/solo_footprint_human.svg'} style={{ width: '120%', margin: '0 0 0 0', padding: 0 }}></img>
								<div style={{ marginRight: '4%' }}>
									<p style={{ fontWeight: 500, fontSize: '140%' }}>{gettext('Mixity Human')}</p>
									<p style={{ fontSize: '90%' }}>
										{gettext(
											"Mixity Human est une solution pour recueillir le sentiment d'inclusion des collaborateurs (f/h/nb). Ce sondage permet d'identifier le niveau de maturité perçu de l'organisation sur les sujets de diversité, d'équité et d'inclusion. ",
										)}
									</p>
									<p style={{ fontSize: '90%' }}>
										{gettext(
											"Avec 6 scores et plus de 50 indicateurs l'organisation obtient une vision globale et détaillée du ressenti. Ce sondage permet d'identifier des axes d'amélioration et d'obtenir une feuille de route pour développer votre politique DE&I.",
										)}
									</p>
								</div>
							</div>
						</div>
						<div style={{ backgroundColor: '#FFFFFF', height: 'auto', borderRadius: '16px', border: '1px solid #DEDFEA' }}>
							<div className="d-flex flex-row align-items-center" style={{ height: '100%' }}>
								<div style={{ marginLeft: '4%' }}>
									<p style={{ fontWeight: 500, fontSize: '140%' }}>{gettext('Sonder la perception de vos équipes sur l’inclusion')}</p>
									<p style={{ fontSize: '90%' }}>
										{gettext(
											"Collecter les besoins et attentes, recueillir des témoignages et identifier les risques sur les 5 dimensions majeures de la diversité et de l'inclusion",
										)}
									</p>
								</div>
								<img src={'/static/img/interview.svg'} style={{ width: '30%', margin: '6% 3% 6.35% 0', padding: 0 }}></img>
							</div>
						</div>
					</div>
					<div
						className="d-flex align-items-center flex-column"
						style={{ backgroundColor: '#FFFFFF', width: '23%', borderRadius: '16px', border: '1px solid #DEDFEA' }}
					>
						<div style={{ width: '70%', marginTop: '7%' }}>
							<p style={{ fontWeight: 500 }}>{gettext('Un sondage anonyme')}</p>
							<p style={{ fontSize: '80%' }}>
								{gettext(
									'20 à 50 questions adressées de manière confidentielle à vos collaborateurs (f/h/nb) sur les dimensions majeures de la diversité et de l’inclusion.',
								)}
							</p>
							<div style={{ display: 'grid', gridRowGap: '10px', marginBottom: '10%' }}>
								<div className="d-flex align-items-center" style={{ width: 'fit-content', listStyleType: 'none' }}>
									<li style={{ width: '14px', height: '14px', backgroundColor: '#FF6F6F', borderRadius: '180px', marginRight: '4px' }}></li>
									<li style={{ fontSize: '85%' }}>{gettext('Genres')}</li>
								</div>
								<div className="d-flex align-items-center" style={{ width: 'fit-content', listStyleType: 'none' }}>
									<li style={{ width: '14px', height: '14px', backgroundColor: '#0099FF', borderRadius: '180px', marginRight: '4px' }}></li>
									<li style={{ fontSize: '85%' }}>{gettext('Handicaps')}</li>
								</div>
								<div className="d-flex align-items-center" style={{ width: 'fit-content', listStyleType: 'none' }}>
									<li style={{ width: '14px', height: '14px', backgroundColor: '#03A87C', borderRadius: '180px', marginRight: '4px' }}></li>
									<li style={{ fontSize: '85%' }}>{gettext('Origines')}</li>
								</div>
								<div className="d-flex align-items-center" style={{ width: 'fit-content', listStyleType: 'none' }}>
									<li style={{ width: '14px', height: '14px', backgroundColor: '#423C6B', borderRadius: '180px', marginRight: '4px' }}></li>
									<li style={{ fontSize: '85%' }}>{gettext('Générations')}</li>
								</div>
								<div className="d-flex align-items-center" style={{ width: 'fit-content', listStyleType: 'none' }}>
									<li style={{ width: '14px', height: '14px', backgroundColor: '#47D4FF', borderRadius: '180px', marginRight: '4px' }}></li>
									<li style={{ fontSize: '85%' }}>{gettext('LGBTQIA+')}</li>
								</div>
							</div>
							<img src={'/static/img/survey_example_stretched.svg'} style={{ width: '100%', margin: '5px 5px 20px 0', padding: 0 }}></img>
						</div>
					</div>
				</div>
			</div>
		) : (
			<Loading message={this.state.placeholder} />
		);
	}
}

export default LandingHuman;
