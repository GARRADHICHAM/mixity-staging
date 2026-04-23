import React from 'react';
import AssessDimensionScore from '../../includes/AssessDimensionScore';

class DisplayEvaluationSynthesis extends React.Component {
	constructor(props) {
		super(props);
		this.state = {
			showEvaluationSynthesis: false,
		};
	}

	handleToggle = () => {
		const newValue = !this.state.showEvaluationSynthesis;
		this.setState({ showEvaluationSynthesis: newValue });
		this.props.updateParentState('showEvaluationSynthesis', newValue);
	};

	async downloadPDF(evalId) {
		const download_msg = document.getElementById('download_msg');
		const download_message_element = document.getElementById('download_message_element');
		const download_button = document.getElementById('download_button');

		download_button.style.opacity = '0.5';
		download_button.disabled = true;
		download_button.style.pointerEvents = 'none';
		download_message_element.style.display = 'flex';
		download_msg.textContent = gettext('Téléchargement en cours ...');

		fetch('/scoring/evaluation/' + evalId + '/download-synthesis-pdf')
        .then(async response => {
			if (!response.ok) {
				throw new Error(await response.text());
			}
			return response.blob(); // Get the PDF as a blob
        })
        .then(blob => {
			// Create a URL for the blob and trigger the download
			const url = URL.createObjectURL(blob);
			const a = document.createElement("a");
			a.href = url;
			a.download = "Synthese_eval.pdf"; // Set the file name
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a); // Clean up the DOM
			URL.revokeObjectURL(url); // Free up memory
			download_msg.textContent = gettext('Téléchargement terminé !');
        })
        .catch(error => {
			download_message_element.style.backgroundColor = 'rgb(255, 15, 0, 50)';
			download_msg.textContent = gettext('Error fetching the PDF: ' + error.message);
		})
		.finally(() => {
			setTimeout(() => {
				download_message_element.style.backgroundColor = 'rgb(255, 255, 255, 0)';
				download_message_element.style.display = 'none';
				download_msg.textContent = '';
				download_button.style.opacity = '1';
				download_button.style.pointerEvents = 'all';
				download_button.disabled = false;
			}, 5000);
		});
	};

	handleDownloadButton = () => {
		this.downloadPDF(this.props.evaluationId);
	};

	render() {
		const { evaluationId, storedScoreCategory, DiagCaracteristicsLoaded, HumanCollaboratorInfoLoaded, synthesis, updateParentState } = this.props;

		return (
			<>
				{(DiagCaracteristicsLoaded ||
					HumanCollaboratorInfoLoaded) && synthesis && (
						<React.Fragment>
							<div
								className="card my-4 mx-3"
								style={{
									borderRadius: '16px',
								}}
								ref={this.downloadRef}
							>
								<div className="d-flex justify-content-between align-items-middle" style={{ cursor: 'pointer' }} onClick={this.handleToggle}>
									<div className="d-flex align-items-center flex-grow-1">
										<div>
											<img src={'/static/favicon.ico'} style={{ width: '22px' }} alt="arrow" />
										</div>
										<h3 className="mxt--normal-bold mb-0 mx-3">{gettext('Synthèse de mon évaluation')}</h3>
									</div>
									<div className="mx-2 d-flex align-items-center">
										<img
											style={{
												width: '20px',
												transition: 'transform 0.3s',
												transform: !this.state.showEvaluationSynthesis ? 'rotate(0deg)' : 'rotate(180deg)',
											}}
											src={'/static/icon/chevron-dropdown.svg'}
											alt="v"
										/>
									</div>
								</div>
								{this.state.showEvaluationSynthesis && (
									<div className="w-100 p-0 mt-5">
										<div className="w-100 mb-5">
											<h2 className="mxt--large-bold mb-3">{gettext('Analyse générale')}</h2>
											<p
												className="mb-5"
												dangerouslySetInnerHTML={{
													__html: synthesis.general_analysis,
												}}
												style={{
													wordBreak: 'break-word',
												}}
											/>
											<div
												className="d-flex flex-row card w-100"
												style={{
													borderRadius: '16px',
													gap: '32px',
												}}
											>
												<div className="d-flex flex-row align-items-center flex-grow-1">
													<div>
														<img
															src={`${synthesis.expert.photo}`}
															className="me-3"
															style={{
																width: '100px',
																borderRadius: '100%',
															}}
															alt={`${synthesis.expert.first_name} ${synthesis.expert.last_name}`}
														/>
													</div>
													<div
														className="d-flex flex-column"
														style={{
															width: 'max-content',
														}}
													>
														<h3 className="mxt--small-bold mb-0">
															{`${synthesis.expert.first_name} ${synthesis.expert.last_name}`}
														</h3>
														<h4 className="mxt--small mb-0">{synthesis.expert.title}</h4>
													</div>
												</div>
												<div>
													<p
														style={{
															wordBreak: 'break-word',
														}}
														dangerouslySetInnerHTML={{
															__html: synthesis.expert.comment,
														}}
													/>
												</div>
											</div>
										</div>
										<div className="w-100 mb-5">
											<h2 className="mxt--large-bold mb-3">{gettext('Analyse par dimension')}</h2>
											{synthesis.dimension_analysis.map((dimension) => (
												<div key={dimension.pk} className="d-flex dimensions mb-4">
													<div
														className="dimension_score"
														style={{
															width: '20%',
															maxWidth: '100px',
														}}
													>
														<AssessDimensionScore
															dimensionPercent={Math.round(
																storedScoreCategory.find((cat) => cat.category === dimension.pk).value,
															)}
															dimensionColor={dimension.color}
														/>
													</div>
													<div className="dimension_content">
														<h3 className="mb-3">
															<span
																className="bullet"
																style={{
																	background: dimension.color,
																}}
															></span>
															{gettext(dimension.category)}
														</h3>
														<p>{dimension.content}</p>
													</div>
												</div>
											))}
										</div>
										<div className="w-100 mb-5">
											<h2 className="mxt--large-bold mb-3">{gettext('Principales recommandations')}</h2>
											<ul>
												{synthesis.key_recommendations.map((recommendation, index) => (
													<li
														key={index}
														className="mt-0 mb-3"
														style={{
															fontSize: '1.1rem',
															lineHeight: '1.5rem',
														}}
													>
														{recommendation}
													</li>
												))}
											</ul>
										</div>
										<div className="w-100 mb-5">
											<h2 className="mxt--large-bold mb-3">{gettext('Bonnes pratiques')}</h2>
											<ul>
												{synthesis.best_practices.map((practice, index) => (
													<li
														key={index}
														className="mt-0 mb-3"
														style={{
															fontSize: '1.1rem',
															lineHeight: '1.5rem',
														}}
													>
														{practice}
													</li>
												))}
											</ul>
										</div>
										{/* <div className="w-100 d-flex">
											<a
												className="mxt--small button border assess_white_btn p-0 px-1"
												role="button"
												onClick={this.handleDownloadButton}
												id="download_button"
											>
												<i className="bi bi-cloud-download"></i>
												{gettext('PDF')}
											</a>
											<div id="download_message_element" className="w-100" style={{ display: 'none', borderRadius: '20px', justifyContent: 'center', alignItems: 'center', }}>
												<h4 style={{ textAlign: 'center' }} id="download_msg"></h4>
											</div>
										</div> */}
									</div>
								)}
							</div>
						</React.Fragment>
					)}
			</>
		);
	}
}

export default DisplayEvaluationSynthesis;
