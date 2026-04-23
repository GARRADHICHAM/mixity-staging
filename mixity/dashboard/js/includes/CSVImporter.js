import React from 'react';
import { createRef } from 'react';

export default class CSVImporter extends React.Component {
	constructor(props) {
		super(props);

		this.hasHeader = createRef();
		this.inputFile = createRef();
		this.state = {
			isUploading: false,
			uploadingError: '',
		};
	}

	uploadCSV(file) {
		this.setState({
			isUploading: true,
		});
		let formData = new FormData();
		formData.append('type', this.props.stats.type);
		formData.append('ignoreFirstLine', this.hasHeader.current.checked.toString());
		formData.append('file', file);
		const params = {
			credentials: 'include',
			method: 'POST',
			headers: { 'X-CSRFToken': csrftoken },
			body: formData,
		};
		fetch('/' + entity_slug + '/api/upload-csv/?eval_id=' + eval_id + '&version=' + currentVersion, params)
			.then((response) => {
				if (response.status >= 400) {
					return this.setState({
						uploadingError: gettext("Une erreur est survenue lors de l'import du CSV"),
						isUploading: false,
					});
				}
				return response.json();
			})
			.then((json) => {
				if (this.state.uploadingError === '') {
					this.setState({ isUploading: false });
					this.props.callback(json);
				}
			});
	}

	render() {
		return (
			<div className="m-3 pt-3">
				<h4 className="fw-medium mb-4">{this.props.stats.name}</h4>
				<div className="mxt--small-bold mb-4">
					{gettext('Statut')} : {this.props.stats.status_label.split('/')[0]}
				</div>
				{
					<div className="d-flex justify-content-start gap-3">
						<span className="w-100 d-block" style={{ lineHeight: '32px' }}>
							{this.props.stats.status === 'error' && (
								<div className="mb-5 d-flex gap-2">
									<span className="d-block" style={{ lineHeight: '32px' }}>
										{gettext(this.props.stats.status_label.split('/').length - 1)}
										{gettext(
											this.props.stats.status_label.split('/').length > 2
											? ' erreurs sont présentes dans le fichier'
											: ' erreur est présente dans le fichier',
										)}
									</span>
									<span className="d-block" style={{ lineHeight: '32px' }}>
										<a
											className="mxt--small p-0 px-1"
											href="#!"
											onClick={() => {
												this.props.toggleShowMoreErrors();
											}}
										>
											{gettext('Voir les erreurs')}
										</a>
									</span>
								</div>
							)}
							{this.props.stats.status === 'finished' ? (
								<span>
									{gettext(
										"Les données ont été traitées avec succès. Vous devriez voir l'indicateur dans l'onglet Origines de votre évaluation ",
									)}
									<a href={'/' + entity_slug + '/diag/assess/' + currentVersion + '/#evaluation-tabs'}>{gettext('Mixity Diag')}</a>.
								</span>
							) : this.props.stats.status === 'processing' ? (
								<span>
									{gettext(
										"Les données ont été importées et sont en cours de traitement. Vous pouvez rester la page pour suivre l'avancée ou la quitter sans perte de données.",
									)}
								</span>
							) : (
								this.props.stats.summary
							)}
							{this.props.stats.status === 'finished' ? (
								<>
									<span className="d-block mt-3">{gettext("Pour importer un nouveau fichier, veuillez-contacter l'équipe de Mixity.")}</span>
								</>
							) : this.props.stats.status === 'processing' ? (
								<div className="d-flex w-100 justify-content-center m-5">
									<div class="spinner-border" role="status">
										<span class="visually-hidden">Loading...</span>
									</div>
								</div>
							) : (
								<>
									<span className="d-block my-3">
										{gettext('Pour importer votre fichier CSV, vérifiez qu’il respecte la structure suivante :')}
									</span>
									<ul>
										<li>{gettext('Chaque ligne représente un seul collaborateur (f/h/nb)')}</li>
										<li>{gettext('Une case ne peut pas contenir de virgule ou de point virgule')}</li>
										<li>{gettext('La première colonne comporte les prénoms de vos collaborateurs (f/h/nb)')}</li>
										<li>{gettext('La seconde colonne comporte les noms de famille de naissance de vos collaborateurs (f/h/nb)')}</li>
										<li>
											{gettext('La troisième colonne comporte le code ')}
											<a target="_blank" href="https://www.iban.com/country-codes">
												ISO-3166-alpha2
											</a>
											{gettext(' de la nationalité de vos collaborateurs (f/h/nb)')}
										</li>
									</ul>
									<span className="d-block">
										{gettext('Vérifiez bien que le fichier ne comporte aucune autre information (colonnes supplémentaires).')}
									</span>

									<div className="d-flex mt-3">
										<span>{gettext("Voici un fichier CSV d'exemple : ")}</span>
										<a href="/static/csv/namsor/ethnicity_example.csv">
											<img className="ms-2 me-1" src={'/static/img/excel.png'} style={{ width: '20px', height: '20px' }} />
											ethnicity_example.csv
										</a>
									</div>
								</>
							)}
							{this.props.stats.can_delete ? (
								<div className="d-flex align-items-center mt-5">
									<div className="d-flex align-items-center me-5">
										<input ref={this.hasHeader} type="checkbox" id={`header_${this.props.stats.type}`} />
										<label className="mxt--small-bold mx-2" htmlFor={`header_${this.props.stats.type}`}>
											&nbsp;{gettext('Ignorer la première ligne')}&nbsp;
										</label>
										<div className="position-relative d-inline-block">
											<span className="tooltip">
												<div className="tooltip__icon">?</div>
												<span className="tooltip__text">
													{gettext(
														"Cochez cette case si la première ligne de votre fichier sert d'en-tête pour les noms de colonnes par exemple.",
													)}
												</span>
											</span>
										</div>
									</div>
									{this.props.stats.can_delete ? (
										!this.state.isUploading ? (
											this.state.uploadingError !== '' ? (
												<span>{this.state.uploadingError}</span>
											) : (
												<a
													className="mxt--small button border assess_white_btn p-0 px-1"
													href="#!"
													onClick={() => {
														this.inputFile.current.click();
													}}
												>
													<i className="bi bi-upload"></i>
													{gettext('Importer un CSV')}
												</a>
											)
										) : (
											<img style={{ width: '188px', marginTop: '-20px' }} src={'/static/img/loading_bar.svg'} />
										)
									) : (
										''
									)}
									<input
										ref={this.inputFile}
										accept=".csv"
										type="file"
										onChange={(e) => {
											this.uploadCSV(e.target.files[0]);
										}}
										className="d-none"
									/>
								</div>
							) : (
								''
							)}
						</span>
					</div>
				}
			</div>
		);
	}
}
