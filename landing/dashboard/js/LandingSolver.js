import React, { Component, useState } from 'react';
import { Breadcrumb } from 'react-bootstrap';
import Header from '../../../mixity/dashboard/js/includes/Header';

class LandingSolver extends Component {
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
							<strong>{gettext('Mixity Diag')}</strong>
						</Breadcrumb.Item>
					</Breadcrumb>
					<Header data={{ url: '/', languages: languages, language_code: language_code, enabled_website_languages: enabled_website_languages }} />
				</div>
				<div className="d-flex flex-row space-between" style={{ justifyContent: 'space-between', margin: '3%', marginBottom: '2%' }}>
					<div className="d-flex flex-row align-items-center" style={{ whiteSpace: 'nowrap' }}>
						<div className="align-self-center" style={{ fontWeight: 700, fontSize: '120%', marginRight: '20px' }}>
							{gettext('Devenir solutionneur')}
						</div>
					</div>
					<div className="d-flex flex-row align-items-center" style={{ whiteSpace: 'nowrap' }}>
						<button
							style={{
								borderRadius: '6px',
								backgroundColor: '#8888E2',
								border: '2px solid',
								borderColor: '#8888E2',
								color: '#FFFFFF',
								padding: '4px 12px 4px 12px',
							}}
							onClick={() => (window.location.href = '/contact/')}
						>
							{gettext("S'inscrire")}
						</button>
					</div>
				</div>
				<div className="d-flex justify-content-between" style={{ margin: '3%', height: 'auto', marginTop: 0 }}>
					<div style={{ width: '100%' }}>
						<div style={{ backgroundColor: '#FFFFFF', width: '100%', marginBottom: '2.5%', borderRadius: '16px', border: '1px solid #DEDFEA' }}>
							<div className="d-flex flex-row align-items-center" style={{ height: '100%' }}>
								<div style={{ marginLeft: '4%', marginRight: '4%' }}>
									<p style={{ fontWeight: 500, fontSize: '140%' }}>
										{gettext(
											'Votre organisation est engagée en faveur de la Diversité, de l’Équité et de l’Inclusion (DE&I) et vous avez des solutions à proposer ?',
										)}
									</p>
									<p style={{ fontSize: '90%' }}>
										{gettext('Mixity vous propose de devenir partenaire et d’être visible auprès de ses organisations clientes.')}
									</p>
									<p style={{ fontSize: '90%' }}>
										{gettext(
											'Au sein d’une plateforme qui favorise la mesure, le pilotage et la promotion des politiques DE&I, vous bénéficierez d’un espace pour valoriser vos solutions',
										)}
									</p>
									<p style={{ fontSize: '90%' }}>
										{gettext('Référencez vos solutions et permettez aux organisations de s’engager à vos côtés')}
									</p>
								</div>
								<img src={'/static/img/peoples_talking_blue.svg'} style={{ width: '60%', margin: '6% 3% 6.35% 0', padding: 0 }}></img>
							</div>
						</div>
						<div className="d-flex justify-content-between">
							<div
								style={{ backgroundColor: '#FFFFFF', width: '48.5%', marginBottom: '2.5%', borderRadius: '16px', border: '1px solid #DEDFEA' }}
							>
								<div className="d-flex flex-row" style={{ height: '100%', margin: '3%' }}>
									<div style={{ marginLeft: '4%', marginRight: '4%' }}>
										<p style={{ fontWeight: 500, fontSize: '140%' }}>{gettext('Comment ça fonctionne ?')}</p>
										<ul style={{ listStyleType: 'disc', width: '90%' }}>
											<li style={{ fontSize: '90%', marginBottom: '5%' }}>{gettext('Rencontrer les équipes Mixity')}</li>
											<li style={{ fontSize: '90%', marginBottom: '5%' }}>{gettext('Valoriser 5 solutions DE&I')}</li>
											<li style={{ fontSize: '90%' }}>{gettext("Améliorer votre visibilité auprès d'organisations engagées")}</li>
										</ul>
									</div>
								</div>
							</div>
							<div
								style={{ backgroundColor: '#FFFFFF', width: '48.5%', marginBottom: '2.5%', borderRadius: '16px', border: '1px solid #DEDFEA' }}
							>
								<div className="d-flex flex-row" style={{ height: '100%', margin: '3%' }}>
									<div style={{ marginLeft: '4%', marginRight: '4%' }}>
										<p style={{ fontWeight: 500, fontSize: '140%' }}>{gettext('Frais de fonctionnement')}</p>
										<p style={{ fontSize: '90%' }}>{gettext('250€ par an pour 5 solutions')}</p>
									</div>
								</div>
							</div>
						</div>
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

export default LandingSolver;
