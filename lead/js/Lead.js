import React, { Component } from 'react';
import { Breadcrumb, Modal, Form } from 'react-bootstrap';
import Header from '../../mixity/dashboard/js/includes/Header';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';

class Lead extends Component {
	constructor(props) {
		super(props);
		this.state = {
			objectives: [],
			categories: [],
			genericKpis: [],
			referentFilter: [],
			entity: {},
			entityFilter: [],
			entities: [],
			all_possible_referent: [],
			structure: {},
			user: {},
			isDisabled: false,
			disableMembersInputs: false,
			disableReadersInputs: false,
			url: '',
			actionToDelete: null,
			activeCategory: 1,
			newObjective: {
				pk: null,
				label: '',
				category: 1,
				subcategory: 130,
				structure: null,
				entity: null,
				actions: [],
				progress_bar: null,
				total_budget: null,
				height: 'auto',
			},
			actionStatusChoices: [
				{ value: 'reflection', name: gettext('Action en réflexion') },
				{ value: 'planned', name: gettext('Action planifiée') },
				{ value: 'in_progress', name: gettext('Action en cours') },
				{ value: 'operation', name: gettext('Action pilote') },
				{ value: 'deployed', name: gettext('Action déployée') },
			],
			unitChoices: [
				{ value: 'value', name: gettext('Valeur') },
				{ value: 'percent', name: gettext('Pourcentage') },
			],
			objectivesLoaded: false,
			categoriesLoaded: false,
			genericKpisLoaded: false,
			entityLoaded: false,
			entitiesLoaded: false,
			manageObjective: false,
			showReferentModal: false,
			showEntityModal: false,
			showObjectiveDeleteModal: false,
			showActionDeleteModal: false,
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
							url: 'https://' + data,
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
										fetch(this.state.url + '/api/entities/')
											.then((response) => {
												if (response.status > 400) {
													return this.setState(() => {
														return { placeholder: gettext("Quelque chose s'est mal passé !") };
													});
												}
												return response.json();
											})
											.then((data) => {
												var filterList = [];
												data.map((entity) => {
													filterList.push(entity.pk);
												});
												var refList = [];
												var refNameList = [];
												this.state.structure.members.map((member) => {
													refList.push(member.pk);
													member.membership = gettext('Structure Admin');
													refNameList.push(member);
												});
												data.map((entity) => {
													entity.members.map((member) => {
														if (!refList.includes(member.pk)) {
															refList.push(member.pk);
															member.membership = entity.name;
															refNameList.push(member);
														}
													});
												});
												this.setState(() => {
													return {
														entities: data,
														entityFilter: filterList,
														entitiesLoaded: true,
														referentFilter: refList,
														all_possible_referent: refNameList,
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
								this.setState(() => {
									return {
										categories: data.filter((cat) => cat.slug !== 'your-suggestions'),
										categoriesLoaded: true,
									};
								});
							});

						fetch(this.state.url + '/api/objective/')
							.then((response) => {
								if (response.status > 400) {
									return this.setState(() => {
										return { placeholder: gettext("Quelque chose s'est mal passé !") };
									});
								}
								return response.json();
							})
							.then((data) => {
								data.map((objective) => {
									objective.actions.map((action) => {
										action.showKpi = false;
									});
								});
								this.setState(() => {
									return {
										objectives: data,
										objectivesLoaded: true,
									};
								});
							});

						fetch(this.state.url + '/api/generickpi/')
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
										genericKpis: data,
										genericKpisLoaded: true,
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
										disableMembersInputs: data.is_owner !== true,
										disableReadersInputs: data.is_reader == true,
										user: data,
									};
								});
							});
					},
				);
			});
	}

	/* Make requests concerning an objective */
	objectiveApiRequest(params, pk = '') {
		var link = this.state.url + '/api/objective/';
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
					const datas = [...this.state.objectives, data];
					this.setState({
						objectives: datas,
						newObjective: data,
					});
				} else {
					const objectives = this.state.objectives;
					objectives.map((obj) => {
						if (obj.pk === pk) {
							obj = data;
						}
					});
					this.setState({ objectives: objectives });
				}
			});
	}

	/* Make request to create a list of objectives thanks to aims on evaluations */
	aimsToObjectiveApiRequest() {
		fetch(this.state.url + '/api/aims_to_objectives/')
			.then((response) => {
				if (response.status > 400) {
					return this.setState(() => {
						return { placeholder: gettext("Quelque chose s'est mal passé !") };
					});
				}
				return response.json();
			})
			.then((data) => {
				data.map((objective) => {
					objective.actions.map((action) => {
						action.showKpi = false;
					});
				});
				this.setState(() => {
					return {
						objectives: data,
						objectivesLoaded: true,
					};
				});
			});
	}

	/* Make requests concerning an action */
	actionApiRequest(params, pk = '') {
		var link = this.state.url + '/api/action/';
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
					const objective = this.state.newObjective;
					var total_budget = 0;
					objective.actions = objective.actions.filter((action) => action.pk > 0);
					objective.actions.push(data);
					objective.actions.map((action) => {
						total_budget += parseInt(action.budget);
					});
					objective.total_budget = total_budget.toString();
					const actions_count = objective.actions.filter((action) => action.status != 'reflection').length;
					if (actions_count) {
						objective.progress_bar = parseInt((objective.actions.filter((action) => action.status === 'deployed').length / actions_count) * 100);
					} else objective.progress_bar = 0;
					this.setState({
						newObjective: objective,
					});
				} else {
					const objective = this.state.newObjective;
					var total_budget = 0;
					objective.actions.map((action) => {
						if (action.pk === data.pk) action = data;
					});
					objective.actions.map((action) => {
						total_budget += parseInt(action.budget);
					});
					const actions_count = objective.actions.filter((action) => action.status != 'reflection').length;
					if (actions_count) {
						objective.progress_bar = parseInt((objective.actions.filter((action) => action.status === 'deployed').length / actions_count) * 100);
					} else objective.progress_bar = 0;
					objective.total_budget = total_budget.toString();
					this.setState({
						newObjective: objective,
					});
				}
			});
	}

	/* Make requests concerning a kpi */
	kpiApiRequest(params, actionPk, pk = '') {
		var link = this.state.url + '/api/kpi/';
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
					const objective = this.state.newObjective;
					objective.actions.map((action) => {
						if (action.pk === actionPk) {
							action.kpis = action.kpis.filter((kpi) => kpi.pk > 0);
							action.kpis.push(data);
						}
					});
					this.setState({
						newObjective: objective,
					});
				} else {
					const objective = this.state.newObjective;
					objective.actions
						.find((action) => action.pk === actionPk)
						.kpis.map((kpi) => {
							if (kpi.pk === data.pk) kpi = data;
						});
					this.setState({
						newObjective: objective,
					});
				}
			});
	}

	/* Manage parameters to create/update objective requests */
	saveObjective(e, pk) {
		e.preventDefault();
		if (!this.state.user.is_owner) return;

		if (!this.state.newObjective.label) return;
		this.state.newObjective.last_modification_user = this.state.user.user_id;

		if (this.state.newObjective.pk) {
			const requestOptions = {
				credentials: 'include',
				method: 'PUT',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
				body: JSON.stringify(this.state.newObjective),
			};
			this.objectiveApiRequest(requestOptions, pk);
		} else {
			this.state.newObjective.creation_user = this.state.user.user_id;
			const requestOptions = {
				credentials: 'include',
				method: 'POST',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
				body: JSON.stringify(this.state.newObjective),
			};
			this.objectiveApiRequest(requestOptions);
		}
	}

	deleteObjective() {
		if (!this.state.user.is_owner) return;

		if (this.state.newObjective.pk) {
			const filteredItems = this.state.objectives.filter((objective) => objective.pk !== this.state.newObjective.pk);
			const requestOptions = {
				credentials: 'include',
				method: 'DELETE',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
				body: JSON.stringify(this.state.newObjective.pk),
			};
			fetch(this.state.url + '/api/objective/' + this.state.newObjective.pk, requestOptions).then(() =>
				this.setState({
					objectives: filteredItems,
				}),
			);
		}
		this.objectiveManagement();
	}

	/* Manage parameters to create/update actions requests */
	saveAction(e, pk) {
		e.preventDefault();
		if (this.state.user.is_reader) return;

		const action = this.state.newObjective.actions.find((action) => action.pk === pk);

		if (!this.state.newObjective.pk || !action.label || !action.status) return;

		if (!action.budget || action.budget < 0) action.budget = 0;
		action.last_modification_user = this.state.user.user_id;
		if (pk > 0) {
			const requestOptions = {
				credentials: 'include',
				method: 'PUT',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
				body: JSON.stringify(action),
			};
			this.actionApiRequest(requestOptions, pk);
		} else {
			const requestOptions = {
				credentials: 'include',
				method: 'POST',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
				body: JSON.stringify(action),
			};
			this.actionApiRequest(requestOptions);
		}
	}

	deleteAction(pk) {
		if (this.state.user.is_reader) return;

		const objective = this.state.newObjective;
		objective.actions = objective.actions.filter((action) => action.pk !== pk);

		if (pk > 0) {
			const requestOptions = {
				credentials: 'include',
				method: 'DELETE',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
				body: JSON.stringify(pk),
			};
			fetch(this.state.url + '/api/action/' + pk, requestOptions).then(() =>
				this.setState({
					newObjective: objective,
				}),
			);
		} else {
			this.setState({
				newObjective: objective,
			});
		}
	}

	/* Manage parameters to create/update kpis requests */
	saveKpi(e, actionPk, pk) {
		e.preventDefault();
		if (this.state.user.is_reader) return;
		const kpi = this.state.newObjective.actions.find((action) => action.pk === actionPk).kpis.find((kpi) => kpi.pk === pk);

		if (actionPk < 0 || (!kpi.generic_kpi && !kpi.label)) return;

		if (!kpi.value || kpi.value < 0) kpi.value = 0;
		if (!kpi.goal || kpi.goal < 0) kpi.goal = 0;
		kpi.last_modification_user = this.state.user.user_id;

		if (pk > 0) {
			const requestOptions = {
				credentials: 'include',
				method: 'PUT',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
				body: JSON.stringify(kpi),
			};
			this.kpiApiRequest(requestOptions, actionPk, pk);
		} else {
			const requestOptions = {
				credentials: 'include',
				method: 'POST',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
				body: JSON.stringify(kpi),
			};
			this.kpiApiRequest(requestOptions, actionPk);
		}
	}

	deleteKpi(actionPk, pk) {
		if (this.state.user.is_reader) return;

		const objective = this.state.newObjective;
		objective.actions.map((action) => {
			if (action.pk === actionPk) action.kpis = action.kpis.filter((kpi) => kpi.pk !== pk);
		});

		if (pk > 0) {
			const requestOptions = {
				credentials: 'include',
				method: 'DELETE',
				headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
				body: JSON.stringify(pk),
			};
			fetch(this.state.url + '/api/kpi/' + pk, requestOptions).then(() =>
				this.setState({
					newObjective: objective,
				}),
			);
		} else {
			this.setState({
				newObjective: objective,
			});
		}
	}

	handleTextAreaSize(elem) {
		elem.target.style.height = '1px';
		elem.target.style.height = `${elem.target.scrollHeight}px`;
	}

	/* Objective front managment functions */
	handleLabelNewObjective(label, pk, elem) {
		const objective = this.state.newObjective;
		objective.label = label;
		objective.height = elem.target.style.height;
		this.setState({ newObjective: objective });
	}

	handleCategoryNewObjective(e) {
		const newObjective = this.state.newObjective;
		newObjective.category = parseInt(e.target.value);
		newObjective.subcategory = this.state.categories.find((cat) => cat.pk === parseInt(e.target.value)).subcategories[0].pk;
		this.setState({
			newObjective: newObjective,
		});
		this.saveObjective(e, newObjective.pk);
	}

	handleSubcategoryNewObjective(e) {
		const newObjective = this.state.newObjective;
		newObjective.subcategory = parseInt(e.target.value);
		this.setState({ newObjective: newObjective });
		this.saveObjective(e, newObjective.pk);
	}

	/* Action front managment functions */
	addNewAction() {
		const objective = this.state.newObjective;
		objective.actions.push({
			pk: -Date.now(),
			label: '',
			status: 'reflection',
			action_date: null,
			budget: null,
			referent: null,
			objective: this.state.newObjective.pk,
			comment: '',
			kpis: [],
			creation_entity: this.state.entity.pk,
			creation_user: this.state.user.user_id,
			last_modification_user: this.state.user.user_id,
		});
		this.setState({ newObjective: objective });
	}

	handleLabelAction(label, pk, elem) {
		const objective = this.state.newObjective;
		objective.actions.map((action) => {
			if (action.pk === pk) {
				action.label = label;
				action.height = elem.target.style.height;
			}
		});
		this.setState({ newObjective: objective });
	}

	handleReferentAction(e, pk) {
		const objective = this.state.newObjective;
		objective.actions.map((action) => {
			if (action.pk === pk) {
				console.log(e.target.value);
				if (e.target.value == null || e.target.value == -1 || e.target.value == '-')
					action.referent = null
				else
					action.referent = parseInt(e.target.value);
			}	
		});
		this.setState({ newObjective: objective });
		this.saveAction(e, pk);
	}

	handleDateAction(date, pk) {
		const objective = this.state.newObjective;
		objective.actions.map((action) => {
			if (action.pk === pk) action.action_date = date;
		});
		this.setState({ newObjective: objective });
	}

	handleBudgetAction(budget, pk) {
		budget = budget.replace(/^0+/, '');
		const objective = this.state.newObjective;
		objective.actions.map((action) => {
			if (action.pk === pk) action.budget = budget;
		});
		this.setState({ newObjective: objective });
	}

	handleStatusAction(e, pk) {
		const objective = this.state.newObjective;
		objective.actions.map((action) => {
			if (action.pk === pk) action.status = e.target.value;
		});
		this.setState({ newObjective: objective });
		this.saveAction(e, pk);
	}

	showKpiList(pk) {
		const objective = this.state.newObjective;
		objective.actions.map((action) => {
			if (action.pk === pk) action.showKpi = Math.abs(action.showKpi - 1);
		});
		this.setState({ newObjective: objective });
	}

	/* Kpi front managment functions */
	addNewKpi(actionPk) {
		const objective = this.state.newObjective;
		objective.actions
			.find((action) => action.pk === actionPk)
			.kpis.push({
				pk: -Date.now(),
				label: '',
				generic_kpi: null,
				unit: 'value',
				value: 0,
				goal: 0,
				subcategory: this.state.newObjective.subcategory,
				action: actionPk,
				creation_entity: this.state.entity.pk,
				creation_user: this.state.user.user_id,
				last_modification_user: this.state.user.user_id,
			});
		objective.actions.find((action) => action.pk === actionPk).showKpi = true;
		this.setState({ newObjective: objective });
	}

	handleLabelKpi(label, actionPk, pk) {
		const objective = this.state.newObjective;
		objective.actions
			.find((action) => action.pk === actionPk)
			.kpis.map((kpi) => {
				if (kpi.pk === pk) kpi.label = label;
			});
		this.setState({ newObjective: objective });
	}

	handleValueKpi(value, actionPk, pk) {
		value = value.replace(/^0+/, '');
		const objective = this.state.newObjective;
		objective.actions
			.find((action) => action.pk === actionPk)
			.kpis.map((kpi) => {
				if (kpi.pk === pk) kpi.value = value;
			});
		this.setState({ newObjective: objective });
	}

	handleGoalKpi(goal, actionPk, pk) {
		goal = goal.replace(/^0+/, '');

		const objective = this.state.newObjective;
		objective.actions
			.find((action) => action.pk === actionPk)
			.kpis.map((kpi) => {
				if (kpi.pk === pk) kpi.goal = goal;
			});
		this.setState({ newObjective: objective });
	}

	handleGenericKpiKpi(e, actionPk, pk) {
		const objective = this.state.newObjective;
		objective.actions
			.find((action) => action.pk === actionPk)
			.kpis.map((kpi) => {
				if (kpi.pk === pk) kpi.generic_kpi = parseInt(e.target.value);
			});
		this.setState({ newObjective: objective });
		this.saveKpi(e, actionPk, pk);
	}

	handleUnitKpi(e, actionPk, pk) {
		const objective = this.state.newObjective;
		objective.actions
			.find((action) => action.pk === actionPk)
			.kpis.map((kpi) => {
				if (kpi.pk === pk) kpi.unit = e.target.value;
			});
		this.setState({ newObjective: objective });
		this.saveKpi(e, actionPk, pk);
	}

	/* Show active category tab */
	activateCategory(pk) {
		this.setState({ activeCategory: pk });
	}

	/* Swap the state of the page (objectives list <-> specific objective datas) */
	objectiveManagement(categoryPk = 1) {
		var newManageState = Math.abs(this.state.manageObjective - 1);
		this.setState(
			{
				manageObjective: newManageState,
				newObjective: {
					pk: null,
					label: '',
					category: categoryPk,
					subcategory: this.state.categories.find((cat) => cat.pk === categoryPk).subcategories[0].pk,
					structure: this.state.structure.pk,
					entity: this.state.entity.pk,
					actions: [],
					progress_bar: null,
					total_budget: null,
					height: 'auto'
				},
			},
			() => {
				if (newManageState)
					this.setState({
						isDisabled: this.canModify(this.state.newObjective.entity),
					});
			},
		);
	}

	canModify(entity) {
		if (!this.state.disableMembersInputs && !this.state.disableReadersInputs && this.state.entities[0].pk === entity && this.state.entity.pk === entity)
			return false;
		var parent_entity_pk = this.state.entities.find((ent) => ent.pk === entity).parent_entity;
		var is_parent = true;
		while (parent_entity_pk) {
			if (parent_entity_pk === this.state.entity.pk || this.state.entity.pk === entity) {
				is_parent = false;
				break;
			}
			parent_entity_pk = this.state.entities.find((ent) => ent.pk === parent_entity_pk).parent_entity;
		}
		if (this.state.disableMembersInputs || is_parent) return true;
		return false;
	}

	loadObjective(objective) {
		this.objectiveManagement();
		this.setState({ newObjective: objective });
	}

	convertToRGB(hexa) {
		hexa = hexa.slice(1);
		if (hexa.length != 6) {
			return 'rgba(255, 255, 255, 0.1)';
		}

		var aRgbHex = hexa.match(/.{1,2}/g);
		var aRgb = `rgba(${parseInt(aRgbHex[0], 16)},${parseInt(aRgbHex[1], 16)},${parseInt(aRgbHex[2], 16)},0.5)`;
		return aRgb;
	}

	languageSelectorFunction(languageCode) {
		document.cookie = 'language_code=' + languageCode + '; path=/;';
		window.location.reload(true);
	}

	/* Displaying or not the filters modal */
	setshowReferentModal(boolean) {
		this.setState({ showReferentModal: boolean });
	}

	/* Displaying or not the filters modal */
	setshowEntityModal(boolean) {
		this.setState({ showEntityModal: boolean });
	}

	/* Displaying or not the filters modal */
	setshowObjectiveDeleteModal(boolean) {
		this.setState({ showObjectiveDeleteModal: boolean });
	}

	/* Displaying or not the filters modal */
	setshowActionDeleteModal(boolean) {
		this.setState({ showActionDeleteModal: boolean });
	}

	/* Front filter management */
	handleFilterByReferent(pk) {
		var filterList = this.state.referentFilter;
		if (filterList.includes(pk)) filterList = this.state.referentFilter.filter((kpi) => kpi !== pk);
		else filterList.push(pk);
		this.setState({ referentFilter: filterList });
	}

	/* Front filter management */
	handleFilterByEntity(pk) {
		var filterList = this.state.entityFilter;
		if (filterList.includes(pk)) filterList = this.state.entityFilter.filter((kpi) => kpi !== pk);
		else filterList.push(pk);
		this.setState({ entityFilter: filterList });
	}

	/* Front filter management */
	FillFilterByReferent() {
		var filterList = [];
		this.state.structure.members.map((member) => {
			filterList.push(member.pk);
		});
		this.state.entities.map((entity) => {
			entity.members.map((member) => {
				if (!filterList.includes(member.pk)) filterList.push(member.pk);
			});
		});
		this.setState({ referentFilter: filterList });
	}

	/* Front filter management */
	FillFilterByEntity() {
		var filterList = this.state.entityFilter;
		this.state.entities.map((entity) => {
			if (!filterList.includes(entity.pk)) filterList.push(entity.pk);
		});
		this.setState({ entityFilter: filterList });
	}

	render() {
		return this.state.objectivesLoaded &&
			this.state.categoriesLoaded &&
			this.state.genericKpisLoaded &&
			this.state.entityLoaded &&
			this.state.entitiesLoaded ? (
			this.state.manageObjective ? (
				<div style={{ fontFamily: 'DM Sans' }}>
					<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#ffffff' }}>
						<Breadcrumb className="ps-2 w-75" separators=">" aria-label="breadcrumb">
							<Breadcrumb.Item underline="hover" color="inherit" href={'/' + this.state.entity.slug}>
								{gettext('Accueil')}
							</Breadcrumb.Item>
							<Breadcrumb.Item active>{gettext('Piloter')}</Breadcrumb.Item>
							<Breadcrumb.Item underline="hover" color="inherit" onClick={() => this.objectiveManagement()}>
								{gettext("Plan d'action")}
							</Breadcrumb.Item>
							{this.state.newObjective.label ? (
								<Breadcrumb.Item className="text-break" active>{this.state.newObjective.label}</Breadcrumb.Item>
							) : (
								<Breadcrumb.Item active>{gettext('Nouvel objectif')}</Breadcrumb.Item>
							)}
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

					<button className="button p-4 pb-0 pt-3" style={{ backgroundColor: 'transparent' }} onClick={() => this.objectiveManagement()}>
						<i className="bi bi-arrow-left"></i>
						{gettext('Retour')}
					</button>
					<div className="p-4 m-4" style={{ backgroundColor: '#423C6B', borderRadius: '16px' }}>
						<div className="d-flex justify-content-between mb-3">
							<div className="w-100">
								<h6 style={{ color: '#A5A0D2' }}>{gettext('Objectif')}</h6>
								<textarea
									type="text"
									disabled={this.state.isDisabled}
									maxLength="512"
									style={{
										letterSpacing: '-0.04em',
										color: '#ffffff',
										background: 'transparent',
										border: 'none',
										fontSize: '1.5em',
										padding: '0em',
										height: this.state.newObjective.height,
										resize: 'none',
									}}
									placeholder="Untitled"
									id={this.state.newObjective.pk}
									value={this.state.newObjective.label}
									onBlur={(e) => {
										this.saveObjective(e, this.state.newObjective.pk);
									}}
									onInput={(e) => {
										this.handleTextAreaSize(e);
										this.handleLabelNewObjective(e.target.value, this.state.newObjective.pk, e);
									}}
								>
								</textarea>
							</div>
							{this.state.user.is_owner && !this.state.isDisabled && (
								<button
									className="button rounded-circle p-2 m-2"
									style={{ backgroundColor: 'rgba(255, 255, 255, 0.1)', width: '3%', height: '3%' }}
									onClick={() => this.setshowObjectiveDeleteModal(true)}
								>
									<img alt="" src="/static/img/icon_trash.png" />
								</button>
							)}
						</div>
						<div className="d-flex justify-content-start justify-content-align">
							<label style={{ color: '#A5A0D2' }}>
								{gettext('Catégorie')}
								<select
									disabled={this.state.isDisabled}
									defaultValue={this.state.newObjective.category}
									onChange={(e) => this.handleCategoryNewObjective(e)}
									className="ms-2 me-5 text-center"
									style={{
										background: this.convertToRGB(this.state.categories.find((cat) => cat.pk === this.state.newObjective.category).color),
										color: '#ffffff',
										border: 'none',
										borderRadius: '24px',
										width: 'fit-content',
									}}
								>
									{this.state.categories.map((cat) => {
										return (
											<option style={{ color: '#000000' }} key={cat.pk} value={cat.pk}>
												{gettext(cat.name)}
											</option>
										);
									})}
								</select>
							</label>
							<label style={{ color: '#A5A0D2' }}>
								{gettext('Sous-catégorie')}
								<select
									disabled={this.state.isDisabled}
									defaultValue={this.state.newObjective.subcategory}
									onChange={(e) => this.handleSubcategoryNewObjective(e)}
									className="ms-2 text-center"
									style={{
										background: 'rgba(255, 255, 255, 0.1)',
										color: '#ffffff',
										border: 'none',
										borderRadius: '24px',
										width: 'fit-content',
									}}
								>
									{this.state.categories
										.find((cat) => cat.pk === this.state.newObjective.category)
										.subcategories.map((subcat) => {
											return (
												<option style={{ color: '#000000' }} key={subcat.pk} value={subcat.pk}>
													{subcat.name}
												</option>
											);
										})}
								</select>
							</label>
						</div>
					</div>

					<div className="p-4 m-4 border" style={{ background: '#ffffff', borderColor: '#DEDFEA', borderRadius: '16px' }}>
						<div className="d-flex justify-content-between pb-3 pt-2 align-items-center">
							<div>
								<div className="d-flex justify-content-start align-items-center">
									<h4 className="m-0" style={{ fontWeight: '500' }}>
										{gettext('Actions')}
									</h4>
									<div
										className="border text-center"
										style={{ borderRadius: '4px', width: '8%', height: '8%', marginLeft: '5%', background: '#FAFAFA' }}
									>
										{this.state.newObjective.actions.length}
									</div>
								</div>
								<h6 style={{ color: '#9094AA' }}>
									{gettext('Créer des actions pour atteindre votre objectif puis associer des indicateurs clés à piloter')}
								</h6>
							</div>
							{!this.state.user.is_reader && (
								<button
									className="button border"
									style={{
										background: `${this.state.categories.find((cat) => cat.pk === this.state.newObjective.category).color}`,
										borderColor: '#8888E2',
										color: '#ffffff',
										borderRadius: '6px',
									}}
									onClick={() => {
										this.addNewAction();
									}}
								>
									<i className="bi bi-plus-lg me-2"></i>
									{gettext('Nouvelle action')}
								</button>
							)}
						</div>
						{this.state.newObjective.actions.length !== 0 ? (
							<table
								className="border"
								style={{ borderColor: '#FAFAFA', width: '100%', borderRadius: '1em', fontWeight: '500', fontSize: '16px' }}
							>
								<tbody>
									<tr style={{ backgroundColor: '#FAFAFA', color: '#9094AA', fontSize: '14px' }}>
										<th className="py-2 ps-3" colSpan="3" style={{ width: '35%' }}>
											<img alt="" src="/static/img/icon_text.png" style={{ height: '2vh', width: 'auto', marginRight: '1%' }} />
											{gettext("Titre de l'action")}
										</th>
										<th colSpan="1" style={{ width: '12%', cursor: 'pointer' }} onClick={() => this.setshowReferentModal(true)}>
											<img alt="" src="/static/img/icon_manager.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
											{gettext('Référent')}
											<i className="bi bi-funnel-fill"></i>
										</th>
										<th colSpan="1" style={{ width: '12%' }}>
											<img alt="" src="/static/img/icon_deadline.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
											{gettext('Date prévue')}
										</th>
										<th colSpan="1" style={{ width: '12%' }}>
											<img alt="" src="/static/img/icon_budget.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
											{gettext('Budget')}
										</th>
										<th colSpan="1" style={{ width: '12%' }}>
											<img alt="" src="/static/img/icon_status.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
											{gettext('Statut')}
										</th>
										<th colSpan="1" style={{ width: '12%' }}>
											<img alt="" src="/static/img/icon_kpi.png" style={{ height: '2vh', width: 'auto', marginRight: '2%' }} />
											{gettext('Indicateurs clés')}
										</th>
										<th colSpan="1" style={{ width: '5%' }}></th>
									</tr>
									{this.state.newObjective.actions
										.filter(({ referent }) => this.state.referentFilter.includes(referent) || referent === null)
										.map((action) => {
											return (
												<React.Fragment key={action.pk}>
													{/* Modal to delete action */}
													<Modal
														size="lg"
														show={this.state.showActionDeleteModal}
														onHide={() => this.setshowActionDeleteModal(false)}
														aria-labelledby="contained-modal-title-vcenter"
														style={{ zIndex: '1050', width: '100%' }}
														className="m-0 p-0"
													>
														<Modal.Header closeButton>
															<Modal.Title id="contained-modal-title-vcenter">{gettext("Supprimer l'action")}</Modal.Title>
														</Modal.Header>
														<Modal.Body>
															<h6 id="contained-modal-title-vcenter">
																{gettext('Êtes-vous sûr de vouloir supprimer cette action ?')}
															</h6>
														</Modal.Body>
														<Modal.Footer className="d-flex justify-content-between">
															<button
																className="button border m-2"
																style={{ background: '#ffffff', borderColor: '#000000', color: '#000000', borderRadius: '6px' }}
																onClick={() => this.setshowActionDeleteModal(false)}
															>
																{gettext('Annuler')}
															</button>
															<button
																className="button border m-2"
																style={{ background: '#8785BB', borderColor: '#8785BB', color: '#ffffff', borderRadius: '6px' }}
																onClick={() => {
																	this.deleteAction(this.state.actionToDelete), this.setshowActionDeleteModal(false);
																}}
															>
																{gettext('Valider la suppression')}
															</button>
														</Modal.Footer>
													</Modal>
													<tr className="border-top border-bottom">
														<td colSpan="3" className="py-2 ps-3">
															<textarea
																disabled={this.state.disableReadersInputs || this.canModify(action.creation_entity)}
																data-toggle="tooltip"
																data-placement="top"
																title={action.label}
																maxLength="512"
																style={{
																	letterSpacing: '-0.04em',
																	color: '#000000',
																	background: 'transparent',
																	border: 'none',
																	fontWeight: '500',
																	padding: '0em',
																	textOverflow: 'ellipsis',
																	height: action.height ? action.height : 'auto',
																	resize: 'none',
																}}
																value={action.label}
																onBlur={(e) => {
																	this.saveAction(e, action.pk);
																}}
																onChange={(e) => {
																	this.handleTextAreaSize(e);
																	this.handleLabelAction(e.target.value, action.pk, e);
																}}
															>
															</textarea>
														</td>
														<td colSpan="1">
															<select
																disabled={this.state.disableReadersInputs || this.canModify(action.creation_entity)}
																defaultValue={action.referent}
																style={{ background: 'transparent', border: 'none', borderRadius: '24px' }}
																onChange={(e) => {
																	this.handleReferentAction(e, action.pk);
																}}
															>
																<option key={-1} value={-1}>
																	-
																</option>
																{this.state.all_possible_referent.map((user) => {
																	return (
																		<option key={user.pk} value={user.pk}>
																			{user.first_name
																				? user.first_name + ' ' + user.last_name + ' / ' + user.membership
																				: user.username + ' / ' + user.membership}
																		</option>
																	);
																})}
															</select>
														</td>
														<td colSpan="1">
															<input
																disabled={this.state.disableReadersInputs || this.canModify(action.creation_entity)}
																type="date"
																lang="en-EN"
																style={{
																	letterSpacing: '-0.04em',
																	color: '#000000',
																	background: 'transparent',
																	border: 'none',
																	fontWeight: '500',
																	padding: '0em',
																}}
																value={action.action_date}
																onBlur={(e) => {
																	this.saveAction(e, action.pk);
																}}
																onChange={(e) => {
																	this.handleDateAction(e.target.value, action.pk);
																}}
															/>
														</td>
														<td colSpan="1">
															<div className="ms-1" style={{ float: 'left' }}>
																€
															</div>
															<input
																disabled={this.state.disableReadersInputs || this.canModify(action.creation_entity)}
																type="number"
																pattern="[0-9]*"
																style={{
																	letterSpacing: '-0.04em',
																	color: '#000000',
																	background: 'transparent',
																	border: 'none',
																	fontWeight: '500',
																	padding: '0em',
																	width: '60%',
																}}
																onBlur={(e) => {
																	this.saveAction(e, action.pk);
																}}
																value={action.budget}
																onChange={(e) => {
																	this.handleBudgetAction(e.target.value, action.pk);
																}}
															/>
														</td>
														<td colSpan="1">
															<select
																disabled={this.state.disableReadersInputs || this.canModify(action.creation_entity)}
																defaultValue={action.status}
																style={{ background: 'transparent', border: 'none', borderRadius: '24px' }}
																onChange={(e) => this.handleStatusAction(e, action.pk)}
															>
																{this.state.actionStatusChoices.map((status) => {
																	return (
																		<option key={status.value} value={status.value}>
																			{status.name}
																		</option>
																	);
																})}
															</select>
														</td>
														<td colSpan="1">
															<div
																className="border text-center me-2"
																style={{
																	borderRadius: '4px',
																	width: '20%',
																	height: '20%',
																	background: '#FAFAFA',
																	float: 'left',
																}}
															>
																{action.kpis.length}
															</div>
															{!this.state.user.is_reader && (
																<button
																	className="button p-0"
																	data-toggle="tooltip"
																	data-placement="top"
																	title={gettext('Nouvel indicateur clé')}
																	style={{ background: 'transparent' }}
																	onClick={() => {
																		this.addNewKpi(action.pk);
																	}}
																>
																	<i className="bi bi-plus-lg"></i>
																</button>
															)}
															<button
																className="button p-0 ms-2"
																data-toggle="tooltip"
																data-placement="top"
																title={gettext('Afficher/Cacher les KPI')}
																style={{ background: 'transparent' }}
																onClick={() => {
																	this.showKpiList(action.pk);
																}}
															>
																<i className="bi bi-eye"></i>
															</button>
														</td>
														<td colSpan="1" className="text-center">
															{!this.state.user.is_reader && !this.canModify(action.creation_entity) && (
																<button
																	type="button"
																	style={{ color: 'red' }}
																	className="button p-1"
																	data-toggle="tooltip"
																	data-placement="top"
																	title={gettext('Supprimer')}
																	onClick={() => {
																		this.setState({ actionToDelete: action.pk }), this.setshowActionDeleteModal(true);
																	}}
																>
																	<i className="bi bi-trash3"></i>
																</button>
															)}
														</td>
													</tr>
													{action.kpis.length !== 0 && action.showKpi ? (
														<tr>
															<td colSpan="1" style={{ width: '12%' }}></td>
															<td colSpan="8" className="p-0">
																<table
																	className="w-100"
																	style={{
																		width: '100%',
																		borderLeft: '1px solid #DEDFEA',
																		borderBottom: '1px solid #DEDFEA',
																		borderRadius: '1em',
																		fontWeight: '500',
																		fontSize: '16px',
																	}}
																>
																	<tbody>
																		<tr style={{ backgroundColor: '#FAFAFA', color: '#9094AA', fontSize: '14px' }}>
																			<th className="py-2 ps-3" colSpan="3" style={{ width: '35%' }}>
																				<img
																					alt=""
																					src="/static/img/icon_text.png"
																					style={{ height: '2vh', width: 'auto', marginRight: '1%' }}
																				/>
																				{gettext("Titre de l'indicateur clé")}
																			</th>
																			<th colSpan="1" style={{ width: '12%' }}>
																				<img
																					alt=""
																					src="/static/img/icon_generic_kpi.png"
																					style={{ height: '2vh', width: 'auto', marginRight: '2%' }}
																				/>
																				{gettext('KPI générique')}
																			</th>
																			<th colSpan="1" style={{ width: '12%' }}>
																				<img
																					alt=""
																					src="/static/img/icon_unit.png"
																					style={{ height: '2vh', width: 'auto', marginRight: '2%' }}
																				/>
																				{gettext('Unité')}
																			</th>
																			<th colSpan="1" style={{ width: '12%' }}>
																				<img
																					alt=""
																					src="/static/img/icon_value_out.png"
																					style={{ height: '2vh', width: 'auto', marginRight: '2%' }}
																				/>
																				{gettext('Valeur visée')}
																			</th>
																			<th colSpan="1" style={{ width: '12%' }}>
																				<img
																					alt=""
																					src="/static/img/icon_value_in.png"
																					style={{ height: '2vh', width: 'auto', marginRight: '2%' }}
																				/>
																				{gettext('Valeur atteinte')}
																			</th>
																			<th colSpan="1" style={{ width: '5%' }} className="text-center"></th>
																		</tr>
																		{action.kpis.map((kpi) => {
																			return (
																				<tr className="border-top border-bottom" key={kpi.pk}>
																					{kpi.generic_kpi ? (
																						<React.Fragment>
																							<td className="py-2 ps-3" colSpan="3">
																								{
																									this.state.genericKpis.find(
																										(genKpi) => genKpi.pk === kpi.generic_kpi,
																									).label
																								}
																							</td>
																							<td colSpan="1">
																								<select
																									disabled={
																										this.state.disableReadersInputs ||
																										this.canModify(kpi.creation_entity)
																									}
																									defaultValue={kpi.generic_kpi}
																									style={{
																										background: 'transparent',
																										border: 'none',
																										borderRadius: '24px',
																									}}
																									onChange={(e) =>
																										this.handleGenericKpiKpi(e, action.pk, kpi.pk)
																									}
																								>
																									<option key="" value="">
																										-----
																									</option>
																									{this.state.genericKpis
																										.filter((genKpi) =>
																											genKpi.subcategories.includes(
																												this.state.newObjective.subcategory,
																											),
																										)
																										.map((genericKpi) => {
																											return (
																												<option
																													key={genericKpi.pk}
																													value={genericKpi.pk}
																												>
																													{genericKpi.label}
																												</option>
																											);
																										})}
																								</select>
																							</td>
																							<td colSpan="1" disabled>
																								{
																									this.state.unitChoices.find(
																										(unit) =>
																											unit.value ===
																											this.state.genericKpis.find(
																												(genericKpi) =>
																													genericKpi.pk === kpi.generic_kpi,
																											).unit,
																									).name
																								}
																							</td>
																						</React.Fragment>
																					) : kpi.label ? (
																						<React.Fragment>
																							<td className="py-2 ps-3" colSpan="3">
																								<input
																									disabled={
																										this.state.disableReadersInputs ||
																										this.canModify(kpi.creation_entity)
																									}
																									type="text"
																									data-toggle="tooltip"
																									data-placement="top"
																									title={kpi.label}
																									style={{
																										letterSpacing: '-0.04em',
																										color: '#000000',
																										background: 'transparent',
																										border: 'none',
																										fontWeight: '500',
																										padding: '0em',
																										textOverflow: 'ellipsis',
																									}}
																									value={kpi.label}
																									onBlur={(e) => {
																										this.saveKpi(e, action.pk, kpi.pk);
																									}}
																									onChange={(e) => {
																										this.handleLabelKpi(e.target.value, action.pk, kpi.pk);
																									}}
																								/>
																							</td>
																							<td colSpan="1">
																								<select
																									disabled={
																										this.state.disableReadersInputs ||
																										this.canModify(kpi.creation_entity)
																									}
																									defaultValue=""
																									style={{
																										background: 'transparent',
																										border: 'none',
																										borderRadius: '24px',
																									}}
																								>
																									<option key="" value="">
																										-----
																									</option>
																									{this.state.genericKpis
																										.filter((genKpi) =>
																											genKpi.subcategories.includes(
																												this.state.newObjective.subcategory,
																											),
																										)
																										.map((genericKpi) => {
																											return (
																												<option
																													key={genericKpi.pk}
																													value={genericKpi.pk}
																												>
																													{genericKpi.label}
																												</option>
																											);
																										})}
																								</select>
																							</td>
																							<td colSpan="1">
																								<select
																									disabled={
																										this.state.disableReadersInputs ||
																										this.canModify(kpi.creation_entity)
																									}
																									defaultValue={kpi.unit}
																									style={{
																										background: 'transparent',
																										border: 'none',
																										borderRadius: '24px',
																									}}
																									onChange={(e) => this.handleUnitKpi(e, action.pk, kpi.pk)}
																								>
																									{this.state.unitChoices.map((unit) => {
																										return (
																											<option key={unit.value} value={unit.value}>
																												{unit.name}
																											</option>
																										);
																									})}
																								</select>
																							</td>
																						</React.Fragment>
																					) : (
																						<React.Fragment>
																							<td className="py-2 ps-3" colSpan="3">
																								<input
																									disabled={
																										this.state.disableReadersInputs ||
																										this.canModify(kpi.creation_entity)
																									}
																									type="text"
																									style={{
																										letterSpacing: '-0.04em',
																										color: '#000000',
																										background: 'transparent',
																										border: 'none',
																										fontWeight: '500',
																										padding: '0em',
																										textOverflow: 'ellipsis',
																									}}
																									value={kpi.label}
																									onBlur={(e) => {
																										this.saveKpi(e, action.pk, kpi.pk);
																									}}
																									onChange={(e) => {
																										this.handleLabelKpi(e.target.value, action.pk, kpi.pk);
																									}}
																								/>
																							</td>
																							<td colSpan="1">
																								<select
																									disabled={
																										this.state.disableReadersInputs ||
																										this.canModify(kpi.creation_entity)
																									}
																									defaultValue=""
																									style={{
																										background: 'transparent',
																										border: 'none',
																										borderRadius: '24px',
																									}}
																									onChange={(e) =>
																										this.handleGenericKpiKpi(e, action.pk, kpi.pk)
																									}
																								>
																									<option key="" value="">
																										-----
																									</option>
																									{this.state.genericKpis
																										.filter((genKpi) =>
																											genKpi.subcategories.includes(
																												this.state.newObjective.subcategory,
																											),
																										)
																										.map((genericKpi) => {
																											return (
																												<option
																													key={genericKpi.pk}
																													value={genericKpi.pk}
																												>
																													{genericKpi.label}
																												</option>
																											);
																										})}
																								</select>
																							</td>
																							<td colSpan="1">
																								<select
																									disabled={
																										this.state.disableReadersInputs ||
																										this.canModify(kpi.creation_entity)
																									}
																									defaultValue={kpi.unit}
																									style={{
																										background: 'transparent',
																										border: 'none',
																										borderRadius: '24px',
																									}}
																									onChange={(e) => this.handleUnitKpi(e, action.pk, kpi.pk)}
																								>
																									{this.state.unitChoices.map((unit) => {
																										return (
																											<option key={unit.value} value={unit.value}>
																												{unit.name}
																											</option>
																										);
																									})}
																								</select>
																							</td>
																						</React.Fragment>
																					)}
																					<td colSpan="1">
																						<input
																							disabled={
																								this.state.disableReadersInputs ||
																								this.canModify(kpi.creation_entity)
																							}
																							type="number"
																							style={{
																								letterSpacing: '-0.04em',
																								color: '#000000',
																								background: 'transparent',
																								border: 'none',
																								fontWeight: '500',
																								padding: '0em',
																								width: '50%',
																							}}
																							onBlur={(e) => {
																								this.saveKpi(e, action.pk, kpi.pk);
																							}}
																							value={kpi.goal}
																							onChange={(e) => {
																								this.handleGoalKpi(e.target.value, action.pk, kpi.pk);
																							}}
																						/>
																					</td>
																					<td colSpan="1">
																						<input
																							disabled={
																								this.state.disableReadersInputs ||
																								this.canModify(kpi.creation_entity)
																							}
																							type="number"
																							className="me-2"
																							style={{
																								letterSpacing: '-0.04em',
																								color: '#000000',
																								background: 'transparent',
																								border: 'none',
																								fontWeight: '500',
																								padding: '0em',
																								width: '50%',
																							}}
																							onBlur={(e) => {
																								this.saveKpi(e, action.pk, kpi.pk);
																							}}
																							value={kpi.value}
																							onChange={(e) => {
																								this.handleValueKpi(e.target.value, action.pk, kpi.pk);
																							}}
																						/>
																						{kpi.goal !== 0 && kpi.value !== 0 && (
																							<b>{((kpi.value / kpi.goal) * 100).toFixed(1)}%</b>
																						)}
																					</td>
																					<td colSpan="1" className="text-center">
																						{!this.state.user.is_reader && !this.canModify(kpi.creation_entity) && (
																							<button
																								type="button"
																								style={{ color: 'red' }}
																								className="button p-1"
																								data-toggle="tooltip"
																								data-placement="top"
																								title={gettext('Supprimer')}
																								onClick={() => {
																									this.deleteKpi(action.pk, kpi.pk);
																								}}
																							>
																								<i className="bi bi-trash3"></i>
																							</button>
																						)}
																					</td>
																				</tr>
																			);
																		})}
																	</tbody>
																</table>
																{!this.state.user.is_reader && (
																	<button
																		className="button mt-1 mb-1"
																		style={{ background: 'transparent', color: '#8888E2', fontSize: '0.9em' }}
																		onClick={() => {
																			this.addNewKpi(action.pk);
																		}}
																	>
																		<i className="bi bi-plus-lg me-3"></i>
																		{gettext('Nouvel indicateur clé')}
																	</button>
																)}
															</td>
														</tr>
													) : (
														<tr></tr>
													)}
												</React.Fragment>
											);
										})}
								</tbody>
							</table>
						) : (
							<div
								className="w-100 p-5 d-flex flex-column justify-content-center align-items-start"
								style={{ background: '#F1F2F9', borderRadius: '8px' }}
							>
								{/* <div className="w-75 h-75" style={{ position:"absolute", top:"40vh", background:"radial-gradient(37.54% 40.45% at 67.22% 50%, rgba(0, 156, 255, 0.677083) 0.01%, rgba(255, 255, 255, 0) 100%)" }}/> */}
								<div className="py-5 px-5">
									<h4 className="m-2 pb-3">
										{gettext('Créer des actions pour atteindre vos objectifs')}
										<br />
										{gettext("Piloter des indicateurs clés et faire progresser la diversité et l'inclusion")}
									</h4>
									<button
										className="button border m-2"
										style={{
											background: `${this.state.categories.find((cat) => cat.pk === this.state.newObjective.category).color}`,
											borderColor: '#8888E2',
											color: '#ffffff',
											borderRadius: '6px',
											zIndex: '0',
										}}
										onClick={() => {
											this.addNewAction();
										}}
									>
										<i className="bi bi-plus-lg me-2"></i>
										{gettext('Nouvelle action')}
									</button>
								</div>
							</div>
						)}
					</div>
					{/* Modal to filter referent */}
					<Modal
						size="lg"
						show={this.state.showReferentModal}
						onHide={() => this.setshowReferentModal(false)}
						aria-labelledby="contained-modal-title-vcenter"
						style={{ zIndex: '1050', width: '100%' }}
						className="m-0 p-0"
					>
						<Modal.Header closeButton>
							<Modal.Title id="contained-modal-title-vcenter">{gettext('Référents')}</Modal.Title>
						</Modal.Header>
						<Modal.Body>
							<Form>
								{this.state.all_possible_referent.map((member) => (
									<div key={member.pk} className="mb-3">
										<Form.Check
											type={'checkbox'}
											checked={this.state.referentFilter.includes(member.pk) ? true : false}
											value={member.pk}
											label={
												member.first_name
													? member.first_name + ' ' + member.last_name + ' / ' + member.membership
													: member.username + ' / ' + member.membership
											}
											onChange={() => this.handleFilterByReferent(member.pk)}
										/>
									</div>
								))}
							</Form>
						</Modal.Body>
						<Modal.Footer className="d-flex justify-content-between">
							<button
								className="button border m-2"
								style={{ background: '#ffffff', borderColor: '#000000', color: '#000000', borderRadius: '6px' }}
								onClick={() => this.setState({ referentFilter: [] })}
							>
								{gettext('Vider les filtres')}
							</button>
							<button
								className="button border m-2"
								style={{ background: '#8785BB', borderColor: '#8785BB', color: '#ffffff', borderRadius: '6px' }}
								onClick={() => this.setshowReferentModal(false)}
							>
								{gettext('Appliquer')}
							</button>
							<button
								className="button border m-2"
								style={{ background: '#ffffff', borderColor: '#000000', color: '#000000', borderRadius: '6px' }}
								onClick={() => this.FillFilterByReferent()}
							>
								{gettext('Tout sélectionner')}
							</button>
						</Modal.Footer>
					</Modal>
					{/* Modal to delete objective */}
					<Modal
						size="lg"
						show={this.state.showObjectiveDeleteModal}
						onHide={() => this.setshowObjectiveDeleteModal(false)}
						aria-labelledby="contained-modal-title-vcenter"
						style={{ zIndex: '1050', width: '100%' }}
						className="m-0 p-0"
					>
						<Modal.Header closeButton>
							<Modal.Title id="contained-modal-title-vcenter">{gettext("Supprimer l'objectif")}</Modal.Title>
						</Modal.Header>
						<Modal.Body>
							<h6 id="contained-modal-title-vcenter">{gettext('Êtes-vous sûr de vouloir supprimer cet objectif ?')}</h6>
						</Modal.Body>
						<Modal.Footer className="d-flex justify-content-between">
							<button
								className="button border m-2 text-dark"
								style={{ background: '#ffffff', borderColor: '#000000', borderRadius: '6px' }}
								onClick={() => this.setshowObjectiveDeleteModal(false)}
							>
								{gettext('Annuler')}
							</button>
							<button
								className="button border m-2 text-white"
								style={{ background: '#8785BB', borderColor: '#8785BB', borderRadius: '6px' }}
								onClick={() => {
									this.deleteObjective(), this.setshowObjectiveDeleteModal(false);
								}}
							>
								{gettext('Valider la suppression')}
							</button>
						</Modal.Footer>
					</Modal>
				</div>
			) : (
				<div style={{ fontFamily: 'DM Sans' }}>
					<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#ffffff' }}>
						<Breadcrumb className="ps-4" separators=">" aria-label="breadcrumb">
							<Breadcrumb.Item underline="hover" color="inherit" href={'/' + this.state.entity.slug}>
								{gettext('Accueil')}
							</Breadcrumb.Item>
							<Breadcrumb.Item active>{gettext('Piloter')}</Breadcrumb.Item>
							<Breadcrumb.Item active>{gettext("Plan d'action")}</Breadcrumb.Item>
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

					<div
						className="border m-4 pl-5 pr-5"
						style={{ borderRadius: '16px', borderColor: '#DEDFEA', background: '#FFFFFF', boxShadow: '0px 4px 6px 0px #181B3D0D' }}
					>
						<div className="d-flex justify-content-between m-3 pt-3">
							<h4 style={{ fontWeight: '500' }}>{gettext("Plan d'action")}</h4>
							{this.state.entity.evaluations.length > 0 && this.state.user.is_owner && (
								<button
									className="button border"
									style={{ background: '#8785bb', borderColor: '#8888E2', color: '#ffffff', borderRadius: '6px', height: 'fit-content' }}
									onClick={() => this.aimsToObjectiveApiRequest()}
								>
									{gettext("Remplir le plan d'action à partir de vos évaluations")}
								</button>
							)}
						</div>
						<nav className="m-3 tab-menu">
							<div className="nav nav-tabs d-flex justify-content-start" id="nav-tab" role="tablist">
								{this.state.categories.map((category) => {
									return (
										<button
											key={category.pk}
											data-bs-toggle="tab"
											className={`nav-link ${category.pk === 1 ? 'active' : ''}`}
											style={{ borderBottomColor: `${category.color}`, borderWidth: '0 0 2px 0', color: `${category.color}` }}
											onClick={() => this.activateCategory(category.pk)}
										>
											{gettext(category.name)}
										</button>
									);
								})}
							</div>
						</nav>
						<hr className="m-0" style={{ color: '#DEDFEA' }} />
						{this.state.categories
							.filter((cat) => cat.pk === this.state.activeCategory)
							.map((category) => {
								return (
									<div className="m-3" key={category.pk}>
										<div className="d-flex justify-content-between pb-3 pt-3 align-items-center">
											<div>
												<div className="d-flex justify-content-start align-items-center">
													<h4 className="m-0" style={{ fontWeight: '500' }}>
														{gettext('Objectif')}
													</h4>
													<div
														className="border text-center"
														style={{ borderRadius: '4px', width: '8%', height: '8%', marginLeft: '5%', background: '#FAFAFA' }}
													>
														{this.state.objectives.filter((obj) => obj.category === category.pk).length}
													</div>
												</div>
												<h6 style={{ color: '#9094AA' }}>{gettext('Créer des objectifs à atteindre.')}</h6>
											</div>
											{this.state.user.is_owner && (
												<div>
													{/* <button className="p-2 button border" style={{ background:"#fff", borderRadius:"6px", whiteSpace:"nowrap", fontWeight:"550" }}><img alt="" src="/static/img/csv_download.png" className="me-1" style={{ width:"15%" }}/>{gettext("Télécharger en CSV")}</button> */}
													<div className="btn-group" style={{ verticalAlign: 'baseline' }}>
														<button
															className="button border"
															style={{
																background: `${category.color}`,
																borderColor: '#8888E2',
																color: '#ffffff',
																borderRadius: '6px 0px 0px 6px',
															}}
															onClick={() => this.objectiveManagement(category.pk)}
														>
															{gettext('Nouvel objectif')}
														</button>
														<button
															type="button"
															className="button dropdown-toggle border"
															style={{
																background: `${category.color}`,
																borderColor: '#8888E2',
																color: '#ffffff',
																borderRadius: '0px 6px 6px 0px',
																display: 'initial',
															}}
															data-bs-toggle="dropdown"
															aria-expanded="false"
														>
															<span className="caret"></span>
														</button>
														<div className="dropdown-menu p-2" style={{ width: '20vw' }}>
															<h6>{gettext('Modèle')}</h6>
															<p style={{ color: '#9094AA', fontSize: '1rem' }}>
																{gettext(
																	"Vous ne savez pas où commencer ? Notre équipe a élaboré des plans d'action sur mesure pour vous faciliter la tâche.",
																)}
															</p>
															<button
																className="p-2 button border"
																disabled
																style={{ background: '#000000', color: '#ffffff', borderRadius: '4px' }}
															>
																{gettext('Parcourir les modèles')}
															</button>
														</div>
													</div>
												</div>
											)}
										</div>
										{this.state.objectives.filter((obj) => obj.category === category.pk).length !== 0 ? (
											<table className="border" style={{ borderColor: '#FAFAFA', width: '100%', borderRadius: '1em', fontWeight: '500' }}>
												<tbody>
													<tr style={{ backgroundColor: '#FAFAFA', color: '#9094AA', fontSize: '14px' }}>
														<th className="py-2 ps-3" style={{ width: '45%' }}>
															<img
																alt=""
																src="/static/img/icon_text.png"
																style={{ height: '2vh', width: 'auto', marginRight: '1%' }}
															/>
															{gettext('Titre')}
														</th>
														<th style={{ width: '15%', cursor: 'pointer' }} onClick={() => this.setshowEntityModal(true)}>
															<img
																alt=""
																src="/static/img/icon_budget.png"
																style={{ height: '2vh', width: 'auto', marginRight: '2%' }}
															/>
															{gettext('Entité')}
															<i className="bi bi-funnel-fill"></i>
														</th>
														<th style={{ width: '12%' }}>
															<img
																alt=""
																src="/static/img/icon_budget.png"
																style={{ height: '2vh', width: 'auto', marginRight: '2%' }}
															/>
															{gettext('Budget')}
														</th>
														<th style={{ width: '12%' }}>
															<img
																alt=""
																src="/static/img/icon_actions.png"
																style={{ height: '2vh', width: 'auto', marginRight: '2%' }}
															/>
															{gettext('Actions')}
														</th>
														<th style={{ width: '12%' }}>
															<img
																alt=""
																src="/static/img/icon_status.png"
																style={{ height: '2vh', width: 'auto', marginRight: '2%' }}
															/>
															{gettext('Statut')}
														</th>
														<th style={{ width: '5%' }}></th>
													</tr>
													{category.subcategories.map((subcat) => {
														return this.state.objectives.find(
															(obj) => obj.subcategory === subcat.pk && obj.category === category.pk,
														) ? (
															<React.Fragment key={subcat.pk}>
																<tr
																	className="text-uppercase"
																	style={{ marginBottom: '3vh', color: '#9094AA', fontWeight: '600' }}
																>
																	<td className="pt-4 pb-3 ps-3">{subcat.name}</td>
																</tr>
																{this.state.objectives
																	.filter((obj) => obj.subcategory === subcat.pk && obj.category === category.pk)
																	.filter(({ entity }) => this.state.entityFilter.includes(entity) || entity === null)
																	.map((objective) => {
																		return (
																			<tr
																				className="border-top border-bottom"
																				key={objective.pk}
																				style={{ cursor: 'pointer' }}
																				onClick={() => this.loadObjective(objective)}
																			>
																				<td className="py-2 px-3 text-break">
																					{objective.label}
																				</td>
																				<td className="">
																					{this.state.entities.find((entity) => entity.pk === objective.entity).name}
																				</td>
																				<td className="">
																					{objective.total_budget ? '€' + objective.total_budget : ''}
																				</td>
																				<td className="">
																					{objective.actions.length} {gettext('actions')}
																				</td>
																				<td className="text-align">
																					{Math.round(objective.progress_bar)}%
																					<div className="ms-1 score__smallCircle d-inline-block">
																						<CircularProgressbar
																							value={objective.progress_bar}
																							strokeWidth={12}
																							styles={buildStyles({
																								pathColor: '#000000',
																								trailColor: 'rgba(220, 220, 220, 1)',
																							})}
																						></CircularProgressbar>
																					</div>
																				</td>
																				<td className="text-center">
																					<i className="bi bi-arrow-right"></i>
																				</td>
																			</tr>
																		);
																	})}
															</React.Fragment>
														) : (
															<tr key={subcat.pk}></tr>
														);
													})}
												</tbody>
											</table>
										) : (
											<div
												className="w-100 p-5 d-flex flex-column justify-content-center align-items-start"
												style={{ background: '#F1F2F9', borderRadius: '8px' }}
											>
												{/* <div className="w-75 h-75" style={{ position:"absolute", top:"35vh", background:"radial-gradient(37.54% 40.45% at 67.22% 50%, rgba(0, 156, 255, 0.677083) 0.01%, rgba(255, 255, 255, 0) 100%)" }}/> */}
												{this.state.user.is_owner ? (
													<div className="py-5 px-5">
														<h4 className="m-2 pb-3">
															{gettext("L'action commence par la planification.")}
															<br />
															{gettext('Faisons le premier pas.')}
														</h4>
														<div>
															<button
																className="button border m-2"
																style={{
																	background: `${category.color}`,
																	borderColor: '#8888E2',
																	color: '#ffffff',
																	borderRadius: '6px',
																	zIndex: '0',
																}}
																onClick={() => this.objectiveManagement(category.pk)}
															>
																<i className="bi bi-plus-lg me-2"></i>
																{gettext('Nouvel objectif')}
															</button>
															<button
																className="button border m-2"
																disabled
																style={{ background: '#ffffff', borderRadius: '6px', whiteSpace: 'nowrap', zIndex: '0' }}
															>
																{gettext('Commencer avec un modèle')}
															</button>
														</div>
													</div>
												) : (
													<div className="py-5 px-5">
														<h4 className="m-2 pb-3">{gettext('Aucuns objectifs crées sur cette dimension pour le moment')}</h4>
													</div>
												)}
											</div>
										)}
									</div>
								);
							})}
					</div>
					{/* Modal to filter entity */}
					<Modal
						size="lg"
						show={this.state.showEntityModal}
						onHide={() => this.setshowEntityModal(false)}
						aria-labelledby="contained-modal-title-vcenter"
						style={{ zIndex: '1050', width: '100%' }}
						className="m-0 p-0"
					>
						<Modal.Header closeButton>
							<Modal.Title id="contained-modal-title-vcenter">{gettext('Entités')}</Modal.Title>
						</Modal.Header>
						<Modal.Body>
							<Form>
								{this.state.entities.map((entity) => (
									<div key={entity.pk} className="mb-3">
										<Form.Check
											type={'checkbox'}
											checked={this.state.entityFilter.includes(entity.pk) ? true : false}
											value={entity.pk}
											label={entity.name}
											onChange={() => this.handleFilterByEntity(entity.pk)}
										/>
									</div>
								))}
							</Form>
						</Modal.Body>
						<Modal.Footer className="d-flex justify-content-between">
							<button
								className="button border m-2"
								style={{ background: '#ffffff', borderColor: '#000000', color: '#000000', borderRadius: '6px' }}
								onClick={() => this.setState({ entityFilter: [] })}
							>
								{gettext('Vider les filtres')}
							</button>
							<button
								className="button border m-2"
								style={{ background: '#8785BB', borderColor: '#8785BB', color: '#ffffff', borderRadius: '6px' }}
								onClick={() => this.setshowEntityModal(false)}
							>
								{gettext('Appliquer')}
							</button>
							<button
								className="button border m-2"
								style={{ background: '#ffffff', borderColor: '#000000', color: '#000000', borderRadius: '6px' }}
								onClick={() => this.FillFilterByEntity()}
							>
								{gettext('Tout sélectionner')}
							</button>
						</Modal.Footer>
					</Modal>
				</div>
			)
		) : (
			<h4 className="d-flex justify-content-center align-items-middle">{this.state.placeholder}</h4>
		);
	}
}

export default Lead;
