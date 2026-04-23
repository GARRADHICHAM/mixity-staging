// Ce composant permet de générer des entités à partir d'un fichier CSV
import React, { Component } from 'react';

class UploadTemplateEntitiesCSV extends Component {
	constructor(props) {
		super(props);
	}
	downloadEntitiesTemplate() {
		const csvContent = `name;slug;workforce;entity_level;parent_entity_slug;tag;tag;tag;tag;tag;tag;tag;tag;tag;tag;tag;tag;tag;tag;tag;tag;tag;tag;tag;tag;tag\ncompany;company;56;0;;fr\ncompany-1;company-1;45;1;company;us\ncompany-2;company-2;34;1;company;de\ncompany-1a;company-1a;16;2;company-1;us\ncompany-1b;company-1b;16;2;company-1;de\ncompany-2a;company-2a;88;2;company-2;campus`;

		const blob = new Blob([csvContent], { type: 'text/csv' });

		const a = document.createElement('a');
		const url = window.URL.createObjectURL(blob);
		a.href = url;
		a.download = 'Upload_Entities_Template.csv';
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
				onClick={this.downloadEntitiesTemplate}
			>
				<i className="bi bi-cloud-download" style={{ padding: '10px' }}></i>
				{gettext('Télécharger template CSV')}
			</button>
		);
	}
}
export default UploadTemplateEntitiesCSV;
