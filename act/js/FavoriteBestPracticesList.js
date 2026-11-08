import React, { Component } from 'react';
import Loading from '../../mixity/dashboard/js/includes/Loading';
import { useDefaultBestPracticeImage, useDefaultLogo } from '../../mixity/dashboard/js/includes/imageFallback';
import { Breadcrumb, Card, Form } from 'react-bootstrap';
import Header from '../../mixity/dashboard/js/includes/Header';

class FavoriteBestPractices extends Component {
	constructor(props) {
		super(props);
		this.state = {
			structure: {},
			entity: {},
			bestPractices: [],
			filteredBestPractices: [],
			detailedBestPractice: {},
			categories: [],
			subcategories: [],
			keywords: [],
			countries: [],
			publics: [],
			type: [],
			organization_type: [],
			size: [],
			url: '',
			categoriesLoaded: false,
			subcategoriesLoaded: false,
			keywordsLoaded: false,
			publicsLoaded: false,
			typeLoaded: false,
			organizationTypeLoaded: false,
			sizeLoaded: false,
			entityLoaded: false,
			bestPracticesLoaded: false,
			detailPage: false,
			placeholder: gettext('Chargement'),
		};
	}

	/* Fetch all the datas needed once when loading the page */
	componentDidMount() {
		fetch('api/url/')
			.then((response) => {
				if (response.status > 400) {
					return this.setState(() => {
						return { placeholder: gettext("Quelque chose s'est mal passé !") };
					});
				}
				return response.json();
			})
			.then((data) => {
				if (window.location.pathname.split('/').filter(Boolean)[0]) data += '/' + window.location.pathname.split('/').filter(Boolean)[0];
				this.setState(
					() => {
						return {
							url: window.location.protocol + '//' + data,
						};
					},
					() => {
						fetch(this.state.url + '/api/entity/')
							.then((response) => {
								if (response.status > 400) {
									return this.setState(() => {
										return { placeholder: gettext("Quelque chose s'est mal passé !") };
									});
								}
								return response.json();
							})
							.then((data) => {
								console.log('entity is = ', data[0], ' and structure is = ', data[0].structure);
								this.setState(
									() => {
										return {
											entity: data[0],
											structure: data[0].structure,
											entityLoaded: true,
										};
									},
									() => {
										fetch(this.state.url + '/api/best-practice/')
											.then((response) => {
												if (response.status > 400) {
													return this.setState(() => {
														return { placeholder: gettext("Quelque chose s'est mal passé !") };
													});
												}
												return response.json();
											})
											.then((data) => {
												let filteredBestPractices = data.filter((bp) => this.state.entity.favorite_best_practices.includes(bp.pk));
												this.setState(() => {
													return {
														bestPractices: filteredBestPractices,
														bestPracticesLoaded: true,
													};
												});
											});
									},
								);
							});
						fetch(this.state.url + '/api/category/')
							.then((response) => {
								if (response.status > 400) {
									return this.setState(() => {
										return { placeholder: gettext("Quelque chose s'est mal passé !") };
									});
								}
								return response.json();
							})
							.then((data) => {
								var subcategories = [];
								data.map((cat) => {
									subcategories = subcategories.concat(cat.subcategories);
								});
								this.setState(() => {
									return {
										categories: data,
										subcategories: subcategories,
										categoriesLoaded: true,
									};
								});
							});
						fetch(this.state.url + '/api/bestpractice-keyword/')
							.then((response) => {
								if (response.status > 400) {
									return this.setState(() => {
										return { placeholder: gettext("Quelque chose s'est mal passé !") };
									});
								}
								return response.json();
							})
							.then((data) => {
								this.setState(() => {
									return {
										keywords: data,
										keywordsLoaded: true,
									};
								});
							});
						fetch(this.state.url + '/api/bestpractice-type/')
							.then((response) => {
								if (response.status > 400) {
									return this.setState(() => {
										return { placeholder: gettext("Quelque chose s'est mal passé !") };
									});
								}
								return response.json();
							})
							.then((data) => {
								this.setState(() => {
									return {
										type: data,
										typeLoaded: true,
									};
								});
							});
						fetch(this.state.url + '/api/bestpractice-public/')
							.then((response) => {
								if (response.status > 400) {
									return this.setState(() => {
										return { placeholder: gettext("Quelque chose s'est mal passé !") };
									});
								}
								return response.json();
							})
							.then((data) => {
								this.setState(() => {
									return {
										publics: data,
										publicsLoaded: true,
									};
								});
							});
						fetch(this.state.url + '/api/organization-type/')
							.then((response) => {
								if (response.status > 400) {
									return this.setState(() => {
										return { placeholder: gettext("Quelque chose s'est mal passé !") };
									});
								}
								return response.json();
							})
							.then((data) => {
								this.setState(() => {
									return {
										organization_type: data,
										organizationTypeLoaded: true,
									};
								});
							});
						fetch(this.state.url + '/api/bestpractice-size/')
							.then((response) => {
								if (response.status > 400) {
									return this.setState(() => {
										return { placeholder: gettext("Quelque chose s'est mal passé !") };
									});
								}
								return response.json();
							})
							.then((data) => {
								this.setState(() => {
									return {
										size: data,
										sizeLoaded: true,
									};
								});
							});
						fetch(this.state.url + '/api/region/')
							.then((response) => {
								if (response.status > 400) {
									return this.setState(() => {
										return { placeholder: gettext("Quelque chose s'est mal passé !") };
									});
								}
								return response.json();
							})
							.then((data) => {
								this.setState(() => {
									return {
										countries: data['countries'],
									};
								});
							});
					},
				);
			});
	}

	favoritesBestPracticesManagement(e, pk) {
		e.preventDefault();

		let entity_to_update = {
			pk: this.state.entity.pk,
			name: this.state.entity.name,
			slug: this.state.entity.slug,
			favorite_best_practices: this.state.entity.favorite_best_practices,
		};

		if (entity_to_update.favorite_best_practices.includes(pk))
			entity_to_update.favorite_best_practices = entity_to_update.favorite_best_practices.filter((fav) => fav !== pk);
		else entity_to_update.favorite_best_practices.push(pk);

		const requestOptions = {
			credentials: 'include',
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
			body: JSON.stringify(entity_to_update),
		};
		fetch(this.state.url + '/api/entity/' + entity_to_update.pk + '/', requestOptions)
			.then((response) => {
				if (response.status > 400) {
					return this.setState(() => {
						return { placeholder: gettext("Quelque chose s'est mal passé !") };
					});
				}
				return response.json();
			})
			.then((data) => {
				this.setState(() => {
					return {
						entity: data,
					};
				});
			});
	}

	manageDetailedBestPractice(bp = {}) {
		var detailPageState = Math.abs(this.state.detailPage - 1);

		this.setState({
			detailPage: detailPageState,
			detailedBestPractice: bp,
		});
	}

	render() {
		return this.state.bestPracticesLoaded &&
			this.state.categoriesLoaded &&
			this.state.keywordsLoaded &&
			this.state.publicsLoaded &&
			this.state.typeLoaded &&
			this.state.organizationTypeLoaded &&
			this.state.sizeLoaded ? (
			this.state.detailPage ? (
				<div style={{ fontFamily: 'DM Sans' }}>
					<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
						<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
							<Breadcrumb.Item underline="hover" color="inherit" href={'/' + this.state.entity.slug}>
								{gettext('Accueil')}
							</Breadcrumb.Item>
							<Breadcrumb.Item active>{gettext('Agir')}</Breadcrumb.Item>
							<Breadcrumb.Item underline="hover" color="inherit" onClick={() => this.manageDetailedBestPractice()}>
								{gettext('Mes favoris')}
							</Breadcrumb.Item>
							<Breadcrumb.Item underline="hover" color="inherit" active>
								{this.state.detailedBestPractice.label}
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
					<div className="p-3 d-flex justify-content-between">
						<Card className="p-4 border" style={{ width: '62%', borderRadius: '16px', borderColor: '#DEDFEA', backgroundColor: '#fff' }}>
							<button
								className="p-2"
								style={{
									position: 'absolute',
									top: '6%',
									right: '5%',
									borderRadius: '4px',
									border: 'none',
									backgroundColor: '#fff',
									fontSize: '18px',
								}}
								onClick={(e) => this.favoritesBestPracticesManagement(e, this.state.detailedBestPractice.pk)}
							>
								{this.state.entity.favorite_best_practices.includes(this.state.detailedBestPractice.pk) ? (
									<i className="bi bi-bookmark-fill pe-0"></i>
								) : (
									<i className="bi bi-bookmark pe-0"></i>
								)}
							</button>
							<Card.Img
								style={{ borderRadius: '6px', height: '45vh', objectFit: 'cover' }}
								variant="top"
								src={
									this.state.detailedBestPractice.logo
										? this.state.detailedBestPractice.logo + '?text=Image cap'
										: '/static/best_practices_catalog/best_practice.jpg?text=Image cap'
								}
								onError={useDefaultBestPracticeImage}
							/>
							<Card.Body className="px-0 py-2">
								<div className="d-flex flex-wrap mb-2">
									{this.state.detailedBestPractice.categories.map((category) => {
										return (
											<Card.Text
												key={'bp-' + this.state.detailedBestPractice.pk + '-type-' + category}
												className="border py-1 px-2 mb-0 me-2"
												style={{
													borderRadius: '24px',
													width: 'fit-content',
													fontSize: '12px',
													fontWeight: '500',
													letterSpacing: '-0.02rem',
													color: `${this.state.categories.find((cat) => cat.pk === category).color}`,
												}}
											>
												<i className="bi bi-circle-fill me-1 pe-1" style={{ fontSize: '8px', top: '1%' }}></i>
												{this.state.categories.find((cat) => cat.pk === category).name}
											</Card.Text>
										);
									})}
								</div>
								<div className="d-flex flex-wrap mb-2">
									{this.state.detailedBestPractice.subcategories.map((subcat) => {
										return (
											<Card.Text
												key={'bp' + this.state.detailedBestPractice.pk + '-type-' + subcat}
												className="border py-1 px-2 mb-0 me-2"
												style={{
													borderRadius: '24px',
													width: 'fit-content',
													fontSize: '12px',
													fontWeight: '500',
													letterSpacing: '-0.02rem',
												}}
											>
												{this.state.subcategories.find((subcategory) => subcategory.pk === subcat).name}
											</Card.Text>
										);
									})}
								</div>
								<Card.Title className="mb-3" style={{ fontSize: '20px', lineHeight: '28px' }}>
									{this.state.detailedBestPractice.label}
								</Card.Title>
								<Card.Text className="mb-0" style={{ fontSize: '14px' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '1%' }} />
									{gettext('Résumé')}
								</Card.Text>
								<Card.Text className="mb-3 ps-4" style={{ fontWeight: '400', fontSize: '16px' }}>
									{this.state.detailedBestPractice.summary}
								</Card.Text>
								<Card.Text className="mb-0" style={{ fontSize: '14px' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '1%' }} />
									{gettext('Date de déploiement')}
								</Card.Text>
								<Card.Text className="mb-3 ps-4" style={{ fontWeight: '400', fontSize: '16px' }}>
									{this.state.detailedBestPractice.deployment_date}
								</Card.Text>
								<Card.Text className="mb-0" style={{ fontSize: '14px' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '1%' }} />
									{gettext('Description')}
								</Card.Text>
								<div className="mb-3 ps-4" dangerouslySetInnerHTML={{ __html: this.state.detailedBestPractice.description }}></div>
								<Card.Text className="mb-0" style={{ fontSize: '14px' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '1%' }} />
									{gettext('Mise en place')}
								</Card.Text>
								<div className="mb-3 ps-4" dangerouslySetInnerHTML={{ __html: this.state.detailedBestPractice.setting_up }}></div>
								<Card.Text className="mb-0" style={{ fontSize: '14px' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '1%' }} />
									{gettext('Difficultés')}
								</Card.Text>
								<div className="mb-3 ps-4" dangerouslySetInnerHTML={{ __html: this.state.detailedBestPractice.difficulties }}></div>
								<Card.Text className="mb-0" style={{ fontSize: '14px' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '1%' }} />
									{gettext('Conseil')}
								</Card.Text>
								<div className="mb-3 ps-4" dangerouslySetInnerHTML={{ __html: this.state.detailedBestPractice.advice }}></div>
								<Card.Text className="mb-0" style={{ fontSize: '14px' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '1%' }} />
									{gettext('Témoignage')}
								</Card.Text>
								<div className="mb-3 ps-4" dangerouslySetInnerHTML={{ __html: this.state.detailedBestPractice.testimony }}></div>
								<Card.Text className="mb-0" style={{ fontSize: '14px' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '1%' }} />
									{gettext('Résultats')}
								</Card.Text>
								<div className="mb-3 ps-4" dangerouslySetInnerHTML={{ __html: this.state.detailedBestPractice.results }}></div>
								<a
									className="button border px-5"
									href={'mailto:' + this.state.detailedBestPractice.email}
									style={{ background: '#8888E2', borderColor: '#8888E2', color: '#fff', borderRadius: '6px', zIndex: '0' }}
								>
									{gettext('Contacter')}
								</a>
							</Card.Body>
						</Card>
						<Card className="p-4 border" style={{ width: '36%', borderRadius: '16px', borderColor: '#DEDFEA', backgroundColor: '#fff' }}>
							<Card.Body className="px-4 py-2 row">
								<Card.Title className="col-12" style={{ fontSize: '24px', lineHeight: '32px' }}>
									{gettext('À propos')}
								</Card.Title>
								<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
									<img alt="" src="/static/img/icon_organisation.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
									{gettext('Organisation')}
								</Card.Text>
								<Card.Text className="my-2 col-8" style={{ fontSize: '16px' }}>
									{this.state.structure.juridic_name}
								</Card.Text>
								<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
									<img alt="" src="/static/img/icon_logo.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
									{gettext('Logo')}
								</Card.Text>
								<div className="my-2 col-8">
									{this.state.structure.logo && (
										<Card.Img
											style={{ borderRadius: '6px', height: '4vh', width: 'auto' }}
											variant="top"
											src={this.state.structure.logo + '?text=Image cap'}
											onError={useDefaultLogo}
										/>
									)}
								</div>
								<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
									<img alt="" src="/static/img/icon_manager.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
									{gettext('Référent')}
								</Card.Text>
								<Card.Text className="my-2 col-8" style={{ fontSize: '16px' }}>
									{this.state.detailedBestPractice.referent}
								</Card.Text>
								<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
									<img alt="" src="/static/img/icon_kpi.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
									{gettext('Mots-clés')}
								</Card.Text>
								<div className="d-flex flex-wrap my-2 col-8">
									{this.state.detailedBestPractice.keywords.map((keyword) => {
										return (
											<Card.Text className="p-0 m-0" key={keyword} style={{ fontSize: '16px' }}>
												{this.state.keywords.find((kw) => kw.pk === keyword).label}&nbsp;
											</Card.Text>
										);
									})}
								</div>
								<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
									<img alt="" src="/static/img/icon_country.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
									{gettext('Pays')}
								</Card.Text>
								<Card.Text className="my-2 col-8" style={{ fontSize: '16px' }}>
									{this.state.countries.find((country) => country[0] === this.state.detailedBestPractice.country)[1]}
								</Card.Text>
								<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
									{gettext('Public')}
								</Card.Text>
								<div className="d-flex flex-wrap my-2 col-8">
									{this.state.detailedBestPractice.publics.map((pub) => {
										return (
											<Card.Text className="p-0 m-0" key={pub} style={{ fontSize: '16px' }}>
												{this.state.publics.find((p) => p.pk === pub).label}&nbsp;
											</Card.Text>
										);
									})}
								</div>
								<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
									{gettext('Type')}
								</Card.Text>
								<div className="d-flex flex-wrap my-2 col-8">
									{this.state.detailedBestPractice.type.map((type) => {
										return (
											<Card.Text className="p-0 m-0" key={type} style={{ fontSize: '16px' }}>
												{this.state.type.find((t) => t.pk === type).label}&nbsp;
											</Card.Text>
										);
									})}
								</div>
								<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
									{gettext("Type d'organisation")}
								</Card.Text>
								<div className="d-flex flex-wrap my-2 col-8">
									{this.state.detailedBestPractice.organization_type.map((organization_type) => {
										return (
											<Card.Text className="p-0 m-0" key={organization_type} style={{ fontSize: '16px' }}>
												{this.state.organization_type.find((ot) => ot.pk === organization_type).label}&nbsp;
											</Card.Text>
										);
									})}
								</div>
								<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
									{gettext('Taille')}
								</Card.Text>
								<div className="d-flex flex-wrap my-2 col-8">
									{this.state.detailedBestPractice.size.map((size) => {
										return (
											<Card.Text className="p-0 m-0" key={size} style={{ fontSize: '16px' }}>
												{this.state.size.find((s) => s.pk === size).label}&nbsp;
											</Card.Text>
										);
									})}
								</div>
							</Card.Body>
						</Card>
					</div>
				</div>
			) : (
				<div style={{ fontFamily: 'DM Sans' }}>
					<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
						<Breadcrumb className="ps-4" separators=">" aria-label="breadcrumb">
							<Breadcrumb.Item underline="hover" color="inherit" href={'/' + this.state.entity.slug}>
								{gettext('Accueil')}
							</Breadcrumb.Item>
							<Breadcrumb.Item active>{gettext('Agir')}</Breadcrumb.Item>
							<Breadcrumb.Item underline="hover" color="inherit" active>
								{gettext('Mes favoris')}
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
					<div className="p-5 text-center">
						<h4 className="p-2">{gettext('Mes favoris')}</h4>
					</div>
					<div className="py-3" style={{ paddingLeft: '5vw', paddingRight: '5vw' }}>
						<div className="d-flex justify-content-around flex-wrap">
							{this.state.bestPractices.length > 0 ? (
								this.state.bestPractices.map((bp) => {
									return (
										<Card key={bp.pk} className="p-0 my-3" style={{ width: '30%', borderRadius: '16px' }}>
											<button
												className="p-2"
												style={{
													position: 'absolute',
													top: '6%',
													right: '5%',
													borderRadius: '4px',
													border: 'none',
													backgroundColor: '#fff',
													fontSize: '18px',
												}}
												onClick={(e) => this.favoritesBestPracticesManagement(e, bp.pk)}
											>
												{this.state.entity.favorite_best_practices.includes(bp.pk) ? (
													<i className="bi bi-bookmark-fill pe-0"></i>
												) : (
													<i className="bi bi-bookmark pe-0"></i>
												)}
											</button>
											<Card.Img
												style={{ borderTopLeftRadius: '16px', borderTopRightRadius: '16px', height: '25vh', objectFit: 'cover' }}
												variant="top"
												src={bp.logo ? bp.logo + '?text=Image cap' : '/static/best_practices_catalog/best_practice.jpg?text=Image cap'}
												onError={useDefaultBestPracticeImage}
											/>
											<Card.Body
												className="px-4 pt-2 pb-0"
												style={{ cursor: 'pointer' }}
												onClick={() => this.manageDetailedBestPractice(bp)}
											>
												<div className="d-flex flex-wrap mb-2">
													{bp.categories.map((category) => {
														return (
															<Card.Text
																key={'bp-' + bp.pk + '-type-' + category}
																className="border py-1 px-2 mb-0 me-2"
																style={{
																	borderRadius: '24px',
																	width: 'fit-content',
																	fontSize: '12px',
																	fontWeight: '500',
																	letterSpacing: '-0.02rem',
																	color: `${this.state.categories.find((cat) => cat.pk === category).color}`,
																}}
															>
																<i className="bi bi-circle-fill me-1 pe-1" style={{ fontSize: '8px', top: '1%' }}></i>
																{this.state.categories.find((cat) => cat.pk === category).name}
															</Card.Text>
														);
													})}
												</div>
												<Card.Title style={{ fontWeight: '500', fontSize: '16px' }}>{bp.label}</Card.Title>
												<Card.Text style={{ color: '#9094AA', fontWeight: '400', fontSize: '14px' }}>{bp.summary}</Card.Text>
												<div className="d-flex flex-wrap">
													{bp.keywords.map((keyword) => {
														return (
															<Card.Text
																key={keyword}
																className="border py-1 px-2 mb-3 me-2"
																style={{
																	borderRadius: '4px',
																	backgroundColor: '#FAFAFA',
																	borderColor: '#F0F0F0',
																	width: 'fit-content',
																	fontSize: '12px',
																	fontWeight: '500',
																	letterSpacing: '-0.02rem',
																}}
															>
																{this.state.keywords.find((kw) => kw.pk === keyword).label}
															</Card.Text>
														);
													})}
												</div>
											</Card.Body>
											<Card.Footer style={{ background: '#fff', borderColor: '#fff', borderRadius: '16px' }}>
												{this.state.structure.logo && (
													<Card.Img
														style={{ borderRadius: '6px', height: '3vh', width: 'auto', float: 'right' }}
														variant="top"
														src={this.state.structure.logo + '?text=Image cap'}
														onError={useDefaultLogo}
													/>
												)}
											</Card.Footer>
										</Card>
									);
								})
							) : (
								<a
									href={'/' + this.state.entity.slug + '/take-action/search-best-practices/'}
									className="button border m-2"
									style={{
										background: '#8785BB',
										borderColor: '#8785BB',
										color: '#fff',
										borderRadius: '14px',
										whiteSpace: 'nowrap',
										fontWeight: '550',
										maxWidth: 'fit-content',
									}}
								>
									{gettext('Chercher une bonne pratique')}
								</a>
							)}
						</div>
					</div>
				</div>
			)
		) : (
			<Loading message={this.state.placeholder} />
		);
	}
}

export default FavoriteBestPractices;
