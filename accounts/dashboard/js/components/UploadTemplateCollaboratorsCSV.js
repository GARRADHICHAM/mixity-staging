// Ce composant permet de générer des entités à partir d'un fichier CSV
import React, { Component } from 'react';

class UploadTemplateCollaboratorsCSV extends Component {
	constructor(props) {
		super(props);
	}

	downloadCollaboratorsTemplate() {
		const csvContent = `first_name;last_name;email;entity_slug;is_owner;is_reader\nExample;Example;example@example.com;test-collaborateurs;false;true`;

		const blob = new Blob([csvContent], { type: 'text/csv' });

		const a = document.createElement('a');
		const url = window.URL.createObjectURL(blob);
		a.href = url;
		a.download = 'Upload_Collaborators_Template.csv';

		document.body.appendChild(a);
		a.click();

		window.URL.revokeObjectURL(url);
		document.body.removeChild(a);
	}

	render() {
		return (
			<button
				style={{
					padding: '10px, 16px, 10px, 16px',
					backgroundColor: '#FFFFFF',
					border: '1px solid #181B3D',
					borderRadius: '6px',
					margin: '8px 8px 8px 8px',
				}}
				onClick={this.downloadCollaboratorsTemplate}
			>
				<i className="bi bi-cloud-download" style={{ padding: '10px' }}></i>
				{gettext('Télécharger template CSV')}
			</button>
		);
	}
}

export default UploadTemplateCollaboratorsCSV;
