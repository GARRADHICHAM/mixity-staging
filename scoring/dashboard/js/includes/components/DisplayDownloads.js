import React, { Component } from 'react';
import AssessSheetDownload from '../../includes/AssessSheetDownload';
import AssessSheetDirectDownload from '../../includes/AssessSheetDirectDownload';
import { Modal } from 'react-bootstrap';

class DisplayDownloads extends Component {
	async startEvaluation() {
		const requestOptions = {
			credentials: 'include',
			method: 'POST',
			headers: {
				'Content-Type': 'application/json;charset=utf-8',
				'X-CSRFToken': csrftoken,
			},
		};
		const response = await fetch(this.props.urlEvaluation + '/api/' + this.props.evaluation.pk + '/start-evaluation/', requestOptions);
		this.fetchErrorMessage(response);
		const data = await response.json();
		const new_evaluation = this.props.evaluation;
		new_evaluation.is_started = true;
		// this.props.evaluation = new_evaluation;
		// this.props.evaluationStarted = true;
		alert(gettext('Votre évaluation a bien été lancée. Vous pouvez désormais répondre aux questions.'));
		window.location.reload();
	}

	fetchErrorMessage(response) {
		if (response.status == 403) {
			alert(gettext("Vous n'avez pas les droits requis pour cette action !"));
			return;
		}
		if (response.status > 400) {
			return this.setState(() => {
				return {
					placeholder: gettext("Quelque chose s'est mal passé !"),
				};
			});
		}
		return;
	}

	async openResponses() {
		try {
			const response = await fetch(this.props.urlEvaluation + '/api/open-responses/');
			this.fetchErrorMessage(response);
			const data = await response.json();

			this.props.refresh_entity_evaluation();
		} catch (error) {
			console.error('>>>>> ERROR in open responses : ', error);
		}
	}

	async blockResponses() {
		try {
			const response = await fetch(this.props.urlEvaluation + '/api/block-responses/');
			this.fetchErrorMessage(response);
			const data = await response.json();

			this.props.refresh_entity_evaluation();
		} catch (error) {
			console.error('>>>>> ERROR in block responses : ', error);
		}
	}

	async sendPdfByMail(pk) {
		const download_msg = document.getElementById('direct_download_msg');
		const download_message_element = document.getElementById('direct_download_element');
		const send_button = document.getElementById('send_synthesis_mail_button');

		send_button.style.opacity = '0.5';
		send_button.disabled = true;
		send_button.style.pointerEvents = 'none';
		download_message_element.style.display = 'flex';
		download_msg.textContent = gettext('Envoi en cours ...');

		fetch('/scoring/evaluation/' + pk + '/send-synthesis-pdf-mail', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': csrftoken,
			},
		})
			.then(async (response) => {
				if (!response.ok) {
					throw new Error(await response.text());
				}
				return;
			})
			.then(() => {
				download_message_element.style.backgroundColor = 'rgb(50, 255, 50, 50)';
				download_msg.textContent = gettext('Téléchargement terminé !');
			})
			.catch((error) => {
				download_message_element.style.backgroundColor = 'rgb(255, 15, 0, 50)';
				download_msg.textContent = gettext('Error sending the PDF: ' + error.message);
			})
			.finally(() => {
				setTimeout(() => {
					download_message_element.style.backgroundColor = 'rgb(255, 255, 255, 0)';
					download_message_element.style.display = 'none';
					download_msg.textContent = '';
					send_button.style.opacity = '1';
					send_button.style.pointerEvents = 'all';
					send_button.disabled = false;
				}, 5000);
			});
	}

	handleDownloadSynthesisButton = () => {
		this.sendPdfByMail(this.props.evaluation.pk);
	};

	render() {
		const {
			evaluation,
			entity,
			entityLoaded,
			isDiagPage,
			versionsList,
			is_reader,
			is_owner,
			enabled_lang,
			languages,
			evaluationStarted,
			nbAnswers,
			product,
			formChoicesLoaded,
			human_selected_filters,
			google_sheet_lang,
			isSubscriptionCurrent,
			DiagCaracteristicsLoaded,
			HumanCollaboratorInfoLoaded,
			synthesis,
		} = this.props;
		return (
			<div className="d-flex flex-column" style={{ maxWidth: '50%' }}>
				<h1 className="mxt--large-bold mb-3">{gettext('Votre questionnaire')}</h1>
				{!(this.props.isScanPage && evaluation.display_version !== 'en-cours') && (
					<div className="card-light card-light-green row p-3 flex-grow-1">
						<p className="mxt--normal-bold" style={{ fontWeight: 500 }}>
							{gettext('Revoir et éditer vos questions')}
						</p>
						<div className="d-flex flex-column justify-content-start gap-3">
							<div className="d-flex gap-3 button-container">
								{entityLoaded &&
									evaluation.is_validated_by_admin &&
									isDiagPage &&
									isSubscriptionCurrent &&
									evaluation.display_version == versionsList[0].display_version &&
									versionsList[0].display_version !== 'en-cours' && (
										<button className="mxt--small button border assess_white_btn p-0 px-3" onClick={() => this.props.handleRequest()}>
											{gettext("Demander à rouvrir l'évaluation")}
										</button>
									)}

								{entityLoaded &&
									evaluation &&
									evaluation.is_diag &&
									isSubscriptionCurrent &&
									!evaluation.is_validated_by_user &&
									!evaluation.is_validated_by_admin &&
									!is_reader && (
										<a
											href={`/scoring/evaluation/${evaluation.pk}/confirm/`}
											className="mxt--small button border assess_white_btn p-0 px-1"
										>
											<i className="bi bi-pencil-fill"></i>
											{gettext('Reprendre le questionnaire')}
										</a>
									)}
								<AssessSheetDirectDownload evaluation={evaluation} languages={languages} enabled_lang={enabled_lang} />
								<div className="modal fade" id="launch_eval_modal" tabIndex="-1" aria-labelledby="launch_eval_modal_label" aria-hidden="true">
									<div className="modal-dialog">
										<div className="modal-content">
											<div className="modal-header">
												<h5 className="modal-title" id="excel_human_filters_label">
													{gettext("Voulez-vous vraiment lancer l'évaluation ?")}
												</h5>
												<button
													type="button"
													id="close_btn_excel_human_filters"
													className="btn-close"
													data-bs-dismiss="modal"
													aria-label="Close"
												></button>
											</div>
											<div className="modal-body">
												<div className="d-flex justify-content-end gap-3">
													<button
														className="mxt--small button border assess_white_btn p-0 px-3"
														data-bs-dismiss="modal"
														aria-label="Close"
													>
														{gettext('Annuler')}
													</button>
													<button
														className="mxt--small button border assess_white_btn p-0 px-3"
														onClick={() => {
															this.startEvaluation();
														}}
													>
														{gettext('Confirmer')}
													</button>
												</div>
											</div>
										</div>
									</div>
								</div>
								{nbAnswers === 0 && (evaluation.is_human || evaluation.is_scan) && evaluationStarted === false && (
									<>
										{product.slug && (
											<a
												href={`/${entity.slug}/${product.slug}/filters/${evaluation.display_version_slugified}`}
												className="mxt--small button border assess_white_btn p-0 px-3"
											>
												{gettext('Filtres')}
											</a>
										)}
										<button
											className="mxt--small button border assess_white_btn p-0 px-3"
											data-bs-toggle="modal"
											data-bs-target="#launch_eval_modal"
										>
											{gettext("Lancer l'évaluation")}
										</button>
									</>
								)}
							</div>
							{entityLoaded &&
								evaluation &&
								isSubscriptionCurrent &&
								!evaluation.is_validated_by_user &&
								evaluation.is_started &&
								(evaluation.is_human || evaluation.is_scan) &&
								is_owner && (
									<div className="d-flex flex-column">
										<p
											style={{
												fontSize: '.8rem',
												fontWeight: '500',
											}}
										>
											{gettext('URL de votre évaluation à partager à vos collaborateurs (f/h/nb) :')}
										</p>
										<div className="d-flex gap-3">
											<a
												id={`eval_${evaluation}_id`}
												href={evaluation.collaborator_url}
												style={{
													display: 'none',
												}}
											>
												{evaluation.collaborator_url}
											</a>
											{evaluation.is_human ? (
												<button
													className="mxt--small button border assess_white_btn p-0 px-3"
													onClick={() => {
														navigator.clipboard.writeText(window.location.host + this.props.evaluation.collaborator_url);
													}}
												>
													{gettext('Copier le lien')}
												</button>
											) : (
												<a
													href={`/${entity.slug}/${product.slug}/survey`}
													className="mxt--small button border assess_white_btn p-0 px-3"
												>
													{gettext('Reprendre le questionnaire')}
												</a>
											)}
											{!is_reader && (
												<button className="mxt--small button border assess_white_btn p-0 px-3" onClick={() => this.blockResponses()}>
													<i className="bi bi-lock"></i>
													{gettext('Valider et bloquer les nouvelles réponses')}
												</button>
											)}
										</div>
									</div>
								)}
							{evaluation &&
								entityLoaded &&
								evaluation.is_started &&
								(evaluation.is_human || evaluation.is_scan) &&
								evaluation.is_validated_by_user &&
								!evaluation.is_validated_by_admin &&
								is_owner && (
									<div className="d-flex flex-column">
										<p
											style={{
												fontSize: '.8rem',
												fontWeight: '500',
											}}
										>
											{gettext('URL de votre évaluation à partager à vos collaborateurs (f/h/nb) :')}
										</p>
										<div className="d-flex gap-3">
											<a
												id={`eval_${evaluation}_id`}
												href={evaluation.collaborator_url}
												style={{
													display: 'none',
												}}
											>
												{evaluation.collaborator_url}
											</a>
											<button
												className="mxt--small button border assess_white_btn p-0 px-3"
												onClick={() => {
													navigator.clipboard.writeText(window.location.host + this.props.evaluation.collaborator_url);
												}}
											>
												{gettext('Copier le lien')}
											</button>
											{!is_reader && (
												<button className="mxt--small button border assess_white_btn p-0 px-1" onClick={() => this.openResponses()}>
													<i className="bi bi-unlock"></i>
													{gettext('Rouvrir et autoriser les nouvelles réponses')}
												</button>
											)}
										</div>
									</div>
								)}
						</div>
					</div>
				)}
				{entityLoaded && evaluation && is_owner && (
					<div className="d-flex justify-content-start w-95 gap-5 m-auto flex-grow-1">
						<div
							className={`card-light card-light-blue row px-3 py-4 align-content-start ${!evaluation.is_validated_by_admin ? 'disabled' : ''} ${
								evaluation.is_scan && evaluation.display_version !== 'en-cours' ? 'h-50' : ''
							}`}
						>
							<h3 className="mxt--normal-bold mb-4" style={{ fontWeight: 500 }}>
								{gettext('Publier votre évaluation')}
							</h3>
							<div className="d-flex justify-content-start gap-5">
								{evaluation.is_validated_by_admin && !evaluation.is_trial && (
									<a
										href={`/scoring/evaluation/${evaluation.pk}/publish/`}
										className="mxt--small button border assess_secondary_btn p-0 px-3"
									>
										{evaluation.public_display ? (
											<p
												className="my-auto d-flex"
												style={{
													fontSize: '0.8rem',
												}}
											>
												<i
													className="bi bi-share pe-3"
													style={{
														maxWidth: 'fit-content',
													}}
												></i>
												{gettext('Rendre privée')}
											</p>
										) : (
											<p
												className="my-auto d-flex"
												style={{
													fontSize: '0.8rem',
												}}
											>
												<i
													className="bi bi-share pe-3"
													style={{
														maxWidth: 'fit-content',
													}}
												></i>
												{gettext('Rendre publique')}
											</p>
										)}
									</a>
								)}
							</div>
						</div>
						<div
							className={`card-light card-light-blue row px-1 py-4 align-content-start ${!evaluation.is_started ? 'disabled' : ''} ${
								evaluation.is_scan && evaluation.display_version !== 'en-cours' ? 'h-50' : ''
							}`}
						>
							<h3 className="mxt--normal-bold mb-4" style={{ fontWeight: 500 }}>
								{gettext('Télécharger les résultats de votre questionnaire')}
							</h3>
							<div className="d-flex flex-column justify-content-start gap-3">
								{evaluation && languages && formChoicesLoaded && human_selected_filters && (
									<>
										<AssessSheetDownload
											entity_pk={entity.pk}
											evaluation={evaluation}
											filters={human_selected_filters}
											languages={languages}
											google_sheet_lang={google_sheet_lang}
											enabled_lang={enabled_lang}
											csrd_tag_is_on={evaluation.csrd_tag_on}
										/>
									</>
								)}
								{/* {(DiagCaracteristicsLoaded || HumanCollaboratorInfoLoaded) && synthesis && (
									<>
										<a
											className="mxt--small button border assess_white_btn p-0 px-1"
											role="button"
											onClick={this.handleDownloadSynthesisButton}
											id="send_synthesis_mail_button"
										>
											<i className="bi bi-envelope"></i>
											{gettext('Recevoir la synthèse par e-mail')}
										</a>
									</>
								)} */}
							</div>
						</div>
					</div>
				)}
			</div>
		);
	}
}

export default DisplayDownloads;
