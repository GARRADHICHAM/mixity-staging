import React, { Component } from 'react';
import Loading from '../../mixity/dashboard/js/includes/Loading';
import { useDefaultBestPracticeImage, useDefaultLogo } from '../../mixity/dashboard/js/includes/imageFallback';
import { Breadcrumb, Card, Form, Modal } from 'react-bootstrap';
import { Editor } from '@tinymce/tinymce-react';
import Header from '../../mixity/dashboard/js/includes/Header';

class BestPracticesManagement extends Component {
	constructor(props) {
		super(props);
		this.state = {
			url: '',
			entity: {},
			structure: {},
			bestPractices: [],
			detailedBestPractice: {},
			modificationBestPractice: {
				pk: null,
				structure: null,
				logo: '',
				referent: '',
				email: '',
				label: '',
				summary: '',
				description: '',
				website: '',
				results: '',
				setting_up: '',
				deployment_date: this.setDefaultDate(),
				difficulties: '',
				advice: '',
				testimony: '',
				type: [],
				size: [],
				country: 'FR',
				organization_type: [],
				categories: [],
				subcategories: [],
				keywords: [],
				publics: [],
				is_public: null,
			},
			publics: [],
			publics_count: 0,
			publics_limit: false,
			keywords: [],
			keywords_count: 0,
			keywords_limit: false,
			categories: [],
			categories_count: 0,
			categories_limit: false,
			subcategories: [],
			subcategories_count: 0,
			subcategories_limit: false,
			countries: [],
			size: [],
			type: [],
			organization_type: [],
			entityLoaded: false,
			bestPracticesLoaded: false,
			keywordsLoaded: false,
			categoriesLoaded: false,
			publicsLoaded: false,
			TypeLoaded: false,
			organizationTypeLoaded: false,
			sizeLoaded: false,
			errors: {},
			detailPage: false,
			modifyBestPractice: false,
			lgShow: false,
			placeholder: gettext('Chargement'),
		};
	}

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
						fetch(this.state.url + '/api/best-practice-management/')
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
										bestPractices: data,
										bestPracticesLoaded: true,
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

	uploadBestPracticeLogo(pk, logo) {
		var formData = new FormData();
		const truncatedName = logo.name.substring(0, 60) + logo.name.substring(logo.name.length - 5);
		const newLogo = new File([logo], truncatedName, { type: logo.type });
		formData.append('pk', pk);
		formData.append('logo', newLogo);
		const params = {
			credentials: 'include',
			method: 'PATCH',
			headers: { 'X-CSRFToken': csrftoken },
			body: formData,
		};
		fetch(this.state.url + '/api/best-practice-management/' + pk + '/', params)
			.then((response) => {
				if (response.status > 400) {
					return this.setState(() => {
						return { placeholder: gettext("Quelque chose s'est mal passé !") };
					});
				}
				return response.json();
			})
			.then((data) => {
				var bestPracticesData = [];
				if (this.state.bestPractices.find((bp) => bp.pk === data.pk)) {
					this.state.bestPractices.map((bp) => {
						if (bp.pk === data.pk) bestPracticesData.push(data);
						else bestPracticesData.push(bp);
					});
				} else {
					bestPracticesData = [...this.state.bestPractices, data];
				}
				this.setState({
					detailedBestPractice: data,
					bestPractices: bestPracticesData,
					detailPage: true,
					modifyBestPractice: false,
				});
			});
	}

	/* Make requests concerning a best practice */
	bestPracticeApiRequest(params, logo, pk = '') {
		var link = this.state.url + '/api/best-practice-management/';
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
					if (logo) {
						this.uploadBestPracticeLogo(data.pk, logo);
					} else {
						const datas = [...this.state.bestPractices, data];
						this.setState({
							detailedBestPractice: data,
							bestPractices: datas,
							detailPage: true,
							modifyBestPractice: false,
						});
					}
				} else {
					if (logo) {
						this.uploadBestPracticeLogo(data.pk, logo);
					} else {
						var bestPracticesData = [];
						this.state.bestPractices.map((bp) => {
							if (bp.pk === data.pk) bestPracticesData.push(data);
							else bestPracticesData.push(bp);
						});
						this.setState({
							detailedBestPractice: data,
							bestPractices: bestPracticesData,
							detailPage: true,
							modifyBestPractice: false,
						});
					}
				}
			});
	}

	/* Manage parameters to create/update best practice requests */
	saveBestPractice(e) {
		e.preventDefault();
		var best_practice = this.state.modificationBestPractice;
		let errors = {};
		let formIsValid = true;

		// The required fields in best practices are :
		// all except référent, email, deployment_date, website, keywords,logo and the text fields (except description)
		if (best_practice.description == null) {
			errors['description'] = gettext('Ne peut être vide');
			formIsValid = false;
		}
		if (best_practice.publics.length === 0) {
			errors['publics'] = gettext('Ne peut être vide');
			formIsValid = false;
		}
		if (best_practice.type.length === 0) {
			errors['type'] = gettext('Ne peut être vide');
			formIsValid = false;
		}
		if (best_practice.size.length === 0) {
			errors['size'] = gettext('Ne peut être vide');
			formIsValid = false;
		}
		if (best_practice.categories.length === 0) {
			errors['categories'] = gettext('Ne peut être vide');
			formIsValid = false;
		}
		if (best_practice.subcategories.length === 0) {
			errors['subcategories'] = gettext('Ne peut être vide');
			formIsValid = false;
		}
		if (best_practice.organization_type.length === 0) {
			errors['organization_type'] = gettext('Ne peut être vide');
			formIsValid = false;
		}
		if (best_practice.is_public == null) {
			errors['best_practice_is_public'] = gettext('Ne peut être vide');
			formIsValid = false;
		}
		if (best_practice.label == null) {
			errors['label'] = gettext('Ne peut être vide');
			formIsValid = false;
		}

		if (!formIsValid) {
			this.setState({ errors: errors });
			return;
		}

		if (best_practice.deployment_date == '') best_practice.deployment_date = null;

		var logo = null;
		if (best_practice.hasOwnProperty('logo')) {
			if (typeof best_practice.logo !== 'string' && best_practice.logo != null) logo = best_practice.logo;
			delete best_practice['logo'];
		}

		if (best_practice.pk) {
			const requestOptions = {
				credentials: 'include',
				method: 'PUT',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
				body: JSON.stringify(best_practice),
			};
			this.bestPracticeApiRequest(requestOptions, logo, best_practice.pk);
		} else {
			const requestOptions = {
				credentials: 'include',
				method: 'POST',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
				body: JSON.stringify(best_practice),
			};
			this.bestPracticeApiRequest(requestOptions, logo);
		}
	}

	deleteBestPractice() {
		if (this.state.detailedBestPractice.pk) {
			const filteredItems = this.state.bestPractices.filter((bp) => bp.pk !== this.state.detailedBestPractice.pk);
			const requestOptions = {
				credentials: 'include',
				method: 'DELETE',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
				body: JSON.stringify(this.state.detailedBestPractice.pk),
			};
			fetch(this.state.url + '/api/best-practice-management/' + this.state.detailedBestPractice.pk, requestOptions).then(() =>
				this.setState({
					bestPractices: filteredItems,
					detailPage: false,
					lgShow: false,
				}),
			);
		}
	}

	/* To display or not detailed page */
	manageBestPracticeModification(bp = null) {
		var modifyBestPracticeState = Math.abs(this.state.modifyBestPractice - 1);
		if (!bp) {
			bp = {
				pk: null,
				structure: this.state.structure.pk,
				logo: '',
				referent: '',
				email: '',
				label: '',
				summary: '',
				description: '',
				website: '',
				results: '',
				setting_up: '',
				deployment_date: this.setDefaultDate(),
				difficulties: '',
				advice: '',
				testimony: '',
				type: [],
				size: [],
				country: 'FR',
				organization_type: [],
				categories: [],
				subcategories: [],
				keywords: [],
				publics: [],
				is_public: null,
			};
		}

		this.setState({
			modifyBestPractice: modifyBestPracticeState,
			modificationBestPractice: bp,
		});
	}

	manageDetailedBestPractice(bp = {}) {
		var detailPageState = Math.abs(this.state.detailPage - 1);

		this.setState({
			detailedBestPractice: bp,
			detailPage: detailPageState,
		});
	}

	/* Front filter management */
	handleModificationBestPracticeTitle(title) {
		const bestPractice = this.state.modificationBestPractice;
		bestPractice.label = title;
		this.setState({ modificationBestPractice: bestPractice });
	}
	handleModificationBestPracticeSummary(summary) {
		const bestPractice = this.state.modificationBestPractice;
		bestPractice.summary = summary;
		this.setState({ modificationBestPractice: bestPractice });
	}
	handleModificationBestPracticeLogo(logo) {
		const bestPractice = this.state.modificationBestPractice;
		bestPractice.logo = logo;
		this.setState({ modificationBestPractice: bestPractice });
	}
	handleModificationBestPracticeReferent(referent) {
		const bestPractice = this.state.modificationBestPractice;
		bestPractice.referent = referent;
		this.setState({ modificationBestPractice: bestPractice });
	}
	handleModificationBestPracticeEmail(email) {
		const bestPractice = this.state.modificationBestPractice;
		bestPractice.email = email;
		this.setState({ modificationBestPractice: bestPractice });
	}
	handleModificationBestPracticeWebsite(website) {
		const bestPractice = this.state.modificationBestPractice;
		bestPractice.website = website;
		this.setState({ modificationBestPractice: bestPractice });
	}
	handleCountryAction(e) {
		const bestPractice = this.state.modificationBestPractice;
		bestPractice.country = e.target.value;
		this.setState({ modificationBestPractice: bestPractice });
	}
	// Text fields handlers
	handleModificationBestPracticeDeploymentDate(date) {
		const bestPractice = this.state.modificationBestPractice;
		bestPractice.deployment_date = date;
		this.setState({ modificationBestPractice: bestPractice });
	}
	handleModificationBestPracticeDescription(description, editor) {
		const bestPractice = this.state.modificationBestPractice;
		bestPractice.description = description;
		this.setState({ modificationBestPractice: bestPractice });
	}
	handleModificationBestPracticeSettingUp(settingUp, editor) {
		const bestPractice = this.state.modificationBestPractice;
		bestPractice.setting_up = settingUp;
		this.setState({ modificationBestPractice: bestPractice });
	}
	handleModificationBestPracticeDifficulties(difficulties, editor) {
		const bestPractice = this.state.modificationBestPractice;
		bestPractice.difficulties = difficulties;
		this.setState({ modificationBestPractice: bestPractice });
	}
	handleModificationBestPracticeAdvice(advice, editor) {
		const bestPractice = this.state.modificationBestPractice;
		bestPractice.advice = advice;
		this.setState({ modificationBestPractice: bestPractice });
	}
	handleModificationBestPracticeTestimony(testimony, editor) {
		const bestPractice = this.state.modificationBestPractice;
		bestPractice.testimony = testimony;
		this.setState({ modificationBestPractice: bestPractice });
	}
	handleModificationBestPracticeResults(results, editor) {
		const bestPractice = this.state.modificationBestPractice;
		bestPractice.results = results;
		this.setState({ modificationBestPractice: bestPractice });
	}
	// Multiple choices fields handlers
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
	// Two choices fields
	handleModificationBestPracticePublics(pk) {
		var bestPractice = this.state.modificationBestPractice;
		let { count, limit } = this.limitChoicesFieldsCounter(event, this.state.publics_count, this.state.publics_limit);
		this.state.publics_count = count;
		this.state.publics_limit = limit;
		if (!this.state.publics_limit) {
			if (this.state.publics_count == 2) {
				this.state.publics_limit = true;
			}
			if (bestPractice.publics.includes(pk)) bestPractice.publics = this.state.modificationBestPractice.publics.filter((pubPk) => pubPk !== pk);
			else bestPractice.publics.push(pk);
		}
		this.setState({ modificationBestPractice: bestPractice });
	}

	handleModificationBestPracticeCategories(pk) {
		var bestPractice = this.state.modificationBestPractice;
		let { count, limit } = this.limitChoicesFieldsCounter(event, this.state.categories_count, this.state.categories_limit);
		this.state.categories_count = count;
		this.state.categories_limit = limit;
		if (!this.state.categories_limit) {
			if (this.state.categories_count == 2) {
				this.state.categories_limit = true;
			}
			if (bestPractice.categories.includes(pk)) bestPractice.categories = this.state.modificationBestPractice.categories.filter((catPk) => catPk !== pk);
			else bestPractice.categories.push(pk);
		}
		this.setState({ modificationBestPractice: bestPractice });
	}

	handleModificationBestPracticeSubCategories(pk) {
		var bestPractice = this.state.modificationBestPractice;
		let { count, limit } = this.limitChoicesFieldsCounter(event, this.state.subcategories_count, this.state.subcategories_limit);
		this.state.subcategories_count = count;
		this.state.subcategories_limit = limit;
		if (!this.state.subcategories_limit) {
			if (this.state.subcategories_count == 2) {
				this.state.subcategories_limit = true;
			}
			if (bestPractice.subcategories.includes(pk))
				bestPractice.subcategories = this.state.modificationBestPractice.subcategories.filter((subcatPk) => subcatPk !== pk);
			else bestPractice.subcategories.push(pk);
		}
		this.setState({ modificationBestPractice: bestPractice });
	}

	handleModificationBestPracticeKeywords(pk) {
		var bestPractice = this.state.modificationBestPractice;
		let { count, limit } = this.limitChoicesFieldsCounter(event, this.state.keywords_count, this.state.keywords_limit);
		this.state.keywords_count = count;
		this.state.keywords_limit = limit;
		if (!this.state.keywords_limit) {
			if (this.state.keywords_count == 2) {
				this.state.keywords_limit = true;
			}
			if (bestPractice.keywords.includes(pk)) bestPractice.keywords = this.state.modificationBestPractice.keywords.filter((keyPk) => keyPk !== pk);
			else bestPractice.keywords.push(pk);
		}
		this.setState({ modificationBestPractice: bestPractice });
	}

	// One choice fields
	handleModificationBestPracticeType(pk) {
		var bestPractice = this.state.modificationBestPractice;
		if (bestPractice.type.length == 0) {
			bestPractice.type.push(pk);
		} else if (bestPractice.type.length == 1) {
			if (!bestPractice.type.includes(pk)) bestPractice.type = [];
			bestPractice.type.push(pk);
		} else {
			bestPractice.type = [];
			bestPractice.type.push(pk);
		}
		this.setState({ modificationBestPractice: bestPractice });
	}

	handleModificationBestPracticeSize(pk) {
		var bestPractice = this.state.modificationBestPractice;
		if (bestPractice.size.length == 0) {
			bestPractice.size.push(pk);
		} else if (bestPractice.size.length == 1) {
			if (!bestPractice.size.includes(pk)) bestPractice.size = [];
			bestPractice.size.push(pk);
		} else {
			bestPractice.size = [];
			bestPractice.size.push(pk);
		}
		this.setState({ modificationBestPractice: bestPractice });
	}

	handleModificationBestPracticeOrganizationType(pk) {
		var bestPractice = this.state.modificationBestPractice;
		if (bestPractice.organization_type.length == 0) {
			bestPractice.organization_type.push(pk);
		} else if (bestPractice.organization_type.length == 1) {
			if (!bestPractice.organization_type.includes(pk)) bestPractice.organization_type = [];
			bestPractice.organization_type.push(pk);
		} else {
			bestPractice.organization_type = [];
			bestPractice.organization_type.push(pk);
		}
		this.setState({ modificationBestPractice: bestPractice });
	}

	handleModificationBestPracticeStatus(value) {
		var bestPractice = this.state.modificationBestPractice;
		if (value === 'public') {
			bestPractice.is_public = true;
		} else if (value === 'private') {
			bestPractice.is_public = false;
		}
		this.setState({ modificationBestPractice: bestPractice });
	}

	// Set current date as default
	setDefaultDate() {
		// The date should be inserted in this format YYYY-MM-DD
		const today = new Date();
		const yyyy = today.getFullYear();
		let mm = today.getMonth() + 1;
		let dd = today.getDate();
		if (dd < 10) dd = '0' + dd;
		if (mm < 10) mm = '0' + mm;
		const formattedToday = yyyy + '-' + mm + '-' + dd;

		return formattedToday;
	}

	/* Displaying or not the filters modal */
	setLgShow(boolean) {
		this.setState({ lgShow: boolean });
	}

	render() {
		return this.state.entityLoaded &&
			this.state.bestPracticesLoaded &&
			this.state.categoriesLoaded &&
			this.state.keywordsLoaded &&
			this.state.bestPracticesLoaded &&
			this.state.publicsLoaded &&
			this.state.typeLoaded &&
			this.state.organizationTypeLoaded &&
			this.state.sizeLoaded ? (
			this.state.detailPage || this.state.modifyBestPractice ? (
				this.state.modifyBestPractice ? (
					// Best practices creation page and modification page
					<div style={{ fontFamily: 'DM Sans' }}>
						<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
							<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
								<Breadcrumb.Item underline="hover" color="inherit" href={'/' + this.state.entity.slug}>
									{gettext('Accueil')}
								</Breadcrumb.Item>
								<Breadcrumb.Item underline="hover" color="inherit" onClick={() => this.manageBestPracticeModification()}>
									{this.state.detailPage ? this.state.detailedBestPractice.label : gettext('Mes bonnes pratiques')}
								</Breadcrumb.Item>
								<Breadcrumb.Item underline="hover" color="inherit" active>
									{this.state.modificationBestPractice.label
										? this.state.modificationBestPractice.label
										: gettext("Création d'une nouvelle bonne pratique")}
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
								<form onSubmit={(e) => this.saveBestPractice(e)}>
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
										value={this.state.modificationBestPractice.label}
										onChange={(e) => this.handleModificationBestPracticeTitle(e.target.value)}
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
										value={this.state.modificationBestPractice.summary}
										onChange={(e) => this.handleModificationBestPracticeSummary(e.target.value)}
									/>

									<Card.Title style={{ fontSize: '16px' }}>{gettext('Logo')} :</Card.Title>
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
										onChange={(e) => this.handleModificationBestPracticeLogo(e.target.files[0])}
									/>

									<div className="row mb-3">
										<div className="col-6">
											<Card.Title style={{ fontSize: '16px' }}>
												{gettext('Personne référente')} : <i style={{ fontSize: '14px' }}>(50 {gettext('caractères maximum')})</i>
											</Card.Title>
											<input
												type="text"
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
												value={this.state.modificationBestPractice.referent}
												onChange={(e) => this.handleModificationBestPracticeReferent(e.target.value)}
											/>
										</div>
										<div className="col-6">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Adresse email')} :</Card.Title>
											<input
												type="email"
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
												value={this.state.modificationBestPractice.email}
												onChange={(e) => this.handleModificationBestPracticeEmail(e.target.value)}
											/>
										</div>
										<div className="col-6">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Website')} :</Card.Title>
											<input
												type="url"
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
												value={this.state.modificationBestPractice.website}
												onChange={(e) => this.handleModificationBestPracticeWebsite(e.target.value)}
											/>
										</div>
										<div className="col-6">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Date de déploiement')} :</Card.Title>
											<input
												type="date"
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
												value={this.state.modificationBestPractice.deployment_date}
												onChange={(e) => this.handleModificationBestPracticeDeploymentDate(e.target.value)}
											/>
										</div>
										<div className="col-6">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Pays')} : *</Card.Title>
											<select
												defaultValue={this.state.modificationBestPractice.country}
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
									</div>

									{/* Text Fields with TinyMCE */}
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
											value={this.state.modificationBestPractice.description}
											onEditorChange={(desc) => this.handleModificationBestPracticeDescription(desc)}
										/>
										<span style={{ color: 'red' }}>{this.state.errors['description']}</span>
									</div>

									<Card.Title style={{ fontSize: '16px' }}>{gettext('Mise en place')} :</Card.Title>
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
											value={this.state.modificationBestPractice.setting_up}
											onEditorChange={(setting_up) => this.handleModificationBestPracticeSettingUp(setting_up)}
										/>
									</div>

									<Card.Title style={{ fontSize: '16px' }}>{gettext('Difficultés')} :</Card.Title>
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
											value={this.state.modificationBestPractice.difficulties}
											onEditorChange={(difficulties) => this.handleModificationBestPracticeDifficulties(difficulties)}
										/>
									</div>

									<Card.Title style={{ fontSize: '16px' }}>{gettext('Conseil')} :</Card.Title>
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
											value={this.state.modificationBestPractice.advice}
											onEditorChange={(advice) => this.handleModificationBestPracticeAdvice(advice)}
										/>
									</div>

									<Card.Title style={{ fontSize: '16px' }}>{gettext('Témoignage')} :</Card.Title>
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
											value={this.state.modificationBestPractice.testimony}
											onEditorChange={(testimony) => this.handleModificationBestPracticeTestimony(testimony)}
										/>
									</div>

									<Card.Title style={{ fontSize: '16px' }}>{gettext('Résultats')} :</Card.Title>
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
											value={this.state.modificationBestPractice.results}
											onEditorChange={(results) => this.handleModificationBestPracticeResults(results)}
										/>
									</div>

									{/* Multiple choices fields */}
									{/* Two choices fields */}
									<div className="row mb-3">
										<div className="col">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Public')} : *</Card.Title>
											{this.state.publics.map((pub) => (
												<div key={pub.pk} className="mb-3">
													<Form.Check
														type={'checkbox'}
														checked={this.state.modificationBestPractice.publics.includes(pub.pk) ? true : false}
														value={pub.pk}
														label={pub.label}
														onChange={(event) => this.handleModificationBestPracticePublics(pub.pk, event)}
													/>
												</div>
											))}
											<span style={{ color: 'red' }}>{this.state.errors['publics']}</span>
										</div>
										<div className="col">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Catégories')} : *</Card.Title>
											{this.state.categories.map((cat) => (
												<div key={cat.pk} className="mb-3">
													<Form.Check
														type={'checkbox'}
														checked={this.state.modificationBestPractice.categories.includes(cat.pk) ? true : false}
														value={cat.pk}
														label={cat.name}
														onChange={(event) => this.handleModificationBestPracticeCategories(cat.pk, event)}
													/>
												</div>
											))}
											<span style={{ color: 'red' }}>{this.state.errors['categories']}</span>
										</div>
										<div className="col">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Dimensions')} : *</Card.Title>
											{this.state.categories[0].subcategories.map((subcat) => (
												<div key={subcat.pk} className="mb-3">
													<Form.Check
														type={'checkbox'}
														checked={this.state.modificationBestPractice.subcategories.includes(subcat.pk) ? true : false}
														value={subcat.pk}
														label={subcat.name}
														onChange={(event) => this.handleModificationBestPracticeSubCategories(subcat.pk, event)}
													/>
												</div>
											))}
											<span style={{ color: 'red' }}>{this.state.errors['subcategories']}</span>
										</div>
										<div className="col">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Mots-clés')} : *</Card.Title>
											{this.state.keywords.map((keyword) => (
												<div key={keyword.pk} className="mb-3">
													<Form.Check
														type={'checkbox'}
														checked={this.state.modificationBestPractice.keywords.includes(keyword.pk) ? true : false}
														value={keyword.pk}
														label={keyword.label}
														onChange={(event) => this.handleModificationBestPracticeKeywords(keyword.pk, event)}
													/>
												</div>
											))}
											<span style={{ color: 'red' }}>{this.state.errors['subcategories']}</span>
										</div>
									</div>
									{/* One choice field */}
									<div className="row mb-3">
										<div className="col">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Type')} : *</Card.Title>
											{this.state.type.map((t) => (
												<div key={t.pk} className="mb-3">
													<Form.Check
														type={'radio'}
														checked={this.state.modificationBestPractice.type.includes(t.pk) ? true : false}
														name="bestPracticeType"
														value={t.pk}
														label={t.label}
														onClick={(event) => this.handleModificationBestPracticeType(t.pk)}
													/>
												</div>
											))}
											<span style={{ color: 'red' }}>{this.state.errors['type']}</span>
										</div>
										<div className="col">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Taille')} : *</Card.Title>
											{this.state.size.map((s) => (
												<div key={s.pk} className="mb-3">
													<Form.Check
														type={'radio'}
														checked={this.state.modificationBestPractice.size.includes(s.pk) ? true : false}
														name="bestPracticeSize"
														value={s.pk}
														label={s.label}
														onClick={(event) => this.handleModificationBestPracticeSize(s.pk)}
													/>
												</div>
											))}
											<span style={{ color: 'red' }}>{this.state.errors['size']}</span>
										</div>
										<div className="col">
											<Card.Title style={{ fontSize: '16px' }}>{gettext("Type d'organisation")} : *</Card.Title>
											{this.state.organization_type.map((ot) => (
												<div key={ot.pk} className="mb-3">
													<Form.Check
														type={'radio'}
														checked={this.state.modificationBestPractice.organization_type.includes(ot.pk) ? true : false}
														name="bestPracticeOrganizationType"
														value={ot.pk}
														label={ot.label}
														onClick={(event) => this.handleModificationBestPracticeOrganizationType(ot.pk)}
													/>
												</div>
											))}
											<span style={{ color: 'red' }}>{this.state.errors['organization_type']}</span>
										</div>
										<div className="col">
											<Card.Title style={{ fontSize: '16px' }}>{gettext('Statut')} : *</Card.Title>
											<div key="bp-public" className="mb-3">
												<Form.Check
													type={'radio'}
													checked={this.state.modificationBestPractice.is_public == true ? true : false}
													name="bestPracticeStatus"
													value="public"
													label="publique"
													onClick={(event) => this.handleModificationBestPracticeStatus('public')}
												/>
											</div>
											<div key="bp-private" className="mb-3">
												<Form.Check
													type={'radio'}
													checked={this.state.modificationBestPractice.is_public == false ? true : false}
													name="bestPracticeStatus"
													value="private"
													label="privée"
													onClick={(event) => this.handleModificationBestPracticeStatus('private')}
												/>
											</div>
											<span style={{ color: 'red' }}>{this.state.errors['best_practice_is_public']}</span>
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
											{gettext('Sauvegarder la bonne pratique')}
										</button>
									</div>
								</form>
							</Card>
						</div>
					</div>
				) : (
					// Best practices detail page and deletion modal
					<div style={{ fontFamily: 'DM Sans' }}>
						<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
							<Breadcrumb className="ps-4" separators=">" aria-label="breadcrumb">
								<Breadcrumb.Item underline="hover" color="inherit" href={'/' + this.state.entity.slug}>
									{gettext('Accueil')}
								</Breadcrumb.Item>
								<Breadcrumb.Item underline="hover" color="inherit" onClick={() => this.manageDetailedBestPractice()}>
									{gettext('Mes bonnes pratiques')}
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
													key={this.state.detailedBestPractice.pk + '-type-' + category}
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
													key={this.state.detailedBestPractice.pk + '-type-' + subcat}
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
										{gettext('Date de déploiement ')}
									</Card.Text>
									<div className="mb-3 ps-4" dangerouslySetInnerHTML={{ __html: this.state.detailedBestPractice.deployment_date }}></div>
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
												onError={useDefaultLogo}
											/>
										)}
									</div>
									<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
										<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
										{gettext('Statut')}
									</Card.Text>
									<Card.Text className="my-2 col-8" style={{ fontSize: '16px' }}>
										{this.state.detailedBestPractice.is_public ? gettext('Publique') : gettext('Privée')}
									</Card.Text>
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
										<img alt="" src="/static/img/icon_language.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
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
										{this.state.detailedBestPractice.type.map((t) => {
											return (
												<Card.Text className="p-0 m-0" key={t} style={{ fontSize: '16px' }}>
													{this.state.type.find((t_) => t_.pk === t).label}&nbsp;
												</Card.Text>
											);
										})}
									</div>
									<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
										<img alt="" src="/static/img/icon_summary.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
										{gettext("Type d'organisation")}
									</Card.Text>
									<div className="d-flex flex-wrap my-2 col-8">
										{this.state.detailedBestPractice.organization_type.map((ot) => {
											return (
												<Card.Text className="p-0 m-0" key={ot} style={{ fontSize: '16px' }}>
													{this.state.organization_type.find((ot_) => ot_.pk === ot).label}&nbsp;
												</Card.Text>
											);
										})}
									</div>
									<Card.Text className="my-2 col-4" style={{ fontSize: '14px', color: '#9094AA' }}>
										<img alt="" src="/static/img/icon_language.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
										{gettext('Taille')}
									</Card.Text>
									<div className="d-flex flex-wrap my-2 col-8">
										{this.state.detailedBestPractice.size.map((s) => {
											return (
												<Card.Text className="p-0 m-0" key={s} style={{ fontSize: '16px' }}>
													{this.state.size.find((s_) => s_.pk === s).label}&nbsp;
												</Card.Text>
											);
										})}
									</div>

									<div className="d-flex justify-content-between">
										<a
											onClick={() => this.manageBestPracticeModification(this.state.detailedBestPractice)}
											className="mxt--small button border assess_secondary_btn p-0 px-4"
										>
											{gettext('Modifier la bonne pratique')}
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
								<Modal.Title id="contained-modal-title-vcenter">{gettext('Supprimer la bonne pratique')}</Modal.Title>
							</Modal.Header>
							<Modal.Body>
								<h6 id="contained-modal-title-vcenter">{gettext('Êtes-vous sûr de vouloir supprimer cette bonne pratique ?')}</h6>
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
									onClick={() => this.deleteBestPractice()}
								>
									{gettext('Valider la suppression')}
								</button>
							</Modal.Footer>
						</Modal>
					</div>
				)
			) : (
				// Best practices home page
				<div style={{ fontFamily: 'DM Sans' }}>
					<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
						<Breadcrumb className="ps-4" separators=">" aria-label="breadcrumb">
							<Breadcrumb.Item underline="hover" color="inherit" href={'/' + this.state.entity.slug}>
								{gettext('Accueil')}
							</Breadcrumb.Item>
							<Breadcrumb.Item underline="hover" color="inherit" active>
								{gettext('Mes bonnes pratiques')}
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
						<h4 className="p-2">{gettext('Mes bonnes pratiques')}</h4>
						<a
							onClick={() => this.manageBestPracticeModification()}
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
							{gettext('Proposer une nouvelle bonne pratique')}
						</a>
					</div>
					<div className="py-3" style={{ paddingLeft: '5vw', paddingRight: '5vw' }}>
						<div className="d-flex justify-content-around flex-wrap">
							{this.state.bestPractices.map((bp) => {
								return (
									<Card key={bp.pk} className="p-0 my-3" style={{ width: '30%', borderRadius: '16px' }}>
										<Card.Img
											style={{ borderTopLeftRadius: '16px', borderTopRightRadius: '16px', height: '25vh', objectFit: 'cover' }}
											variant="top"
											src={bp.logo ? bp.logo + '?text=Image cap' : '/static/best_practices_catalog/best_practice.jpg?text=Image cap'}
											onError={useDefaultBestPracticeImage}
										/>
										<Card.Body className="px-4 pt-2 pb-0" style={{ cursor: 'pointer' }} onClick={() => this.manageDetailedBestPractice(bp)}>
											<div className="d-flex flex-wrap mb-2">
												{bp.categories.map((category) => {
													return (
														<Card.Text
															key={bp.pk + '-type-' + category}
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

export default BestPracticesManagement;
