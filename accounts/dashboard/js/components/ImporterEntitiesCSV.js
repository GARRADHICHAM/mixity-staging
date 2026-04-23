// Ce composant permet de générer des entités à partir d'un fichier CSV
import React, { Component } from 'react';

class ImporterEntitiesCSV extends Component {
	constructor(props) {
		super(props);
		this.state = {
			csvFile: null,
		};
		this.fileInputRef = React.createRef();
	}

	handleOnChange = async (event) => {
		const file = event.target.files[0];
		if (file) {
			this.setState({ csvFile: file }, this.handleOnSubmit);
		}
	};

	handleOnSubmit = async (event) => {
		const { csvFile } = this.state;
		const pathname = window.location.pathname;

		const segments = pathname.split('/');
		const entity_slug = segments[2];
		if (!csvFile) {
			alert(gettext('Veuillez importer un fichier CSV.'));
			return;
		}

		const formData = new FormData();
		formData.append('file', csvFile);
		formData.append('entity_slug', entity_slug);

		try {
			const response = await fetch('/api/upload_entities_csv/', {
				method: 'POST',
				body: formData,
				headers: {
					'X-CSRFToken': csrftoken,
				},
			});

			const data = await response.json();
			if (data.success) {
				alert(gettext('Les entités ont été créées avec succès !'));
			} else {
				alert(gettext(data.message));
			}
		} catch (error) {
			alert(gettext('Une erreur est survenue.'));
		}
	};

	handleButtonClick = () => {
		this.fileInputRef.current.click();
	};

	render() {
		return (
			<div className="d-flex">
				<input
					type="file"
					accept=".csv"
					ref={this.fileInputRef}
					onChange={this.handleOnChange}
					style={{
						display: 'none',
					}}
				/>
				<button
					className="button border"
					onClick={this.handleButtonClick}
					style={{
						padding: '10px 16px',
						backgroundColor: '#8888E2',
						color: '#FFFFFF',
						border: '1px solid #8888E2',
						borderRadius: '6px',
						margin: '8px 0',
					}}
				>
					{gettext('Importer les entités via CSV')}
				</button>
			</div>
		);
	}
}

export default ImporterEntitiesCSV;
