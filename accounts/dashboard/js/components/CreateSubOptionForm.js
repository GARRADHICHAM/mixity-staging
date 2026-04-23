// Ce composant permet de renvoyer au composant parent le produit séléctionné dans la liste par l'utilisateur.

import React, { Component } from 'react';

class CreateSubOptionForm extends Component {
	constructor(props) {
		super(props);
		this.state = {
			options: {
				diag: gettext('Mixity Diag'),
				human: gettext('Mixity Human'),
				pack360: gettext('Pack 360'),
				start: gettext('Mixity Start'),
			},
		};
	}

	handleChange = (event) => {
		const selectedProduct = event.target.value;
		this.props.updateProduct(selectedProduct);
	};

	render() {
		return (
			<div className="d-flex align-items-center justify-content-center flex-column" style={{ height: '100%', width: '80%', margin: '3%' }}>
				<label className="mb-1 d-flex flex-row w-100 p-2" style={{ fontWeight: 520, fontSize: '14px' }}>
					{gettext('Option')}
					<span style={{ color: '#DE3838', fontWeight: 520, fontSize: '14px', margin: 0 }}>*</span>
				</label>
				<div className="d-flex flex-rows align-items-center justify-content-center" style={{ width: '100%', maxHeight: '30px' }}>
					<select
						style={{ background: '#F6F7FB', borderColor: '#F6F7FB', margin: 0, borderRadius: '8px', whiteSpace: 'nowrap', boxShadow: 'none' }}
						value={this.props.product}
						onChange={this.handleChange}
					>
						{Object.keys(this.state.options).map((key) => (
							<option key={key} value={key}>
								{this.state.options[key]}
							</option>
						))}
					</select>
				</div>
			</div>
		);
	}
}

export default CreateSubOptionForm;
