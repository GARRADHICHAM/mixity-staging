import React, { Component } from 'react';

class MailValidation extends Component {
	constructor(props) {
		super(props);
		this.state = {
			//related to front-end display
			everythingLoaded: true,
			placeholder: gettext('Chargement'),
		};
	}

	render() {
		return this.state.everythingLoaded ? (
			<div className="d-flex justify-content-center align-items-center" style={{ height: '80vh' }}>
				<div
					className="bg-white d-flex align-items-center flex-column"
					style={{ width: '32%', minWidth: '300px', height: 'auto', borderRadius: '16px' }}
				>
					<p className="text-center" style={{ marginBottom: '5px', fontWeight: 570, fontSize: '22px' }}>
						{gettext('Merci pour votre inscription !')}
					</p>
					<p className="text-center mb-3" style={{ margin: 0, fontWeight: 520, fontSize: '12px' }}>
						{gettext('Un mail vous a été envoyé à l’adresse renseignée, cliquez sur le lien pour confirmer votre inscription.')}
					</p>
					<img src={'/static/img/register_design.png'} alt="register_design" style={{ width: '65%', marginTop: '2%', marginBottom: '5%' }} />
				</div>
			</div>
		) : (
			<h4 className="d-flex justify-content-center align-items-middle" style={{ marginTop: '40%' }}>
				{this.state.placeholder}
			</h4>
		);
	}
}

export default MailValidation;
