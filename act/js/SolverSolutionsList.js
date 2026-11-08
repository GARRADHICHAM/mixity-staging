import React, { Component } from 'react';
import Loading from '../../mixity/dashboard/js/includes/Loading';
import { Breadcrumb, Card, Form, Modal } from 'react-bootstrap';
import { Editor } from '@tinymce/tinymce-react';
import Header from '../../mixity/dashboard/js/includes/Header';

class SolverSolutions extends Component {
	constructor(props) {
		super(props);
		this.state = {
			entity: {},
			structure: {},
			solver: {},
			solutions: [],
			detailedSolution: {},
			url: '',
			user: {},
			modificationSolution: {
				pk: null,
				title: '',
				summary: '',
				photo: '',
				referent: '',
				email: '',
				description: '',
				country: 'FR',
				region: 'FR-ARA',
				price_desc: '',
				public: '',
				objective: '',
				format_session: '',
				solution_formats: [],
				solver: null,
				categories: [],
				subcategories: [],
				languages: [],
				keywords: [],
				structures: [],
				users_tracked: [],
				users_tracked_contact: [],
			},
			categories: [],
			categories_count: 0,
			categories_limit: false,
			subcategories: [],
			subcategories_count: 0,
			subcategories_limit: false,
			languages: [],
			keywords: [],
			countries: [],
			regions: [],
			errors: {},
			solution_formats: [],
			solution_formats_count: 0,
			solution_formats_limit: false,
			solutionsLoaded: false,
			categoriesLoaded: false,
			keywordsLoaded: false,
			languagesLoaded: false,
			solutionFormatsLoaded: false,
			solverLoaded: false,
			entityLoaded: false,
			detailPage: false,
			modifySolution: false,
			lgShow: false,
			placeholder: gettext('Chargement'),
		};

		this.saveSolution = this.saveSolution.bind(this);
		this.handleModificationSolutionDescription = this.handleModificationSolutionDescription.bind(this);
		this.handleModificationSolutionPrice = this.handleModificationSolutionPrice.bind(this);
		this.handleModificationSolutionPublic = this.handleModificationSolutionPublic.bind(this);
		this.handleModificationSolutionObjective = this.handleModificationSolutionObjective.bind(this);
		this.handleModificationSolutionFormat = this.handleModificationSolutionFormat.bind(this);
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
								this.setState(() => {
									return {
										entity: data[0],
										structure: data[0].structure,
										entityLoaded: true,
									};
								});
							});
						fetch(this.state.url + '/api/solver-solution/')
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
										solutions: data,
										solutionsLoaded: true,
									};
								});
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
						fetch(this.state.url + '/api/solver/')
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
										solver: data[0],
										solverLoaded: true,
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

	uploadSolutionPicture(pk, picture) {
		var formData = new FormData();
		const truncatedName = picture.name.substring(0, 60) + picture.name.substring(picture.name.length - 5);
		const newPicture = new File([picture], truncatedName, { type: picture.type });
		formData.append('pk', pk);
		formData.append('photo', newPicture);
		const params = {
			credentials: 'include',
			method: 'PATCH',
			headers: { 'X-CSRFToken': csrftoken },
			body: formData,
		};
		fetch(this.state.url + '/api/solver-solution/' + pk + '/', params)
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
				if (this.state.solutions.find((solution) => solution.pk === data.pk)) {
					this.state.solutions.map((sol) => {
						if (sol.pk === data.pk) solutionsData.push(data);
						else solutionsData.push(sol);
					});
				} else {
					solutionsData = [...this.state.solutions, data];
				}
				this.setState({
					detailedSolution: data,
					solutions: solutionsData,
					detailPage: true,
					modifySolution: false,
				});
			});
	}

	/* Make requests concerning a solution */
	solutionApiRequest(params, picture, pk = '') {
		var link = this.state.url + '/api/solver-solution/';
		if (pk) link = link + pk + '/';
		fetch(link, params)
			.then((response) => {
				if (response.status > 400) {
					return this.setState(() => {
						return { placeholder: gettext("Quelque chose s'est mal passé !") };
					});
				}
				return response.json();
			})
			.then((data) => {
				if (!pk) {
					if (picture) {
						this.uploadSolutionPicture(data.pk, picture);
					} else {
						const datas = [...this.state.solutions, data];
						this.setState({
							detailedSolution: data,
							solutions: datas,
							detailPage: true,
							modifySolution: false,
						});
					}
				} else {
					if (picture) {
						this.uploadSolutionPicture(data.pk, picture);
					} else {
						var solutionsData = [];
						this.state.solutions.map((sol) => {
							if (sol.pk === data.pk) solutionsData.push(data);
							else solutionsData.push(sol);
						});
						this.setState({
							detailedSolution: data,
							solutions: solutionsData,
							detailPage: true,
							modifySolution: false,
						});
					}
				}
			});
	}

	/* Manage parameters to create/update solution requests */
	saveSolution(e) {
		e.preventDefault();
		var solution = this.state.modificationSolution;

		let errors = {};
		let formIsValid = true;

		if (solution.description === '') {
			errors['description'] = gettext('Ne peut être vide');
			formIsValid = false;
		}
		if (solution.categories.length === 0) {
			errors['categories'] = gettext('Nécessite au moins un choix');
			formIsValid = false;
		}
		if (solution.subcategories.length === 0) {
			errors['subcategories'] = gettext('Nécessite au moins un choix');
			formIsValid = false;
		}
		if (solution.languages.length === 0) {
			errors['languages'] = gettext('Nécessite au moins un choix');
			formIsValid = false;
		}
		if (solution.solution_formats.length === 0) {
			errors['solution_formats'] = gettext('Nécessite au moins un choix');
			formIsValid = false;
		}
		if (!formIsValid) {
			this.setState({ errors: errors });
			return;
		}

		var picture = null;
		if (solution.hasOwnProperty('photo')) {
			if (typeof solution.photo !== 'string' && solution.photo != null) picture = solution.photo;
			delete solution['photo'];
		}

		if (solution.pk) {
			const requestOptions = {
				credentials: 'include',
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
				body: JSON.stringify(solution),
			};
			this.solutionApiRequest(requestOptions, picture, solution.pk);
		} else {
			const requestOptions = {
				credentials: 'include',
				method: 'POST',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
				body: JSON.stringify(solution),
			};
			this.solutionApiRequest(requestOptions, picture);
		}
	}

	deleteSolution() {
		if (this.state.detailedSolution.pk) {
			const filteredItems = this.state.solutions.filter((solution) => solution.pk !== this.state.detailedSolution.pk);
			const requestOptions = {
				credentials: 'include',
				method: 'DELETE',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
				body: JSON.stringify(this.state.detailedSolution.pk),
			};
			fetch(this.state.url + '/api/solver-solution/' + this.state.detailedSolution.pk, requestOptions).then(() =>
				this.setState({
					solutions: filteredItems,
					detailPage: false,
					lgShow: false,
				}),
			);
		}
	}

	/* To display or not detailed page */
	manageDetailedSolution(solution = {}) {
		var detailPageState = Math.abs(this.state.detailPage - 1);

		this.setState({
			detailedSolution: solution,
			detailPage: detailPageState,
		});
	}

	/* To display or not detailed page */
	manageSolutionModification(solution = null) {
		var modifySolutionState = Math.abs(this.state.modifySolution - 1);
		if (!solution) {
			solution = {
				pk: null,
				title: '',
				summary: '',
				photo: '',
				referent: '',
				email: '',
				description: '',
				country: 'FR',
				region: 'FR-ARA',
				price_desc: '',
				public: '',
				objective: '',
				format_session: '',
				solution_formats: [],
				solver: this.state.solver.pk,
				categories: [],
				subcategories: [],
				languages: [],
				keywords: [],
				structures: [],
				users_tracked: [],
				users_tracked_contact: [],
			};
		}

		this.setState({
			modifySolution: modifySolutionState,
			modificationSolution: solution,
		});
	}

	/* Front filter management */
	handleModificationSolutionTitle(title) {
		const solution = this.state.modificationSolution;
		solution.title = title;
		this.setState({ modificationSolution: solution });
	}

	handleModificationSolutionSummary(summary) {
		const solution = this.state.modificationSolution;
		solution.summary = summary;
		this.setState({ modificationSolution: solution });
	}

	handleModificationSolutionPhoto(photo) {
		const solution = this.state.modificationSolution;
		solution.photo = photo;
		this.setState({ modificationSolution: solution });
	}

	handleModificationSolutionReferent(referent) {
		const solution = this.state.modificationSolution;
		solution.referent = referent;
		this.setState({ modificationSolution: solution });
	}

	handleModificationSolutionEmail(email) {
		const solution = this.state.modificationSolution;
		solution.email = email;
		this.setState({ modificationSolution: solution });
	}

	handleCountryAction(e) {
		const solution = this.state.modificationSolution;
		if (e.target.value === 'FR') solution.region = 'FR-ARA';
		solution.country = e.target.value;
		this.setState({ modificationSolution: solution });
	}

	handleRegionAction(e) {
		const solution = this.state.modificationSolution;
		solution.region = e.target.value;
		this.setState({ modificationSolution: solution });
	}

	handleModificationSolutionDescription(description, editor) {
		const solution = this.state.modificationSolution;
		solution.description = description;
		this.setState({ modificationSolution: solution });
	}

	handleModificationSolutionPrice(price_desc, editor) {
		const solution = this.state.modificationSolution;
		solution.price_desc = price_desc;
		this.setState({ modificationSolution: solution });
	}

	handleModificationSolutionPublic(public_text, editor) {
		const solution = this.state.modificationSolution;
		solution.public = public_text;
		this.setState({ modificationSolution: solution });
	}

	handleModificationSolutionObjective(objective, editor) {
		const solution = this.state.modificationSolution;
		solution.objective = objective;
		this.setState({ modificationSolution: solution });
	}

	handleModificationSolutionFormat(format_session, editor) {
		const solution = this.state.modificationSolution;
		solution.format_session = format_session;
		this.setState({ modificationSolution: solution });
	}

	handleModificationSolutionLanguages(pk) {
		var solution = this.state.modificationSolution;

		if (solution.languages.includes(pk)) solution.languages = this.state.modificationSolution.languages.filter((langPk) => langPk !== pk);
		else solution.languages.push(pk);
		this.setState({ modificationSolution: solution });
	}

	handleModificationSolutionKeywords(pk) {
		var solution = this.state.modificationSolution;

		if (solution.keywords.includes(pk)) solution.keywords = this.state.modificationSolution.keywords.filter((langPk) => langPk !== pk);
		else solution.keywords.push(pk);
		this.setState({ modificationSolution: solution });
	}

	limitChoicesFieldsCounter(e, count, limit_bool) {
		//  Limiting number of choices in form fields to 2 choices only
		// Incrementing on checking
		if (e.target.checked) {
			if (count < 2) {
				count++;
			}
		} else {
			// Decrementing on unchecking
			if (count > 0) {
				count--;
				limit_bool = false;
			} else {
				count = 0;
			}
		}
		return { count: count, limit: limit_bool };
	}

	handleModificationSolutionCategories(pk, event) {
		var solution = this.state.modificationSolution;
		let { count, limit } = this.limitChoicesFieldsCounter(event, this.state.categories_count, this.state.categories_limit);
		this.state.categories_count = count;
		this.state.categories_limit = limit;
		if (!this.state.categories_limit) {
			if (this.state.categories_count == 2) {
				this.state.categories_limit = true;
			}
			if (solution.categories.includes(pk)) solution.categories = this.state.modificationSolution.categories.filter((langPk) => langPk !== pk);
			else solution.categories.push(pk);
		}
		this.setState({ modificationSolution: solution });
	}

	handleModificationSolutionSubCategories(pk, event) {
		var solution = this.state.modificationSolution;
		let { count, limit } = this.limitChoicesFieldsCounter(event, this.state.subcategories_count, this.state.subcategories_limit);
		this.state.subcategories_count = count;
		this.state.subcategories_limit = limit;
		if (!this.state.subcategories_limit) {
			if (this.state.subcategories_count == 2) {
				this.state.subcategories_limit = true;
			}
			if (solution.subcategories.includes(pk)) solution.subcategories = this.state.modificationSolution.subcategories.filter((langPk) => langPk !== pk);
			else solution.subcategories.push(pk);
		}
		this.setState({ modificationSolution: solution });
	}

	handleModificationSolutionFormats(pk, event) {
		var solution = this.state.modificationSolution;
		let { count, limit } = this.limitChoicesFieldsCounter(event, this.state.solution_formats_count, this.state.solution_formats_limit);
		this.state.solution_formats_count = count;
		this.state.solution_formats_limit = limit;
		if (!this.state.solution_formats_limit) {
			if (this.state.solution_formats_count == 2) {
				this.state.solution_formats_limit = true;
			}
			if (solution.solution_formats.includes(pk))
				solution.solution_formats = this.state.modificationSolution.solution_formats.filter((formatPk) => formatPk !== pk);
			else solution.solution_formats.push(pk);
		}
		this.setState({ modificationSolution: solution });
	}

	/* Displaying or not the filters modal */
	setLgShow(boolean) {
		this.setState({ lgShow: boolean });
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
			this.state.solverLoaded &&
			this.state.entityLoaded &&
			this.state.solutionFormatsLoaded ? (
			this.state.detailPage || this.state.modifySolution ? (
				this.state.modifySolution ? (
					// Solver solutions creation page and modification page
					<div style={{ fontFamily: 'DM Sans' }}>
						<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
							<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
								<Breadcrumb.Item underline="hover" color="inherit" href={'/' + this.state.entity.slug}>
									{gettext('Accueil')}
								</Breadcrumb.Item>
								<Breadcrumb.Item underline="hover" color="inherit" onClick={() => this.manageSolutionModification()}>
									{this.state.detailPage ? this.state.detailedSolution.title : gettext('Mes solutions')}
								</Breadcrumb.Item>
								<Breadcrumb.Item underline="hover" color="inherit" active>
									{this.state.modificationSolution.title
										? this.state.modificationSolution.title
										: gettext("Création d'une nouvelle solution")}
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
						<div className="d-flex justify-content-center">
							<Card className="p-4 border" style={{ width: '70%', borderRadius: '16px', borderColor: '#DEDFEA', backgroundColor: '#fff' }}>
								<form onSubmit={this.saveSolution}>
									<Card.Title style={{ fontSize: '16px' }}>
										{gettext('Titre')} : * <i style={{ fontSize: '14px' }}>(80 {gettext('caractères maximum')})</i>
									</Card.Title>
									<input
										type="text"
										required
										maxLength="80"
										className="mb-3"
										style={{
											letterSpacing: '-0.04em',
											color: '#000',
											background: 'transparent',
											border: 'solid',
											borderRadius: '12px',
											borderWidth: '1px',
											borderColor: '#000',
											fontSize: '1em',
											padding: '0.5em',
										}}
										value={this.state.modificationSolution.title}
										onChange={(e) => this.handleModificationSolutionTitle(e.target.value)}
									/>

									<Card.Title style={{ fontSize: '16px' }}>
										{gettext('Résumé')} : * <i style={{ fontSize: '14px' }}>(250 {gettext('caractères maximum')})</i>
									</Card.Title>
									<textarea
										type="text"
										required
										maxLength="250"
										className="mb-3"
										style={{
											letterSpacing: '-0.04em',
											color: '#000',
											background: 'transparent',
											border: 'solid',
											borderRadius: '12px',
											borderWidth: '1px',
											borderColor: '#000',
											fontSize: '1em',
											padding: '0.5em',
										}}
										value={this.state.modificationSolution.summary}
										onChange={(e) => this.handleModificationSolutionSummary(e.target.value)}
									/>

									<Card.Title style={{ fontSize: '16px' }}>{gettext('Miniature de la solution')} :</Card.Title>
									<input
										type="file"
										className="mb-3"
										style={{
											letterSpacing: '-0.04em',
											color: '#000',
											background: 'transparent',
											border: 'solid',
											borderRadius: '12px',
											borderWidth: '1px',
											borderColor: '#000',
											padding: '0.5em',
										}}
										onChange={(e) => this.handleModificationSolutionPhoto(e.target.files[0])}
									/>

									<div className="row mb-3">
										<div className="col-6">
											<Card.Title style={{ fontSize: '16px' }}>
												{gettext('Responsable')} : * <i style={{ fontSize: '14px' }}>(50 {gettext('caractères maximum')})</i>
											</Card.Title>
											<input
												type="text"
												required
												maxLength="50"
												style={{
													width: '70%',
													letterSpacing: '-0.04em',
													color: '#000',
													background: 'transparent',
													border: 'solid',
													borderRadius: '12px',
													borderWidth: '1px',
													borderColor: '#000',
													fontSize: '1em',
													padding: '0.5em',
												}}
												value={this.state.modificationSolution.referent}
												onChange={(e) => this.handleModificationSolutionReferent(e.target.value)}
											/>
										</div>
										<div className="col-6">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Adresse email')} : *</Card.Title>
											<input
												type="email"
												required
												style={{
													width: '70%',
													letterSpacing: '-0.04em',
													color: '#000',
													background: 'transparent',
													border: 'solid',
													borderRadius: '12px',
													borderWidth: '1px',
													borderColor: '#000',
													fontSize: '1em',
													padding: '0.5em',
												}}
												value={this.state.modificationSolution.email}
												onChange={(e) => this.handleModificationSolutionEmail(e.target.value)}
											/>
										</div>
									</div>

									<div className="row mb-3">
										<div className="col-6">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Pays')} : *</Card.Title>
											<select
												defaultValue={this.state.modificationSolution.country}
												required
												style={{ width: '70%', background: 'transparent', border: 'solid', borderRadius: '24px', borderWidth: '1px' }}
												onChange={(e) => this.handleCountryAction(e)}
											>
												{this.state.countries.map((country) => {
													return (
														<option key={country[0]} value={country[0]}>
															{country[1]}
														</option>
													);
												})}
											</select>
										</div>
										{this.state.modificationSolution.country === 'FR' && (
											<div className="col-6">
												<Card.Title style={{ fontSize: '16px' }}>{gettext('Région')} :</Card.Title>
												<select
													defaultValue={this.state.modificationSolution.region}
													style={{
														width: '70%',
														background: 'transparent',
														border: 'solid',
														borderRadius: '24px',
														borderWidth: '1px',
													}}
													onChange={(e) => this.handleRegionAction(e)}
												>
													{this.state.regions.map((region) => {
														return (
															<option key={region[0]} value={region[0]}>
																{region[1]}
															</option>
														);
													})}
												</select>
											</div>
										)}
									</div>

									<Card.Title style={{ fontSize: '16px' }}>{gettext('Description')} : *</Card.Title>
									<div className="mb-3">
										<Editor
											required
											tinymceScriptSrc="/static/dist/js/tinymce/tinymce.min.js"
											init={{
												height: 300,
												menubar: false,
												plugins: [
													'advlist',
													'autolink',
													'lists',
													'link',
													'image',
													'charmap',
													'anchor',
													'searchreplace',
													'visualblocks',
													'code',
													'fullscreen',
													'insertdatetime',
													'media',
													'table',
													'preview',
													'help',
													'wordcount',
												],
												toolbar:
													'undo redo | blocks | ' +
													'bold italic forecolor | alignleft aligncenter ' +
													'alignright alignjustify | bullist numlist outdent indent | ' +
													'removeformat | help',
												content_style: 'body { font-family:Helvetica,Arial,sans-serif; font-size:14px }',
											}}
											value={this.state.modificationSolution.description}
											onEditorChange={this.handleModificationSolutionDescription}
										/>
										<span style={{ color: 'red' }}>{this.state.errors['description']}</span>
									</div>
									<Card.Title style={{ fontSize: '16px' }}>{gettext('Description des tarifs')} :</Card.Title>
									<div className="mb-3">
										<Editor
											tinymceScriptSrc="/static/dist/js/tinymce/tinymce.min.js"
											init={{
												height: 200,
												menubar: false,
												plugins: [
													'advlist',
													'autolink',
													'lists',
													'link',
													'image',
													'charmap',
													'anchor',
													'searchreplace',
													'visualblocks',
													'code',
													'fullscreen',
													'insertdatetime',
													'media',
													'table',
													'preview',
													'help',
													'wordcount',
												],
												toolbar:
													'undo redo | blocks | ' +
													'bold italic forecolor | alignleft aligncenter ' +
													'alignright alignjustify | bullist numlist outdent indent | ' +
													'removeformat | help',
												content_style: 'body { font-family:Helvetica,Arial,sans-serif; font-size:14px }',
											}}
											value={this.state.modificationSolution.price_desc}
											onEditorChange={this.handleModificationSolutionPrice}
										/>
									</div>
									<Card.Title style={{ fontSize: '16px' }}>{gettext('Public')} :</Card.Title>
									<div className="mb-3">
										<Editor
											tinymceScriptSrc="/static/dist/js/tinymce/tinymce.min.js"
											init={{
												height: 200,
												menubar: false,
												plugins: [
													'advlist',
													'autolink',
													'lists',
													'link',
													'image',
													'charmap',
													'anchor',
													'searchreplace',
													'visualblocks',
													'code',
													'fullscreen',
													'insertdatetime',
													'media',
													'table',
													'preview',
													'help',
													'wordcount',
												],
												toolbar:
													'undo redo | blocks | ' +
													'bold italic forecolor | alignleft aligncenter ' +
													'alignright alignjustify | bullist numlist outdent indent | ' +
													'removeformat | help',
												content_style: 'body { font-family:Helvetica,Arial,sans-serif; font-size:14px }',
											}}
											value={this.state.modificationSolution.public}
											onEditorChange={this.handleModificationSolutionPublic}
										/>
									</div>
									<Card.Title style={{ fontSize: '16px' }}>{gettext('Objectif')} :</Card.Title>
									<div className="mb-3">
										<Editor
											tinymceScriptSrc="/static/dist/js/tinymce/tinymce.min.js"
											init={{
												height: 200,
												menubar: false,
												plugins: [
													'advlist',
													'autolink',
													'lists',
													'link',
													'image',
													'charmap',
													'anchor',
													'searchreplace',
													'visualblocks',
													'code',
													'fullscreen',
													'insertdatetime',
													'media',
													'table',
													'preview',
													'help',
													'wordcount',
												],
												toolbar:
													'undo redo | blocks | ' +
													'bold italic forecolor | alignleft aligncenter ' +
													'alignright alignjustify | bullist numlist outdent indent | ' +
													'removeformat | help',
												content_style: 'body { font-family:Helvetica,Arial,sans-serif; font-size:14px }',
											}}
											value={this.state.modificationSolution.objective}
											onEditorChange={this.handleModificationSolutionObjective}
										/>
									</div>
									<Card.Title style={{ fontSize: '16px' }}>{gettext('Format')} :</Card.Title>
									<div className="mb-3">
										<Editor
											tinymceScriptSrc="/static/dist/js/tinymce/tinymce.min.js"
											init={{
												height: 200,
												menubar: false,
												plugins: [
													'advlist',
													'autolink',
													'lists',
													'link',
													'image',
													'charmap',
													'anchor',
													'searchreplace',
													'visualblocks',
													'code',
													'fullscreen',
													'insertdatetime',
													'media',
													'table',
													'preview',
													'help',
													'wordcount',
												],
												toolbar:
													'undo redo | blocks | ' +
													'bold italic forecolor | alignleft aligncenter ' +
													'alignright alignjustify | bullist numlist outdent indent | ' +
													'removeformat | help',
												content_style: 'body { font-family:Helvetica,Arial,sans-serif; font-size:14px }',
											}}
											value={this.state.modificationSolution.format_session}
											onEditorChange={this.handleModificationSolutionFormat}
										/>
									</div>

									<div className="row mb-3">
										<div className="col">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Formats de la solution')} : *</Card.Title>
											{this.state.solution_formats.map((sol_format) => (
												<div key={sol_format.pk} className="mb-3">
													<Form.Check
														type={'checkbox'}
														checked={this.state.modificationSolution.solution_formats.includes(sol_format.pk) ? true : false}
														value={sol_format.pk}
														label={sol_format.label}
														onChange={(event) => this.handleModificationSolutionFormats(sol_format.pk, event)}
													/>
												</div>
											))}
											<span style={{ color: 'red' }}>{this.state.errors['solution_formats']}</span>
										</div>
										<div className="col">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Catégories')} : *</Card.Title>
											{this.state.categories.map((cat) => (
												<div key={cat.pk} className="mb-3">
													<Form.Check
														type={'checkbox'}
														checked={this.state.modificationSolution.categories.includes(cat.pk) ? true : false}
														value={cat.pk}
														label={cat.name}
														onChange={(event) => this.handleModificationSolutionCategories(cat.pk, event)}
													/>
												</div>
											))}
											<span style={{ color: 'red' }}>{this.state.errors['categories']}</span>
										</div>
										<div className="col">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Sous-catégories')} : *</Card.Title>
											{this.state.categories[0].subcategories.map((subcat) => (
												<div key={subcat.pk} className="mb-3">
													<Form.Check
														type={'checkbox'}
														checked={this.state.modificationSolution.subcategories.includes(subcat.pk) ? true : false}
														value={subcat.pk}
														label={subcat.name}
														onChange={(event) => this.handleModificationSolutionSubCategories(subcat.pk, event)}
													/>
												</div>
											))}
											<span style={{ color: 'red' }}>{this.state.errors['subcategories']}</span>
										</div>
										<div className="col">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Langues')} : *</Card.Title>
											{this.state.languages.map((language) => (
												<div key={language.pk} className="mb-3">
													<Form.Check
														type={'checkbox'}
														checked={this.state.modificationSolution.languages.includes(language.pk) ? true : false}
														value={language.pk}
														label={language.label}
														onChange={() => this.handleModificationSolutionLanguages(language.pk)}
													/>
												</div>
											))}
											<span style={{ color: 'red' }}>{this.state.errors['languages']}</span>
										</div>
										<div className="col">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Mots-clés')} :</Card.Title>
											{this.state.keywords.map((keyword) => (
												<div key={keyword.pk} className="mb-3">
													<Form.Check
														type={'checkbox'}
														checked={this.state.modificationSolution.keywords.includes(keyword.pk) ? true : false}
														value={keyword.pk}
														label={keyword.label}
														onChange={() => this.handleModificationSolutionKeywords(keyword.pk)}
													/>
												</div>
											))}
										</div>
									</div>
									<div className="text-center">
										<button
											type="submit"
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
											{gettext('Sauvegarder la solution')}
										</button>
									</div>
								</form>
							</Card>
						</div>
					</div>
				) : (
					// Solver solutions detail page and deletion modal
					<div style={{ fontFamily: 'DM Sans' }}>
						<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
							<Breadcrumb className="ps-4" separators=">" aria-label="breadcrumb">
								<Breadcrumb.Item underline="hover" color="inherit" href={'/' + this.state.entity.slug}>
									{gettext('Accueil')}
								</Breadcrumb.Item>
								<Breadcrumb.Item underline="hover" color="inherit" onClick={() => this.manageDetailedSolution()}>
									{gettext('Mes solutions')}
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
								<Card.Img
									style={{ borderRadius: '6px', height: '45vh', objectFit: 'cover' }}
									variant="top"
									src={
										this.state.detailedSolution.photo
											? this.state.detailedSolution.photo + '?text=Image cap'
											: '/static/solvers_catalog/solution.jpg?text=Image cap'
									}
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
									<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
										<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
										{gettext('Formats de la solution')}
									</Card.Text>
									<div className="d-flex flex-wrap my-2 col-8">
										{this.state.detailedSolution.solution_formats.map((solFormat) => {
											return (
												<Card.Text className="p-0 m-0" key={solFormat} style={{ fontSize: '16px' }}>
													{this.state.solution_formats.find((sf) => sf.pk === solFormat).label}&nbsp;
												</Card.Text>
											);
										})}
									</div>
									{this.state.user.is_owner && (
										<div className="d-flex justify-content-between">
											<a
												onClick={() => this.manageSolutionModification(this.state.detailedSolution)}
												className="mxt--small button border assess_secondary_btn p-0 px-4"
											>
												{gettext('Modifier la solution')}
											</a>
											<button
												type="button"
												style={{ color: 'red', fontSize: '1.3em' }}
												className="button p-1"
												data-toggle="tooltip"
												data-placement="top"
												title={gettext('Supprimer')}
												onClick={() => {
													this.setLgShow(true);
												}}
											>
												<i className="bi bi-trash3"></i>
											</button>
										</div>
									)}
								</Card.Body>
							</Card>
						</div>
						<Modal
							size="lg"
							show={this.state.lgShow}
							onHide={() => this.setLgShow(false)}
							aria-labelledby="contained-modal-title-vcenter"
							style={{ zIndex: '1050', width: '100%' }}
							className="m-0 p-0"
						>
							<Modal.Header closeButton>
								<Modal.Title id="contained-modal-title-vcenter">{gettext('Supprimer la solution')}</Modal.Title>
							</Modal.Header>
							<Modal.Body>
								<h6 id="contained-modal-title-vcenter">{gettext('Êtes-vous sûr de vouloir supprimer cette solution ?')}</h6>
							</Modal.Body>
							<Modal.Footer className="d-flex justify-content-between">
								<button
									className="button border m-2"
									style={{ background: '#fff', borderColor: '#000', color: '#000', borderRadius: '6px' }}
									onClick={() => this.setLgShow(false)}
								>
									{gettext('Annuler')}
								</button>
								<button
									className="button border m-2"
									style={{ background: '#8785BB', borderColor: '#8785BB', color: '#fff', borderRadius: '6px' }}
									onClick={() => this.deleteSolution()}
								>
									{gettext('Valider la suppression')}
								</button>
							</Modal.Footer>
						</Modal>
					</div>
				)
			) : (
				// Solver solutions home page
				<div style={{ fontFamily: 'DM Sans' }}>
					<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
						<Breadcrumb className="ps-4" separators=">" aria-label="breadcrumb">
							<Breadcrumb.Item underline="hover" color="inherit" href={'/' + this.state.entity.slug}>
								{gettext('Accueil')}
							</Breadcrumb.Item>
							<Breadcrumb.Item underline="hover" color="inherit" active>
								{gettext('Mes solutions')}
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
						<h4 className="p-2">{gettext('Mes solutions')}</h4>
						{this.state.solver.is_validated_by_admin ? (
							this.state.user.is_owner && (
								<a
									onClick={() => this.manageSolutionModification()}
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
									<i className="bi bi-plus-lg me-2"></i>
									{gettext('Proposer une nouvelle solution')}
								</a>
							)
						) : (
							<h6>
								{gettext(
									'Bienvenue, votre demande est en cours de validation, une fois votre demande validée, vous pourrez créer modifier ou supprimer vos solutions.',
								)}
							</h6>
						)}
					</div>
					<div className="py-3" style={{ paddingLeft: '5vw', paddingRight: '5vw' }}>
						<div className="d-flex justify-content-around flex-wrap">
							{this.state.solutions.map((solution) => {
								return (
									<Card key={solution.pk} className="p-0 my-3" style={{ width: '30%', borderRadius: '16px' }}>
										<Card.Img
											style={{ borderTopLeftRadius: '16px', borderTopRightRadius: '16px', height: '25vh', objectFit: 'cover' }}
											variant="top"
											src={solution.photo ? solution.photo + '?text=Image cap' : '/static/solvers_catalog/solution.jpg?text=Image cap'}
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
											<div className="d-flex justify-content-between">
												<div className="w-50 d-flex justify-content-start">
													<Card.Text className="pe-2" style={{ color: '#9094AA', fontWeight: '400', fontSize: '14px' }}>
														<i className="bi bi-eye pe-1 align-top"></i>
														{solution.users_tracked.length}
													</Card.Text>
													<Card.Text className="pe-2" style={{ color: '#9094AA', fontWeight: '400', fontSize: '14px' }}>
														<i className="bi bi-bookmark-fill pe-1 align-top"></i>
														{solution.structures.length}
													</Card.Text>
													<Card.Text style={{ color: '#9094AA', fontWeight: '400', fontSize: '14px' }}>
														<i className="bi bi-envelope pe-1 align-top"></i>
														{solution.users_tracked_contact.length}
													</Card.Text>
												</div>
												{this.state.structure.logo && (
													<Card.Img
														style={{ borderRadius: '6px', height: '3vh', width: 'auto', float: 'right' }}
														variant="top"
														src={this.state.structure.logo + '?text=Image cap'}
													/>
												)}
											</div>
										</Card.Footer>
									</Card>
								);
							})}
						</div>
					</div>
				</div>
			)
		) : (
			<Loading message={this.state.placeholder} />
		);
	}
}

export default SolverSolutions;
