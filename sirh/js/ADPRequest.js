import React, { Component } from 'react';
import { Breadcrumb, Modal } from 'react-bootstrap';
import Header from '../../mixity/dashboard/js/includes/Header';
// https://0.0.0.0:8080/dashboard/maaf/sirh/request/
class ADPRequest extends Component {
	constructor(props) {
		super(props);
		this.state = {
			software: 'decidium',
			text: '',
			errorMessage: '',
			isProcessing: false,
			isSent: false,
		};
	}

	sendForm(context) {
		const requestOptions = {
			credentials: 'include',
			method: 'POST',
			headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
			body: JSON.stringify({ text: context.state.text, software: context.state.software }),
		};
		context.setState({ isProcessing: true });
		fetch('../api/request/', requestOptions).then((response) => {
			if (response.status >= 400) {
				return context.setState(() => {
					return { errorMessage: gettext("Quelque chose s'est mal passé !"), isProcessing: false };
				});
			} else {
				context.setState(() => {
					return {
						isProcessing: false,
						isSent: true,
					};
				});
				setTimeout(() => (window.location = '../status/'), 2000);
			}
			return response.json();
		});
	}
	render() {
		return (
			<div style={{ fontFamily: 'DM Sans' }}>
				<div className="d-flex justify-content-between px-3 pt-3 pb-2 border-bottom" style={{ backgroundColor: '#fff' }}>
					<Breadcrumb className="ps-2" separators=">" aria-label="breadcrumb">
						<Breadcrumb.Item underline="hover" color="inherit" href={'/' + entity_slug}>
							{gettext('Accueil')}
						</Breadcrumb.Item>
						<Breadcrumb.Item color="inherit">{gettext('Mesurer')}</Breadcrumb.Item>
						<Breadcrumb.Item active>{gettext('Demande de connexion ADP')}</Breadcrumb.Item>
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
				<div className="row p-4 flex-grow-1">
					<div className="d-flex col-xl-6 col-12 gap-3 flex-column justify-content-evenly align-items-stretch">
						<div className="d-flex flex-grow-1 flex-column align-items-start justify-content-start gap-3 w-100 mb-0 p-4 border dashboard-main-container">
							<h3 className="fw-medium mb-0" style={{ fontSize: '1.2rem' }}>
								{gettext('Demande de connexion')}
							</h3>
							<span className="mxt--small color-text-grey" style={{ marginTop: '-15px' }}>
								{gettext('Ces étapes vont assurer que nous communiquons de la bonne manière')}
							</span>
							<h4 className="fw-medium mb-0" style={{ fontSize: '1.0rem' }}>
								{gettext('Logiciel ADP voulu :')}
							</h4>
							<select
								className="w-100"
								onChange={(e) => {
									this.setState({ software: e.target.value });
								}}
							>
								<option value="decidium">ADP Decidium</option>
							</select>
							<h4 className="fw-medium mb-0" style={{ fontSize: '1.0rem' }}>
								{gettext('Demande ou remarque particulière :')}
							</h4>
							<textarea
								className="w-100"
								rows="8"
								onChange={(e) => {
									this.setState({ text: e.target.value });
								}}
							></textarea>
							{this.state.errorMessage ? <span className="text-danger">{this.state.errorMessage}</span> : ''}
							{this.state.isSent ? (
								<span className="text-success">{gettext('Demande soumise avec succès')}</span>
							) : (
								<button
									onClick={() => this.sendForm(this)}
									className={`mxt--small button button_nasmor border assess_white_btn px-3 mt-2 ${this.state.isProcessing ? 'disabled' : ''}`}
								>
									{this.state.isProcessing ? gettext('Envoi en cours...') : gettext('Faire une demande de connexion')}
								</button>
							)}
						</div>
					</div>
					<div className="d-flex col-xl-6 col-12 gap-3 flex-column justify-content-evenly align-items-stretch">
						<div className="d-flex flex-grow-1 flex-column align-items-start justify-content-start gap-3 w-100 mb-0 p-4 border dashboard-main-container">
							<h3 className="fw-medium mb-0" style={{ fontSize: '1.2rem' }}>
								{gettext('Comment se déroule la demande de connexion ?')}
							</h3>
							<span className="mxt--small color-text-grey" style={{ marginTop: '-15px' }}>
								{gettext('Ces étapes vont assurer que nous communiquons de la bonne manière')}
							</span>
							<img className="w-100" src="/static/img/drawings/comparison.svg" />
							<span>
								Lorem ipsum dolor sit amet consectetur. Massa duis lacus varius tortor nulla pellentesque eu blandit lacus. Volutpat et nunc
								ornare amet nisi eu lacus senectus. Sit vehicula velit at turpis. Habitant massa a ullamcorper viverra tempus arcu. Quis
								habitant in lacus quam facilisi. Imperdiet dolor tristique urna amet dui mauris. Aenean malesuada aliquet est arcu rhoncus
								elementum. Accumsan quis cras ultrices viverra massa et venenatis dignissim in. Lorem ipsum dolor sit amet consectetur. Massa
								duis lacus varius tortor nulla pellentesque eu blandit lacus. Volutpat et nunc ornare amet nisi eu lacus senectus. Sit vehicula
								velit at turpis. Habitant massa a ullamcorper viverra tempus arcu. Quis habitant in lacus quam facilisi. Imperdiet dolor
								tristique urna amet dui mauris.{' '}
							</span>
						</div>
					</div>
				</div>
			</div>
		);
	}
}

export default ADPRequest;
