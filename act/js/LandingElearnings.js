import React, { useState, useEffect } from 'react';
import { Breadcrumb, Card, Form } from 'react-bootstrap';
import Header from '../../mixity/dashboard/js/includes/Header';

function LandingElearnings() {
	const [entity, setEntity] = useState(null);
	const [placeholder, setPlaceholder] = useState('Chargement');
	const [entityLoaded, setEntityLoaded] = useState(false);

	const [environmentUrl, setEnvironmentUrl] = useState('');

	return (
		<div style={{ height: '100%', width: '100%' }}>
			{/*header block*/}
			<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
				<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
					<Breadcrumb.Item href={'/'}>{gettext('Accueil')}</Breadcrumb.Item>
					<Breadcrumb.Item active>{gettext('Agir')}</Breadcrumb.Item>
					<Breadcrumb.Item active>
						<strong>{gettext('E-learnings')}</strong>
					</Breadcrumb.Item>
				</Breadcrumb>
				<Header data={{ url: '/', languages: languages, language_code: language_code, enabled_website_languages: enabled_website_languages }} />
			</div>
			<div className="d-flex flex-row space-between" style={{ justifyContent: 'space-between', margin: '3%', marginBottom: '2%' }}>
				<div className="d-flex flex-row align-items-center" style={{ whiteSpace: 'nowrap' }}>
					<div className="align-self-center" style={{ fontWeight: 700, fontSize: '120%', marginRight: '20px' }}>
						{gettext('E-learning')}
					</div>
					<div style={{ fontWeight: 700, fontSize: '80%' }}>
						<img src={'/static/icon/elearning.svg'} style={{ width: '10%', margin: '0 5px 2px 0', padding: 0 }}></img>
						{gettext('MIXITY E-LEARNING')}
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
						onClick={() => (window.location.href = '/elearning/list/')}
					>
						{gettext('Consulter le catalogue')}
					</button>
				</div>
			</div>
			<div className="d-flex flex-grow" style={{ margin: '3%', height: 'auto', marginTop: 0, justifyContent: 'space-between' }}>
				<div style={{ width: '74%' }}>
					<div style={{ backgroundColor: '#FFFFFF', height: '48%', marginBottom: '2.5%', borderRadius: '16px', border: '1px solid #DEDFEA' }}>
						<div className="d-flex flex-row align-items-center" style={{ height: '100%' }}>
							<div className="d-flex" style={{ margin: '4%' }}>
								<img
									className="d-flex"
									src={'/static/img/elearning/landingelearning.svg'}
									style={{ width: '50%', margin: '0 0 0 0', padding: 0 }}
								></img>
								<div className="d-flex flex-column" style={{ marginLeft: '4%' }}>
									<p style={{ fontWeight: 500, fontSize: '140%' }}>{gettext('Mixity E-learning')}</p>
									<p style={{ fontSize: '90%' }}>
										{gettext(
											'Chez Mixity, nous proposons des modules courts et didactiques agrémentés de quiz et de validations de connaissances pour mieux appréhender les basiques de la Diversité, l’Équité et l’Inclusion sur toutes ses dimensions.',
										)}
									</p>
									<p style={{ fontSize: '90%' }}>
										{gettext(
											'Mixity allie intelligence artificielle pédagogique et adaptive learning pour un apprentissage réellement efficace : 93% des utilisateurs voient leur travail impacté positivement par la formation.',
										)}
									</p>
								</div>
							</div>
						</div>
					</div>
					<div style={{ backgroundColor: '#FFFFFF', height: 'auto', borderRadius: '16px', border: '1px solid #DEDFEA' }}>
						<div className="d-flex flex-row align-items-center" style={{ height: '100%', margin: '6% 4% 6% 4%' }}>
							<img src={'/static/img/elearning/elearningpersonnes.png'} style={{ width: '33.2%', margin: '0 0 0 3%', padding: 0 }}></img>
							<div style={{ marginLeft: '4%' }}>
								<p style={{ fontWeight: 500, fontSize: '140%' }}>{gettext('Les bénéfices de l’e-learning basé sur les sciences cognitives')}</p>
								<p style={{ fontSize: '90%' }}>
									{gettext(
										'Nos formations e-learning s’appuient sur les sciences cognitives pour passer de l’exposition à une information à une transformation effective.',
									)}
								</p>
								<p style={{ fontSize: '90%' }}>
									{gettext(
										'Chaque module de formation est conçu pour offrir un feedback immédiat et détaillé, personnalisé en fonction des réponses. Les utilisateurs ne reçoivent pas seulement des réponses binaires mais des explications complètes qui leur permettent de comprendre leurs erreurs et d’améliorer leur compréhension.',
									)}
								</p>
							</div>
						</div>
					</div>
				</div>
				{/* On est ici */}
				<div
					className="d-flex align-items-center flex-column"
					style={{ backgroundColor: '#FFFFFF', width: '23%', borderRadius: '16px', border: '1px solid #DEDFEA' }}
				>
					<div style={{ width: '70%', marginTop: '7%' }}>
						<p style={{ fontWeight: 500, fontSize: '140%' }}>{gettext('Des e-learnings sur toutes les dimensions')}</p>
						<p style={{ fontSize: '90%' }}>
							{gettext(
								'Notre série d’e-learnings permet de se former aux notions essentielles de la Diversité, de l’Équité et de l’Inclusion sur toutes les dimensions afin de transformer la culture de l’entreprise et ses pratiques de recrutement et de management.',
							)}
						</p>
						<div>
							<div className="d-flex align-items-center" style={{ width: 'fit-content', listStyleType: 'none', marginBottom: '6%' }}>
								<li style={{ width: '14px', height: '14px', backgroundColor: '#FF6F6F', borderRadius: '180px', marginRight: '4px' }}></li>
								<li style={{ fontSize: '90%' }}>{gettext('Genres')}</li>
							</div>
							<div className="d-flex align-items-center" style={{ width: 'fit-content', listStyleType: 'none', marginBottom: '6%' }}>
								<li style={{ width: '14px', height: '14px', backgroundColor: '#0099FF', borderRadius: '180px', marginRight: '4px' }}></li>
								<li style={{ fontSize: '90%' }}>{gettext('Handicaps')}</li>
							</div>
							<div className="d-flex align-items-center" style={{ width: 'fit-content', listStyleType: 'none', marginBottom: '6%' }}>
								<li style={{ width: '14px', height: '14px', backgroundColor: '#03A87C', borderRadius: '180px', marginRight: '4px' }}></li>
								<li style={{ fontSize: '90%' }}>{gettext('Origines')}</li>
							</div>
							<div className="d-flex align-items-center" style={{ width: 'fit-content', listStyleType: 'none', marginBottom: '6%' }}>
								<li style={{ width: '14px', height: '14px', backgroundColor: '#423C6B', borderRadius: '180px', marginRight: '4px' }}></li>
								<li style={{ fontSize: '90%' }}>{gettext('Générations')}</li>
							</div>
							<div className="d-flex align-items-center" style={{ width: 'fit-content', listStyleType: 'none', marginBottom: '6%' }}>
								<li style={{ width: '14px', height: '14px', backgroundColor: '#47D4FF', borderRadius: '180px', marginRight: '4px' }}></li>
								<li style={{ fontSize: '90%' }}>{gettext('LGBTQIA+')}</li>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}

export default LandingElearnings;
