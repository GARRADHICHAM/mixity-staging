import React, { useState, useEffect } from 'react';
import { Breadcrumb, Card, Form, Button } from 'react-bootstrap';
import Header from '../../mixity/dashboard/js/includes/Header';

function ElearningDetails() {
	const [placeholder, setPlaceholder] = useState('Chargement');
	const [environmentUrl, setEnvironmentUrl] = useState('');
	const [currentElearning, setCurrentElearning] = useState(null);

	const fetchEnvironmentUrl = () => {
		fetch('/api/url/')
			.then((response) => response.json())
			.then((data) => {
				const domain = data;
				const firstSegment = window.location.pathname.split('/').filter(Boolean)[0];
				setEnvironmentUrl(`https://${domain}/${firstSegment}`);
			})
			.then(() => {
				fetchElearning();
			})
			.catch(() => {
				setPlaceholder(gettext("Impossible de charger l'URL de l'environnement."));
			});
	};

	const fetchElearning = () => {
		const currentUrl = window.location.pathname;
		const urlSegments = currentUrl.split('/');
		const slug = urlSegments[urlSegments.length - 3];
		fetch(`${environmentUrl}/api/${slug}/elearning/`)
			.then((response) => {
				if (!response.ok) {
					throw new Error('Network response was not ok');
				}
				return response.json();
			})
			.then((data) => {
				setCurrentElearning(data);
			})
			.catch(() => {
				setPlaceholder(gettext("Impossible de charger l'e-learning."));
			});
	};

	useEffect(() => {
		fetchEnvironmentUrl();
	}, []);

	if (currentElearning) {
		return (
			<div style={{ fontFamily: 'DM Sans' }}>
				<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
					<Breadcrumb className="ps-4" separators=">" aria-label="breadcrumb">
						<Breadcrumb.Item href={'/'} underline="hover" color="inherit">
							{gettext('Accueil')}
						</Breadcrumb.Item>
						<Breadcrumb.Item active>{gettext('Agir')}</Breadcrumb.Item>
						<Breadcrumb.Item underline="hover" color="inherit" active>
							{currentElearning.title}
						</Breadcrumb.Item>
					</Breadcrumb>
					<Header
						data={{
							url: '/',
							languages: languages,
							language_code: language_code,
							enabled_website_languages: enabled_website_languages,
						}}
					/>
				</div>
				<div className="elearning-details-component m-4">
					<div className="d-flex w-100">
						<Card className="elearning-description-card col-8">
							<Card.Body>
								<div className="d-flex mb-4">
									{currentElearning.category.map((cat) => (
										<Card.Text
											key={cat.slug}
											className="border py-1 px-2 mb-0 me-2 category-tag"
											style={{
												borderRadius: '24px',
												width: 'fit-content',
												fontSize: '12px',
												fontWeight: '500',
												letterSpacing: '-0.02rem',
												color: cat.color,
											}}
										>
											<i className="bi bi-circle-fill me-1 pe-1" style={{ fontSize: '8px', top: '1%' }}></i>
											{cat.name}
										</Card.Text>
									))}
									{currentElearning.notions.map((notion) => (
										<Card.Text
											key={notion.slug}
											className="border py-1 px-2 mb-0 me-2 notion-text mb-0"
											style={{
												borderRadius: '24px',
												width: 'fit-content',
												fontSize: '12px',
												fontWeight: '500',
												letterSpacing: '-0.02rem',
											}}
										>
											{notion.label}
										</Card.Text>
									))}
								</div>
								<h4 style={{ marginTop: '3rem' }}>{currentElearning.title}</h4>
								<Card.Text style={{ color: '#9094AA' }}>{currentElearning.description}</Card.Text>
								<div className="spacing-container">
									<h5>{gettext('Objectifs')}</h5>
									<Card.Text style={{ color: '#9094AA' }}>{currentElearning.objective}</Card.Text>
								</div>
								<div className="spacing-container">
									<h5>{gettext('Plus-value')}</h5>
									<Card.Text style={{ color: '#9094AA' }}>{currentElearning.added_value}</Card.Text>
								</div>
								<div style={{ marginTop: '3rem' }} className="d-flex keywords-list spacing-container">
									{currentElearning.keywords.map((keyword) => (
										<Card.Text key={keyword.slug} className="keywords-text border">
											{keyword.label}
										</Card.Text>
									))}
								</div>
							</Card.Body>
						</Card>
						<div className="w-100">
							<iframe
								className="p-0 elearning-video-card"
								style={{ borderRadius: '16px', aspectRatio: '16 / 9', height: '250', width: '100%' }}
								src={currentElearning.video}
								title="YouTube video player"
								frameborder="0"
								allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
								referrerpolicy="strict-origin-when-cross-origin"
								allowfullscreen
							></iframe>

							<Card className="elearning-summary-card">
								<Card.Body>
									<h4>{gettext('Résumé')}</h4>
									<Card.Text className="summary-text">{currentElearning.summary}</Card.Text>
									<div className="mt-4">
										<div className="d-flex flex-wrap">
											<div className="d-flex mb-1 align-items-center" style={{ marginRight: '0.5rem' }}>
												<img className="elearning-icon" src="/static/img/Time.svg" />
												<Card.Text>{currentElearning.time + 'min'}</Card.Text>
											</div>
											<>&nbsp;</>
											<div className="d-flex mb-1 align-items-center">
												<img className="elearning-icon" src="/static/img/Public.svg" />
												<Card.Text>{currentElearning.target}</Card.Text>
											</div>
											<>&nbsp;</>
											{currentElearning.languages.length > 0 && (
												<div className="d-flex mb-1 align-items-center" style={{ marginRight: '0.5rem' }}>
													<img className="elearning-icon" src="/static/img/Web.svg" alt="Language icon" />
													{currentElearning.languages.map((language, index) => (
														<Card.Text key={language.code}>
															{language.label}
															{index !== currentElearning.languages.length - 1 && <>,&nbsp;</>}
														</Card.Text>
													))}
												</div>
											)}
											<>&nbsp;</>
											{currentElearning.is_certifiable && (
												<div className="d-flex mb-1 align-items-center" style={{ marginRight: '0.5rem' }}>
													<img className="elearning-icon" src="/static/img/Certified.svg" alt="Certified icon" />
													<Card.Text>{gettext('Certifiable')}</Card.Text>
												</div>
											)}
											<>&nbsp;</>
											<div className="d-flex mb-1">
												{currentElearning.evaluation_methods.map((evaluation_method) => {
													return (
														<div className="d-flex">
															<img
																className="elearning-icon"
																src={`/static/img/elearning/${evaluation_method.slug}.svg`}
																alt="Evaluation method icon"
															/>
															<Card.Text>{evaluation_method.label}</Card.Text>{' '}
														</div>
													);
												})}
												{/* TODO image icone méthode d'évaluation */}
												{/* <img></img> */}
											</div>
										</div>
										<button
											className="mt-4"
											style={{
												borderRadius: '6px',
												backgroundColor: '#8888E2',
												border: '2px solid',
												borderColor: '#8888E2',
												color: '#FFFFFF',
												padding: '4px 12px 4px 12px',
											}}
											onClick={() => (window.location.href = 'https://share.hsforms.com/1q3vTPc4CS4C-zQkzphekeQ43j1b')}
										>
											{gettext('Créer votre projet')}
										</button>
									</div>
								</Card.Body>
							</Card>
						</div>
					</div>
					<Card className="elearning-contact">
						<Card.Body>
							<h4 className="mb-4">{gettext('Vous n’avez pas encore trouvez votre e-learning ?')} </h4>
							<button
								style={{
									borderRadius: '6px',
									backgroundColor: '#8888E2',
									border: '2px solid',
									borderColor: '#8888E2',
									color: '#FFFFFF',
									padding: '4px 12px 4px 12px',
								}}
								onClick={() => (window.location.href = 'https://www.mixity.io/demo')}
							>
								{gettext('Contactez-nous')}
							</button>
						</Card.Body>
					</Card>
				</div>
			</div>
		);
	} else {
		return (
			<div className="placeholder">
				<p>{gettext('Chargement...')}</p>
			</div>
		);
	}
}

export default ElearningDetails;
