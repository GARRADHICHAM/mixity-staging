import React, { Component, useState } from 'react';
import Loading from '../../../mixity/dashboard/js/includes/Loading';
import { Breadcrumb } from 'react-bootstrap';
import Header from '../../../mixity/dashboard/js/includes/Header';
import { openMarketingPage } from './marketing';

import Background from '../../../mixity/static/img/background/bg_header.svg';

class LandingPilot extends Component {
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
							<img src={'/static/icon/offer-management.svg'} style={{ width: '30%', margin: '0 5px 2px 0', padding: 0 }}></img>
							{gettext("PLAN D'ACTIONS")}
						</div>
					</div>
					<div className="d-flex flex-row align-items-center" style={{ whiteSpace: 'nowrap' }}>
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
						<div style={{ backgroundColor: '#FFFFFF', height: '48%', marginBottom: '2.5%', borderRadius: '16px', border: '1px solid #DEDFEA' }}>
							<div className="d-flex flex-row align-items-center" style={{ height: '100%' }}>
								<div style={{ marginLeft: '4%', marginRight: '4%' }}>
									<p style={{ fontWeight: 500, fontSize: '140%' }}>{gettext('Fixez vous des objectifs...')}</p>
									<p style={{ fontSize: '90%' }}>
										{gettext(
											'Créez des objectifs clairs et mesurables en fonction des résultats de votre évaluation pour définir une stratégie d’évolution de votre politique diversité, équité et inclusion.',
										)}
									</p>
									<p style={{ fontSize: '90%' }}>
										{gettext(
											'Notre système de création d’objectifs est compatible avec la méthode SMART (Spécifique, Mesurable, Atteignable, Réalisable et Temporel). De plus, vous pouvez classer ces objectifs en fonction des 6 dimensions et de leurs sous-catégories pour avoir une feuille de route précise.',
										)}
									</p>
								</div>
								<img src={'/static/img/interview_purple.svg'} style={{ width: '40%', margin: '6% 3% 6.35% 0', padding: 0 }}></img>
							</div>
						</div>
						<div style={{ backgroundColor: '#FFFFFF', height: 'auto', borderRadius: '16px', border: '1px solid #DEDFEA' }}>
							<div className="d-flex flex-row align-items-center" style={{ height: '100%' }}>
								<img src={'/static/img/interview_purple_2.svg'} style={{ width: '40%', margin: '6% 3% 6.35% 4%', padding: 0 }}></img>
								<div style={{ marginRight: '4%' }}>
									<p style={{ fontWeight: 500, fontSize: '140%' }}>{gettext('...planifiez des actions...')}</p>
									<p style={{ fontSize: '90%' }}>
										{gettext(
											"Une fois vos objectifs établis, passez à l'étape suivante en identifiant et en élaborant les actions spécifiques nécessaires pour les atteindre. Vous avez la possibilité d'assigner ces actions à un responsable, de définir des échéances précises, d'allouer un budget adéquat, de définir des indicateurs clés de performance et de suivre leur progression de manière systématique.",
										)}
									</p>
								</div>
							</div>
						</div>
					</div>
					<div
						className="d-flex align-items-center flex-column"
						style={{ backgroundColor: '#FFFFFF', width: '23%', borderRadius: '16px', border: '1px solid #DEDFEA' }}
					>
						<div style={{ width: '70%', marginTop: '7%' }}>
							<p style={{ fontWeight: 550 }}>{gettext('...et suivez votre progression')}</p>
							<p style={{ fontSize: '90%', fontWeight: 530 }}>{gettext('INDICATEURS CLÉS')}</p>
							<p style={{ fontSize: '80%' }}>{gettext('Vous pouvez assigner un ou plusieurs indicateurs clés à une action.')}</p>
							<p style={{ fontSize: '80%' }}>
								{gettext(
									'Vous pouvez définir la valeur visée et celle atteinte, ce qui vous permet de mesurer la performance de votre action et de l’adapter au besoin.',
								)}
							</p>
							<p style={{ fontSize: '90%', fontWeight: 530 }}>{gettext('CALENDRIER')}</p>
							<p style={{ fontSize: '80%' }}>
								{gettext(
									'Pour ne pas manquer le déploiement d’une seule action, Mixity vous propose un calendrier qui recense toutes les actions et leur échéance',
								)}
							</p>
							<p style={{ fontSize: '80%' }}>{gettext('Vous pouvez donc avoir une vue globale de votre plan d’actions dans le temps.')}</p>
							<img src={'/static/img/pilot_clock.svg'} style={{ width: '100%', margin: 0, padding: 0 }}></img>
						</div>
					</div>
				</div>
			</div>
		) : (
			<Loading message={this.state.placeholder} />
		);
	}
}

export default LandingPilot;
