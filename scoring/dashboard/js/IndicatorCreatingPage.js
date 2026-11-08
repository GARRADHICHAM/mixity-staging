import React, { Component, Fragment } from 'react';
import Loading from '../../../mixity/dashboard/js/includes/Loading';
import { Breadcrumb, Card, Form, Button, Container, Row, Col } from 'react-bootstrap';
import Header from '../../../mixity/dashboard/js/includes/Header';
import './includes/stylesheet/autocomplete.css';

class IndicatorCreatingPage extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to /api/url/ request
			emptyurl: '',
			url: '',
			url_loaded: false,

			params: [{}],
			nb_params: 1,

			display_params: [{ linked_with: '0' }],
			sub_display_params: [{ 0: '0' }],
			nb_display_params: 1,

			title_fr: '',
			title_en: '',
			title_es: '',
			is_a_selector: false,
			selector_title_fr: '',
			selector_title_en: '',
			selector_title_es: '',
			result: [],
			to_display_results: '',

			already_created: [],

			total_number_to_load: 0,
			total_number_to_load_loaded: false,
			number_already_loaded: 0,
			timeRemaining: 0,
			timeRemainingLoaded: false,

			jsonlistparsedautocomplete: [],

			placeholder: gettext('Chargement'),
			current_id: 0,

			activeSuggestion: 0,
			filteredSuggestions: [],
			showSuggestions: false,
			userInput: '',

			element_loaded: false,

			url: '',
			indicator_list: [],
		};

		this.add_param = this.add_param.bind(this);
		this.remove_param = this.remove_param.bind(this);
		this.add_display_param = this.add_display_param.bind(this);
		this.remove_display_param = this.remove_display_param.bind(this);
	}

	async componentDidMount() {
		// ------------------- LOADING ELEMENTS -----------------

		try {
			var new_jsonlistparsedautocomplete = [];
			const response_indicator_list = await fetch(`/api/get-indicators/`);
			this.fetchErrorMessage(response_indicator_list);
			const data_indicator_list = await response_indicator_list.json();
			data_indicator_list.forEach((obj) => {
				new_jsonlistparsedautocomplete.push(obj);
			});
			this.setState(() => {
				return {
					jsonlistparsedautocomplete: new_jsonlistparsedautocomplete,
					element_loaded: true,
				};
			});
		} catch (error) {
			console.log(error);
			alert(gettext("Quelque chose s'est mal passé en chargeant les éléments !"));
		}
	}

	// ------------------- END LOADING ELEMENTS -----------------

	// ------------------- FETCH ERROR MESSAGE -----------------

	fetchErrorMessage(response) {
		if (response.status > 400) {
			return this.setState(() => {
				return { placeholder: gettext("Quelque chose s'est mal passé en chargeant les messages d'erreurs") };
			});
		}
		return;
	}

	// ------------------- END FETCH ERROR MESSAGE -----------------

	// ------------------- HANDLE SUBMIT -----------------

	handleSubmit = (event) => {
		try {
			event.preventDefault();
			if (event.keyCode == 13) return;
			let form = event.target;
			let indicator_id = form.indicatorid.value;
			let indicator_type = form.indicator_type.value;
			let title_fr = form.title_fr.value;
			let title_en = form.title_en.value;
			let title_es = form.title_es.value;
			let is_selector = form.is_selector.value;
			let selector_title_fr = form.selector_title_fr.value;
			let selector_title_en = form.selector_title_en.value;
			let selector_title_es = form.selector_title_es.value;
			let selector_link = form.selector_link.value;
			let colors = form.colors.value;
			//go throught every params and add them to a list of params
			let params = [];
			for (let i = 0; i < this.state.nb_params; i++) {
				var param_value = '';
				param_value = this.state.params[i];
				let param = '{' + param_value + '}';
				params.push(param);
			}
			let display_params = '';
			for (let i = 0; i < this.state.nb_display_params; i++) {
				var sub_display_params = '';
				if (form.sub_display_params[i] == undefined) sub_display_params = form.sub_display_params.value;
				else sub_display_params = form.sub_display_params[i].value;
				if (form.display_params[i].value == '"linked_with"') display_params += form.display_params[i].value + ': [ ' + sub_display_params + ' ],';
				else display_params += form.display_params[i].value + ':"' + sub_display_params + '",';
			}
			display_params = display_params.slice(0, -1);
			let result = `
                {
                    "${indicator_id}": {
                        "display_params": {
                            ${display_params}
                        },
                        "params": [
                            ${params}
                        ],
                        "indicator_type": ${indicator_type},
                        "title_fr": "${title_fr}",
                        "title_en": "${title_en}",
                        "title_es": "${title_es}",
                        "selector": "${is_selector}",
                        "selector_title_fr": "${selector_title_fr}",
                        "selector_title_en": "${selector_title_en}",
                        "selector_title_es": "${selector_title_es}",
                        "selector_link": "${selector_link}",
                        "colors": "${colors}"
                    }
                }`;
			console.log(result);
			var to_display_results = result;
			var newresult = this.state.result;
			newresult.push(JSON.parse(result));
			this.setState(() => {
				return {
					result: newresult,
					to_display_results: to_display_results,
				};
			});
		} catch (error) {
			console.log(error);
			alert(gettext("Quelque chose s'est mal passé en essayant de créer l'indicateur !"));
		}
	};

	// ------------------- END HANDLE SUBMIT -----------------

	// ------------------- DISPLAY PARAMS FUNCTIONS -----------------

	add_display_param() {
		try {
			let new_display_params = this.state.display_params;

			new_display_params.push({});
			this.setState(() => {
				return {
					display_params: new_display_params,
					nb_display_params: this.state.nb_display_params + 1,
				};
			});
		} catch (error) {
			console.log(error);
			alert(gettext("Quelque chose s'est mal passé en ajoutant un paramètre d'affichage !"));
		}
	}

	remove_display_param() {
		try {
			let new_display_params = this.state.display_params;

			new_display_params.pop();
			this.setState(() => {
				return {
					display_params: new_display_params,
					nb_display_params: this.state.nb_display_params - 1,
				};
			});
		} catch (error) {
			console.log(error);
			alert(gettext("Quelque chose s'est mal passé en supprimant un paramètre d'affichage !"));
		}
	}

	display_each_display_params(dispelemparam, main_index) {
		try {
			return [
				{ value: '"linked_with"' },
				{ value: '"order"' },
				{ value: '"size"' },
				{ value: '"stacked"' },
				{ value: '"svg": "name.svg"' },
				{ value: '"ending"' },
			].map((option, index) => (
				<option key={index} value={option.value} id={'input_' + option.value + '_' + main_index} defaultValue={dispelemparam == option.value}>
					{option.value}
				</option>
			));
		} catch (error) {
			console.log(error);
			alert(gettext("Quelque chose s'est mal passé en affichant les possibilité des paramètres d'affichage !"));
		}
	}

	load_display_params(index, nb_display_params, dispelemparam) {
		try {
			return (
				<Row xs="auto" style={{ marginBottom: '5px' }} key={index}>
					<Col md={{ span: 2, offset: 3 }}>
						<Form.Select
							name="display_params"
							onChange={(e) => {
								this.state.display_params[index] = e.target.value;
							}}
						>
							{this.display_each_display_params(dispelemparam, index)}
						</Form.Select>
					</Col>
					:
					<Col md={{ span: 2 }}>
						<Form.Control
							name="sub_display_params"
							id={'text_input_param_' + index}
							onChange={(e) => {
								this.state.sub_display_params[index] = e.target.value;
							}}
							type="text"
						></Form.Control>
					</Col>
					{index == 0 ? (
						<Col xs>
							<Button
								variant="outline-dark"
								onClick={() => {
									this.add_display_param();
								}}
								style={{ marginLeft: '35px' }}
							>
								ajouter un param
							</Button>
						</Col>
					) : (
						<Col></Col>
					)}
					{index == 1 && nb_display_params > 1 ? (
						<Col xs>
							<Button
								variant="outline-dark"
								onClick={() => {
									this.remove_display_param();
								}}
							>
								supprimer un param
							</Button>
						</Col>
					) : (
						<Col></Col>
					)}
				</Row>
			);
		} catch (error) {
			console.log(error);
			alert(gettext("Quelque chose s'est mal passé en affichant les paramètres d'affichage !"));
		}
	}

	// ------------------- END DISPLAY PARAMS FUNCTIONS -----------------

	// ------------------- PARAMS FUNCTIONS -----------------

	add_param() {
		try {
			let newparam = this.state.params;

			newparam.push({});
			this.setState(() => {
				return {
					params: newparam,
					nb_params: this.state.nb_params + 1,
				};
			});
		} catch (error) {
			console.log(error);
			alert(gettext("Quelque chose s'est mal passé en ajoutant un paramètre !"));
		}
	}

	remove_param() {
		try {
			let newparam = this.state.params;

			newparam.pop();
			this.setState(() => {
				return {
					params: newparam,
					nb_params: this.state.nb_params - 1,
				};
			});
		} catch (error) {
			console.log(error);
			alert(gettext("Quelque chose s'est mal passé en enlevant un paramètre !"));
		}
	}

	load_params(main_index, nb_params, elemparam) {
		try {
			return (
				<Row xs="auto" style={{ marginBottom: '5px' }}>
					<Col md={{ offset: 3 }}>{'{'}</Col>
					<Col md={{ span: 5 }}>
						<Form.Select
							name="params"
							id="paramselector"
							onChange={(e) => {
								this.state.params[main_index] = e.target.value;
							}}
							key={main_index}
						>
							{[
								{ value: '"type": "value"' },
								{ value: '"type":"rate_choice"' },
								{ value: '"type":"rate_subanswers"' },
								{ value: '"type":"rate_subanswers_choice_count"' },
								{ value: '"combine":"0,1"' },
								{ value: '"sort":"combined_value"' },
								{ value: '"sort":"value"' },
								{ value: '"type":"rate_choice_total"' },
								{ value: '"type": "rate_subanswers", "sort": "value"' },
								{ value: '"type": "rate_choice", "combine": "0,1"' },
								{ value: '"type":"rate_choice_total","collaborator_filters":{"civility":"woman"}' },
								{ value: '"type":"rate_choice_total","collaborator_filters":{"civility":"man"}' },
								{ value: '"type":"rate_choice_total","collaborator_filters":{"civility":"non-binary"}' },
							].map((option, index) => (
								<option key={index} value={option.value} selected={elemparam == option.value} id={'input_' + option.value + '_' + main_index}>
									{option.value}
								</option>
							))}
						</Form.Select>
					</Col>
					<Col>{'}'}</Col>
					{main_index == 0 ? (
						<Col xs>
							<Button
								variant="outline-dark"
								onClick={() => {
									this.add_param();
								}}
								style={{ marginLeft: '35px' }}
							>
								ajouter un param
							</Button>
						</Col>
					) : (
						<Col></Col>
					)}
					{main_index == 1 && nb_params > 1 ? (
						<Col xs>
							<Button
								variant="outline-dark"
								onClick={() => {
									this.remove_param();
								}}
							>
								supprimer un param
							</Button>
						</Col>
					) : (
						<Col></Col>
					)}
				</Row>
			);
		} catch (error) {
			console.log(error);
			alert(gettext("Quelque chose s'est mal passé en affichant les paramètres !"));
		}
	}

	// ------------------- END PARAMS FUNCTIONS -----------------

	// ------------------- AUTO COMPLETE FUNCTIONS -----------------
	async id_autocomplete_value_changed(newval) {
		try {
			// look if the newval is in the jsonlistparsedautocomplete and if it is, load the content of the indicator
			if (Object.values(this.state.jsonlistparsedautocomplete.map((elem) => elem.google_sheets_id)).indexOf(parseInt(newval)) > -1) {
				let content = [];
				const response_indicator_list = await fetch(`/api/info-indicators/?indicator=${newval}`);
				await this.fetchErrorMessage(response_indicator_list);
				const data_indicator_list = await response_indicator_list.json();
				var jsonparsed = this.state.already_created;
				data_indicator_list.forEach((obj) => {
					jsonparsed.push(obj.google_sheets_id);
					jsonparsed[obj.google_sheets_id] = obj;
				});
				this.setState(() => {
					return {
						already_created: jsonparsed,
					};
				});

				if (this.state.already_created[newval] != undefined) {
					content.push(this.state.already_created[newval]);

					let indicator_infos = content[0].indicator_infos;
					if (indicator_infos != undefined) {
						if (indicator_infos.Indicator_Slug != undefined) {
							document.querySelectorAll('#indicator_slug_selector option').forEach((option) => {
								option.selected = false;
								if (option.value == '"' + indicator_infos.Indicator_Slug.slug + '"') option.selected = true;
							});
						}
						if (indicator_infos.title != undefined) {
							document.getElementById('inputTitlefr').value = indicator_infos.title;
							document.getElementById('inputTitleen').value = indicator_infos.title;
							document.getElementById('inputTitlees').value = indicator_infos.title;
						}

						this.setState(() => {
							return {
								nb_display_params: 0,
							};
						});

						var acutalindex = 0;
						var new_display_params;
						var new_sub_display_params;
						var new_nb_display_params;
						if (Object.keys(indicator_infos.displaying_params).length == 0) {
							new_display_params = this.state.display_params;
							new_sub_display_params = this.state.sub_display_params;
							new_nb_display_params = this.state.nb_display_params;
						} else {
							new_display_params = [];
							new_sub_display_params = [];
							new_nb_display_params = 0;
						}
						await this.setState(() => {
							return {
								display_params: new_display_params,
								nb_display_params: new_nb_display_params,
								sub_display_params: new_sub_display_params,
							};
						});

						for (var i = 0; i < Object.keys(indicator_infos.displaying_params).length; i++) {
							if (i != Object.keys(indicator_infos.displaying_params).length - 1) {
								new_display_params.push({});
								new_sub_display_params.push({});
								new_nb_display_params += 1;
							}

							await this.setState(() => {
								return {
									display_params: new_display_params,
									nb_display_params: new_nb_display_params,
									sub_display_params: new_sub_display_params,
								};
							});
						}

						for (const [key, value] of Object.entries(indicator_infos.displaying_params)) {
							var new_display_params = this.state.display_params;
							var new_sub_display_params = this.state.sub_display_params;

							new_display_params[acutalindex] = key;
							new_sub_display_params[acutalindex] = value;

							if (document.getElementById('text_input_param_' + acutalindex) != undefined)
								document.getElementById('text_input_param_' + acutalindex).value = value;

							if (document.getElementById('input_"' + key + '"_' + acutalindex) != undefined)
								document.getElementById('input_"' + key + '"_' + acutalindex).selected = true;
							this.setState(() => {
								return {
									display_params: new_display_params,
									sub_display_params: new_sub_display_params,
								};
							});
							acutalindex++;
						}
						acutalindex = 0;
						var new_param = this.state.params;
						new_param[acutalindex] = indicator_infos.params.slice(1, -2);
						await this.setState(() => {
							return {
								params: new_param,
							};
						});
						if (document.getElementById('input_' + indicator_infos.params.slice(1, -2) + '_' + acutalindex) != undefined) {
							document.getElementById('input_' + indicator_infos.params.slice(1, -2) + '_' + acutalindex).selected = true;
						}
						if (indicator_infos.get_colors != undefined) document.getElementById('inputcolors').value = indicator_infos.get_colors;

						if (indicator_infos.selector == true) {
							document.getElementById('is_selector_true').selected = true;
							document.getElementById('is_selector_false').selected = false;
							document.getElementById('inputselectorTitlefr').value = indicator_infos.selector_labels;
							document.getElementById('inputselectorTitleen').value = indicator_infos.selector_labels;
							document.getElementById('inputselectorTitlees').value = indicator_infos.selector_labels;
						} else {
							document.getElementById('is_selector_true').selected = false;
							document.getElementById('is_selector_false').selected = true;
							document.getElementById('inputselectorTitlefr').value = '';
							document.getElementById('inputselectorTitleen').value = '';
							document.getElementById('inputselectorTitlees').value = '';
						}
					}
				}
			}
		} catch (error) {
			console.log(error);
			alert(gettext("Quelque chose s'est mal passé en changeant les valeurs grâce à l'autocompletion !"));
		}
	}

	id_autocomplete_changed = (e) => {
		try {
			const suggestions = this.state.jsonlistparsedautocomplete.map((elem) => elem.google_sheets_id);
			const userInput = e.currentTarget.value;
			let filteredSuggestions = [];
			if (userInput.length > 0) {
				const regex = new RegExp(`^${userInput}`, 'i');
				filteredSuggestions = suggestions.sort().filter((v) => regex.test(v));
			}
			this.setState({
				activeSuggestion: 0,
				filteredSuggestions,
				showSuggestions: true,
				userInput: e.currentTarget.value,
			});
			this.id_autocomplete_value_changed(e.currentTarget.value);
		} catch (error) {
			console.log(error);
			alert(gettext("Quelque chose s'est mal passé en changeant les possibilité d'autocompletion !"));
		}
	};

	on_click_on_id_autocomplete = (e) => {
		try {
			this.setState({
				activeSuggestion: 0,
				filteredSuggestions: [],
				showSuggestions: false,
				userInput: e.currentTarget.innerText,
			});
			this.id_autocomplete_value_changed(e.currentTarget.innerText);
		} catch (error) {
			console.log(error);
			alert(gettext("Quelque chose s'est mal passé quand l'utilisateur a cliqué sur une possibilité d'autocompletion !"));
		}
	};

	on_key_down_on_id_autocomplete = (e) => {
		try {
			const { activeSuggestion, filteredSuggestions } = this.state;

			if (e.keyCode === 13) {
				this.setState({
					activeSuggestion: 0,
					showSuggestions: false,
					userInput: filteredSuggestions[activeSuggestion],
				});
				this.id_autocomplete_value_changed(filteredSuggestions[activeSuggestion]);
			} else if (e.keyCode === 38) {
				if (activeSuggestion === 0) return;
				this.setState({ activeSuggestion: activeSuggestion - 1 });
			} else if (e.keyCode === 40) {
				if (activeSuggestion - 1 === filteredSuggestions.length) return;
				this.setState({ activeSuggestion: activeSuggestion + 1 });
			}
		} catch (error) {
			console.log(error);
			alert(gettext("Quelque chose s'est mal passé quand l'utilisateur a appuyé sur une touche en utilisant l'autocompletion !"));
		}
	};

	// ------------------- END AUTO COMPLETE FUNCTIONS -----------------

	// ------------------- RENDER -----------------
	render() {
		const {
			id_autocomplete_changed,
			on_click_on_id_autocomplete,
			on_key_down_on_id_autocomplete,
			state: { activeSuggestion, filteredSuggestions, showSuggestions, userInput },
		} = this;
		let suggestionsListComponent;
		if (showSuggestions && userInput) {
			if (filteredSuggestions.length) {
				suggestionsListComponent = (
					<ul className="suggestions">
						{filteredSuggestions.map((suggestion, index) => {
							let className;

							// Flag the active suggestion with a class
							if (index === activeSuggestion) {
								className = 'suggestion-active';
							}
							if (suggestion == userInput) return;
							return (
								<li
									className={className}
									key={suggestion}
									onClick={() => {
										on_click_on_id_autocomplete();
									}}
								>
									{suggestion}
								</li>
							);
						})}
					</ul>
				);
			} else {
				suggestionsListComponent = (
					<div className="no-suggestions">
						<em>No suggestions available.</em>
					</div>
				);
			}
		}
		return this.state.element_loaded ? (
			<>
				<div style={{ fontFamily: 'DM Sans' }}>
					{/* page header */}
					<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
						<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
							<Breadcrumb.Item href={'/'}>{gettext('Accueil')}</Breadcrumb.Item>
							<Breadcrumb.Item active>
								<strong>{gettext('créer un indicateur')}</strong>
							</Breadcrumb.Item>
						</Breadcrumb>
						<Header
							data={{
								url: '/create-indicator',
								languages: languages,
								language_code: language_code,
								enabled_website_languages: enabled_website_languages,
							}}
						/>
					</div>
					{/* page body */}
					<Card className="text-center">
						<Card.Body>
							<Card.Title style={{ marginBottom: '100px', marginTop: '50px' }}>{gettext('créer votre indicateur')}</Card.Title>
							<Form
								onSubmit={this.handleSubmit}
								id="main_indicator_form"
								onKeyPress={(e) => {
									e.key === 'Enter' && e.preventDefault();
								}}
							>
								<Container>
									<Row>
										<Col md={1}>{'{'}</Col>
									</Row>
									<Row xs="auto">
										<Col md={{ offset: 1 }}>"</Col>
										<Col md={{ span: 4 }}>
											<Fragment>
												<input
													type="text"
													onChange={id_autocomplete_changed}
													onKeyDown={on_key_down_on_id_autocomplete}
													name="indicatorid"
													value={userInput}
													autoComplete="off"
												/>
												{suggestionsListComponent}
											</Fragment>
										</Col>
										<Col>" : {'{'}</Col>
									</Row>
									<Row style={{ marginTop: '20px' }} xs="auto">
										<Col md={{ offset: 2 }}>"display params" : {'{'}</Col>
									</Row>
									{this.state.display_params.map((param, index) => this.load_display_params(index, this.state.nb_display_params, param))}
									<Row xs="auto">
										<Col md={{ offset: 2 }}>{'},'}</Col>
									</Row>
									<Row style={{ marginTop: '20px' }} xs="auto">
										<Col md={{ offset: 2 }}>"params" : {'['}</Col>
									</Row>
									{this.state.params.map((param, index) => this.load_params(index, this.state.nb_params, param))}
									<Row xs="auto">
										<Col md={{ offset: 2 }}>{'],'}</Col>
									</Row>
									<Row xs="auto">
										<Col md={{ offset: 2 }}>"indicator_type" : </Col>
										<Col md={{ span: 4 }}>
											<Form.Select name="indicator_type" id="indicator_slug_selector" style={{ marginLeft: '22px' }}>
												<option value='"LineChart"'>"LineChart"</option>
												<option value='"BarChart"'>"BarChart"</option>
												<option value='"CircularChart"'>"CircularChart"</option>
												<option value='"ProgressBarChart"'>"ProgressBarChart"</option>
												<option value='"TextChart"'>"TextChart"</option>
												<option value='"PieChart"'>"PieChart"</option>
												<option value='"GapChart"'>"GapChart"</option>
												<option value='"MutipleBarChart"'>"MutipleBarChart"</option>
											</Form.Select>
										</Col>
									</Row>
									<Row style={{ marginTop: '20px' }} xs="auto">
										<Col md={{ offset: 2 }}>"title_fr" : </Col>
										<Col md={{ span: 4 }}>
											<Form.Control
												type="text"
												id="inputTitlefr"
												name="title_fr"
												style={{ marginLeft: '80px' }}
												onChange={(e) => {
													this.state.title_fr_change = e.target.value;
													document.getElementById('inputTitleen').value == '' ||
													document.getElementById('inputTitleen').value ==
														e.target.value.slice(0, document.getElementById('inputTitleen').value.length)
														? (document.getElementById('inputTitleen').value = e.target.value)
														: null;
													document.getElementById('inputTitlees').value == '' ||
													document.getElementById('inputTitlees').value ==
														e.target.value.slice(0, document.getElementById('inputTitlees').value.length)
														? (document.getElementById('inputTitlees').value = e.target.value)
														: null;
												}}
											/>
										</Col>
									</Row>
									<Row style={{ marginTop: '20px' }} xs="auto">
										<Col md={{ offset: 2 }}>"title_en" : </Col>
										<Col md={{ span: 4 }}>
											<Form.Control
												type="text"
												id="inputTitleen"
												name="title_en"
												style={{ marginLeft: '74px' }}
												onChange={(e) => {
													this.state.title_en_change = e.target.value;
												}}
											/>
										</Col>
									</Row>
									<Row style={{ marginTop: '20px' }} xs="auto">
										<Col md={{ offset: 2 }}>"title_es" : </Col>
										<Col md={{ span: 4 }}>
											<Form.Control type="text" id="inputTitlees" name="title_es" style={{ marginLeft: '73px' }} />
										</Col>
									</Row>
									<Row style={{ marginTop: '20px' }} xs="auto">
										<Col md={{ offset: 2 }}>"selector" : </Col>
										<Col md={{ span: 4 }}>
											<Form.Select name="is_selector" style={{ marginLeft: '70px' }}>
												<option id="is_selector_false" value="false">
													false
												</option>
												<option id="is_selector_true" value="true">
													true
												</option>
											</Form.Select>
										</Col>
									</Row>
									<Row style={{ marginTop: '20px' }} xs="auto">
										<Col md={{ offset: 2 }}>"selector_title_fr" : </Col>
										<Col md={{ span: 4 }}>
											<Form.Control
												type="text"
												id="inputselectorTitlefr"
												name="selector_title_fr"
												onChange={(e) => {
													this.state.title_fr_change = e.target.value;
													document.getElementById('inputselectorTitleen').value == '' ||
													document.getElementById('inputselectorTitleen').value ==
														e.target.value.slice(0, document.getElementById('inputselectorTitleen').value.length)
														? (document.getElementById('inputselectorTitleen').value = e.target.value)
														: null;
													document.getElementById('inputselectorTitlees').value == '' ||
													document.getElementById('inputselectorTitlees').value ==
														e.target.value.slice(0, document.getElementById('inputselectorTitlees').value.length)
														? (document.getElementById('inputselectorTitlees').value = e.target.value)
														: null;
												}}
												style={{ marginLeft: '7px' }}
											/>
										</Col>
									</Row>
									<Row style={{ marginTop: '20px' }} xs="auto">
										<Col md={{ offset: 2 }}>"selector_title_en" : </Col>
										<Col md={{ span: 4 }}>
											<Form.Control type="text" id="inputselectorTitleen" name="selector_title_en" style={{ marginLeft: '1px' }} />
										</Col>
									</Row>
									<Row style={{ marginTop: '20px' }} xs="auto">
										<Col md={{ offset: 2 }}>"selector_title_es" : </Col>
										<Col md={{ span: 4 }}>
											<Form.Control type="text" id="inputselectorTitlees" name="selector_title_es" />
										</Col>
									</Row>
									<Row style={{ marginTop: '20px' }} xs="auto">
										<Col md={{ offset: 2 }}>"selector_link" : </Col>
										<Col md={{ span: 4 }}>
											<Form.Control type="text" id="inputselectorlink" name="selector_link" style={{ marginLeft: '32px' }} />
										</Col>
									</Row>
									<Row style={{ marginTop: '20px' }} xs="auto">
										<Col md={{ offset: 2 }}>"colors" : {'['}</Col>
										<Col md={{ span: 4 }}>
											<Form.Control type="text" id="inputcolors" name="colors" />
										</Col>
										<Col>{']'}</Col>
									</Row>
									<Row xs="auto">
										<Col md={{ offset: 1 }}>{'}'}</Col>
									</Row>
									<Row xs="auto">
										<Col>{'}'}</Col>
									</Row>
									<Button type="submit"> afficher le resultat </Button>
								</Container>
							</Form>
						</Card.Body>
					</Card>
					<Card>
						<Card.Header>
							<Row xs="auto">
								<Col md={{ span: 2, offset: 2 }}>
									<h3>results</h3>
								</Col>
								<Col md={{ span: 2, offset: 5 }}>
									<Button
										onClick={() => {
											navigator.clipboard.writeText(this.state.to_display_results);
										}}
									>
										{' '}
										copier le resultat
									</Button>
								</Col>
							</Row>
						</Card.Header>
						<Card.Body style={{ backgroundColor: '#EEE', marginBottom: '400px' }}>
							<pre>
								<code>{this.state.to_display_results}</code>
							</pre>
						</Card.Body>
					</Card>
				</div>
			</>
		) : (
			<>
				<Loading message={this.state.placeholder} />
			</>
		);
	}
}

export default IndicatorCreatingPage;
