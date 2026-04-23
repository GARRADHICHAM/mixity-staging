import React, { component } from 'react';
import { Modal } from 'react-bootstrap';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import { getColors, dataLabelColor } from '../ColorData';
import { array } from '../../../../../theme/src/js/jszip';

ChartJS.register(ArcElement, Tooltip, Legend, ChartDataLabels);

class DisplayDataRepartitionBySkills extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			selectOptions: {
				general: gettext('TOTAL GÉNÉRAL'),
				drh: gettext('DIRECTEURS (f/h/nb)'),
				manage: gettext('MANAGERS (f/h/nb)'),
				recruit: gettext('RECRUTEURS (f/h/nb)'),
				others: gettext('AUTRES (f/h/nb)'),
			},
			titles: {
				'Prise de recul': gettext('PRISE DE RECUL'),
				Écoute: gettext('ÉCOUTE'),
				Curiosité: gettext('CURIOSITÉ'),
				Organisation: gettext('ORGANISATION'),
			},
			labels: ['MAÎTRISÉE', 'ACQUISE', 'À APPROFONDIR', 'À DÉVELOPPER', 'À ACQUÉRIR'],
			activeJob: '',
			showModal: false,
		};
	}

	handleChange = (value) => {
		this.setState({ activeJob: value });
	};

	componentDidMount() {
		if (this.props.datas) this.setState({ activeJob: this.props.datas[0].name });
	}

	generateIndicatorInfo(key, job, levels) {
		let colors = [1, 2, 3, 4, 5];
		let labels = [];
		let values = Object.values(levels).reverse();
		let delayed;
		const options = {
			responsive: true,
			maintainAspectRatio: false,
			animation: {
				onComplete: () => {
					delayed = true;
				},
				delay: (context) => {
					let delay = 0;
					if (context.type === 'data' && context.mode === 'default' && !delayed) {
						delay = context.dataIndex * 300 + context.datasetIndex * 100;
					}
					return delay;
				},
			},
			plugins: {
				legend: {
					position: 'bottom',
					display: false,
					labels: {
						usePointStyle: true,
						pointStyle: 'rounded',
					},
				},
				title: {
					display: false,
					text: this.state.titles[key],
					position: 'bottom',
					color: '#181B3D',
					weight: 'bold',
					family: 'DM Sans',
				},
				tooltip: {
					padding: 16,
					backgroundColor: 'rgba(255, 255, 255, 1)',
					borderColor: 'rgba(222, 223, 234, 1)',
					borderWidth: 1,
					titleColor: '#181B3D',
					titleFont: {
						weight: 'bold',
						family: 'DM Sans',
					},
					bodyColor: '#181B3D',
					bodyFont: {
						weight: 'normal',
						family: 'DM Sans',
					},
					callbacks: {
						label: ({ label, formattedValue }) => `${label} : ${parseFloat(formattedValue.replace(',', '.')).toFixed(2)} %`,
					},
				},
				datalabels: {
					display: true,
					borderWidth: 0,
					color: function (context) {
						//We make the condition: if a value of the label is a certain color
						var index = context.dataIndex;
						return dataLabelColor(context.dataset.backgroundColor[index]);
					},
					font: {
						size: 16,
					},
					formatter: function (value) {
						return Math.round(value) > 6 ? `${Math.round(value)}%` : '';
					},
				},
				deferred: {
					xOffset: 150, // defer until 150px of the canvas width are inside the viewport
					yOffset: '50%', // defer until 50% of the canvas height are inside the viewport
					delay: 500, // delay of 500 ms after the canvas is considered inside the viewport
				},
			},
			elements: {
				arc: {
					borderWidth: 0,
				},
			},
		};
		var data = {
			labels: labels,
			datasets: [
				{
					label: '',
					data: values,
					backgroundColor: getColors('repartition_list', colors),
				},
			],
		};
		return (
			<div className="mb-3" style={{ position: 'relative', width: '13vw' }}>
				<Pie data={data} options={options} />
			</div>
		);
	}

	render() {
		const { datas } = this.props;
		return (
			<>
				{datas && this.state.activeJob && (
					<React.Fragment>
						<div className="card">
							<div className="d-flex justify-content-between align-items-center">
								<div className="d-flex align-items-center flex-grow-1">
									<h3 className="mxt--normal-bold mb-0">{gettext('Répartition des compétences de vos recruteurs (f/h/nb)')}</h3>
									<div className="ms-3 custom_tooltip" onClick={() => this.setState({ showModal: !this.state.showModal })}>
										?
									</div>
								</div>
								<select
									id="skills"
									name="Skills"
									className="select_indicator me-3 p-2"
									style={{ backgroundColor: 'white', width: 'fit-content' }}
									onChange={(e) => this.handleChange(e.target.value)}
								>
									{datas.map((job) => (
										<option key={job.name} value={job.name}>
											{this.state.selectOptions[job.name]}
										</option>
									))}
								</select>
							</div>
							<div className="w-100 mt-4">
								<p className="p-0 m-0">
									{gettext(
										'La prise de recul et la curiosité permettent une évaluation objective et ouverte, tandis que l’écoute assure un échange enrichissant avec les candidats, et l’organisation structure l’ensemble du processus pour réduire au maximum les biais et les stéréotypes, éviter les préjugés.',
									)}
								</p>
							</div>
							<div className="w-100 p-0 mt-5 d-flex flex-row justify-content-between">
								{datas.find((job) => job.name === this.state.activeJob) &&
									datas
										.filter((job) => job.name === this.state.activeJob)
										.map((job) => {
											return (
												<React.Fragment>
													<div className="d-flex flex-column">
														<div className="d-flex justify-content-between text-center">
															{job.scores.map((score, index) => (
																<div key={index}>
																	{Object.entries(score).map(
																		([skill, levels]) =>
																			Object.values(levels).filter((value) => value !== 0).length !== 0 && (
																				<div className="p-3" key={skill}>
																					{this.generateIndicatorInfo(skill, job.name, levels)}
																					<b>{this.state.titles[skill]}</b>
																				</div>
																			),
																	)}
																</div>
															))}
														</div>
													</div>
												</React.Fragment>
											);
										})}
								<div className="h-100 d-flex justify-content-center pt-3 pe-3">
									<div className="d-flex flex-column">
										{this.state.labels.map((label, index) => {
											return (
												<div key={index} className="d-flex align-items-center py-2 w-100">
													<div>
														<div
															className="indic-score"
															style={{
																backgroundColor: `${getColors('repartition_list', [[1, 2, 3, 4, 5][index]])[0]}`,
															}}
														></div>
													</div>
													<span className="legend_value" style={{ wordBreak: 'keep-all', whiteSpace: 'nowrap' }}>
														<b>{label}</b>
													</span>
												</div>
											);
										})}
									</div>
								</div>
							</div>
						</div>
						<Modal
							show={this.state.showModal}
							onHide={() => this.setState({ showModal: false })}
							aria-labelledby="contained-modal-title-vcenter"
							size={'lg'}
							style={{ zIndex: '1050' }}
							className="criteria_modal m-0 p-0"
							centered
						>
							<Modal.Header closeButton className="align-items-start" style={{ border: 'none' }}>
								<div className="w-100">
									<h2>{gettext('Méthodologie : évaluation des compétences Scan Recruit')}</h2>
								</div>
							</Modal.Header>
							<Modal.Body>
								<div className="w-100">
									<p>
										{gettext(
											'L’évaluation des compétences de recrutement inclusif a été conçue en se basant sur un référentiel issu d’une veille scientifique associée à l’expertise des équipes Mixity. Celui-ci cible des compétences spécifiques et des notions essentielles pour s’assurer des pratiques inclusives dans le recrutement.',
										)}
									</p>
									<h3 className="mt-5">{gettext('Choix des compétences évaluées')}</h3>
									<ul className="mt-4">
										<li>
											<h3><b>{gettext('Prise de recul :')}</b></h3>
										</li>
									</ul>
									<p>
										<b>{gettext('Définition dans le contexte de recrutement inclusif : ')}</b>
										{gettext(
											'La capacité à analyser une situation ou une candidature sans céder à des jugements hâtifs ou à des biais inconscients. Elle permet de considérer les candidats avec une certaine objectivité et de mettre en perspective des situations complexes.',
										)}
									</p>
									<p>
										<b>{gettext("Exemple d'application : ")}</b>
										{gettext(
											'Lorsqu’un recruteur évalue une personne candidate, il doit être capable d’identifier ses biais potentiels liés aux expériences passées ou aux stéréotypes qui peuvent être positifs ou négatifs, en s’appuyant sur des faits objectifs. Les stéréotypes positifs sont aussi réducteurs que les négatifs.',
										)}
									</p>
									<p>
										<b>{gettext('Question type : ')}</b>
										<i>
											{gettext(
												'« Vous rencontrez un candidat avec un accent prononcé qui pourrait affecter sa communication avec les clients. Comment réagissez-vous ? : »',
											)}
										</i>
									</p>
									<ul className="mt-5">
										<li>
											<h3><b>{gettext('Écoute :')}</b></h3>
										</li>
									</ul>
									<p>
										<b>{gettext('Définition dans le contexte du recrutement inclusif : ')}</b>
										{gettext(
											"L'aptitude à accueillir les informations fournies comme des éléments factuels par un candidat avec attention et sans préjugés, tout en créant un espace de dialogue bienveillant.",
										)}
									</p>
									<p>
										<b>{gettext('Exemple d’application : ')}</b>
										{gettext(
											'L’écoute active est essentielle pour comprendre les expériences d’un candidat, surtout si elles ne correspondent pas aux parcours habituels.',
										)}
									</p>
									<p>
										<b>{gettext('Question type : ')}</b>
										<i>{gettext("« Un candidat arrive 15 minutes en retard à l'entretien prévu : comment réagissez-vous ? »")}</i>
									</p>
									<ul className="mt-5">
										<li>
											<h3><b>{gettext('Curiosité :')}</b></h3>
										</li>
									</ul>
									<p>
										<b>{gettext('Définition dans le contexte du recrutement inclusif : ')}</b>
										{gettext(
											"L’ouverture d’esprit nécessaire pour explorer des profils différents, remettre en question ses pratiques et apprendre de nouvelles perspectives en matière de profils différents qui permettent d'ouvrir encore les champs de diversité donc d'inclusion.",
										)}
									</p>
									<p>
										<b>{gettext('Exemple d’application : ')}</b>
										{gettext(
											'Un recruteur curieux cherchera à comprendre comment des compétences non conventionnelles peuvent s’appliquer au poste.',
										)}
									</p>
									<p>
										<b>{gettext('Question type : ')}</b>
										<i>
											{gettext(
												"«Vous recevez une candidature de la part de votre mission handicap. Lors de l'entretien, quelle(s) question(s) posez-vous à cette personne en situation de handicap ?»",
											)}
										</i>
									</p>
									<ul className="mt-5">
										<li>
											<h3><b>{gettext('Organisation :')}</b></h3>
										</li>
									</ul>
									<p>
										<b>{gettext('Définition dans le contexte du recrutement inclusif : ')}</b>
										{gettext(
											'La capacité à structurer le processus de recrutement pour garantir l’équité, la transparence et une évaluation cohérente entre les candidats.',
										)}
									</p>
									<p>
										<b>{gettext('Exemple d’application : ')}</b>
										{gettext(
											'Mettre en place des grilles d’évaluation objectives pour chaque entretien et planifier des étapes claires pour réduire les biais.',
										)}
									</p>
									<p>
										<b>{gettext('Question type : ')}</b>
										<i>
											{gettext(
												'« Entre deux personnes candidates avec les mêmes compétences, comment choisir la personne à recruter ? »',
											)}
										</i>
									</p>
									<h3 className="mt-5">{gettext('Synthèse : ')}</h3>
									<p>
										{gettext(
											'Ces notions se complètent pour faire évoluer vers des pratiques de recrutement toujours plus inclusives. La prise de recul et la curiosité permettent une évaluation objective et ouverte, tandis que l’écoute assure un échange enrichissant avec les candidats, et l’organisation structure l’ensemble du processus pour réduire au maximum les biais et les stéréotypes, éviter les préjugés.',
										)}
									</p>
								</div>
							</Modal.Body>
						</Modal>
					</React.Fragment>
				)}
			</>
		);
	}
}

export default DisplayDataRepartitionBySkills;
