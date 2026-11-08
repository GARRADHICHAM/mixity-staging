import React, { Component } from 'react';
import Loading from '../../mixity/dashboard/js/includes/Loading';
import { useDefaultLogo, useDefaultSolutionImage } from '../../mixity/dashboard/js/includes/imageFallback';
import { Breadcrumb, Card, Form } from 'react-bootstrap';
import Header from '../../mixity/dashboard/js/includes/Header';

class Favorites extends Component {
	constructor(props) {
		super(props);
		this.state = {
			entity: {},
			structure: {},
			solutions: [],
			filteredSolutions: [],
			detailedSolution: {},
			solvers: [],
			categories: [],
			subcategories: [],
			languages: [],
			solution_formats: [],
			keywords: [],
			countries: [],
			regions: [],
			mixity_members: [],
			url: '',
			user: {},
			solutionsLoaded: false,
			categoriesLoaded: false,
			keywordsLoaded: false,
			languagesLoaded: false,
			solutionFormatsLoaded: false,
			entityLoaded: false,
			solversLoaded: false,
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
								this.setState(
									() => {
										return {
											entity: data[0],
											structure: data[0].structure,
											entityLoaded: true,
										};
									},
									() => {
										fetch(this.state.url + '/api/solution/')
											.then((response) => {
												if (response.status > 400) {
													return this.setState(() => {
														return { placeholder: gettext("Quelque chose s'est mal passé !") };
													});
												}
												return response.json();
											})
											.then((data) => {
												var filteredSolutions = data.filter((solution) =>
													this.state.structure.favorite_solutions.includes(solution.pk),
												);
												this.setState(() => {
													return {
														solutions: filteredSolutions,
														solutionsLoaded: true,
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
						fetch(this.state.url + '/api/mixity-members/')
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
										mixity_members: data,
									};
								});
							});
						fetch(this.state.url + '/api/solvers/')
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
										solvers: data,
										solversLoaded: true,
									};
								});
							});
						fetch(this.state.url + '/api/solutionkeyword/')
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
						fetch(this.state.url + '/api/language/')
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
										languages: data,
										languagesLoaded: true,
									};
								});
							});
						fetch(this.state.url + '/api/membership/')
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
										user: data,
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
										regions: data['regions'],
									};
								});
							});
						fetch(this.state.url + '/api/formats/')
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
										solution_formats: data,
										solutionFormatsLoaded: true,
									};
								});
							});
					},
				);
			});
	}

	/* Add/Remove from favorites */
	favoritesManagement(e, pk) {
		e.preventDefault();

		var structure = {
			pk: this.state.structure.pk,
			juridic_name: this.state.structure.juridic_name,
			slug: this.state.structure.slug,
			favorite_solutions: this.state.structure.favorite_solutions,
		};

		if (structure.favorite_solutions.includes(pk)) structure.favorite_solutions = structure.favorite_solutions.filter((fav) => fav !== pk);
		else structure.favorite_solutions.push(pk);

		const requestOptions = {
			credentials: 'include',
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
			body: JSON.stringify(structure),
		};
		fetch(this.state.url + '/api/structure/' + structure.pk + '/', requestOptions)
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
						structure: data,
					};
				});
			});
	}

	/* Manage parameters to add tracked users to the clicked solution */
	saveSolution(solution, tracker) {
		if (tracker === 'solution_tracker') solution.users_tracked.push(this.state.user.user_id);
		else solution.users_tracked_contact.push(this.state.user.user_id);
		const requestOptions = {
			credentials: 'include',
			method: 'PATCH',
			headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
			body: JSON.stringify({
				pk: solution.pk,
				users_tracked: solution.users_tracked,
				users_tracked_contact: solution.users_tracked_contact,
			}),
		};

		fetch(this.state.url + '/api/solution/' + solution.pk + '/', requestOptions)
			.then((response) => {
				if (response.status > 400) {
					return this.setState(() => {
						return { placeholder: gettext("Quelque chose s'est mal passé !") };
					});
				}
				return response.json();
			})
			.then((data) => {
				var solutionsData = [];
				this.state.solutions.map((sol) => {
					if (sol.pk === data.pk) solutionsData.push(data);
					else solutionsData.push(sol);
				});
				this.setState({
					detailedSolution: data,
					solutions: solutionsData,
				});
			});
	}

	tracking_contact = (event) => {
		if (
			!this.state.detailedSolution.users_tracked_contact.includes(this.state.user.user_id) &&
			!this.state.mixity_members.includes(this.state.user.user_id)
		)
			this.saveSolution(this.state.detailedSolution, 'contact_tracker');
		event.preventDefault();
		window.location.href = 'mailto:' + this.state.detailedSolution.email;
	};

	/* To display or not detailed page */
	manageDetailedSolution(solution = {}) {
		var detailPageState = Math.abs(this.state.detailPage - 1);
		this.setState({
			detailPage: detailPageState,
			detailedSolution: solution,
		});
		if (detailPageState && !solution.users_tracked.includes(this.state.user.user_id) && !this.state.mixity_members.includes(this.state.user.user_id))
			this.saveSolution(solution, 'solution_tracker');
	}

	languageSelectorFunction(languageCode) {
		document.cookie = 'language_code=' + languageCode + '; path=/;';
		window.location.reload(true);
	}

	render() {
		return this.state.solutionsLoaded &&
			this.state.categoriesLoaded &&
			this.state.keywordsLoaded &&
			this.state.languagesLoaded &&
			this.state.entityLoaded &&
			this.state.solversLoaded &&
			this.state.solutionFormatsLoaded ? (
			this.state.detailPage ? (
				<div style={{ fontFamily: 'DM Sans' }}>
					<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
						<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
							<Breadcrumb.Item underline="hover" color="inherit" href={'/' + this.state.entity.slug}>
								{gettext('Accueil')}
							</Breadcrumb.Item>
							<Breadcrumb.Item active>{gettext('Agir')}</Breadcrumb.Item>
							<Breadcrumb.Item underline="hover" color="inherit" onClick={() => this.manageDetailedSolution()}>
								{gettext('Mes favoris')}
							</Breadcrumb.Item>
							<Breadcrumb.Item underline="hover" color="inherit" active>
								{this.state.detailedSolution.title}
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
							{!this.state.user.is_reader && (
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
									onClick={(e) => this.favoritesManagement(e, this.state.detailedSolution.pk)}
								>
									{this.state.structure.favorite_solutions.includes(this.state.detailedSolution.pk) ? (
										<i className="bi bi-bookmark-fill pe-0"></i>
									) : (
										<i className="bi bi-bookmark pe-0"></i>
									)}
								</button>
							)}
							<Card.Img
								style={{ borderRadius: '6px', height: '45vh', objectFit: 'cover' }}
								variant="top"
								src={
									this.state.detailedSolution.photo
										? this.state.detailedSolution.photo + '?text=Image cap'
										: '/static/solvers_catalog/solution.jpg?text=Image cap'
								}
								onError={useDefaultSolutionImage}
							/>
							<Card.Body className="px-0 py-2">
								<div className="d-flex flex-wrap mb-2">
									{this.state.detailedSolution.categories.map((category) => {
										return (
											<Card.Text
												key={this.state.detailedSolution.pk + '-type-' + category}
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
									{this.state.detailedSolution.subcategories.map((subcat) => {
										return (
											<Card.Text
												key={this.state.detailedSolution.pk + '-type-' + subcat}
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
									{this.state.detailedSolution.title}
								</Card.Title>
								<Card.Text className="mb-0" style={{ fontSize: '14px' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '1%' }} />
									{gettext('Résumé')}
								</Card.Text>
								<Card.Text className="mb-3 ps-4" style={{ fontWeight: '400', fontSize: '16px' }}>
									{this.state.detailedSolution.summary}
								</Card.Text>
								<Card.Text className="mb-0" style={{ fontSize: '14px' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '1%' }} />
									{gettext('Description')}
								</Card.Text>
								<div className="mb-3 ps-4" dangerouslySetInnerHTML={{ __html: this.state.detailedSolution.description }}></div>
								<Card.Text className="mb-0" style={{ fontSize: '14px' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '1%' }} />
									{gettext('Public')}
								</Card.Text>
								<div className="mb-3 ps-4" dangerouslySetInnerHTML={{ __html: this.state.detailedSolution.public }}></div>
								<Card.Text className="mb-0" style={{ fontSize: '14px' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '1%' }} />
									{gettext('Objectif')}
								</Card.Text>
								<div className="mb-3 ps-4" dangerouslySetInnerHTML={{ __html: this.state.detailedSolution.objective }}></div>
								<Card.Text className="mb-0" style={{ fontSize: '14px' }}>
									<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '1%' }} />
									{gettext('Format')}
								</Card.Text>
								<div className="mb-3 ps-4" dangerouslySetInnerHTML={{ __html: this.state.detailedSolution.format_session }}></div>
								{!this.state.user.is_reader && (
									<a
										className="button border px-5"
										onClick={this.tracking_contact}
										style={{ background: '#8888E2', borderColor: '#8888E2', color: '#fff', borderRadius: '6px', zIndex: '0' }}
									>
										{gettext('Contacter')}
									</a>
								)}
							</Card.Body>
						</Card>
						<Card className="p-4 border" style={{ width: '36%', borderRadius: '16px', borderColor: '#DEDFEA', backgroundColor: '#fff' }}>
							<Card.Body className="px-0 py-2 row">
								<Card.Title className="col-12" style={{ fontSize: '24px', lineHeight: '32px' }}>
									{gettext('À propos')}
								</Card.Title>
								<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
									<img alt="" src="/static/img/icon_organisation.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
									{gettext('Organisation')}
								</Card.Text>
								<Card.Text className="my-2 col-8" style={{ fontSize: '16px' }}>
									{this.state.solvers.find((solver) => solver.pk === this.state.detailedSolution.solver).structure.juridic_name}
								</Card.Text>
								<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
									<img alt="" src="/static/img/icon_logo.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
									{gettext('Logo')}
								</Card.Text>
								<div className="my-2 col-8">
									{this.state.solvers.find((solver) => solver.pk === this.state.detailedSolution.solver).structure.logo && (
										<Card.Img
											style={{ borderRadius: '6px', height: '4vh', width: 'auto' }}
											variant="top"
											src={
												this.state.solvers.find((solver) => solver.pk === this.state.detailedSolution.solver).structure.logo +
												'?text=Image cap'
											}
											onError={useDefaultLogo}
										/>
									)}
								</div>
								<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
									<img alt="" src="/static/img/icon_manager.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
									{gettext('Référent')}
								</Card.Text>
								<Card.Text className="my-2 col-8" style={{ fontSize: '16px' }}>
									{this.state.detailedSolution.referent}
								</Card.Text>
								<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
									<img alt="" src="/static/img/icon_kpi.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
									{gettext('Mots-clés')}
								</Card.Text>
								<div className="d-flex flex-wrap my-2 col-8">
									{this.state.detailedSolution.keywords.map((keyword) => {
										return (
											<Card.Text className="p-0 m-0" key={keyword} style={{ fontSize: '14px' }}>
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
									{this.state.countries.find((country) => country[0] === this.state.detailedSolution.country)[1]}
									{this.state.detailedSolution.country === 'FR' && this.state.detailedSolution.region
										? ' - ' + this.state.regions.find((region) => region[0] === this.state.detailedSolution.region)[1]
										: ''}
								</Card.Text>
								<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
									<img alt="" src="/static/img/icon_language.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
									{gettext('Langues')}
								</Card.Text>
								<div className="d-flex flex-wrap my-2 col-8">
									{this.state.detailedSolution.languages.map((lang) => {
										return (
											<Card.Text className="p-0 m-0" key={lang} style={{ fontSize: '16px' }}>
												{this.state.languages.find((kw) => kw.pk === lang).label}&nbsp;
											</Card.Text>
										);
									})}
								</div>
								<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
									<img alt="" src="/static/img/icon_budget.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
									{gettext('Prix')}
								</Card.Text>
								<div
									className="my-2 col-8"
									style={{ fontSize: '16px' }}
									dangerouslySetInnerHTML={{ __html: this.state.detailedSolution.price_desc }}
								></div>
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
							{this.state.solutions.length > 0 ? (
								this.state.solutions.map((solution) => {
									return (
										<Card key={solution.pk} className="p-0 my-3" style={{ width: '30%', borderRadius: '16px' }}>
											{!this.state.user.is_reader && (
												<button
													className="p-2"
													style={{
														position: 'absolute',
														top: '3%',
														right: '3%',
														borderRadius: '4px',
														border: 'none',
														backgroundColor: '#fff',
														fontSize: '18px',
													}}
													onClick={(e) => this.favoritesManagement(e, solution.pk)}
												>
													{this.state.structure.favorite_solutions.includes(solution.pk) ? (
														<i className="bi bi-bookmark-fill pe-0"></i>
													) : (
														<i className="bi bi-bookmark pe-0"></i>
													)}
												</button>
											)}
											<Card.Img
												style={{ borderTopLeftRadius: '16px', borderTopRightRadius: '16px', height: '25vh', objectFit: 'cover' }}
												variant="top"
												src={
													solution.photo ? solution.photo + '?text=Image cap' : '/static/solvers_catalog/solution.jpg?text=Image cap'
												}
												onError={useDefaultSolutionImage}
											/>
											<Card.Body
												className="px-4 pt-2 pb-0"
												style={{ cursor: 'pointer' }}
												onClick={() => this.manageDetailedSolution(solution)}
											>
												<div className="d-flex flex-wrap mb-2">
													{solution.categories.map((category) => {
														return (
															<Card.Text
																key={solution.pk + '-type-' + category}
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
												<Card.Title style={{ fontWeight: '500', fontSize: '16px' }}>{solution.title}</Card.Title>
												<Card.Text style={{ color: '#9094AA', fontWeight: '400', fontSize: '14px' }}>{solution.summary}</Card.Text>
												<div className="d-flex flex-wrap">
													{solution.keywords.map((keyword) => {
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
												{this.state.solvers.find((solver) => solver.pk === solution.solver).structure.logo && (
													<Card.Img
														style={{ borderRadius: '6px', height: '3vh', width: 'auto', float: 'right' }}
														variant="top"
														src={
															this.state.solvers.find((solver) => solver.pk === solution.solver).structure.logo +
															'?text=Image cap'
														}
														onError={useDefaultLogo}
													/>
												)}
											</Card.Footer>
										</Card>
									);
								})
							) : (
								<a
									href={'/' + this.state.entity.slug + '/take-action/search-solutions/'}
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
									{gettext('Chercher une solution')}
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

export default Favorites;
