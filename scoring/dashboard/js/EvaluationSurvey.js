import React, { Component } from 'react';
import Header from '../../../mixity/dashboard/js/includes/Header';
import { QCMQuestionWithSolution } from './includes/questions_type/QCMQuestionWithSolution';
import { CriteriasFields } from './includes/questions_type/CriteriasFields';
import { getColors } from './includes/ColorData';

class EvaluationSurvey extends Component {
	constructor(props) {
		super(props);
		this.state = {
			entity: null,
			product: null,

			criteriasSelection: false,

			//related to /api/url/ request
			url: '',
			urlEvaluation: '',
			synthesis: {},

			//related to /api/language/ request
			languages: [],
			enabled_lang: [],
			google_sheet_lang: [],
			languagesLoaded: false,

			//related to /api/membership/ request
			collaborator: {},

			//related to human and scan criterias
			criterias: {},

			//related to evaluation type
			isDiagPage: false,
			isHumanPage: false,
			isScanPage: false,

			//related to questions
			questions: [],
			questionIndex: 0,
			questionLoaded: false,

			//related to questions
			answers: [],
			answerLoaded: false,

			// gestion design toast pour les reeavaluations requests
			notification_is_active: false,

			nextQuestionDisabled: true,
		};
	}

	async componentDidMount() {
		try {
			//  URL
			const response_url = await fetch('api/url/');
			this.fetchErrorMessage(response_url);
			const data_url = await response_url.json();

			let url = 'https://' + data_url;
			let url_evaluation = 'https://' + data_url;
			if (window.location.pathname.split('/').filter(Boolean)[1])
				url_evaluation += '/' + window.location.pathname.split('/').filter(Boolean)[0] + '/' + window.location.pathname.split('/').filter(Boolean)[1];
			const is_diag_page = window.location.href.includes('diag');
			const is_human_page = window.location.href.includes('human');
			const is_scan_page = window.location.href.includes('scan');

			this.setState(() => {
				return {
					url: url,
					entity: window.location.pathname.split('/').filter(Boolean)[0],
					product: window.location.pathname.split('/').filter(Boolean)[1],
					urlEvaluation: url_evaluation,
					isDiagPage: is_diag_page,
					isHumanPage: is_human_page,
					isScanPage: is_scan_page,
				};
			});
			if (!is_diag_page) {
				this.setState({ criteriasSelection: true });
			}
			const [response_language, response_criterias, response_collaborator_info, response_answer] = await Promise.all([
				fetch(this.state.url + '/api/language/'),
				fetch(this.state.url + `/api/${this.state.entity}/${this.state.product}/criterias/`),
				fetch(this.state.url + `/api/${this.state.entity}/${this.state.product}/survey/collaborator-info/`),
				fetch(this.state.url + `/api/${this.state.entity}/${this.state.product}/answer/`),
			]);
			this.fetchErrorMessage(response_language);
			this.fetchErrorMessage(response_criterias);
			this.fetchErrorMessage(response_collaborator_info);
			this.fetchErrorMessage(response_answer);
			const [data_languages, data_criterias, data_collaborator_info, data_answer] = await Promise.all([
				response_language.json(),
				response_criterias.json(),
				response_collaborator_info.json(),
				response_answer.json(),
			]);
			this.setState(() => {
					return {
						//language
						languages: data_languages,
						enabled_lang: Object.values(data_languages.filter(lang => lang.is_enabled)),
						google_sheet_lang: Object.values(data_languages.filter(lang => lang.is_google_sheet_lang)),
						languagesLoaded: true,
						//subscription
						collaborator: data_collaborator_info[0],
						//criterias
						criterias: data_criterias,
						// answers
						answers: data_answer,
						answerLoaded: true,
					};
				},
			);
		} catch (error) {
			console.error('>>>>> ERROR in assess evaluation : ', error);
		}
	}

	handleRequest = () => {
		// Mettre à jour l'état is_active à true
		this.setState({ notification_is_active: true });
	};

	handleRequestComplete = (isActive) => {
		this.setState({ notification_is_active: isActive });
	};

	// Fetch Functions
	fetchErrorMessage(response) {
		if (response.status > 400) {
			return this.setState(() => {
				return { placeholder: gettext('Quelque chose s\'est mal passé !') };
			});
		}
		return;
	}

	changePage(index) {
		if (this.state.isScanPage) {
			let disabled = true
			if (this.state.answers && this.state.answers.find(answer => answer.question === this.state.questions[this.state.questionIndex + index].google_sheets_id))
				disabled = false
			this.setState({ questionIndex: this.state.questionIndex + index, nextQuestionDisabled: disabled });
		}
	}

	defineCollabProfile() {
		event.preventDefault();
		let body = {
			'actiontype': "profile",
		};
		const requestOptions = {
			credentials: 'include',
			method: 'POST',
			headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
			body: JSON.stringify(body),
		};
		fetch(this.state.url + `/api/${this.state.entity}/${this.state.product}/survey/collaborator-info/`, requestOptions)
			.then((response) => {
				this.fetchErrorMessage(response);
				return response.json();
			})
			.then((data) => {
				this.setState(() => {
					return {
						collaborator: data[0],
					};
				}, () => {
					window.location.href = `/${this.state.entity}/scan/score-card`
				});
			})

	}

	shuffleQuestions(questions) {
		let questionsWithAnswer = [];
		let questionsWithoutAnswer = [];

		questions.forEach(question => {
			// Vérifier si la question a une réponse en se basant sur le google_sheets_id
			let hasAnswer = this.state.answers.some(answer => answer.question === question.google_sheets_id);
			if (hasAnswer)
				questionsWithAnswer.push(question);
			else
				questionsWithoutAnswer.push(question);
		});

		//Randomiser les questions sans réponses
		for (let i = questionsWithoutAnswer.length - 1; i > 0; i--) {
			const j = Math.floor(Math.random() * (i + 1));
			[questionsWithoutAnswer[i], questionsWithoutAnswer[j]] = [questionsWithoutAnswer[j], questionsWithoutAnswer[i]];
		}
		
		// Étape 3 : Combiner les deux listes
		let shuffledQuestions = [...questionsWithAnswer, ...questionsWithoutAnswer];
		return shuffledQuestions
	}

	saveCollaboratorInfo = (selectedChoices) => {
		event.preventDefault();
		let body = {
			'actiontype': "criterias",
			'choices': selectedChoices,
		};
		const requestOptions = {
			credentials: 'include',
			method: 'POST',
			headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
			body: JSON.stringify(body),
		};
		fetch(this.state.url + `/api/${this.state.entity}/${this.state.product}/survey/collaborator-info/`, requestOptions)
			.then((response) => {
				this.fetchErrorMessage(response);
				return response.json();
			})
			.then((data) => {
				this.setState(() => {
					return {
						collaborator: data[0],
					};
				}, () => {
					fetch(this.state.url + `/api/${this.state.entity}/${this.state.product}/question/`)
						.then((response) => {
							this.fetchErrorMessage(response);
							return response.json();
						})
						.then((data) => {
							this.setState(() => {
								data = this.shuffleQuestions(data)
								return {
									questions: data,
									questionIndex: this.state.answers.length === data.length ? this.state.answers.length - 1 : this.state.answers.length,
									questionLoaded: true,
									criteriasSelection: false,
								};
							});
						});
				});
			});
	}

		submitAnswer = (requestOptions) => {
			fetch(this.state.url + `/api/${this.state.entity}/${this.state.product}/answer/`, requestOptions)
				.then((response) => {
					this.fetchErrorMessage(response);
					return response.json();
				})
				.then((data) => {
					let answers = this.state.answers;
					answers.push(data[0]);
					this.setState(() => {
						return {
							answers: answers,
							nextQuestionDisabled: false,
						};
					});
				});
		};

		render()
		{
			return (
				this.state.languagesLoaded &&
				<div style={{ fontFamily: 'DM Sans', flexDirection: "column", minHeight: "100vh" }} className="d-flex m-0">
					{/* Dashboard Header */}
					<div className="d-flex justify-content-between px-3 pt-4 pb-2">
						<div className="d-flex justify-content-start align-items-center">
							<img src={'/static/img/scan/Scan.svg'} style={{ width: '15%' }} alt="Logo Scan" />
							<h3 className="m-0" style={{color:"#fff"}}><b>{gettext('Mixity Scan Recruit')}</b></h3>
						</div>
						<Header data={({
							url: this.state.url,
							languages: languages,
							language_code: language_code,
							enabled_website_languages: enabled_website_languages,
						})} />
					</div>
					{/* Body */}
					{!this.state.questionLoaded && !this.state.answerLoaded ?
						<h4 className="d-flex justify-content-center align-items-middle"
							style={{ marginTop: '40%' }}>{this.state.placeholder}</h4>
						:
						<div className="py-3 d-flex align-items-center justify-content-center dashboard-assess-indicator-font-size text-center" style={{flex:"1"}}>
							{
								this.state.criteriasSelection ?
									<div>
										<CriteriasFields data={{
											criterias: this.state.criterias,
											collaborators_info: this.state.collaborator,
											saveInfo: this.saveCollaboratorInfo,
										}} />
									</div>
									:
									<div className="p-4 w-75" style={{ justifySelf: 'center' }}>
										{/* Mettre les avancées de questionnaires ici */}
										{this.state.isDiagPage ?
											this.state.questions.map((question) =>
												<div className="m-3 p-3 rounded"
													 style={{ backgroundColor: '#FFF' }}>
													<QCMQuestionWithSolution data={question} />
												</div>,
											)
											:
											<QCMQuestionWithSolution data={{
												question: this.state.questions[this.state.questionIndex],
												answer: this.state.answers ? this.state.answers.find(answer => answer.question === this.state.questions[this.state.questionIndex].google_sheets_id) : null,
												submitAnswer: this.submitAnswer,
											}} />
										}
										<div className="d-flex w-100 mt-4">
											<div className="bg-white d-flex flex-wrap p-2 me-3" style={{flexDirection:"row", borderRadius: '16px'}}>
												<div className="my-2 d-flex justify-content-start">
												{this.state.questionIndex !== 0 &&
													<button type="button" className="d-flex align-self-center mx-2"
															name="return"
															style={{
																borderRadius: '6px',
																padding: '10px 16px 10px 16px',
																borderColor: '#000',
																backgroundColor: '#fff',
																border: '2px solid',
															}}
															onClick={() => {
																this.changePage(-1);
															}}
													>
														{gettext('Question précédente')}
													</button>
												}
												{this.state.questionIndex + 1 < this.state.questions.length &&
													<button type="button" className="d-flex align-self-center mx-2"
															name="save_next"
															style={{
																borderRadius: '6px',
																padding: '10px 16px 10px 16px',
																color : `${this.state.nextQuestionDisabled ? "#fff" : "#000"}`,
																borderColor: `${this.state.nextQuestionDisabled ? "#D2D2D2" : "#000"}`,
																backgroundColor: `${this.state.nextQuestionDisabled ? "#D2D2D2" : "#fff"}`,
																border: '2px solid',
															}}
															disabled={this.state.nextQuestionDisabled}
															onClick={() => {
																this.changePage(1);
															}}
													>
														{gettext('Question suivante')}
													</button>
												}
												<button type="button" className="d-flex align-self-center mx-2"
														name="finished_survey"
														style={{
															borderRadius: '6px',
															padding: '10px 16px 10px 16px',
															color : "#fff",
															borderColor: `${!(this.state.answers.length === this.state.questions.length) ? "#D2D2D2" : "#000"}`,
															backgroundColor: `${!(this.state.answers.length === this.state.questions.length) ? "#D2D2D2" : "#000"}`,
															border: '2px solid',
														}}
														disabled={!(this.state.answers.length === this.state.questions.length)}
														onClick={() => {
															this.defineCollabProfile();
														}}
												>
													{gettext('Terminer le questionnaire')}
												</button>
											</div>
											</div>
											<div className="bg-white p-2 ms-3 d-flex justify-content-center align-items-center" style={{ flexGrow: "1", borderRadius: '16px' }}>
												<div className="progress-bar"
													style={{
														backgroundColor: '#E9E9E9',
														height: '1vh',
														width: "90%",
														borderRadius: '6px',
													}}>
													<div
														className="progress-bar"
														style={{
															backgroundColor: '#000',
															bottom: 0,
															left: 0,
															width: `${this.state.answers.length / this.state.questions.length * 100}%`,
															height: '1vh',
															borderRadius: '6px',
														}}
													></div>
												</div>
											</div>
										</div>
									</div>
							}</div>}
				</div>
			);
		}
}

export default EvaluationSurvey;
